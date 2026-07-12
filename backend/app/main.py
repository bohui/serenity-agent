"""
FastAPI server: triggers pipeline runs in a background thread, stores full
reasoning traces in SQLite, serves the React UI.

Run:  uvicorn app.main:app --reload --port 8000   (from backend/)
Then open http://localhost:8000
"""
import json
import os
import sqlite3
import tempfile
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .pipeline import run_pipeline
from . import knowledge as kb

DB_PATH = Path(os.environ.get("BOTTLENECK_DB",
                              Path(__file__).resolve().parent.parent / "runs.db"))
FRONTEND = Path(__file__).resolve().parent.parent.parent / "frontend"

app = FastAPI(title="Bottleneck Agent", version="1.0")
_lock = threading.Lock()
_progress: dict[str, dict] = {}  # run_id -> {pct, msg, status}

_SCHEMA = """CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY, created TEXT, status TEXT, result TEXT)"""


def _db():
    global DB_PATH
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(_SCHEMA)
        return conn
    except sqlite3.OperationalError:
        # e.g. network mounts that don't support SQLite locking
        DB_PATH = Path(tempfile.gettempdir()) / "bottleneck_runs.db"
        conn = sqlite3.connect(DB_PATH)
        conn.execute(_SCHEMA)
        return conn


def _run_job(run_id: str, top_n: int):
    def cb(pct, msg):
        _progress[run_id] = {"pct": pct, "msg": msg, "status": "running"}
    try:
        result = run_pipeline(top_n=top_n, progress_cb=cb)
        with _lock, _db() as conn:
            conn.execute("UPDATE runs SET status=?, result=? WHERE id=?",
                         ("done", json.dumps(result), run_id))
        _progress[run_id] = {"pct": 100, "msg": "done", "status": "done"}
    except Exception as e:
        with _lock, _db() as conn:
            conn.execute("UPDATE runs SET status=?, result=? WHERE id=?",
                         ("error", json.dumps({"error": str(e)}), run_id))
        _progress[run_id] = {"pct": 100, "msg": str(e), "status": "error"}


@app.post("/api/runs")
def create_run(top_n: int = 5):
    run_id = uuid.uuid4().hex[:12]
    from .crawler import now_iso
    with _lock, _db() as conn:
        conn.execute("INSERT INTO runs VALUES (?,?,?,?)",
                     (run_id, now_iso(), "running", None))
    _progress[run_id] = {"pct": 0, "msg": "starting", "status": "running"}
    threading.Thread(target=_run_job, args=(run_id, top_n), daemon=True).start()
    return {"run_id": run_id}


@app.get("/api/runs")
def list_runs():
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, created, status FROM runs ORDER BY created DESC LIMIT 50").fetchall()
    return [{"id": r[0], "created": r[1], "status": r[2],
             "progress": _progress.get(r[0])} for r in rows]


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    with _db() as conn:
        row = conn.execute("SELECT status, result FROM runs WHERE id=?",
                           (run_id,)).fetchone()
    if not row:
        raise HTTPException(404, "run not found")
    status, result = row
    return {"id": run_id, "status": status,
            "progress": _progress.get(run_id),
            "result": json.loads(result) if result else None}


@app.get("/api/knowledge")
def get_knowledge():
    return {"themes": kb.THEMES, "weights": kb.FACTOR_WEIGHTS,
            "bottleneck_threshold": kb.BOTTLENECK_THRESHOLD}


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
