# Agent Instructions

These instructions apply across Autonomous Payment Reconciliation Agent.

## Product and financial-safety invariants

- Reconciliation output is an analysis of imported records, not permission to initiate, reverse, settle, or transfer money.
- Never invent transactions, references, invoice IDs, currencies, dates, amounts, or settlement status.
- Every match or exception must be traceable to the source records and the matching rule that produced it.
- Keep tolerances explicit, finite, bounded, and applied consistently; do not silently coerce malformed amounts or dates.
- Use synthetic data in tests and examples. Do not commit real bank statements, customer records, payment credentials, or account identifiers.

## Repository map

- `src/`: import normalization, reconciliation engine, persistence, service layer, and reports.
- `app.py`: Streamlit interface.
- `sample_data/`: synthetic demonstration records only.
- `tests/`: deterministic reconciliation and service tests.
- `docs/`: setup and workflow documentation.

## Working rules

- Read the matching logic, source normalization, exception model, and tests before changing reconciliation behavior.
- Never make a match imply a financial action or final accounting decision.
- Keep source identifiers and exception provenance intact.
- Reject invalid tolerances (negative, non-finite, boolean, or incorrectly typed).
- Use the existing database/persistence boundary; do not add a competing owner of reconciliation state.
- Do not store or print actual bank/customer records in fixtures, snapshots, logs, or screenshots.
- Document currency, sign, date parsing, and tolerance semantics explicitly.

## Validation

```bash
python -m pytest -q
```
