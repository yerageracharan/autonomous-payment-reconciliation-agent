"""Application service layer shared by the dashboard and MCP tools."""
from __future__ import annotations
from typing import Any
import pandas as pd

from reconciliation import run_reconciliation
import storage


def import_dataset(source: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    storage.save_dataset(source, records)
    return {"source": source, "rows_imported": len(records), "status": "saved locally"}


def run_and_save(date_tolerance_days: int = 3, amount_tolerance: float = 0.01) -> dict[str, Any]:
    datasets = {name: pd.DataFrame(storage.get_dataset(name)) for name in ["bank", "gateway", "invoices"]}
    missing = [name for name, frame in datasets.items() if frame.empty]
    if missing:
        raise ValueError("Missing datasets: " + ", ".join(missing))
    result = run_reconciliation(
        datasets["bank"], datasets["gateway"], datasets["invoices"],
        date_tolerance_days=date_tolerance_days, amount_tolerance=amount_tolerance
    )
    storage.save_run(result)
    return result


def get_summary() -> dict[str, Any]:
    run = storage.get_latest_run()
    if not run:
        return {"status": "no_run", "message": "No reconciliation has been run yet. Import all three datasets and run reconciliation."}
    return {"run_id": run["run_id"], "created_at": run["created_at"], **run["summary"]}


def list_exceptions(severity: str = "all", exception_type: str = "all") -> dict[str, Any]:
    run = storage.get_latest_run()
    if not run:
        return {"status": "no_run", "exceptions": []}
    rows = run["exceptions"]
    if severity != "all":
        rows = [x for x in rows if x["severity"] == severity]
    if exception_type != "all":
        rows = [x for x in rows if x["type"] == exception_type]
    compact = [{k: v for k, v in row.items() if k not in {"record", "related_record"}} for row in rows]
    return {"run_id": run["run_id"], "count": len(compact), "exceptions": compact}


def investigate_exception(exception_id: str) -> dict[str, Any]:
    run = storage.get_latest_run()
    if not run:
        return {"status": "no_run"}
    for row in run["exceptions"]:
        if row["exception_id"].lower() == exception_id.lower():
            return row
    return {"error": f"Exception {exception_id} was not found in the latest run."}


def search_transactions(query: str, limit: int = 20) -> dict[str, Any]:
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise TypeError("limit must be an integer")
    if limit < 1:
        raise ValueError("limit must be at least 1")
    needle = query.strip().lower()
    if not needle:
        return {"count": 0, "records": []}
    result_limit = min(limit, 100)
    found = []
    for source in ["bank", "gateway", "invoices"]:
        for row in storage.get_dataset(source):
            blob = " ".join(str(v) for v in row.values()).lower()
            if needle in blob:
                found.append({"source": source, **row})
                if len(found) >= result_limit:
                    return {"count": len(found), "records": found}
    return {"count": len(found), "records": found}


def report_markdown() -> str:
    run = storage.get_latest_run()
    if not run:
        return "No reconciliation run exists yet."
    summary = run["summary"]
    lines = ["# Payment Reconciliation Report", "", f"Run: {run['run_id']}", f"Created: {run['created_at']}", "", "## Summary", ""]
    lines.extend([f"- {key.replace('_', ' ').title()}: {value}" for key, value in summary.items()])
    lines.extend(["", "## Exceptions", ""])
    for item in run["exceptions"]:
        lines.append(f"- **{item['exception_id']} | {item['severity'].upper()} | {item['type']}** — {item['message']} (reference: {item['reference'] or 'none'})")
    lines.extend(["", "## Controls", "", "This report is generated from deterministic rules. Exceptions require human review; this tool does not initiate payments, reversals, or ledger changes."])
    return "\n".join(lines)
