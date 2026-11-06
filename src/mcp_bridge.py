"""MCP Streamable HTTP client bridge for the dashboard and LLM agent."""
from __future__ import annotations
import asyncio
import json
import os
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

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
    structured = getattr(result, "structuredContent", None) or getattr(result, "structured_content", None)
    if structured is not None:
        return structured
    parts = getattr(result, "content", []) or []
    texts = [getattr(part, "text", "") for part in parts if getattr(part, "text", None)]
    if len(texts) == 1:
        try:
            return json.loads(texts[0])
        except json.JSONDecodeError:
            return texts[0]
    return texts


async def _session():
    raise RuntimeError("Use _with_session for MCP operations.")


async def _call_tool(name: str, arguments: dict[str, Any]) -> Any:
    async with streamablehttp_client(MCP_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            if getattr(result, "isError", False):
                raise RuntimeError(str(_content_to_python(result)))
            return _content_to_python(result)


async def _list_tools() -> list[dict[str, Any]]:
    async with streamablehttp_client(MCP_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()
            return [{
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            } for tool in result.tools]


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> Any:
    return _sync(_call_tool(name, arguments or {}))


def list_tools() -> list[dict[str, Any]]:
    return _sync(_list_tools())
