"""Small MCP client bridge used by the Streamlit UI and LLM orchestrator."""
from __future__ import annotations
import asyncio
import json
import os
from typing import Any

from mcp import Client

MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:8001/mcp")


def _sync(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def _content_to_python(result: Any) -> Any:
    structured = getattr(result, "structured_content", None)
    if structured is None:
        structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return structured
    content = getattr(result, "content", []) or []
    texts = [getattr(part, "text", "") for part in content if getattr(part, "text", None)]
    if len(texts) == 1:
        try:
            return json.loads(texts[0])
        except json.JSONDecodeError:
            return texts[0]
    return texts


async def _call_tool(name: str, arguments: dict[str, Any]) -> Any:
    async with Client(MCP_URL) as client:
        result = await client.call_tool(name, arguments)
        if getattr(result, "is_error", False) or getattr(result, "isError", False):
            raise RuntimeError(str(_content_to_python(result)))
        return _content_to_python(result)


async def _list_tools() -> list[dict[str, Any]]:
    async with Client(MCP_URL) as client:
        result = await client.list_tools()
        tools = []
        for tool in result.tools:
            schema = getattr(tool, "input_schema", None) or getattr(tool, "inputSchema", None) or {"type": "object", "properties": {}}
            tools.append({"name": tool.name, "description": getattr(tool, "description", "") or "", "input_schema": schema})
        return tools


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> Any:
    return _sync(_call_tool(name, arguments or {}))


def list_tools() -> list[dict[str, Any]]:
    return _sync(_list_tools())
