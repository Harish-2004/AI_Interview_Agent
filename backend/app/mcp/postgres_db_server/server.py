"""PostgreSQL Database MCP Server providing dynamic schema introspection and safe read-only SQL execution tools."""

from typing import Any
from mcp.server.fastmcp import FastMCP
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.guardrails import sanitize_db_result_guardrail, validate_sql_query_guardrail

mcp = FastMCP("postgres-db-mcp")


def _get_pg_url() -> str:
    url = settings.database_url
    if "postgresql" not in url:
        return "postgresql+asyncpg://postgres:postgres@localhost:5432/interview_agent"
    return url


@mcp.tool()
async def get_postgres_tables() -> dict[str, Any]:
    """Retrieve all user table names from the PostgreSQL database."""
    pg_url = _get_pg_url()
    engine = create_async_engine(pg_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
                )
            )
            tables = [row[0] for row in result.fetchall()]
        await engine.dispose()
        return {"status": "success", "engine": "postgresql", "tables": tables}
    except Exception as e:
        await engine.dispose()
        return {"status": "error", "engine": "postgresql", "message": str(e)}


@mcp.tool()
async def describe_postgres_table(table_name: str) -> dict[str, Any]:
    """Describe the column schema, data types, and nullability for a specific PostgreSQL table."""
    pg_url = _get_pg_url()
    engine = create_async_engine(pg_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT column_name, data_type, is_nullable, column_default "
                    "FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = :tname "
                    "ORDER BY ordinal_position;"
                ),
                {"tname": table_name},
            )
            columns = [
                {
                    "column_name": row[0],
                    "data_type": row[1],
                    "is_nullable": row[2],
                    "column_default": row[3],
                }
                for row in result.fetchall()
            ]
        await engine.dispose()
        return {"status": "success", "engine": "postgresql", "table": table_name, "columns": columns}
    except Exception as e:
        await engine.dispose()
        return {"status": "error", "engine": "postgresql", "message": str(e)}


@mcp.tool()
async def execute_postgres_read_query(query: str) -> dict[str, Any]:
    """Safely execute a read-only SELECT SQL query on PostgreSQL with guardrail validation and PII sanitization."""
    # 1. Apply SQL Guardrail Check
    guardrail_res = validate_sql_query_guardrail(query)
    if not guardrail_res["passed"]:
        return {"status": "error", "engine": "postgresql", "message": guardrail_res["error"]}

    safe_query = guardrail_res["query"]
    pg_url = _get_pg_url()
    engine = create_async_engine(pg_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(safe_query))
            keys = result.keys()
            rows = [dict(zip(keys, row)) for row in result.fetchall()]
        await engine.dispose()

        # 2. Apply PII Data Sanitization Guardrail
        sanitized_rows = sanitize_db_result_guardrail(rows)
        return {
            "status": "success",
            "engine": "postgresql",
            "row_count": len(sanitized_rows),
            "data": sanitized_rows,
        }
    except Exception as e:
        await engine.dispose()
        return {"status": "error", "engine": "postgresql", "message": str(e)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
