"""
FastAPI server: triggers pipeline runs in a background thread, stores full
reasoning traces in PostgreSQL (persistent run history), serves the React UI.

Run (containerized):  docker compose up --build   →  http://localhost:8000
Run (local):          uvicorn app.main:app --reload --port 8000  (needs a
                      reachable Postgres via DATABASE_URL)
"""
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import db
from .pipeline import run_pipeline
from . import knowledge as kb

FRONTEND = Path(__file__).resolve().parent.parent.parent / "frontend"

app = FastAPI(title="Bottleneck Agent", version="1.1")
_progress: dict[str, dict] = {}  # run_id -> {pct, msg, status}


@app.on_event("startup")
def _startup():
    db.init_db()


def _run_job(run_id: str, top_n: int):
    def cb(pct, msg):
        _progress[run_id] = {"pct": pct, "msg": msg, "status": "running"}
    try:
        result = run_pipeline(top_n=top_n, progress_cb=cb)
        db.update_run(run_id, "done", result)
        _progress[run_id] = {"pct": 100, "msg": "done", "status": "done"}
    except Exception as e:
        db.update_run(run_id, "error", {"error": str(e)})
        _progress[run_id] = {"pct": 100, "msg": str(e), "status": "error"}


@app.post("/api/runs")
def create_run(top_n: int = 5):
    run_id = uuid.uuid4().hex[:12]
    from .crawler import now_iso
    db.insert_run(run_id, now_iso(), "running")
    _progress[run_id] = {"pct": 0, "msg": "starting", "status": "running"}
    threading.Thread(target=_run_job, args=(run_id, top_n), daemon=True).start()
    return {"run_id": run_id}


@app.get("/api/runs")
def list_runs():
    return [{**r, "progress": _progress.get(r["id"])} for r in db.list_runs(50)]


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    row = db.get_run(run_id)
    if not row:
        raise HTTPException(404, "run not found")
    status, result = row
    return {"id": run_id, "status": status,
            "progress": _progress.get(run_id), "result": result}


@app.get("/api/knowledge")
def get_knowledge():
    return {"themes": kb.THEMES, "weights": kb.FACTOR_WEIGHTS,
            "bottleneck_threshold": kb.BOTTLENECK_THRESHOLD}


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
