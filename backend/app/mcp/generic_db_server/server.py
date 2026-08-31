"""Dynamic Multi-Database MCP Server supporting engine-agnostic schema introspection and safe query execution across PostgreSQL and MongoDB."""

from typing import Any
from mcp.server.fastmcp import FastMCP

from app.mcp.db_client import DBMCPClient

mcp = FastMCP("generic-db-mcp")
db_mcp_client = DBMCPClient()


@mcp.tool()
async def get_tables() -> dict[str, Any]:
    """Retrieve all accessible tables and collections across configured databases."""
    res = await db_mcp_client.list_database_structures()
    # Map for backward compatibility
    pg_tables = res.get("structures", {}).get("postgresql", {}).get("tables", [])
    return {"status": "success", "tables": pg_tables, "all_structures": res["structures"]}


@mcp.tool()
async def describe_table(table_name: str) -> dict[str, Any]:
    """Describe the schema structure for a table (Postgres) or collection (MongoDB)."""
    return await db_mcp_client.describe_database_schema(table_name)


@mcp.tool()
async def execute_read_query(query: str) -> dict[str, Any]:
    """Safely execute a read query on PostgreSQL or document query on MongoDB with guardrail validation."""
    return await db_mcp_client.execute_safe_query(query)


if __name__ == "__main__":
    mcp.run(transport="stdio")
