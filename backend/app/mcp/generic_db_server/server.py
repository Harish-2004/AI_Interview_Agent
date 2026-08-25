"""Generic DB MCP Server providing schema introspection and safe read-only SQL execution tools."""

import sqlite3
from typing import Any
from mcp.server.fastmcp import FastMCP

from app.config import settings
from app.guardrails import sanitize_db_result_guardrail, validate_sql_query_guardrail

mcp = FastMCP("generic-db-mcp")


def _get_db_path() -> str:
    url = settings.database_url
    if ":///" in url:
        return url.split(":///")[-1]
    return "./interview_agent.db"


@mcp.tool()
async def get_tables() -> dict[str, Any]:
    """Retrieve all table names from the database."""
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {"status": "success", "tables": tables}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
async def describe_table(table_name: str) -> dict[str, Any]:
    """Describe the column schema and metadata for a specific table."""
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [
            {"id": row[0], "name": row[1], "type": row[2], "notnull": row[3], "default_value": row[4], "pk": row[5]}
            for row in cursor.fetchall()
        ]
        conn.close()
        return {"status": "success", "table": table_name, "columns": columns}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
async def execute_read_query(query: str) -> dict[str, Any]:
    """Safely execute a read-only SELECT SQL query with guardrail validation and PII sanitization."""
    # 1. Apply SQL Execution Guardrail
    guardrail_res = validate_sql_query_guardrail(query)
    if not guardrail_res["passed"]:
        return {"status": "error", "message": guardrail_res["error"]}

    safe_query = guardrail_res["query"]
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(safe_query)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # 2. Apply PII Data Sanitization Guardrail
        sanitized_rows = sanitize_db_result_guardrail(rows)
        return {"status": "success", "row_count": len(sanitized_rows), "data": sanitized_rows}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
