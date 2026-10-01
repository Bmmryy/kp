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
def list_tables(type: str, host: str, port: int, user: str, password: str = "", database: str = "") -> Dict[str, List[str]]:
    """List semua tabel di satu database."""
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
