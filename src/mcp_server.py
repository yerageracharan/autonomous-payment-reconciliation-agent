"""MCP server exposing payment-reconciliation tools over Streamable HTTP."""
from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP
import service
import storage

mcp = FastMCP("agent08-payment-reconciliation")


@mcp.tool()
def run_reconciliation(date_tolerance_days: int = 3, amount_tolerance: float = 0.01) -> dict:
    """Run deterministic invoice-to-gateway-to-bank reconciliation and save the result."""
    return service.run_and_save(date_tolerance_days, amount_tolerance)


@mcp.tool()
def get_reconciliation_summary() -> dict:
    """Get counts and run metadata for the latest reconciliation."""
    return service.get_summary()


@mcp.tool()
def list_reconciliation_exceptions(severity: str = "all", exception_type: str = "all") -> dict:
    """List exceptions. Severity: all, high, or medium. Type: all or an exception type."""
    return service.list_exceptions(severity, exception_type)


@mcp.tool()
def investigate_exception(exception_id: str) -> dict:
    """Retrieve transaction evidence and related record for one exception."""
    return service.investigate_exception(exception_id)


@mcp.tool()
def search_transactions(query: str, limit: int = 20) -> dict:
    """Search imported bank, gateway, and invoice records by ID, reference, merchant, or text."""
    return service.search_transactions(query, limit)


@mcp.tool()
def generate_reconciliation_report() -> dict:
    """Generate a Markdown report from the latest saved reconciliation."""
    return {"markdown": service.report_markdown()}


@mcp.tool()
def get_import_status() -> dict:
    """Show imported local datasets and row counts."""
    return {"datasets": storage.dataset_status()}


if __name__ == "__main__":
    storage.init_db()
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)
