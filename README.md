# Agent #8 — Autonomous Payment Reconciliation Agent

**200 AI Agents in 200 Days · Agent #8**

Hello! 👋 Welcome to this little payment-reconciliation workshop.

This project helps compare three kinds of financial records:

1. **Invoices** — what a customer was asked to pay.
2. **Payment gateway records** — what the payment service says it collected.
3. **Bank records** — what actually appeared in the bank statement.

The program checks whether these records appear to belong together. If something looks unusual, it puts it in an exception list. An AI assistant can then help explain the evidence.

The goal is simple: let Python do the careful counting, and let AI help with the detective work.

> **A small but important note:** This is a learning prototype. It is read-only. It does not send money, issue refunds, change bank records, or write accounting entries. Please keep a human in charge of financial decisions. The computer is clever, but it has not earned its accountant badge yet.

---

# 1. What will we build?

By the end, you should have a small local web application with four areas:

- **Data & reconciliation:** upload CSV files or load the included demo files, then run matching.
- **Exceptions:** inspect payments or invoices that need attention.
- **AI investigator:** ask questions about the results in normal language.
- **Architecture:** see how the pieces connect.

The app runs on your own computer.

| Part | What it does |
|---|---|
| Python reconciliation engine | Compares records using fixed rules |
| SQLite database | Saves imported data and reconciliation results on your computer |
| MCP server | Makes the app's functions available as tools |
| LLM agent | Calls those tools and explains the evidence |
| Streamlit | Gives you the web dashboard |

You do not need to understand every line of code before starting. First, let's make the little machine run.

# 2. Before starting — a tiny checklist

You will need:

- A Windows, macOS, or Linux computer.
- Python 3.11 or newer.
- Internet access for installing packages.
- About 10–15 minutes for setup, depending on your internet connection.
- Optional: Ollama, if you want to run the AI model locally.

**What is Ollama?** It is a program that lets you run certain AI models on your own computer. Think of it as giving the AI a small room in your computer to work in.

If you do not want to set up a local model, you can use a compatible hosted API instead. That option needs an API key.

# 3. Download the project

Open the project repository:

