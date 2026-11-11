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

## Change ownership and proof

- Keep one authoritative owner for each domain rule and each persisted state. UI, CLI, MCP, and provider adapters translate inputs and outputs; they must not reimplement business policy or become competing sources of truth.
- Before changing a contract, trace the input through its owner to every consumer. Update callers, schemas, examples, docs, and regression tests together. Remove superseded paths unless a documented public-compatibility requirement keeps them.
- Keep optional external model/provider integrations behind adapters. Use injected or mocked adapters for deterministic unit tests; label live network/provider checks separately and never describe a mock as live verification.
- Validate untrusted user, model, file, and network data at the boundary. Preserve the product's evidence/provenance rules and reject malformed inputs rather than silently inventing defaults.
- Verify the supported user entry point and at least one relevant failure path. Report exact commands and results; CI on a different commit SHA is not proof for the current change.
- Keep the root README as the user entry point, `docs/README.md` as the documentation map, and focused guides as the owners of detailed contracts. Update links when files move. Do not hand-edit generated output when a source or generator owns it.


## Repository automation rules

- Treat files under `.github/workflows/` as production code. When changing a workflow, inspect the triggered run for the exact commit SHA; a prior green run is not proof for a newer commit.
- Pin third-party GitHub Actions to full 40-character commit SHAs and keep the upstream release tag in a trailing comment. Do not replace a pinned SHA with a floating major-version tag.
- Use the least-privilege `permissions` block. Default to read-only; grant write access only to the specific job that must publish or commit generated output.
- Give every job a finite `timeout-minutes`. Add a clear `concurrency` group for expensive or supersedable work; cancel stale pull-request runs, but do not cancel workflows whose purpose is to publish a completed artifact or evidence.
- Keep workflow logs and uploaded artifacts free of secrets and personal data. Set retention to the shortest period that still serves the evaluation or debugging purpose.
- Rely on the existing Dependabot configuration for action updates, then review release notes and run the affected workflow before considering the update complete.
