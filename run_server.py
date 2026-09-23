"""FlowETL Web UI — Entry point.

Jalankan dengan:
    python run_server.py

Atau dengan reload otomatis saat development:
    python run_server.py --reload
"""
import sys
import uvicorn

if __name__ == "__main__":
    reload = "--reload" in sys.argv
    print("=" * 60)
    print("  FlowETL — Visual Data Integration Platform")
    print("  Web UI: http://localhost:8000")
    print("  API Docs: http://localhost:8000/api/docs")
    print("=" * 60)
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=reload,
        log_level="info",
    )
