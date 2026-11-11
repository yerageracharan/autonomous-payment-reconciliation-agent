# Documentation map

The [project README](../README.md) is the canonical user handbook. It covers Windows/macOS setup, CSV imports, the matching engine, tolerance settings, exceptions, the optional AI investigator, MCP integration, privacy, and troubleshooting.

## Visual field guide

The `art/` directory contains the numbered SVG illustrations embedded throughout the README. They are source assets for documentation; update the relevant illustration and README reference together when a workflow changes.

- [Manga field guide cover](art/cover-manga.svg)
- [Data-source overview](art/data-lineup.svg)
- [Reconciliation workflow](art/12-match.svg)
- [Tolerance explanation](art/13-tolerance.svg)
- [Exception review](art/15-exceptions.svg)
- [Human approval boundary](art/16-human.svg)
- [MCP integration](art/17-mcp.svg)
- [Privacy model](art/20-privacy.svg)

## Code ownership map

| Area | Source of truth | Responsibility |
|---|---|---|
| Reconciliation rules | `src/reconciliation.py` | Normalisation, matching, tolerances, exceptions |
| Data services | `src/service.py` | Dataset imports, reconciliation runs, reports, search |
| Persistence | `src/storage.py` | SQLite schema and stored runs |
| Optional AI investigation | `src/llm_agent.py` | Explain findings; never replace deterministic reconciliation |
| MCP server and bridge | `src/mcp_server.py`, `src/mcp_bridge.py` | Tool interface for external assistants |
| Dashboard | `app.py` | User workflow and review UI |
| Sample data | `sample_data/` | Synthetic/demo datasets |
| Regression coverage | `tests/` | Matching, tolerances, refunds, duplicates, and service behavior |

## Local configuration and validation

- [Example environment file](../.env.example)
- [Example MCP configuration](../mcp_config.example.json)
- [Windows setup script](../setup.bat)
- [Windows launch script](../start.bat)
- [Automated tests](../tests/)
- [Contribution workflow](../CONTRIBUTING.md)
- [AI coding-agent instructions](../AGENTS.md)
- [Security policy](../SECURITY.md)

Never use the deterministic match result as an automatic money movement instruction. Reconciliation exceptions and any payment action require human review.
