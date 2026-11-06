"""MCP server exposing payment-reconciliation tools to LLM hosts.

Run with: python src/mcp_server.py
Default endpoint: http://127.0.0.1:8001/mcp (Streamable HTTP)
"""
from dotenv import load_dotenv
load_dotenv()

from mcp.server import MCPServer
import service
import storage

mcp = MCPServer("agent08-payment-reconciliation")


@mcp.tool()
def run_reconciliation(date_tolerance_days: int = 3, amount_tolerance: float = 0.01) -> dict:
    """Run deterministic invoice↔gateway↔bank reconciliation and persist the result locally."""
    return service.run_and_save(date_tolerance_days, amount_tolerance)


@mcp.tool()
def get_reconciliation_summary() -> dict:
    """Get counts and run metadata for the latest reconciliation."""
    return service.get_summary()


@mcp.tool()
def list_reconciliation_exceptions(severity: str = "all", exception_type: str = "all") -> dict:
    """List exceptions. severity may be all, high, or medium; exception_type may be all or a specific exception type."""
    return service.list_exceptions(severity, exception_type)


@mcp.tool()
def investigate_exception(exception_id: str) -> dict:
    """Retrieve the underlying transaction evidence and related record for one exception."""
    return service.investigate_exception(exception_id)


@mcp.tool()
def search_transactions(query: str, limit: int = 20) -> dict:
    """Search imported bank, gateway, and invoice records by ID, reference, merchant, or text."""
    return service.search_transactions(query, limit)


@mcp.tool()
def generate_reconciliation_report() -> dict:
    """Generate a Markdown reconciliation report from the latest saved run."""
    return {"markdown": service.report_markdown()}


@mcp.tool()
def get_import_status() -> dict:
    """Show which local CSV datasets are imported and how many rows each contains."""
    return {"datasets": storage.dataset_status()}


if __name__ == "__main__":
    storage.init_db()
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)
