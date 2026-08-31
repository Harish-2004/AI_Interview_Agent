"""Production Multi-Database MCP Client Manager providing engine-agnostic schema introspection and safe query execution across PostgreSQL and MongoDB."""

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.mcp.postgres_db_server.server import (
    describe_postgres_table,
    execute_postgres_read_query,
    get_postgres_tables,
)
from app.mcp.mongo_db_server.server import (
    describe_mongo_collection,
    find_mongo_documents,
    list_mongo_collections,
)


class PostgresMCPClient:
    """MCP Client handler for PostgreSQL database operations."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db

    async def get_tables(self) -> dict[str, Any]:
        return await get_postgres_tables()

    async def describe_table(self, table_name: str) -> dict[str, Any]:
        return await describe_postgres_table(table_name)

    async def execute_query(self, query: str) -> dict[str, Any]:
        return await execute_postgres_read_query(query)


class MongoDBMCPClient:
    """MCP Client handler for MongoDB document store operations."""

    async def list_collections(self) -> dict[str, Any]:
        return await list_mongo_collections()

    async def describe_collection(self, collection_name: str) -> dict[str, Any]:
        return await describe_mongo_collection(collection_name)

    async def find_documents(self, collection_name: str, query_filter: str = "{}", limit: int = 50) -> dict[str, Any]:
        return await find_mongo_documents(collection_name, query_filter, limit)


class DBMCPClient:
    """Unified Multi-Database MCP Client Manager enabling dynamic, engine-agnostic database interaction for AI Agents."""

    def __init__(self, db: AsyncSession | None = None):
        self.postgres = PostgresMCPClient(db)
        self.mongo = MongoDBMCPClient()
        self.active_type = settings.active_db_mcp_type

    async def list_database_structures(self) -> dict[str, Any]:
        """Dynamically list all accessible database structures (tables and collections)."""
        res = {"status": "success", "structures": {}}
        
        # 1. PostgreSQL Tables
        pg_res = await get_postgres_tables()
        res["structures"]["postgresql"] = pg_res

        # 2. MongoDB Collections
        mongo_res = await list_mongo_collections()
        res["structures"]["mongodb"] = mongo_res

        return res

    async def describe_database_schema(self, name: str, engine: str = "auto") -> dict[str, Any]:
        """Describe column or document schema for a table/collection across Postgres or Mongo."""
        if engine == "mongodb" or (engine == "auto" and self.active_type == "mongodb"):
            return await describe_mongo_collection(name)
        # Default / Fallback to PostgreSQL
        return await describe_postgres_table(name)

    async def execute_safe_query(
        self, query_or_filter: str, target: str | None = None, engine: str = "auto"
    ) -> dict[str, Any]:
        """Execute a safe, guardrail-validated read query against Postgres or Mongo."""
        if engine == "mongodb" or (engine == "auto" and target and not query_or_filter.strip().upper().startswith("SELECT")):
            coll_name = target or "candidates"
            return await find_mongo_documents(coll_name, query_or_filter)
        
        # Default SQL / PostgreSQL Execution
        return await execute_postgres_read_query(query_or_filter)


def get_db_mcp_client(db: AsyncSession | None = None) -> DBMCPClient:
    return DBMCPClient(db)
