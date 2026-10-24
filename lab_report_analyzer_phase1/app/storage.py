import sqlite3, uuid
from pathlib import Path
from datetime import datetime, timezone
from .schemas import ReportAnalysis
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "reports.db"

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS reports (report_id TEXT PRIMARY KEY, filename TEXT NOT NULL, created_at TEXT NOT NULL, analysis_json TEXT NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS reviews (report_id TEXT PRIMARY KEY, status TEXT NOT NULL DEFAULT 'pending', reviewer TEXT, note TEXT, updated_at TEXT NOT NULL, FOREIGN KEY(report_id) REFERENCES reports(report_id))")
    return conn

def save_report(filename: str, analysis: ReportAnalysis) -> dict:
    report_id, created_at = str(uuid.uuid4()), datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        conn.execute("INSERT INTO reports VALUES (?, ?, ?, ?)", (report_id, filename, created_at, analysis.model_dump_json()))
    return {"report_id": report_id, "filename": filename, "created_at": created_at, "analysis": analysis, "stored": True}

def list_reports():
    with connect() as conn:
        rows = conn.execute("SELECT report_id, filename, created_at FROM reports ORDER BY created_at DESC").fetchall()
    return [{"report_id": r[0], "filename": r[1], "created_at": r[2]} for r in rows]

def get_report(report_id: str):
    with connect() as conn:
        row = conn.execute("SELECT report_id, filename, created_at, analysis_json FROM reports WHERE report_id=?", (report_id,)).fetchone()
    if not row: return None
    return {"report_id": row[0], "filename": row[1], "created_at": row[2], "analysis": ReportAnalysis.model_validate_json(row[3])}


def get_review(report_id: str):
    with connect() as conn:
        row = conn.execute("SELECT status, reviewer, note, updated_at FROM reviews WHERE report_id=?", (report_id,)).fetchone()
    return {"report_id": report_id, "status": row[0], "reviewer": row[1], "note": row[2], "updated_at": row[3]} if row else {"report_id": report_id, "status": "pending", "reviewer": None, "note": None, "updated_at": None}


def update_review(report_id: str, status: str, reviewer: str | None = None, note: str | None = None):
    updated_at = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        exists = conn.execute("SELECT 1 FROM reports WHERE report_id=?", (report_id,)).fetchone()
        if not exists:
            return None
        conn.execute("INSERT INTO reviews(report_id,status,reviewer,note,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(report_id) DO UPDATE SET status=excluded.status, reviewer=excluded.reviewer, note=excluded.note, updated_at=excluded.updated_at", (report_id, status, reviewer, note, updated_at))
    return get_review(report_id)
