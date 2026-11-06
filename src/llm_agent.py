"""LLM↔MCP agent loop supporting hosted APIs and local Ollama models.

Both modes use the OpenAI-compatible Chat Completions interface. The model gets
its tools from the MCP server at runtime, and every tool call is executed via MCP.
"""
from __future__ import annotations
import json
from typing import Any

from openai import OpenAI
from mcp_bridge import list_tools, call_tool

SYSTEM_PROMPT = """You are the AI investigation assistant for a payment reconciliation platform.

Rules:
- Use MCP tools to inspect the imported records and latest reconciliation. Do not invent transaction data.
- Financial matching, amounts, differences, and exception types are computed deterministically by the reconciliation engine. Never override those calculations.
- When asked to investigate, call the relevant MCP tools (summary, exceptions, exception detail, transaction search, or report) before answering.
- Clearly distinguish confirmed data from possible explanations. State what evidence supports each conclusion and what a human should verify.
- Never claim to have moved money, issued a refund, changed a ledger, or contacted a bank. This app is read-only.
- Avoid exposing full account numbers or sensitive personal data. If records contain them, redact them in your answer.
- Keep responses direct, structured, and useful to a finance operations analyst.
"""


def _client(provider: str, api_key: str | None, base_url: str | None) -> OpenAI:
    if provider == "ollama":
        return OpenAI(base_url=(base_url or "http://127.0.0.1:11434/v1"), api_key="ollama", timeout=120.0)
    if not api_key:
        raise ValueError("An API key is required for cloud/API mode.")
    return OpenAI(api_key=api_key, base_url=base_url or None, timeout=90.0)


def _tool_specs(mcp_tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for tool in mcp_tools:
        schema = tool["input_schema"]
        if not isinstance(schema, dict) or schema.get("type") != "object":
            schema = {"type": "object", "properties": {}}
        result.append({"type": "function", "function": {
            "name": tool["name"],
            "description": tool["description"][:900],
            "parameters": schema,
        }})
    return result


def chat_with_agent(user_message: str, history: list[dict[str, str]] | None = None,
                    provider: str = "ollama", model: str = "qwen3:8b",
                    api_key: str | None = None, base_url: str | None = None,
                    max_tool_rounds: int = 6) -> tuple[str, list[dict[str, str]]]:
    """Run one model turn with MCP tool calling; return response and visible tool log."""
    client = _client(provider, api_key, base_url)
    tools = _tool_specs(list_tools())
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-12:])
    messages.append({"role": "user", "content": user_message})
    tool_log: list[dict[str, str]] = []

    for _ in range(max_tool_rounds):
        request_args = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "temperature": 0.2,
        }
        if provider != "ollama":
            request_args["tool_choice"] = "auto"
        response = client.chat.completions.create(**request_args)
        message = response.choices[0].message
        if not message.tool_calls:
            return message.content or "The model returned an empty response.", tool_log

        messages.append(message.model_dump(exclude_none=True))
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
                output = call_tool(name, arguments)
                output_text = json.dumps(output, ensure_ascii=False, default=str)
                tool_log.append({"tool": name, "status": "success"})
            except Exception as exc:
                output_text = json.dumps({"error": str(exc)})
                tool_log.append({"tool": name, "status": "error"})
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": output_text[:30000]})

    return "I reached the tool-call limit for this turn. Please narrow the investigation or ask a more specific question.", tool_log
