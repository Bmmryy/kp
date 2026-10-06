"""FlowETL Connector Helper — API endpoints untuk verifikasi & discovery koneksi database.

Menyediakan endpoint untuk:
- Verifikasi koneksi MySQL/PostgreSQL
- List database yang tersedia
- List tabel dalam satu database
"""
from __future__ import annotations

from typing import Any, Dict, List

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
    pw = password or ""
    if db_type in ("mysql", "mysql+pymysql"):
        db_part = f"/{database}" if database else ""
        return f"mysql+pymysql://{user}:{pw}@{host}:{port}{db_part}?charset=utf8mb4"
    elif db_type in ("postgresql", "postgres", "postgresql+psycopg2"):
        db_part = f"/{database}" if database else "/postgres"
        return f"postgresql+psycopg2://{user}:{pw}@{host}:{port}{db_part}"
    else:
        raise ValueError(f"Tipe database tidak didukung: {db_type}")


def _get_engine(db_type: str, host: str, port: int, user: str, password: str, database: str = "") -> sa.Engine:
    url = _build_url(db_type, host, port, user, password, database)
    return sa.create_engine(url, pool_pre_ping=True, pool_timeout=5, connect_args={"connect_timeout": 5})


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ConnectParams(BaseModel):
    type: str
    host: str
    port: int
    user: str
    password: str = ""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/verify")
def verify_connection(params: ConnectParams) -> Dict[str, Any]:
    """Test apakah koneksi ke database bisa dibuat dengan parameter yang diberikan."""
    try:
        engine = _get_engine(params.type, params.host, params.port, params.user, params.password)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return {"ok": True, "message": "Koneksi berhasil!"}
    except OperationalError as e:
        return {"ok": False, "error": str(e.orig or e)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


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
        import csv as _csv
        from pathlib import Path as _Path
        fpath = _Path(path)
        if not fpath.exists():
            raise HTTPException(status_code=404, detail=f"File '{path}' tidak ditemukan.")
        try:
            with open(fpath, "r", encoding="utf-8-sig", errors="replace") as f:
                reader = _csv.reader(f)
                header = next(reader, [])
            return {
                "table": fpath.stem,
                "columns": [{"name": h.strip(), "type": "VARCHAR(255)", "nullable": True, "primary_key": False} for h in header if h.strip()],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # 3. JSON File
    if type in ("json", "jsonl"):
        import json as _json
        from pathlib import Path as _Path
        fpath = _Path(path)
        if not fpath.exists():
            raise HTTPException(status_code=404, detail=f"File '{path}' tidak ditemukan.")
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                if type == "jsonl":
                    first_line = f.readline()
                    sample = _json.loads(first_line) if first_line else {}
                else:
                    data = _json.load(f)
                    sample = data[0] if isinstance(data, list) and data else (data if isinstance(data, dict) else {})
            keys = list(sample.keys()) if isinstance(sample, dict) else []
            return {
                "table": fpath.stem,
                "columns": [{"name": k, "type": "VARCHAR(255)", "nullable": True, "primary_key": False} for k in keys],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # 4. Relational SQL (MySQL / PostgreSQL)
    if not database or not table:
        raise HTTPException(status_code=400, detail="Parameter 'database' dan 'table' wajib diisi.")
    try:
        engine = _get_engine(type, host, port, user, password, database)
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
    except OperationalError as e:
        raise HTTPException(status_code=503, detail=f"Koneksi gagal: {e.orig or e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

