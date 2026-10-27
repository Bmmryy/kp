"""FlowETL Connector Helper — API endpoints untuk verifikasi & discovery koneksi database.

Menyediakan endpoint untuk:
- Verifikasi koneksi MySQL/PostgreSQL
- List database yang tersedia
- List tabel dalam satu database
"""
from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import quote_plus

import sqlalchemy as sa
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import inspect as sa_inspect, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

router = APIRouter(prefix="/api/connector", tags=["connector"])


# ---------------------------------------------------------------------------
# Helpers: URL builder
# ---------------------------------------------------------------------------

def _build_url(db_type: str, host: str, port: int, user: str, password: str, database: str = "") -> str:
    """Build SQLAlchemy connection URL dari parameter koneksi."""
    u = quote_plus(user.strip()) if user else ""
    raw_pw = password.strip() if (password and db_type in ("oracle", "oracle+oracledb")) else (password or "")
    pw = f":{quote_plus(raw_pw)}" if raw_pw else ""
    if db_type in ("mysql", "mysql+pymysql"):
        db_part = f"/{database}" if database else ""
        return f"mysql+pymysql://{u}{pw}@{host}:{port}{db_part}?charset=utf8mb4"
    elif db_type in ("postgresql", "postgres", "postgresql+psycopg2"):
        db_part = f"/{database}" if database else "/postgres"
        return f"postgresql+psycopg2://{u}{pw}@{host}:{port}{db_part}"
    elif db_type in ("oracle", "oracle+oracledb"):
        # Untuk Oracle: database parameter = schema/user, service_name selalu FREEPDB1
        # Gunakan service_name tetap FREEPDB1 agar koneksi tidak putus saat ganti schema
        return f"oracle+oracledb://{u}{pw}@{host}:{port}/?service_name=FREEPDB1"
    else:
        raise ValueError(f"Tipe database tidak didukung: {db_type}")


def _get_engine(db_type: str, host: str, port: int, user: str, password: str, database: str = "") -> sa.Engine:
    url = _build_url(db_type, host, port, user, password, database)
    connect_args = {}
    if db_type not in ("oracle", "oracle+oracledb"):
        connect_args["connect_timeout"] = 5
    return sa.create_engine(url, pool_pre_ping=True, pool_timeout=5, connect_args=connect_args)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ConnectParams(BaseModel):
    type: str
    host: str
    port: int
    user: str
    password: str = ""


