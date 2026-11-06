"""SQLite persistence for uploaded datasets and reconciliation runs."""
from __future__ import annotations
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("DATABASE_PATH", "data/reconciliation.db"))


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS datasets (
            source TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS reconciliation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")


def save_dataset(source: str, records: list[dict[str, Any]]) -> None:
    if source not in {"bank", "gateway", "invoices"}:
        raise ValueError("source must be bank, gateway, or invoices")
    payload = json.dumps(records, default=str)
    with _connect() as conn:
        conn.execute("""INSERT INTO datasets(source,payload_json,row_count,updated_at)
            VALUES(?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(source) DO UPDATE SET payload_json=excluded.payload_json,
            row_count=excluded.row_count, updated_at=CURRENT_TIMESTAMP""",
            (source, payload, len(records)))


def get_dataset(source: str) -> list[dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT payload_json FROM datasets WHERE source=?", (source,)).fetchone()
    return json.loads(row["payload_json"]) if row else []


def dataset_status() -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("SELECT source,row_count,updated_at FROM datasets ORDER BY source").fetchall()
    return [dict(r) for r in rows]


def save_run(payload: dict[str, Any]) -> None:
    with _connect() as conn:
        conn.execute("INSERT INTO reconciliation_runs(run_id,payload_json) VALUES(?,?)",
                     (payload["run_id"], json.dumps(payload, default=str)))


def get_latest_run() -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT payload_json FROM reconciliation_runs ORDER BY id DESC LIMIT 1").fetchone()
    return json.loads(row["payload_json"]) if row else None


def clear_all() -> None:
    """Delete local imported data and run history. This is intentionally explicit."""
    with _connect() as conn:
        conn.execute("DELETE FROM datasets")
        conn.execute("DELETE FROM reconciliation_runs")
