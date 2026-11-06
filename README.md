# Agent #8 — Autonomous Payment Reconciliation Agent

**200 AI Agents in 200 Days · Agent #8**  
**Category:** Finance Operations / AI Agents / MCP  
**Status:** Working prototype · Local-first · Read-only

An AI-assisted payment reconciliation system that compares three financial data sources—**invoices, payment-gateway transactions, and bank settlements**—to identify matches and surface exceptions for review.

The project combines a deterministic Python reconciliation engine with an LLM investigation assistant. The engine makes the matching decisions and performs the arithmetic. The LLM uses tools exposed by the **Model Context Protocol (MCP)** to retrieve evidence and explain exceptions in plain language.

> **Important:** This is an educational prototype, not production accounting software. It does not initiate payments, issue refunds, alter bank records, post journal entries, or approve financial actions. Human review is required.

---

## Table of contents

- [Why this project exists](#why-this-project-exists)
- [What it does](#what-it-does)
- [How reconciliation works](#how-reconciliation-works)
- [System architecture](#system-architecture)
- [Technology stack](#technology-stack)
- [Repository structure](#repository-structure)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Windows quick start](#windows-quick-start)
  - [Manual Windows setup](#manual-windows-setup)
  - [macOS and Linux setup](#macos-and-linux-setup)
- [Run the application](#run-the-application)
- [Use the dashboard](#use-the-dashboard)
- [Prepare your CSV files](#prepare-your-csv-files)
- [Matching configuration](#matching-configuration)
- [Exception types](#exception-types)
- [AI investigator](#ai-investigator)
- [MCP server and tools](#mcp-server-and-tools)
- [Configuration reference](#configuration-reference)
- [Database and data persistence](#database-and-data-persistence)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Security and privacy](#security-and-privacy)
- [Known limitations](#known-limitations)
- [Potential next steps](#potential-next-steps)
- [Contributing](#contributing)
- [License](#license)

---

## Why this project exists

A business may have several records for what is intended to be the same financial event:

1. An invoice records what a customer is expected to pay.
2. A payment gateway records the payment collected from that customer.
3. A bank statement records the settlement that eventually reaches the business bank account.

These records do not always line up perfectly. References may be inconsistent, settlements may arrive later, fees can change the amount received, duplicate-looking entries may appear, and refunds need separate review.

Manually comparing exports is repetitive and makes it easy to overlook exceptions. This project demonstrates how an AI agent can assist the investigation process while keeping financial calculations deterministic and auditable.

### Core design principle

**Use conventional code for financial matching. Use the LLM for investigation and explanation.**

The model is not trusted to calculate balances, decide that two records match, or silently resolve a discrepancy. It receives the evidence returned by the reconciliation tools and helps an analyst understand what to check next.

---

## What it does

### Data ingestion

- Accepts CSV exports for bank transactions, payment-gateway transactions, and invoices.
- Recognizes common variations in column names.
- Normalizes dates, numeric amounts, currencies, references, and statuses.
- Stores the imported datasets locally in SQLite.
- Includes synthetic sample data for a repeatable demonstration.

### Reconciliation

- Compares invoices against gateway payments.
- Compares gateway transactions against bank settlements.
- Uses references, currency, amount tolerances, and date windows to identify candidate matches.
- Tracks which records have already been allocated during a matching pass.
- Produces match records and a structured exception list.
- Saves each reconciliation run so the latest result can be inspected later.

### Exception investigation

The system can surface issues such as:

- Invoices without a corresponding gateway payment.
- Gateway payments that cannot be allocated to an invoice.
- Gateway transactions without a corresponding bank settlement.
- Amount differences between related records.
- Possible duplicate transactions.
- Refund-like gateway entries that need review.

### AI-assisted analysis

- Connects to a local Ollama model or a hosted OpenAI-compatible API.
- Discovers available MCP tools dynamically.
- Lets the model call those tools to retrieve summaries, transaction records, and exception evidence.
- Returns an explanation with evidence and suggested human checks.
- Keeps the matching engine authoritative: the LLM must not override its results.

### Dashboard

A Streamlit interface provides:

- CSV upload and import.
- Demo-data loading.
- Dataset status.
- Reconciliation controls.
- Summary metrics.
- An exception queue with filters.
- Exception detail inspection.
- Markdown and CSV report downloads.
- An AI investigation chat.

---

## How reconciliation works

The workflow follows the financial record lifecycle:

```text
                 INVOICE
                    |
                    | Match by reference, currency,
                    | amount and date tolerance
                    v
             PAYMENT GATEWAY
                    |
                    | Match by reference / amount,
                    | currency and date tolerance
                    v
              BANK SETTLEMENT
                    |
                    v
          MATCHES + EXCEPTIONS
                    |
                    v
        HUMAN REVIEW / INVESTIGATION
```

### Stage 1 — Normalize the source data

Each uploaded CSV is converted into a common internal structure:

| Field | Purpose |
|---|---|
| `source` | Origin: bank, gateway, or invoice |
| `transaction_id` | Unique identifier from the source, or a generated fallback |
| `reference` | Invoice, payment, order, or transaction reference |
| `date` | Parsed transaction or document date |
| `amount` | Numeric amount rounded to two decimal places |
| `currency` | Uppercase currency code |
| `status` | Normalized status text |
| `description` | Merchant, customer, narration, or other descriptive text |

Column names are matched against a set of common aliases. For example, `transaction_date`, `created_at`, and `value_date` can be recognized as date fields.

An amount column is required. Rows with blank or non-numeric amounts are rejected with a row-level validation message instead of being silently treated as zero.

### Stage 2 — Match invoices to gateway payments

The engine first looks for a reference and currency match. It then checks the configured date and amount tolerances.

If the reference matches but the amount differs, the engine records an amount-mismatch exception rather than treating the records as a successful match.

If an exact reference match is not available, the engine can look for a candidate using amount, currency, and date proximity.

### Stage 3 — Match gateway payments to bank settlements

The engine attempts to associate gateway transactions with bank records using the available reference, amount, currency, and date information.

A settlement can legitimately differ from the gross gateway payment because of fees, batching, reserves, or timing. This prototype does not model every provider's settlement rules, so such cases should be reviewed rather than automatically adjusted.

### Stage 4 — Identify exceptions and save the run

Unmatched or suspicious records are represented as structured exceptions. Each exception includes an ID, type, severity, source, transaction details, and—where applicable—expected amount, actual amount, difference, and related record.

The completed run is saved in SQLite and can be retrieved by the dashboard and MCP tools.

---

## System architecture

```text
                         USER
                          |
                          v
                STREAMLIT DASHBOARD
                 localhost:8501
                          |
              +-----------+-----------+
              |                       |
              v                       v
       CSV / SQLite access       AI chat interface
                                      |
                                      v
                               LLM ORCHESTRATOR
                               src/llm_agent.py
                                      |
                        +-------------+-------------+
                        |                           |
                        v                           v
                 LOCAL OLLAMA                HOSTED API
                 localhost:11434             OpenAI-compatible
                        |                           |
                        +-------------+-------------+
                                      |
                               tool calls / results
                                      |
                                      v
                                MCP CLIENT
                              src/mcp_bridge.py
                                      |
                           Streamable HTTP / MCP
                                      |
                                      v
                                 MCP SERVER
                           localhost:8001/mcp
                              src/mcp_server.py
                                      |
                                      v
                             SERVICE LAYER
                              src/service.py
                                      |
                         +------------+------------+
                         |                         |
                         v                         v
                 RECONCILIATION ENGINE        SQLITE STORAGE
                 src/reconciliation.py        src/storage.py
```

### Component responsibilities

| Component | Responsibility |
|---|---|
| `app.py` | Streamlit dashboard and user interaction |
| `src/reconciliation.py` | Data normalization, matching logic, and exception generation |
| `src/service.py` | Application-level operations shared by the UI and MCP server |
| `src/storage.py` | SQLite persistence for datasets and reconciliation runs |
| `src/mcp_server.py` | Exposes application operations as MCP tools |
| `src/mcp_bridge.py` | Connects the dashboard and agent to the MCP server |
| `src/llm_agent.py` | LLM orchestration and tool-calling loop |
| `sample_data/` | Synthetic CSV files for demonstration |
| `tests/` | Automated tests for reconciliation behavior |

### Why MCP?

The Model Context Protocol provides a standard interface through which an AI application can discover and call external tools.

Instead of embedding every data operation directly inside the model prompt, this project exposes specific capabilities—such as listing exceptions or retrieving transaction evidence—as MCP tools. The LLM can discover the available tools and request structured results when needed.

---

## Technology stack

| Technology | Role |
|---|---|
| Python 3.11+ | Application and reconciliation logic |
| Pandas | CSV processing and tabular data |
| SQLite | Local persistence |
| Streamlit | Web dashboard |
| Model Context Protocol (MCP) | Tool interface between the agent and application |
| OpenAI Python SDK | OpenAI-compatible chat completions and tool calling |
| Ollama | Local model serving |
| python-dotenv | Environment configuration |
| pytest | Automated tests |

---

## Repository structure

```text
autonomous-payment-reconciliation-agent/
|
|-- app.py
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- README.md
|-- setup.bat
|-- start.bat
|-- mcp_config.example.json
|
|-- sample_data/
|   |-- bank.csv
|   |-- gateway.csv
|   |-- invoices.csv
|
|-- src/
|   |-- llm_agent.py
|   |-- mcp_bridge.py
|   |-- mcp_server.py
|   |-- reconciliation.py
|   |-- service.py
|   |-- storage.py
|
|-- tests/
    |-- conftest.py
    |-- test_reconciliation.py
```

---

## Requirements

- Python **3.11 or later** recommended.
- Windows 10/11, macOS, or Linux.
- Internet access for installing Python packages.
- For local AI mode: [Ollama](https://ollama.com/) and enough memory to run your chosen model.
- For hosted AI mode: an API key from an OpenAI-compatible provider.

The reconciliation engine and dashboard data operations do not require a hosted LLM. The AI investigation chat requires a reachable model endpoint.

---

## Installation

### Windows quick start

1. Download or clone this repository.
2. Open the project folder.
3. Run `setup.bat`.
4. Install and start [Ollama](https://ollama.com/) if you want local model inference.
5. Download the default model:

```powershell
ollama pull qwen3:8b
```

6. Run `start.bat`.

The dashboard should be available at:

- **Dashboard:** http://localhost:8501
- **MCP endpoint:** http://127.0.0.1:8001/mcp

If Windows blocks a script, open PowerShell in the project directory and run the commands in the manual setup section.

### Manual Windows setup

Open PowerShell in the repository directory:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

For local AI mode, install Ollama and run:

```powershell
ollama pull qwen3:8b
```

### macOS and Linux setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
cp .env.example .env
```

For local AI mode, install Ollama and run:

```bash
ollama pull qwen3:8b
```

---

## Run the application

The application uses two local processes: the MCP server and the Streamlit dashboard. Start both from the repository root, with the virtual environment activated.

### Terminal 1 — Start the MCP server

**Windows:**

```powershell
.venv\Scripts\Activate.ps1
python src\mcp_server.py
```

**macOS / Linux:**

```bash
source .venv/bin/activate
python src/mcp_server.py
```

The MCP server is configured for Streamable HTTP at:

```text
http://127.0.0.1:8001/mcp
```

Keep this terminal open while using the dashboard.

### Terminal 2 — Start Streamlit

**Windows:**

```powershell
.venv\Scripts\Activate.ps1
streamlit run app.py
```

**macOS / Linux:**

```bash
source .venv/bin/activate
streamlit run app.py
```

Open the local URL printed by Streamlit, usually:

```text
http://localhost:8501
```

---

## Use the dashboard

### 1. Load data

Open the **Data & reconciliation** tab.

You can either:

- Click **Load demo data** to populate all three datasets with the included synthetic records; or
- Upload your own bank, gateway, and invoice CSV exports.

The application displays a preview of uploaded CSV files before import.

Importing a dataset replaces the currently stored dataset for that source. For example, importing a new bank CSV replaces the previous bank dataset in the local database.

### 2. Check dataset status

The dataset status table shows which sources have been imported, their row counts, and the last update time.

A reconciliation run requires all three datasets:

- Bank
- Gateway
- Invoices

### 3. Run reconciliation

Set the matching tolerances:

- **Date tolerance (days):** maximum date distance allowed for a candidate match.
- **Amount tolerance:** maximum absolute amount difference allowed for a candidate match.

Click **Run reconciliation through MCP**.

The dashboard sends the request to the MCP server, which invokes the service layer and deterministic engine. The result is persisted in SQLite.

### 4. Review the summary

The dashboard displays summary metrics for the latest run, including matched pairs, exceptions, severity counts, and bank transaction count.

### 5. Inspect exceptions

Open the **Exceptions** tab.

- Filter by severity.
- Enter an exception type or leave it as `all`.
- Load the exception list.
- Select an exception ID to inspect its full evidence.
- Download the exception list as CSV.
- Download the generated Markdown reconciliation report.

### 6. Ask the AI investigator

Open the **AI investigator** tab and ask a question such as:

- "Summarize the latest reconciliation."
- "Investigate the highest-risk exception."
- "Find the transaction associated with invoice INV-1003."
- "Explain the amount difference and what evidence should be checked."
- "List the unmatched gateway transactions."

The agent should retrieve the relevant records using MCP tools before answering. Its explanation is advisory; verify all financial decisions against the original source records.

---

## Prepare your CSV files

The app accepts CSV files. It attempts to map common column names to a shared internal schema, so your headers do not have to match one exact naming convention.

### Required field

Every dataset must contain an amount column. Recognized examples include:

- `amount`
- `gross_amount`
- `net_amount`
- `total`
- `transaction_amount`
- `amount_inr`
- `amount_usd`
- `paid_amount`
- `invoice_amount`

### Recognized field aliases

| Internal field | Example accepted column names |
|---|---|
| Transaction ID | `transaction_id`, `txn_id`, `payment_id`, `bank_transaction_id`, `gateway_transaction_id`, `invoice_id` |
| Reference | `reference`, `reference_id`, `payment_reference`, `transaction_reference`, `invoice_number`, `invoice_no`, `order_id`, `external_id` |
| Date | `date`, `transaction_date`, `created_at`, `timestamp`, `paid_at`, `settlement_date`, `invoice_date`, `value_date` |
| Amount | `amount`, `gross_amount`, `net_amount`, `total`, `transaction_amount`, `paid_amount`, `invoice_amount` |
| Currency | `currency`, `currency_code`, `ccy` |
| Status | `status`, `payment_status`, `transaction_status`, `state` |
| Description | `description`, `narration`, `memo`, `merchant`, `vendor`, `customer`, `details`, `counterparty` |

If a transaction ID is not supplied, the normalizer generates a fallback ID for that imported dataset.

### Example bank CSV

```csv
bank_transaction_id,reference,transaction_date,amount,currency,status,narration
BK-001,GW-001,2026-10-02,125.00,USD,settled,Example merchant payout
```

### Example gateway CSV

```csv
gateway_transaction_id,invoice_number,created_at,amount,currency,status,merchant
GW-001,INV-1001,2026-10-01,125.00,USD,succeeded,Example merchant
```

### Example invoice CSV

```csv
invoice_id,invoice_number,invoice_date,amount,currency,status,customer
INV-1001,INV-1001,2026-10-01,125.00,USD,issued,Example customer
```

### Data preparation advice

- Export dates in a consistent, parseable format such as `YYYY-MM-DD`.
- Use numeric amounts. Currency symbols and common thousands separators are stripped during normalization.
- Use consistent currency codes across the three datasets.
- Preserve invoice numbers and gateway references wherever possible.
- Do not combine different currencies into one reconciliation batch unless you have implemented explicit FX conversion rules.
- Check whether bank amounts are gross or net of processing fees before interpreting a difference.
- Remove unnecessary personal data and mask account numbers before using real exports.

---

## Matching configuration

The dashboard exposes two matching parameters.

| Parameter | Default | Meaning |
|---|---:|---|
| Date tolerance | 3 days | Maximum number of days between candidate records |
| Amount tolerance | 0.01 | Maximum absolute difference between candidate amounts, in the dataset's currency units |

The matching engine uses the reference and currency when available. It can also consider amount and date proximity when a direct reference match is unavailable.

### Important interpretation notes

- A match is a candidate association based on the configured rules, not proof that the underlying payment is correct.
- The amount tolerance is an absolute amount, not a percentage.
- The engine does not perform foreign-exchange conversion.
- The prototype does not automatically calculate gateway fees, rolling reserves, chargebacks, or payout batching.
- A bank payout can represent several gateway transactions in real payment systems. This prototype's matching approach is not a full many-to-one settlement allocator.
- A missing date can limit date-based matching; validate source exports before relying on results.

---

## Exception types

The reconciliation engine can generate the following exception categories. Exact results depend on the imported data and matching tolerances.

| Exception type | Meaning | Suggested human check |
|---|---|---|
| `unpaid_invoice` | No corresponding gateway payment was found for an invoice | Check payment status, invoice reference, and gateway export date range |
| `invoice_payment_amount_mismatch` | A matching reference was found, but the invoice and gateway amounts differ | Compare invoice total, discounts, tax, partial payments, and gateway amount |
| `unallocated_payment` | A gateway payment was not allocated to an invoice | Search for a missing invoice, alternate reference, or duplicate import |
| `unmatched_bank_transaction` | A bank record could not be associated with a gateway transaction | Check payout references, settlement timing, fees, and bank narration |
| `gateway_bank_amount_mismatch` | Related gateway and bank records have different amounts | Check processing fees, reserves, adjustments, and payout configuration |
| `possible_duplicate` | A repeated transaction ID or reference/amount/date combination was detected | Verify against the original provider export and bank statement |
| `refund_review` | A refund-like gateway entry was detected | Verify the original payment, refund status, and corresponding bank movement |

Severity is assigned by the engine. It is a triage signal, not a final fraud determination.

---

## AI investigator

The AI investigator is designed to answer questions about the latest reconciliation by using tools rather than guessing from the prompt.

### Supported model modes

**Local mode — Ollama**

- Runs inference through the Ollama OpenAI-compatible endpoint.
- Default base URL: `http://127.0.0.1:11434/v1`
- Default model: `qwen3:8b`
- Requires Ollama to be installed and the model to be downloaded.

**Cloud mode — OpenAI-compatible API**

- Uses a hosted chat-completions endpoint.
- Requires a valid API key.
- The provider must support the tool/function-calling format used by the OpenAI Python SDK.
- Configure the base URL and model in the dashboard sidebar.

### Agent behavior

The agent's system instructions require it to:

1. Retrieve relevant reconciliation data through MCP tools.
2. Use engine-produced values for amounts, differences, and exception types.
3. Distinguish confirmed records from possible explanations.
4. Explain what a human analyst should verify.
5. Avoid claiming that it has initiated payments, refunds, or ledger changes.
6. Redact account-like sensitive values if they appear in retrieved records.

The tool-calling loop has a maximum number of rounds to prevent unbounded tool use.

### Example investigation prompt

```text
Investigate the highest-severity exception in the latest run.
Retrieve its full evidence, explain what is known,
identify plausible causes without treating them as facts,
and list the checks a finance analyst should perform.
```

The model's output is an analytical aid. It is not an approval, accounting entry, or substitute for source-system verification.

---

## MCP server and tools

The MCP server uses Streamable HTTP. The default endpoint is:

```text
http://127.0.0.1:8001/mcp
```

The server exposes seven tools:

| Tool | Inputs | Purpose |
|---|---|---|
| `run_reconciliation` | `date_tolerance_days`, `amount_tolerance` | Run matching and save a new reconciliation run |
| `get_reconciliation_summary` | None | Retrieve summary metrics for the latest run |
| `list_reconciliation_exceptions` | `severity`, `exception_type` | List and filter exceptions |
| `investigate_exception` | `exception_id` | Retrieve full evidence for one exception |
| `search_transactions` | `query`, `limit` | Search imported bank, gateway, and invoice records |
| `generate_reconciliation_report` | None | Generate a Markdown report from the latest run |
| `get_import_status` | None | Return imported dataset names and row counts |

An example client configuration is provided in `mcp_config.example.json`. Adjust it to the conventions of the MCP client you are using.

---

## Configuration reference

Copy `.env.example` to `.env` and edit values as required.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_PATH` | `data/reconciliation.db` | Local SQLite database path |
| `MCP_URL` | `http://127.0.0.1:8001/mcp` | MCP endpoint used by the dashboard and agent |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434/v1` | Ollama OpenAI-compatible endpoint |
| `OLLAMA_MODEL` | `qwen3:8b` | Default local model |
| `LLM_BASE_URL` | Provider-specific | Optional hosted API base URL |
| `LLM_MODEL` | Provider-specific | Optional hosted model name |
| `LLM_API_KEY` | Not set | Optional hosted API credential |

Example:

```dotenv
DATABASE_PATH=data/reconciliation.db
MCP_URL=http://127.0.0.1:8001/mcp

OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
OLLAMA_MODEL=qwen3:8b

# Optional hosted API configuration
# LLM_BASE_URL=https://api.openai.com/v1
# LLM_MODEL=your-model-name
# LLM_API_KEY=your-api-key
```

Do not commit your real `.env` file or paste API keys into source files.

---

## Database and data persistence

The application uses SQLite. By default, the database is created at:

```text
data/reconciliation.db
```

The database contains two logical data groups:

- **Datasets:** the latest imported payload for each source—bank, gateway, and invoices.
- **Reconciliation runs:** saved outputs from previous runs, including summary and exception data.

Importing a dataset replaces the stored dataset for that source. Running reconciliation creates a new run record. The dashboard reads the latest saved run.

To start with a clean environment, stop the application and remove the local database file after making any backup you need. The database may contain sensitive financial information.

---

## Testing

Activate the virtual environment and run:

```bash
pytest -q
```

To run Python syntax compilation checks:

```bash
python -m py_compile app.py src/*.py tests/*.py
```

The test suite covers core reconciliation behavior using isolated test database configuration. Tests should use synthetic data and must not connect to production financial systems.

---

## Troubleshooting

### Dashboard opens, but MCP connection fails

1. Confirm the MCP server process is running.
2. Confirm the dashboard and MCP server use the same `MCP_URL`.
3. Check that port `8001` is not already occupied.
4. Review the MCP server terminal for startup errors.

### AI investigator cannot connect to Ollama

1. Confirm Ollama is installed and running.
2. Check the configured Ollama URL.
3. Confirm the model is downloaded:

```bash
ollama list
```

4. If needed, download the default model:

```bash
ollama pull qwen3:8b
```

5. Try a smaller model if your computer does not have enough memory.

### Cloud API mode returns an authentication error

- Check that the API key is valid.
- Confirm the selected provider's base URL.
- Confirm the model name is available to your account.
- Ensure the provider supports tool/function calling.

### CSV import reports a missing amount column

Rename the amount field to a recognized alias such as `amount`, `total`, or `transaction_amount`.

### CSV import reports invalid amounts

Check for blank cells, text values, or unsupported formatting in the amount column. The normalizer strips common currency symbols and spaces, but source data should still be cleaned.

### No matches are found

- Check that references are consistent between systems.
- Check that the currency codes match.
- Increase the date tolerance only if the business process justifies it.
- Check whether one source uses gross values while another uses net settlements.
- Confirm that the correct date range was exported.

---

## Security and privacy

Financial exports can contain confidential business and customer information. Treat imported data as sensitive.

- Use synthetic or masked data for development and demonstrations.
- Keep the database and `.env` file out of version control.
- Do not expose the MCP server or Streamlit dashboard publicly without adding authentication, authorization, network restrictions, and appropriate deployment controls.
- The default configuration binds services to loopback addresses for local use.
- In local Ollama mode, prompts and retrieved evidence are sent to the local Ollama service.
- In cloud mode, prompts and transaction evidence used by the agent may be transmitted to the selected model provider. Review that provider's data handling terms and your organization's policies first.
- Restrict access to the computer and local database.
- Back up the database securely if you need to retain reconciliation history.
- Review all exceptions against original source systems before taking action.

This repository does not implement enterprise-grade access control, audit logging, encryption-at-rest management, or production secrets management.

---

## Known limitations

This project is a prototype and intentionally has a limited scope.

- CSV is the supported import format; there are no direct bank or payment-provider integrations.
- Matching is rule-based and does not learn from analyst decisions.
- Foreign-exchange conversion is not implemented.
- Complex many-to-one or one-to-many settlement allocation is not fully modeled.
- Provider-specific fee, reserve, chargeback, and payout rules are not comprehensively implemented.
- There is no user authentication or multi-tenant access model.
- The local database stores imported records and runs but is not a hardened financial data warehouse.
- The LLM can produce incorrect explanations; tool evidence and source records must be checked.
- No payment, refund, journal-entry, or ledger-write operation is available.

---

## Potential next steps

Possible extensions for future iterations:

- Add configurable mapping profiles for different bank and gateway CSV formats.
- Add many-to-one payout allocation and provider-specific settlement fee models.
- Add currency-aware reconciliation with explicit exchange-rate sources.
- Add a review workflow with analyst decisions, notes, and an immutable audit trail.
- Add role-based access control and encrypted secret management.
- Add scheduled imports and reconciliation runs.
- Add more test fixtures for edge cases, partial payments, reversals, and duplicate batches.
- Add deployment packaging and CI checks for supported operating systems.
- Add integrations with accounting platforms after implementing appropriate authorization and audit controls.

These are proposed improvements, not current features.

---

## Contributing

Contributions are welcome, especially improvements to matching accuracy, CSV normalization, test coverage, and documentation.

A useful contribution workflow:

1. Fork the repository.
2. Create a focused feature branch.
3. Add or update tests for behavior changes.
4. Run `pytest -q` and the syntax check.
5. Submit a pull request describing the change and its limitations.

Do not use real customer or bank data in issues, test fixtures, or pull requests.

---

## License

No license file is currently included. Unless a license is added, the repository should be treated as having **no explicit open-source reuse license**.

---

## Project

Built as **Agent #8** in the **200 AI Agents in 200 Days** challenge.

**Repository:** https://github.com/yerageracharan/autonomous-payment-reconciliation-agent

If you find the project useful, consider starring the repository and sharing feedback.
