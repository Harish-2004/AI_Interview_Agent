import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.mcp.db_client import DBMCPClient
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


@pytest.mark.asyncio
async def test_postgres_mcp_tools():
    with patch("app.mcp.postgres_db_server.server.create_async_engine") as mock_engine:
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name"]
        mock_result.fetchall.return_value = [(1, "Alice")]
        
        mock_conn.execute.return_value = mock_result
        mock_conn.__aenter__.return_value = mock_conn
        mock_conn.__aexit__.return_value = None
        
        mock_engine_inst = MagicMock()
        mock_engine_inst.connect.return_value = mock_conn
        mock_engine_inst.dispose = AsyncMock()
        mock_engine.return_value = mock_engine_inst

        # Test safe read query execution
        res = await execute_postgres_read_query("SELECT id, name FROM candidates;")
        assert res["status"] == "success"
        assert res["engine"] == "postgresql"
        assert res["data"] == [{"id": 1, "name": "Alice"}]

    # Test SQL guardrail blocking non-SELECT queries
    bad_res = await execute_postgres_read_query("DELETE FROM candidates;")
    assert bad_res["status"] == "error"
    assert "Only read-only SELECT queries are allowed" in bad_res["message"]


@pytest.mark.asyncio
async def test_mongo_mcp_tools():
    with patch("app.mcp.mongo_db_server.server._get_mongo_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_db.list_collection_names = AsyncMock(return_value=["candidates", "jobs"])
        
        mock_coll = MagicMock()
        mock_coll.count_documents = AsyncMock(return_value=5)
        mock_coll.find_one = AsyncMock(return_value={"_id": "123", "name": "Alice"})
        
        # Async cursor mock for find()
        async def async_gen():
            yield {"_id": "123", "name": "Alice"}

        mock_cursor = MagicMock()
        mock_cursor.limit.return_value = async_gen()
        mock_coll.find.return_value = mock_cursor
        mock_db.__getitem__.return_value = mock_coll
        
        mock_client_fn.return_value = (mock_client, mock_db)

        # Test list collections
        res = await list_mongo_collections()
        assert res["status"] == "success"
        assert res["collections"] == ["candidates", "jobs"]

        # Test find documents with limit enforcement
        docs_res = await find_mongo_documents("candidates", "{}", limit=10)
        assert docs_res["status"] == "success"
        assert docs_res["engine"] == "mongodb"
        assert len(docs_res["documents"]) == 1


@pytest.mark.asyncio
async def test_db_mcp_client_unified():
    with patch("app.mcp.db_client.get_postgres_tables", new=AsyncMock(return_value={"status": "success", "tables": ["candidates"]})), \
         patch("app.mcp.db_client.list_mongo_collections", new=AsyncMock(return_value={"status": "success", "collections": ["resumes"]})), \
         patch("app.mcp.db_client.describe_postgres_table", new=AsyncMock(return_value={"status": "success", "table": "candidates", "columns": []})), \
         patch("app.mcp.db_client.describe_mongo_collection", new=AsyncMock(return_value={"status": "success", "collection": "resumes", "document_count": 10})):
        
        client = DBMCPClient()

        # Test multi-db structure discovery
        structures = await client.list_database_structures()
        assert structures["status"] == "success"
        assert "postgresql" in structures["structures"]
        assert "mongodb" in structures["structures"]

        # Test dynamic schema description
        pg_schema = await client.describe_database_schema("candidates", engine="postgres")
        assert pg_schema["status"] == "success"

        mongo_schema = await client.describe_database_schema("resumes", engine="mongodb")
        assert mongo_schema["status"] == "success"


@pytest.mark.asyncio
async def test_pii_sanitization_in_db_mcp():
    with patch("app.mcp.postgres_db_server.server.create_async_engine") as mock_engine:
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "password_hash", "ssn", "name"]
        mock_result.fetchall.return_value = [(1, "secret_hash", "123-45-6789", "Alice")]
        
        mock_conn.execute.return_value = mock_result
        mock_conn.__aenter__.return_value = mock_conn
        mock_conn.__aexit__.return_value = None
        
        mock_engine_inst = MagicMock()
        mock_engine_inst.connect.return_value = mock_conn
        mock_engine_inst.dispose = AsyncMock()
        mock_engine.return_value = mock_engine_inst

        res = await execute_postgres_read_query("SELECT id, password_hash, ssn, name FROM users;")
        assert res["status"] == "success"
        data = res["data"]
        assert len(data) == 1
        assert data[0]["password_hash"] == "[REDACTED_PII]"
        assert data[0]["ssn"] == "[REDACTED_PII]"
        assert data[0]["name"] == "Alice"