def _format_connection_error(e: Exception) -> str:
    import re
    msg = str(getattr(e, "orig", None) or e)
    if "Operation not permitted" in msg or "Errno 1" in msg:
        return "Gagal terhubung ke database: Izin koneksi jaringan socket dibatasi oleh sistem. Pastikan port database terbuka dan server dapat diakses."
    if "Can't connect to MySQL server" in msg or "2003" in msg or "2002" in msg or "Connection refused" in msg:
        return "Tidak dapat terhubung ke server database. Pastikan layanan database aktif dan host/port sesuai (contoh: 127.0.0.1:3306)."
    if "ORA-12541" in msg or "DPY-6005" in msg or "DPY-6000" in msg:
        return "Tidak dapat terhubung ke listener Oracle. Pastikan Oracle database aktif dan port 1521 terbuka."
    if "ORA-01017" in msg:
        return "Autentikasi Oracle gagal: username atau password salah."
    if "ORA-12514" in msg:
        return "Service name Oracle tidak ditemukan. Pastikan nama service/database benar (contoh: FREEPDB1 atau XEPDB1)."
    if "Access denied for user" in msg or "1045" in msg or "password authentication failed" in msg:
        return "Autentikasi gagal: username atau password database salah."
    if "Unknown database" in msg or "1049" in msg or ('database "' in msg and 'does not exist' in msg):
        return "Database tidak ditemukan di server SQL."

    m = re.search(r'\(\d+,\s*["\'](.*?)["\']\)', msg)
    if m:
        msg = m.group(1)
    msg = re.sub(r'\[SQL:.*?\]', '', msg)
    msg = re.sub(r'\(Background on this error.*?\)', '', msg)
    return msg.strip() or "Koneksi ke database gagal."


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/verify")
def verify_connection(params: ConnectParams) -> Dict[str, Any]:
    """Test apakah koneksi ke database bisa dibuat dengan parameter yang diberikan."""
    try:
        engine = _get_engine(params.type, params.host, params.port, params.user, params.password)
        with engine.connect() as conn:
            ping_sql = "SELECT 1 FROM DUAL" if params.type in ("oracle", "oracle+oracledb") else "SELECT 1"
            conn.execute(text(ping_sql))
        engine.dispose()
        return {"ok": True, "message": "Koneksi berhasil!"}
    except OperationalError as e:
        return {"ok": False, "error": _format_connection_error(e)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        return {"ok": False, "error": _format_connection_error(e)}
    except Exception as e:
        return {"ok": False, "error": _format_connection_error(e)}


@router.get("/databases")
def list_databases(type: str, host: str, port: int, user: str, password: str = "") -> Dict[str, List[str]]:
    """List semua database yang tersedia di server SQL (setelah verifikasi berhasil)."""
    try:
        engine = _get_engine(type, host, port, user, password)
        with engine.connect() as conn:
            if type in ("mysql", "mysql+pymysql"):
                result = conn.execute(text("SHOW DATABASES"))
                # Filter system databases
                system_dbs = {"information_schema", "performance_schema", "mysql", "sys"}
                dbs = [row[0] for row in result if row[0].lower() not in system_dbs]
            elif type in ("postgresql", "postgres", "postgresql+psycopg2"):
                result = conn.execute(
                    text("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname")
                )
                system_dbs = {"postgres", "template0", "template1"}
                dbs = [row[0] for row in result if row[0].lower() not in system_dbs]
            elif type in ("oracle", "oracle+oracledb"):
                try:
                    # Tampilkan semua schema yang memiliki tabel + schema user yang login
                    result = conn.execute(
                        text("""
                            SELECT DISTINCT owner FROM all_tables
                            WHERE owner NOT IN (
                                'SYS','AUDSYS','SYSTEM','OUTLN','DIP','ORACLE_OCM','DBSNMP',
                                'APPQOSSYS','DBSFWUSER','GGSYS','ANONYMOUS','CTXSYS','DVSYS',
                                'DVF','GSMADMIN_INTERNAL','MDSYS','OLAPSYS','XDB','WMSYS',
                                'GSMCATUSER','MDDATA','SYSBACKUP','REMOTE_SCHEDULER_AGENT',
                                'PDBADMIN','GSMROOTUSER','SI_INFORMTN_SCHEMA','DGGRID',
                                'LBACSYS','ORDS_METADATA','ORDS_PUBLIC_USER','ORDS_PUBLIC_USER2',
                                'ORDS_PUBLIC_USER3','SYS$UMF','SYSRAC','XS$NULL'
                            )
                            ORDER BY owner
                        """)
                    )
                    dbs = [row[0] for row in result]
                except Exception:
                    dbs = []
                # Selalu sertakan schema milik user yang login jika belum ada
                if user.upper() not in dbs:
                    dbs.insert(0, user.upper())
            else:
                raise HTTPException(status_code=400, detail=f"Tipe tidak didukung: {type}")
        engine.dispose()
        return {"databases": dbs}
    except HTTPException:
        raise
    except OperationalError as e:
        raise HTTPException(status_code=503, detail=f"Koneksi gagal: {e.orig or e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables")
def list_tables(type: str, host: str = "localhost", port: int = 3306, user: str = "root", password: str = "", database: str = "", path: str = "") -> Dict[str, List[str]]:
    """List semua tabel di satu database (SQL atau SQLite)."""
    if type == "sqlite":
        db_path = path or database
        if not db_path:
            raise HTTPException(status_code=400, detail="Path file SQLite wajib diisi.")
        try:
            engine = sa.create_engine(f"sqlite:///{db_path}")
            insp = sa_inspect(engine)
            tables = insp.get_table_names()
            engine.dispose()
            return {"tables": tables}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    if not database:
        raise HTTPException(status_code=400, detail="Parameter 'database' wajib diisi.")
    try:
        engine = _get_engine(type, host, port, user, password, database)
        if type in ("oracle", "oracle+oracledb"):
            # Untuk Oracle: gunakan query langsung ke all_tables berdasarkan owner/schema
            schema = database.upper() if database else user.upper()
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT table_name FROM all_tables WHERE owner = :schema ORDER BY table_name"),
                    {"schema": schema}
                )
                tables = [row[0] for row in result]
        else:
            insp = sa_inspect(engine)
            tables = insp.get_table_names()
        engine.dispose()
        return {"tables": tables}
    except OperationalError as e:
        raise HTTPException(status_code=503, detail=f"Koneksi gagal: {e.orig or e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/columns")
