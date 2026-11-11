"""Deterministic, explainable payment reconciliation engine.

This module deliberately does not use an LLM to decide whether payments match.
Matching and amount calculations are deterministic; an LLM can investigate the
resulting evidence through the MCP tools exposed by mcp_server.py.
"""
from __future__ import annotations

from typing import Any
import math
import re
import uuid
import pandas as pd

COLUMN_ALIASES = {
    "transaction_id": ["transaction_id", "txn_id", "id", "payment_id", "bank_transaction_id", "gateway_transaction_id", "invoice_id"],
    "reference": ["reference", "reference_id", "payment_reference", "transaction_reference", "invoice_number", "invoice_no", "order_id", "external_id", "related_transaction_id"],
    "date": ["date", "transaction_date", "created_at", "timestamp", "paid_at", "settlement_date", "invoice_date", "value_date"],
    "amount": ["amount", "gross_amount", "net_amount", "total", "transaction_amount", "amount_inr", "amount_usd", "paid_amount", "invoice_amount"],
    "currency": ["currency", "currency_code", "ccy"],
    "status": ["status", "payment_status", "transaction_status", "state"],
    "description": ["description", "narration", "memo", "merchant", "vendor", "customer", "details", "counterparty"],
}


def _clean_col(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _find_column(columns: list[str], aliases: list[str]) -> str | None:
    lookup = {_clean_col(c): c for c in columns}
    for alias in aliases:
        if alias in lookup:
            return lookup[alias]
    for col in columns:
        cleaned = _clean_col(col)
        if any(cleaned.endswith("_" + a) or cleaned.startswith(a + "_") for a in aliases):
            return col
    return None


def normalize_frame(frame: pd.DataFrame, source: str) -> pd.DataFrame:
    """Map common CSV headers into a consistent schema and normalize values."""
    if frame is None or frame.empty:
        return pd.DataFrame(columns=["source", "transaction_id", "reference", "date", "amount", "currency", "status", "description"])
    raw = frame.copy()
    raw.columns = [str(c).strip() for c in raw.columns]
    selected = {key: _find_column(list(raw.columns), aliases) for key, aliases in COLUMN_ALIASES.items()}
    if selected["amount"] is None:
        raise ValueError(f"The {source} CSV needs an amount column. Recognized names include: amount, total, transaction_amount, paid_amount.")
    out = pd.DataFrame(index=raw.index)
    for key, original in selected.items():
        out[key] = raw[original] if original else None
    out["source"] = source
    out["transaction_id"] = out["transaction_id"].fillna("").astype(str).str.strip()
    out["reference"] = out["reference"].fillna("").astype(str).str.strip()
    out["currency"] = out["currency"].fillna("UNKNOWN").astype(str).str.upper().str.strip()
    out["status"] = out["status"].fillna("unknown").astype(str).str.lower().str.strip()
    out["description"] = out["description"].fillna("").astype(str).str.strip()
    out["date"] = pd.to_datetime(out["date"], errors="coerce", utc=True)
    out["amount"] = pd.to_numeric(out["amount"].astype(str).str.replace(r"[,$₹€£ ]", "", regex=True), errors="coerce").round(2)
    if out["amount"].isna().any():
        bad_rows = [int(i) + 2 for i in out.index[out["amount"].isna()][:10]]
        raise ValueError(f"The {source} CSV has blank or non-numeric amounts on row(s): {bad_rows}.")
    out = out.reset_index(drop=True)
    for i in out.index:
        if not out.at[i, "transaction_id"]:
            out.at[i, "transaction_id"] = f"{source[:3].upper()}-{i + 1:04d}"
    return out


def _date_distance_days(a: Any, b: Any) -> int | None:
    if pd.isna(a) or pd.isna(b):
        return None
    return abs((a.date() - b.date()).days)


def _same_currency(a: Any, b: Any) -> bool:
    return str(a or "USD").upper() == str(b or "USD").upper()


def _same_reference(a: Any, b: Any) -> bool:
    aa, bb = str(a or "").strip().lower(), str(b or "").strip().lower()
    return bool(aa and bb and aa == bb)


def _as_record(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    for key, value in list(item.items()):
        if pd.isna(value):
            item[key] = None
        elif isinstance(value, pd.Timestamp):
            item[key] = value.isoformat()
    if "amount" in item and item["amount"] is not None:
        item["amount"] = round(float(item["amount"]), 2)
    return item


def _exception(kind: str, severity: str, source: str, row: pd.Series, message: str,
               expected: float | None = None, actual: float | None = None,
               related: dict[str, Any] | None = None) -> dict[str, Any]:
    delta = None if expected is None or actual is None else round(float(actual) - float(expected), 2)
    return {
        "exception_id": "EX-" + uuid.uuid4().hex[:8].upper(),
        "type": kind, "severity": severity, "source": source,
        "transaction_id": str(row.get("transaction_id", "")),
        "reference": str(row.get("reference", "")),
        "date": None if pd.isna(row.get("date")) else row.get("date").isoformat(),
        "currency": str(row.get("currency", "USD")),
        "expected_amount": expected, "actual_amount": actual, "difference": delta,
        "message": message, "record": _as_record(row), "related_record": related,
    }


def _find_candidate(source_row: pd.Series, candidates: pd.DataFrame, used: set[int],
                    date_tolerance_days: int, amount_tolerance: float) -> tuple[int | None, str | None, pd.Series | None]:
    available = candidates.loc[~candidates.index.isin(used)]
    if available.empty:
        return None, None, None
    ref_matches = available[
        available.apply(lambda r: _same_reference(source_row["reference"], r["reference"])
                        and _same_currency(source_row["currency"], r["currency"]), axis=1)
    ] if source_row["reference"] else available.iloc[0:0]
    if not ref_matches.empty:
        ranked = []
        for idx, candidate in ref_matches.iterrows():
            days = _date_distance_days(source_row["date"], candidate["date"])
            ranked.append((999 if days is None else days, idx, candidate))
        ranked.sort(key=lambda x: x[0])
        days, idx, candidate = ranked[0]
        if days <= date_tolerance_days or days == 999:
            if abs(float(source_row["amount"]) - float(candidate["amount"])) <= amount_tolerance:
                return int(idx), "reference_amount_date", candidate
            return int(idx), "reference_amount_mismatch", candidate
    amount_matches = available[
        available.apply(lambda r: _same_currency(source_row["currency"], r["currency"])
                        and pd.notna(source_row["amount"]) and pd.notna(r["amount"])
                        and abs(float(source_row["amount"]) - float(r["amount"])) <= amount_tolerance, axis=1)
    ]
    ranked = []
    for idx, candidate in amount_matches.iterrows():
        days = _date_distance_days(source_row["date"], candidate["date"])
        if days is not None and days <= date_tolerance_days:
            same_ref_bonus = 0 if _same_reference(source_row["reference"], candidate["reference"]) else 1
            ranked.append((same_ref_bonus, days, idx, candidate))
    if ranked:
        ranked.sort(key=lambda x: (x[0], x[1]))
        _, _, idx, candidate = ranked[0]
        return int(idx), "amount_date", candidate
    return None, None, None


def _duplicates(frame: pd.DataFrame, source: str) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    groups: dict[tuple[Any, ...], list[pd.Series]] = {}
    for _, row in frame.iterrows():
        transaction_id = str(row.get("transaction_id", "")).strip()
        reference = str(row.get("reference", "")).strip()
        if transaction_id and (frame["transaction_id"].astype(str) == transaction_id).sum() > 1:
            key = ("transaction_id", transaction_id)
        elif reference and len(frame[(frame["reference"].astype(str) == reference)
                                     & (frame["amount"] == row["amount"])
                                     & (frame["date"] == row["date"])
                                     & (frame["currency"] == row["currency"])]) > 1:
            key = ("reference_amount_date", reference, row["amount"], str(row["date"]), row["currency"])
        else:
            continue
        groups.setdefault(key, []).append(row)
    results = []
    for key, rows in groups.items():
        row = rows[0]
        item = _exception("possible_duplicate", "high", source, row,
                          "Repeated transaction identifier or repeated reference/amount/date combination.",
                          actual=None if pd.isna(row["amount"]) else float(row["amount"]))
        item["duplicate_count"] = len(rows)
        item["duplicate_transaction_ids"] = [str(x["transaction_id"]) for x in rows]
        results.append(item)
    return results


def run_reconciliation(bank: pd.DataFrame, gateway: pd.DataFrame, invoices: pd.DataFrame,
                       date_tolerance_days: int = 3, amount_tolerance: float = 0.01) -> dict[str, Any]:
    """Reconcile invoice→gateway and gateway→bank records; return matches and exceptions."""
    if (
        isinstance(date_tolerance_days, bool)
        or not isinstance(date_tolerance_days, int)
        or date_tolerance_days < 0
    ):
        raise ValueError("date_tolerance_days must be a non-negative integer")
    if (
        isinstance(amount_tolerance, bool)
        or not isinstance(amount_tolerance, (int, float))
        or not math.isfinite(amount_tolerance)
        or amount_tolerance < 0
    ):
        raise ValueError("amount_tolerance must be a finite, non-negative number")
    amount_tolerance = float(amount_tolerance)
    bank_n = normalize_frame(bank, "bank")
    gateway_n = normalize_frame(gateway, "gateway")
    invoice_n = normalize_frame(invoices, "invoice")
    exceptions: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []
    refund_mask = gateway_n["status"].str.contains("refund", na=False) | (gateway_n["amount"].fillna(0) < 0)
    payment_gateway_n = gateway_n.loc[~refund_mask]
    used_gateway: set[int] = set()
    for _, invoice in invoice_n.iterrows():
        idx, reason, candidate = _find_candidate(invoice, payment_gateway_n, used_gateway, date_tolerance_days, amount_tolerance)
        if idx is None:
            exceptions.append(_exception("unpaid_invoice", "medium", "invoice", invoice,
                                         "No corresponding payment-gateway transaction was found.",
                                         expected=None if pd.isna(invoice["amount"]) else float(invoice["amount"])))
            continue
        used_gateway.add(idx)
        if reason == "reference_amount_mismatch":
            exceptions.append(_exception("invoice_payment_amount_mismatch", "high", "gateway", candidate,
                                         "Gateway payment reference matches the invoice, but the amount differs.",
                                         expected=float(invoice["amount"]), actual=float(candidate["amount"]),
                                         related=_as_record(invoice)))
        else:
            matches.append({"stage": "invoice_to_gateway", "match_method": reason,
                            "invoice": _as_record(invoice), "gateway": _as_record(candidate)})
    for idx, gateway_row in gateway_n.iterrows():
        is_refund = bool(refund_mask.loc[idx])
        if idx not in used_gateway and not is_refund:
            exceptions.append(_exception("unallocated_payment", "medium", "gateway", gateway_row,
                                         "Gateway transaction does not match an invoice.",
                                         actual=None if pd.isna(gateway_row["amount"]) else float(gateway_row["amount"])))
    used_bank: set[int] = set()
    for _, gateway_row in gateway_n.iterrows():
        if str(gateway_row["status"]).find("refund") >= 0 or (pd.notna(gateway_row["amount"]) and float(gateway_row["amount"]) < 0):
            exceptions.append(_exception("refund_review", "medium", "gateway", gateway_row,
                                         "Refund-like gateway entry found; verify its original payment and bank settlement."))
            continue
        bank_match_row = gateway_row.copy()
        bank_match_row["reference"] = gateway_row["transaction_id"]
        idx, reason, candidate = _find_candidate(bank_match_row, bank_n, used_bank, date_tolerance_days, amount_tolerance)
        if idx is None:
            exceptions.append(_exception("gateway_not_in_bank", "high", "gateway", gateway_row,
                                         "Gateway payment was not found in bank settlement records.",
                                         expected=None if pd.isna(gateway_row["amount"]) else float(gateway_row["amount"])))
            continue
        used_bank.add(idx)
        if reason == "reference_amount_mismatch":
            exceptions.append(_exception("bank_settlement_amount_mismatch", "high", "bank", candidate,
                                         "Bank reference matches the gateway transaction, but the settled amount differs.",
                                         expected=float(gateway_row["amount"]), actual=float(candidate["amount"]),
                                         related=_as_record(gateway_row)))
        else:
            matches.append({"stage": "gateway_to_bank", "match_method": reason,
                            "gateway": _as_record(gateway_row), "bank": _as_record(candidate)})
    for idx, bank_row in bank_n.iterrows():
        if idx not in used_bank:
            exceptions.append(_exception("bank_entry_unmatched", "medium", "bank", bank_row,
                                         "Bank settlement entry has no matched gateway transaction.",
                                         actual=None if pd.isna(bank_row["amount"]) else float(bank_row["amount"])))
    exceptions.extend(_duplicates(bank_n, "bank"))
    exceptions.extend(_duplicates(gateway_n, "gateway"))
    exceptions.extend(_duplicates(invoice_n, "invoice"))
    counts = {
        "bank_transactions": int(len(bank_n)), "gateway_transactions": int(len(gateway_n)),
        "invoices": int(len(invoice_n)), "matched_pairs": int(len(matches)),
        "exceptions": int(len(exceptions)),
        "high_severity": sum(1 for e in exceptions if e["severity"] == "high"),
        "medium_severity": sum(1 for e in exceptions if e["severity"] == "medium"),
    }
    return {
        "run_id": "REC-" + uuid.uuid4().hex[:10].upper(),
        "created_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "tolerances": {"date_tolerance_days": date_tolerance_days, "amount_tolerance": amount_tolerance},
        "summary": counts, "matches": matches, "exceptions": exceptions,
    }
