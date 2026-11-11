# Contributing

Thanks for improving Autonomous Payment Reconciliation Agent. The agent analyzes imported financial records and surfaces possible matches and exceptions. It must never perform payment operations.

## Before changing code

- Search existing issues and commits for overlapping work.
- Open an issue before changes to reconciliation rules, data schema, matching tolerances, or architecture. Include the use case, expected behavior, examples, alternatives, and validation plan.
- For bugs, provide synthetic input rows, exact command, expected match/exception, actual output, and redacted logs.
- Keep data normalization, matching logic, reporting, and UI changes focused.

## Development setup

The current CI workflow tests Python 3.11 and 3.12.

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Validation

```bash
python -m pytest -q
```

For normalization/matching changes, cover duplicate references, amount/date tolerances, currency differences, refunds, missing records, invalid values, and many-to-one candidates. Keep tests deterministic and use synthetic records only.

## Engineering expectations

- Preserve source-row evidence in generated exceptions.
- Never claim that a transaction is settled solely because a candidate match exists.
- Do not initiate, update, reverse, or send payments.
- Keep tolerances bounded and explain their units and effect in reports.
- Use safe handling for identifiers and personal/financial fields; do not log raw imported records unnecessarily.
- Update docs and sample data when schema, normalization, or matching behavior changes.

## Pull requests

Use the repository PR template. Include the problem, financial-data impact, exact test commands/results, and any matching limitation. Link an issue for non-trivial changes.

## Security

Follow [SECURITY.md](SECURITY.md) for private disclosure. Never commit real financial records or credentials.