[GitHub — Autonomous Payment Reconciliation Agent](https://github.com/yerageracharan/autonomous-payment-reconciliation-agent)

You have two ways to get the files.

### Option A — Download ZIP (easiest)

1. Open the GitHub link above.
2. Click the green **Code** button.
3. Choose **Download ZIP**.
4. Find the downloaded ZIP file.
5. Right-click it and choose **Extract All**.
6. Open the extracted project folder.

### Option B — Use Git

If Git is installed, open a terminal and run:

```bash
git clone https://github.com/yerageracharan/autonomous-payment-reconciliation-agent.git
cd autonomous-payment-reconciliation-agent
```

If you are new to Git, Option A is perfectly fine. No developer points are deducted. Probably.

# 4. Install Python dependencies

Dependencies are the extra Python packages this project needs. We install them inside a virtual environment so they do not interfere with other Python projects.

## Windows

1. Open the project folder.
2. Click the address bar in File Explorer.
3. Type `powershell` and press Enter.
4. In the PowerShell window, run:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If your computer has a newer Python version and `py -3.11` is unavailable, try:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**What just happened?**

- `.venv` created a private environment for this project.
- `Activate.ps1` switched your terminal into that environment.
- `pip install -r requirements.txt` installed the packages listed by the project.

You should see `(.venv)` near the beginning of your terminal prompt. That is your little sign that the environment is active.

## macOS or Linux

Open Terminal in the project folder and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**If installation fails:** copy the complete error message and investigate that specific error. Do not randomly install twenty packages from the internet. That is how a peaceful afternoon becomes a documentary.

# 5. Create your local settings file

The project includes a template named `.env.example`.

Make a copy and name the copy `.env`.

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

For the default local setup, you can leave the settings as they are.

The file contains settings such as:

| Setting | Meaning |
|---|---|
| `DATABASE_PATH` | Where the local database is saved |
| `MCP_URL` | Where the dashboard connects to the MCP server |
| `OLLAMA_BASE_URL` | Address of the local Ollama service |
| `OLLAMA_MODEL` | Name of the model to use |

Keep your real `.env` file private. Do not upload API keys or secrets to GitHub.

# 6. Set up the AI model (optional, but useful)

The project is configured to use Ollama by default.

1. Install Ollama from [ollama.com](https://ollama.com/).
2. Start Ollama.
3. Open a new terminal.
4. Download the default model:

```bash
ollama pull qwen3:8b
```

This model download can take a while. It is a fairly large file, so please be kind to your internet connection. Maybe offer it some tea.

To check whether the model is installed:

```bash
ollama list
```

You should see `qwen3:8b` in the list.

**Computer struggling?** A model of this size needs a reasonable amount of memory. If your computer cannot run it comfortably, choose a smaller model supported by your Ollama installation and enter that model name in the app's sidebar.

### Do I need Ollama to use the reconciliation engine?

No. Ollama is for the AI investigation chat. The CSV import and deterministic reconciliation features are separate from the LLM. You can still explore the project without configuring an AI model.

# 7. Start the application

This project has two parts that need to run:

1. The **MCP server** — provides the tools.
2. The **Streamlit dashboard** — the web page you interact with.

Keep both terminal windows open while using the application.

## Terminal 1 — Start the MCP server

Open a terminal in the project folder and activate the virtual environment.

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

The server is intended to listen at:

```text
http://127.0.0.1:8001/mcp
```

Leave this terminal running. Do not close it just because it looks quiet. Servers are often quiet when they are doing their job.

## Terminal 2 — Start the dashboard

Open a **second** terminal in the same project folder.

Activate the virtual environment again.

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

Streamlit will print a local address. Open this in your browser:

[http://localhost:8501](http://localhost:8501)

There it is — your dashboard.

If the browser does not open automatically, copy the URL from the terminal and paste it into your browser.

# 8. Your first run — use the demo data

Let's not begin with real bank statements. That would be an unnecessarily exciting first day.

The repository includes sample CSV files. They contain fictional transactions designed to demonstrate matches and exceptions.

1. Open the **Data & reconciliation** tab.
2. Click **Load demo data**.
3. Wait for the success message.
4. Check the **Dataset status** section.
5. You should see records for bank, gateway, and invoices.
6. Find the **Run matching** section.
7. Leave the default tolerances for your first run:
   - Date tolerance: **3 days**
   - Amount tolerance: **0.01**
8. Click **Run reconciliation through MCP**.
9. Wait for the result.

The dashboard should display a summary of the run.

Congratulations. You have completed your first reconciliation. The sample data is fictional, but the detective work is real.

# 9. Understand the results

Before opening the AI chat, let's understand what the program is checking.

Imagine this is the same payment appearing in three places:

| Source | Reference | Amount |
|---|---|---:|
| Invoice | INV-1001 | $125.00 |
| Gateway | INV-1001 | $125.00 |
| Bank | GW-001 | $125.00 |

The engine tries to connect these records using their references, amounts, currencies, and dates.

If the values line up within the configured tolerances, the engine can record a match.

But what if the invoice says $85 and the gateway says $80? That is a difference of $5. The program should flag it for review instead of pretending everything is perfect.

## What are the tolerances?

**Date tolerance** is the maximum number of days allowed between two candidate records.

For example, with a 3-day tolerance, a payment dated 3 October may be considered against a related record dated 1 October.

**Amount tolerance** is the maximum allowed difference between two amounts.

For example, with a tolerance of 0.01:

- Difference of $0.00 — within tolerance.
- Difference of $0.01 — within tolerance.
- Difference of $0.50 — outside tolerance.

These are matching settings, not permission to ignore real financial differences. Choose them based on the business process.

# 10. Explore the Exceptions tab

Click **Exceptions**.

This is the list of records that need a closer look.

You can:

1. Choose a severity filter.
2. Enter an exception type, or leave it as `all`.
3. Click **Load exceptions**.
4. Select an exception ID.
5. Click **Investigate selected exception**.
6. Read the evidence returned by the system.

You can also download the exceptions as a CSV file and download the reconciliation report as Markdown.

### Common exception types

| Exception | In simple words |
|---|---|
| `unpaid_invoice` | An invoice could not be matched to a gateway payment |
| `invoice_payment_amount_mismatch` | The invoice and payment amounts differ |
| `unallocated_payment` | A gateway payment could not be matched to an invoice |
| `unmatched_bank_transaction` | A bank transaction could not be matched to a gateway record |
| `gateway_bank_amount_mismatch` | The gateway and bank amounts differ |
| `possible_duplicate` | Two or more records look suspiciously similar |
| `refund_review` | A refund-like gateway entry needs checking |

A high-severity label does not automatically mean fraud. It means the record deserves attention. Please do not accuse a transaction of crimes before checking the evidence.

# 11. Talk to the AI investigator

Now for the AI part.

Open the **AI investigator** tab.

Make sure:

- The MCP server is still running.
- Your chosen model service is running.
- The model name and provider settings are correct.

Try asking:

```text
Summarize the latest reconciliation in simple language.
```

Then try:

```text
Investigate the highest-risk exception.
Explain what the records show and what a human should verify.
```

Or:

```text
Find the transaction associated with invoice INV-1003.
```

### What does the AI actually do?

The AI does not independently open your bank account or make financial decisions.

Instead:

1. You ask a question.
2. The LLM decides which available tool could help.
3. It calls the MCP server.
4. The MCP server retrieves information from the application.
5. The LLM reads the returned evidence.
6. It explains the result in normal language.

The matching engine remains responsible for the calculations. The AI is the assistant, not the financial judge.

# 12. Using your own CSV files

Once the demo works, you can try your own files.

The dashboard accepts three CSV files:

- A bank statement.
- A payment-gateway export.
- An invoice export.

Each file must have an amount column. The program recognizes common column names such as `amount`, `total`, `paid_amount`, and `invoice_amount`.

It also tries to recognize common names for:

- Transaction ID
- Reference
- Date
- Currency
- Status
- Description

### A simple example

**Bank CSV:**

```csv
bank_transaction_id,reference,transaction_date,amount,currency,status,narration
BK-001,GW-001,2026-10-02,125.00,USD,settled,Example merchant payout
```

**Gateway CSV:**

```csv
gateway_transaction_id,invoice_number,created_at,amount,currency,status,merchant
GW-001,INV-1001,2026-10-01,125.00,USD,succeeded,Example merchant
```

**Invoice CSV:**

```csv
invoice_id,invoice_number,invoice_date,amount,currency,status,customer
INV-1001,INV-1001,2026-10-01,125.00,USD,issued,Example customer
```

### Upload your files

1. Open **Data & reconciliation**.
2. Select the bank CSV in the bank upload area.
3. Select the gateway CSV in the gateway upload area.
4. Select the invoice CSV in the invoices upload area.
5. Check the previews.
6. Click **Import uploaded CSVs**.
7. Check the dataset status.
8. Run reconciliation.

**Please note:** importing a new file replaces the previously stored dataset for that source. For example, importing a new bank statement replaces the old bank dataset. Keep a backup if you need the old data.

### Data tips

- Use dates such as `2026-10-02`.
- Use consistent currency codes, such as `USD` or `INR`.
- Keep invoice references wherever possible.
- Check whether bank amounts are gross or net of fees.
- Do not mix currencies unless you have implemented exchange-rate conversion.
- Remove unnecessary personal information before importing.

# 13. A little tour of the project files

You do not need to open all these files today. This is just a map for when curiosity wins.

```text
autonomous-payment-reconciliation-agent/
|
|-- app.py                  # The dashboard
|-- requirements.txt        # Python packages
|-- .env.example            # Settings template
|-- setup.bat               # Windows setup helper
|-- start.bat               # Windows start helper
|
|-- sample_data/            # Fictional CSV examples
|   |-- bank.csv
|   |-- gateway.csv
|   |-- invoices.csv
|
|-- src/
|   |-- reconciliation.py   # Matching rules and calculations
|   |-- service.py          # Shared application operations
|   |-- storage.py          # SQLite database
|   |-- mcp_server.py       # MCP tools provided by the app
|   |-- mcp_bridge.py       # Connects to the MCP server
|   |-- llm_agent.py        # AI tool-calling logic
|
|-- tests/                  # Automated tests
```

A good reading order for beginners:

1. Start with `app.py` to see the dashboard.
2. Open `src/reconciliation.py` to understand the matching logic.
3. Read `src/service.py` to see how the app uses the engine.
4. Read `src/storage.py` to understand how data is saved.
5. Explore `src/mcp_server.py` and `src/mcp_bridge.py` to understand MCP.
6. Finish with `src/llm_agent.py` to see how the AI calls tools.

One file at a time. No need to speedrun the entire repository. Even the computer needs to read things in order.

# 14. Run the tests

Tests help check whether the matching logic behaves as expected.

Stop neither terminal just yet if you are still using the app; open a third terminal, or stop the app processes with Ctrl+C first.

Activate the virtual environment and run:

```bash
pytest -q
```

To check Python syntax:

```bash
python -m py_compile app.py src/*.py tests/*.py
```

If the tests pass, that is a good sign for the tested logic. It does not prove that every model, computer, CSV format, or production scenario will work.

# 15. Troubleshooting — when the computer says no

### "Python was not found"

Install Python from [python.org](https://www.python.org/downloads/). On Windows, enable the option to add Python to PATH during installation. Close and reopen PowerShell afterwards.

### "No module named ..."

Your virtual environment may not be active, or the packages may not have installed.

Activate it and run:

```bash
pip install -r requirements.txt
```

### The dashboard opens, but MCP does not connect

- Check that the MCP server terminal is still running.
- Check that the MCP URL in `.env` is `http://127.0.0.1:8001/mcp`.
- Check whether another program is already using port 8001.
- Read the error shown in the MCP server terminal.

### Ollama or the model cannot be reached

- Make sure Ollama is installed and running.
- Run `ollama list` to check the model.
- Confirm the model name in the dashboard matches the installed model.
- Confirm the Ollama URL is `http://127.0.0.1:11434/v1`.

### CSV import says the amount column is missing

Rename the amount column to a recognized name, such as `amount` or `total`.

### No records match

Check the references, dates, currencies, and amounts. Also check whether one file contains gross amounts and another contains amounts after fees.

Do not immediately increase every tolerance. A bigger tolerance can create incorrect matches. We want accurate results, not optimistic results.

# 16. Privacy and safety

Financial data is sensitive. Please treat it carefully.

- Use the included fictional data while learning.
- Do not upload real customer or bank data to a hosted AI provider unless your organization has approved that provider.
- In cloud mode, prompts and transaction evidence may be sent to the selected model provider.
- In local Ollama mode, inference runs through your local Ollama service.
- Do not commit `.env`, API keys, database files, or production exports to GitHub.
- Do not expose the dashboard or MCP server publicly without proper authentication and security controls.
- Check every exception against the original financial records before acting.

This prototype does not include enterprise authentication, role-based access control, encryption management, or a production audit system.

# 17. What this project does not do (yet)

A little honesty is good engineering.

Currently, the project:

- Imports CSV files; it does not connect directly to banks or payment gateways.
- Uses rule-based matching; it does not learn from past analyst decisions.
- Does not perform foreign-exchange conversion.
- Does not fully support complex one-to-many or many-to-one settlement allocation.
- Does not comprehensively model every provider's fees, reserves, or chargebacks.
- Does not support multiple authenticated organizations.
- Does not initiate payments, refunds, or ledger changes.

These are possible future improvements, not existing features.

# 18. Ideas for future improvements

If you want to keep developing the project, here are some sensible next steps:

1. Add more CSV templates for different banks and payment gateways.
2. Improve settlement matching for batches and processing fees.
3. Add support for partial payments and multiple invoices per payout.
4. Add analyst notes and a review/approval workflow.
5. Add a clear audit history of who reviewed each exception.
6. Add stronger access controls and secure deployment options.
7. Add more tests for refunds, reversals, duplicates, and unusual date formats.
8. Add scheduled imports and reconciliation runs.

Build one feature at a time. A small feature that works is better than a giant feature that only works in the developer's imagination.

# 19. Quick reference

| What you want to do | Command / action |
|---|---|
| Create virtual environment | `python -m venv .venv` |
| Activate on Windows | `.venv\Scripts\Activate.ps1` |
| Activate on macOS/Linux | `source .venv/bin/activate` |
| Install packages | `pip install -r requirements.txt` |
| Download Ollama model | `ollama pull qwen3:8b` |
| Start MCP server | `python src/mcp_server.py` |
| Start dashboard | `streamlit run app.py` |
| Run tests | `pytest -q` |
| Dashboard address | http://localhost:8501 |
| MCP address | http://127.0.0.1:8001/mcp |

---

# 20. A small thank you

Thank you for checking out Agent #8.

This project is part of the **200 AI Agents in 200 Days** challenge: learning by building, making mistakes, fixing them, and hopefully becoming a little better with every agent.

If you are also learning, welcome. Nobody understands an entire codebase on the first day. Ask questions, experiment with the demo data, read one file at a time, and remember:

**The goal is not to look like an expert. The goal is to keep learning until the hard things become familiar.**

If you find a bug or have an idea, feel free to open an issue or contribute.

**Repository:** https://github.com/yerageracharan/autonomous-payment-reconciliation-agent

*Built with Python, Streamlit, SQLite, MCP, and a healthy respect for confusing error messages.*
