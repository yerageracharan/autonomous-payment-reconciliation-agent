import pandas as pd
import pytest

from reconciliation import normalize_frame, run_reconciliation


def sample_frames():
    bank = pd.DataFrame([
        {"bank_transaction_id": "B1", "reference": "G1", "transaction_date": "2026-01-02", "amount": 100, "currency": "USD"},
        {"bank_transaction_id": "B2", "reference": "G2", "transaction_date": "2026-01-04", "amount": 49, "currency": "USD"},
    ])
    gateway = pd.DataFrame([
        {"gateway_transaction_id": "G1", "invoice_number": "I1", "created_at": "2026-01-01", "amount": 100, "currency": "USD", "status": "succeeded"},
        {"gateway_transaction_id": "G2", "invoice_number": "I2", "created_at": "2026-01-03", "amount": 50, "currency": "USD", "status": "succeeded"},
    ])
    invoices = pd.DataFrame([
        {"invoice_id": "I1", "invoice_number": "I1", "invoice_date": "2026-01-01", "amount": 100, "currency": "USD"},
        {"invoice_id": "I2", "invoice_number": "I2", "invoice_date": "2026-01-01", "amount": 50, "currency": "USD"},
        {"invoice_id": "I3", "invoice_number": "I3", "invoice_date": "2026-01-01", "amount": 25, "currency": "USD"},
    ])
    return bank, gateway, invoices


def test_normalize_maps_common_columns():
    frame = pd.DataFrame([{"txn_id": "A1", "transaction_date": "2026-01-01", "total": "$12.50"}])
    normalized = normalize_frame(frame, "bank")
    assert normalized.loc[0, "transaction_id"] == "A1"
    assert normalized.loc[0, "amount"] == 12.5


def test_reconciliation_finds_matches_mismatches_and_unpaid_invoice():
    bank, gateway, invoices = sample_frames()
    result = run_reconciliation(bank, gateway, invoices)
    assert result["summary"]["invoices"] == 3
    assert any(row["type"] == "unpaid_invoice" for row in result["exceptions"])
    assert any(row["type"] == "bank_settlement_amount_mismatch" for row in result["exceptions"])
    assert result["summary"]["matched_pairs"] >= 2


def test_missing_amount_column_is_rejected():
    with pytest.raises(ValueError, match="amount column"):
        normalize_frame(pd.DataFrame([{"reference": "x"}]), "bank")


def test_refund_does_not_mark_invoice_as_paid():
    bank = pd.DataFrame(columns=["bank_transaction_id", "reference", "transaction_date", "amount", "currency"])
    gateway = pd.DataFrame([{
        "gateway_transaction_id": "G-REFUND", "invoice_number": "I-REFUND",
        "created_at": "2026-01-05", "amount": -75, "currency": "USD", "status": "refunded"
    }])
    invoices = pd.DataFrame([{
        "invoice_id": "I-REFUND", "invoice_number": "I-REFUND",
        "invoice_date": "2026-01-01", "amount": 75, "currency": "USD"
    }])
    result = run_reconciliation(bank, gateway, invoices)
    kinds = [item["type"] for item in result["exceptions"]]
    assert "unpaid_invoice" in kinds
    assert "refund_review" in kinds
    assert "invoice_payment_amount_mismatch" not in kinds


def test_duplicate_group_is_reported_once():
    bank = pd.DataFrame([
        {"bank_transaction_id": "B1", "reference": "G1", "transaction_date": "2026-01-02", "amount": 100, "currency": "USD"},
        {"bank_transaction_id": "B2", "reference": "G1", "transaction_date": "2026-01-02", "amount": 100, "currency": "USD"},
    ])
    gateway = pd.DataFrame([{"gateway_transaction_id": "G1", "invoice_number": "I1", "created_at": "2026-01-01", "amount": 100, "currency": "USD"}])
    invoices = pd.DataFrame([{"invoice_id": "I1", "invoice_number": "I1", "invoice_date": "2026-01-01", "amount": 100, "currency": "USD"}])
    result = run_reconciliation(bank, gateway, invoices)
    duplicate_rows = [item for item in result["exceptions"] if item["type"] == "possible_duplicate"]
    assert len(duplicate_rows) == 1
    assert duplicate_rows[0]["duplicate_count"] == 2


def test_service_can_import_run_and_report_locally(tmp_path, monkeypatch):
    import storage
    import service
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "reconciliation.db")
    storage.init_db()
    bank, gateway, invoices = sample_frames()
    for name, frame in [("bank", bank), ("gateway", gateway), ("invoices", invoices)]:
        records = frame.astype(object).where(pd.notna(frame), None).to_dict(orient="records")
        service.import_dataset(name, records)
    result = service.run_and_save()
    assert service.get_summary()["run_id"] == result["run_id"]
    assert "Payment Reconciliation Report" in service.report_markdown()
    assert service.list_exceptions()["count"] > 0


@pytest.mark.parametrize("date_tolerance", [-1, 1.5, True, "3"])
def test_date_tolerance_requires_a_non_negative_integer(date_tolerance):
    bank, gateway, invoices = sample_frames()
    with pytest.raises(ValueError, match="date_tolerance_days"):
        run_reconciliation(bank, gateway, invoices, date_tolerance_days=date_tolerance)


@pytest.mark.parametrize("amount_tolerance", [-0.01, float("nan"), float("inf"), True, "0.01"])
def test_amount_tolerance_requires_a_finite_non_negative_number(amount_tolerance):
    bank, gateway, invoices = sample_frames()
    with pytest.raises(ValueError, match="amount_tolerance"):
        run_reconciliation(bank, gateway, invoices, amount_tolerance=amount_tolerance)


def test_search_transactions_validates_inputs_and_caps_results(monkeypatch):
    import service

    rows = [{"transaction_id": f"TX-{i}", "description": "target settlement"} for i in range(150)]
    monkeypatch.setattr(service.storage, "get_dataset", lambda _source: rows)
    with pytest.raises(TypeError, match="query must be a string"):
        service.search_transactions(None)
    with pytest.raises(TypeError, match="limit must be an integer"):
        service.search_transactions("target", True)
    with pytest.raises(ValueError, match="at least 1"):
        service.search_transactions("target", 0)
    result = service.search_transactions("target", 1000)
    assert result["count"] == 100
    assert len(result["records"]) == 100


def test_search_transactions_blank_query_is_empty(monkeypatch):
    import service

    monkeypatch.setattr(service.storage, "get_dataset", lambda _source: pytest.fail("must not read datasets"))
    assert service.search_transactions("   ") == {"count": 0, "records": []}
