# Agent #8 — Autonomous Payment Reconciliation Agent

**200 AI Agents in 200 Days · Agent #8**

A local-first AI-assisted reconciliation workspace for matching invoices, payment-gateway transactions, and bank settlements. It combines a deterministic financial matching engine with a compulsory LLM investigation agent connected through the Model Context Protocol (MCP).

> **Prototype scope:** read-only reconciliation and investigation. It does not move money, issue refunds, alter bank records, post journal entries, or make payment decisions.

## Features

- Import bank statements, payment-gateway exports, and invoices from CSV.
- Normalize common column names, dates, currencies, and monetary amounts.
- Match invoice → gateway and gateway → bank records using references, amount tolerances, and configurable date windows.
- Flag unpaid invoices, unallocated payments, unmatched settlements, amount discrepancies, possible duplicates, and refund-like records.
- Store imported datasets and reconciliation run history in local SQLite.
- Expose reconciliation operations as MCP tools over Streamable HTTP.
- Connect an LLM to MCP tools using dynamic tool discovery and function calling.
- Switch between a hosted OpenAI-compatible API and a local open-source model served by Ollama.
- Use a Streamlit dashboard at `http://localhost:8501`.

## Architecture

```text
Browser: http://localhost:8501
        |
        v
Streamlit dashboard ---- LLM orchestrator
        |                       |
        |                       +---- Hosted OpenAI-compatible API
        |                       |
        |                       +---- Local Ollama API :11434
        |                                  |
        +----------- MCP client <----------+
                         |
                         v
             MCP server :8001/mcp
                         |
                         v
             deterministic Python engine
                         |
                         v
                 local SQLite database
```

**Important design boundary:** the Python engine performs matching and arithmetic. The LLM investigates exceptions, retrieves evidence, and explains the engine's results through MCP. The model must not invent or override match decisions.

## Requirements

- Python 3.11 recommended.
- Windows 10/11 (scripts included); macOS/Linux can use the equivalent commands below.
- [Ollama](https://ollama.com/) for local inference, or an API key for a hosted OpenAI-compatible model.
- Internet access for package installation, model download, and hosted API calls.

## Windows quick start

1. Extract or clone this repository.
2. Double-click `setup.bat`.
3. Download a local model:

```powershell
ollama pull qwen3:8b
```

4. Double-click `start.bat`.

The dashboard opens at `http://localhost:8501`. The MCP server listens at `http://127.0.0.1:8001/mcp`.

## Manual setup (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
ollama pull qwen3:8b
```

Start the MCP server in terminal 1:

```powershell
.venv\Scripts\activate
python src\mcp_server.py
```

Start the dashboard in terminal 2:

```powershell
.venv\Scripts\activate
streamlit run app.py
```

## macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
ollama pull qwen3:8b
```

Run `python src/mcp_server.py` in one terminal and `streamlit run app.py` in another.

## Configure cloud API mode

The sidebar lets you switch from Ollama to Cloud API. Enter an OpenAI-compatible base URL, model name, and API key. OpenAI's standard endpoint is prefilled. Credentials are entered in the dashboard and are not committed to this repository.

You can also set the optional values in `.env`:

```dotenv
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini
LLM_API_KEY=your_key_here
```

## MCP tools

The MCP server exposes:

| Tool | Purpose |
|---|---|
| `run_reconciliation` | Run deterministic matching and persist a run |
| `get_reconciliation_summary` | Read latest run counts |
| `list_reconciliation_exceptions` | Filter exceptions by severity/type |
| `investigate_exception` | Retrieve full evidence for an exception |
| `search_transactions` | Search imported transaction records |
| `generate_reconciliation_report` | Generate a Markdown report |
| `get_import_status` | Check imported datasets and row counts |

Example MCP client configuration is in `mcp_config.example.json`.

## Demo workflow

1. Open the dashboard.
2. Select **Load demo data**.
3. Select **Run reconciliation through MCP**.
4. Review the exception queue.
5. Open **AI investigator** and ask: “Investigate the highest-risk exception and explain the evidence I should verify.”

The sample records intentionally include discrepancies, unmatched items, a refund, and a possible duplicate so the workflow has cases to investigate.

## Tests

```bash
pytest -q
```

## Data and security notes

- Imported CSVs and the SQLite database stay on the local machine by default.
- In local Ollama mode, model inference runs on the local Ollama service.
- In cloud mode, prompts and transaction evidence returned by MCP may be sent to the selected model provider. Use synthetic or masked data unless your organisation has approved the provider for real financial information.
- Do not commit `.env`, API keys, production bank exports, or the local database.
- This is an educational prototype, not a regulated accounting system or production financial control. Human review is required before acting on any exception.

## Stack

Python · Streamlit · Pandas · SQLite · Model Context Protocol · OpenAI-compatible APIs · Ollama · pytest

---

Built as **Agent #8** in the **200 AI Agents in 200 Days** challenge.
