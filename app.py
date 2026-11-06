from __future__ import annotations
import os, sys
from pathlib import Path
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")

import storage
from mcp_bridge import call_tool
from llm_agent import chat_with_agent

storage.init_db()
st.set_page_config(page_title="Agent #8 | Payment Reconciliation", page_icon="💳", layout="wide")
st.title("Agent #8 — Payment Reconciliation")
st.caption("AI-assisted finance operations · Deterministic matching · MCP-connected LLM · Local-first")

with st.sidebar:
    st.header("LLM provider")
    provider_label = st.radio("Choose model", ["Local Ollama", "Cloud API"])
    provider = "ollama" if provider_label == "Local Ollama" else "cloud"
    if provider == "ollama":
        base_url = st.text_input("Ollama URL", os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"))
        model = st.text_input("Model", os.getenv("OLLAMA_MODEL", "qwen3:8b"))
        api_key = None
        st.caption("Run: ollama pull qwen3:8b")
    else:
        base_url = st.text_input("API base URL", os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"))
        model = st.text_input("Model", os.getenv("LLM_MODEL", "gpt-4.1-mini"))
        api_key = st.text_input("API key", os.getenv("LLM_API_KEY", ""), type="password")
    st.divider()
    st.code(os.getenv("MCP_URL", "http://127.0.0.1:8001/mcp"))
    if st.button("Test MCP connection"):
        try:
            st.success("Connected")
            st.json(call_tool("get_import_status"))
        except Exception as exc:
            st.error(str(exc))
    st.caption("Read-only prototype. No payments or refunds are initiated.")

data_tab, exceptions_tab, ai_tab, architecture_tab = st.tabs(["Data & reconciliation", "Exceptions", "AI investigator", "Architecture"])
with data_tab:
    st.subheader("Import financial exports")
    st.write("Upload bank statement, payment gateway and invoice CSV exports. Data is stored in local SQLite.")
    cols = st.columns(3)
    uploads = {}
    for col, source in zip(cols, ["bank", "gateway", "invoices"]):
        with col:
            uploads[source] = st.file_uploader(f"{source.title()} CSV", type=["csv"], key=f"upload_{source}")
            if uploads[source] is not None:
                try:
                    frame = pd.read_csv(uploads[source])
                    st.caption(f"{len(frame)} rows")
                    st.dataframe(frame.head(4), use_container_width=True, hide_index=True)
                except Exception as exc:
                    st.error(f"CSV error: {exc}")
    if st.button("Import uploaded CSVs", type="primary"):
        for source, file in uploads.items():
            if file is not None:
                try:
                    file.seek(0)
                    frame = pd.read_csv(file)
                    records = frame.astype(object).where(pd.notna(frame), None).to_dict(orient="records")
                    storage.save_dataset(source, records)
                    st.success(f"Imported {len(records)} {source} rows")
                except Exception as exc:
                    st.error(f"{source}: {exc}")
    if st.button("Load demo data"):
        for source in ["bank", "gateway", "invoices"]:
            frame = pd.read_csv(ROOT / "sample_data" / f"{source}.csv")
            records = frame.astype(object).where(pd.notna(frame), None).to_dict(orient="records")
            storage.save_dataset(source, records)
        st.success("Demo datasets loaded.")
    st.subheader("Dataset status")
    st.dataframe(pd.DataFrame(storage.dataset_status()), use_container_width=True, hide_index=True)
    st.subheader("Run matching")
    c1, c2 = st.columns(2)
    days = c1.number_input("Date tolerance (days)", 0, 30, 3)
    amount_tol = c2.number_input("Amount tolerance", 0.0, 100.0, 0.01, step=0.01)
    if st.button("Run reconciliation through MCP", type="primary"):
        try:
            result = call_tool("run_reconciliation", {"date_tolerance_days": int(days), "amount_tolerance": float(amount_tol)})
            st.success(f"Completed run {result.get('run_id')}")
            st.json(result.get("summary", {}))
        except Exception as exc:
            st.error(f"Reconciliation failed: {exc}")
    try:
        summary = call_tool("get_reconciliation_summary")
        if summary.get("status") != "no_run":
            st.subheader("Latest run")
            metrics = st.columns(5)
            for col, label, key in zip(metrics, ["Matched", "Exceptions", "High", "Medium", "Bank rows"],
                                       ["matched_pairs", "exceptions", "high_severity", "medium_severity", "bank_transactions"]):
                col.metric(label, summary.get(key, 0))
    except Exception:
        pass

with exceptions_tab:
    st.subheader("Exception queue")
    severity = st.selectbox("Severity", ["all", "high", "medium"])
    exception_type = st.text_input("Type filter (or all)", "all")
    if st.button("Load exceptions"):
        try:
            st.session_state["exceptions"] = call_tool("list_reconciliation_exceptions", {"severity": severity, "exception_type": exception_type.strip() or "all"})
        except Exception as exc:
            st.error(str(exc))
    result = st.session_state.get("exceptions")
    if result:
        rows = result.get("exceptions", [])
        if rows:
            frame = pd.DataFrame(rows)
            st.dataframe(frame, use_container_width=True, hide_index=True)
            selected = st.selectbox("Inspect exception ID", [x["exception_id"] for x in rows])
            if st.button("Investigate selected exception"):
                try:
                    st.session_state["exception_detail"] = call_tool("investigate_exception", {"exception_id": selected})
                except Exception as exc:
                    st.error(str(exc))
            if st.session_state.get("exception_detail"):
                st.json(st.session_state["exception_detail"])
            st.download_button("Download exceptions CSV", frame.to_csv(index=False), "exceptions.csv", "text/csv")
        else:
            st.info("No exceptions found.")
    try:
        report = call_tool("generate_reconciliation_report")
        if report.get("markdown") and "No reconciliation" not in report["markdown"]:
            st.download_button("Download report", report["markdown"], "reconciliation_report.md", "text/markdown")
    except Exception:
        pass

with ai_tab:
    st.subheader("AI investigation workspace")
    st.write("The LLM discovers MCP tools dynamically, calls them to inspect evidence, and explains results. Matching calculations remain deterministic.")
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []
    for item in st.session_state["chat_messages"]:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
            if item.get("tool_log"):
                with st.expander("MCP tool calls"):
                    st.json(item["tool_log"])
    prompt = st.chat_input("Ask: Investigate the highest-risk exception and explain the evidence.")
    if prompt:
        history = [{"role": x["role"], "content": x["content"]} for x in st.session_state["chat_messages"][-10:]]
        st.session_state["chat_messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                with st.spinner("Calling LLM and MCP tools..."):
                    answer, tool_log = chat_with_agent(prompt, history, provider, model, api_key, base_url)
                st.markdown(answer)
                if tool_log:
                    with st.expander("MCP tool calls"):
                        st.json(tool_log)
                st.session_state["chat_messages"].append({"role": "assistant", "content": answer, "tool_log": tool_log})
            except Exception as exc:
                st.error(f"Agent error: {exc}. Check model settings and MCP server.")
    if st.button("Clear chat"):
        st.session_state["chat_messages"] = []
        st.rerun()

with architecture_tab:
    st.subheader("Architecture")
    st.code("""Streamlit dashboard (localhost:8501)
  ├─ CSV import / exception queue / AI chat
  └─ MCP client
       │ Streamable HTTP
       ▼
MCP server (localhost:8001/mcp)
  ├─ reconciliation + summary + exception tools
  ├─ transaction search + report
  ▼
Deterministic Python engine → local SQLite

LLM orchestration:
  ├─ Hosted OpenAI-compatible API
  └─ Local Ollama model
       └─ discovers and calls MCP tools""")
    st.info("Data is stored locally. In cloud mode, prompts and retrieved transaction evidence may be sent to the selected model provider. Use synthetic or masked data unless the provider is approved for your financial data.")
    st.warning("Read-only prototype: it does not initiate payments, refunds, or ledger changes.")
