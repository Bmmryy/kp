"""FlowETL Web UI — Entry point.

Jalankan dengan:
    python run_server.py

Atau dengan reload otomatis saat development:
    python run_server.py --reload
"""
import os
import sys
import uvicorn

if __name__ == "__main__":
    reload = "--reload" in sys.argv
    host = os.environ.get("FLOWETL_HOST", os.environ.get("HOST", "0.0.0.0"))
    port = int(os.environ.get("FLOWETL_PORT", os.environ.get("PORT", "8000")))
    print("=" * 60)
    print("  FlowETL — Visual Data Integration Platform")
    print(f"  Web UI: http://{host}:{port}")
    print(f"  API Docs: http://{host}:{port}/api/docs")
    print("=" * 60)
    uvicorn.run(
        "server.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