def list_columns(
    type: str,
    host: str = "localhost",
    port: int = 3306,
    user: str = "root",
    password: str = "",
    database: str = "",
    table: str = "",
    path: str = "",
) -> Dict[str, Any]:
    """List semua kolom beserta tipe data untuk satu tabel atau file."""
    # 1. SQLite File
    if type == "sqlite":
        db_path = path or database
        if not db_path:
            raise HTTPException(status_code=400, detail="Path SQLite wajib diisi.")
        if not table:
            raise HTTPException(status_code=400, detail="Nama tabel wajib diisi.")
        try:
            engine = sa.create_engine(f"sqlite:///{db_path}")
            insp = sa_inspect(engine)
            col_infos = insp.get_columns(table)
            engine.dispose()
            return {
                "table": table,
                "columns": [
                    {
                        "name": c["name"],
                        "type": str(c["type"]),
                        "nullable": bool(c.get("nullable", True)),
                        "primary_key": bool(c.get("primary_key", False)),
                    }
                    for c in col_infos
                ],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # 2. CSV File
    if type == "csv":
        from pathlib import Path as _Path
        fpath = _Path(path)
        if not fpath.exists():
            raise HTTPException(status_code=404, detail=f"File '{path}' tidak ditemukan.")
        try:
            from app.connectors.base import ConnectorConfig
            from app.connectors.csv import CSVSource
            cfg = ConnectorConfig(name="tmp", connector_type="csv", options={"path": str(fpath)})
            src = CSVSource(cfg)
            schema = src.get_schema(fpath.stem)
            return {
                "table": schema.name,
                "columns": [
                    {
                        "name": col.name,
                        "type": col.data_type.value,
                        "nullable": col.nullable,
                        "primary_key": col.primary_key,
                    }
                    for col in schema.columns
                ],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # 3. JSON / JSONL File
    if type in ("json", "jsonl"):
        from pathlib import Path as _Path
        fpath = _Path(path)
        if not fpath.exists():
            raise HTTPException(status_code=404, detail=f"File '{path}' tidak ditemukan.")
        try:
            from app.connectors.base import ConnectorConfig
            from app.connectors.json import JSONSource
            cfg = ConnectorConfig(name="tmp", connector_type=type, options={"path": str(fpath), "format": type})
            src = JSONSource(cfg)
            schema = src.get_schema(fpath.stem)
            return {
                "table": schema.name,
                "columns": [
                    {
                        "name": col.name,
                        "type": col.data_type.value,
                        "nullable": col.nullable,
                        "primary_key": col.primary_key,
                    }
                    for col in schema.columns
                ],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # 4. Relational SQL (MySQL / PostgreSQL / Oracle)
    if not database or not table:
        raise HTTPException(status_code=400, detail="Parameter 'database' dan 'table' wajib diisi.")
    try:
        engine = _get_engine(type, host, port, user, password, database)
        insp = sa_inspect(engine)
        if type in ("oracle", "oracle+oracledb"):
            col_infos = insp.get_columns(table, schema=database.upper()) or insp.get_columns(table)
        else:
            col_infos = insp.get_columns(table)
        engine.dispose()
        return {
            "table": table,
            "columns": [
                {
                    "name": c["name"],
                    "type": str(c["type"]),
                    "nullable": bool(c.get("nullable", True)),
                    "primary_key": bool(c.get("primary_key", False)),
                }
                for c in col_infos
            ],
        }
    except OperationalError as e:
        raise HTTPException(status_code=503, detail=f"Koneksi gagal: {e.orig or e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

