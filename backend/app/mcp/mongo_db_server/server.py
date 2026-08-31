"""MongoDB MCP Server providing document store collection discovery, schema profiling, and safe document querying tools."""

import json
from typing import Any
from mcp.server.fastmcp import FastMCP

from app.config import settings
from app.guardrails import sanitize_db_result_guardrail

mcp = FastMCP("mongo-db-mcp")


def _get_mongo_client():
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=2000)
    db = client[settings.mongodb_database]
    return client, db


def _serialize_doc(doc: dict[str, Any]) -> dict[str, Any]:
    """Convert BSON non-serializable objects (like ObjectId) into standard JSON representations."""
    if not isinstance(doc, dict):
        return doc
    clean = {}
    for key, val in doc.items():
        if hasattr(val, "__str__") and type(val).__name__ == "ObjectId":
            clean[key] = str(val)
        elif isinstance(val, dict):
            clean[key] = _serialize_doc(val)
        elif isinstance(val, list):
            clean[key] = [_serialize_doc(item) if isinstance(item, dict) else str(item) if type(item).__name__ == "ObjectId" else item for item in val]
        else:
            clean[key] = val
    return clean


@mcp.tool()
async def list_mongo_collections() -> dict[str, Any]:
    """List all collection names in the MongoDB database."""
    try:
        client, db = _get_mongo_client()
        collections = await db.list_collection_names()
        client.close()
        return {"status": "success", "engine": "mongodb", "collections": collections}
    except Exception as e:
        return {"status": "error", "engine": "mongodb", "message": str(e)}


@mcp.tool()
async def describe_mongo_collection(collection_name: str) -> dict[str, Any]:
    """Describe sample field schema and document metrics for a MongoDB collection."""
    try:
        client, db = _get_mongo_client()
        coll = db[collection_name]
        doc_count = await coll.count_documents({})
        sample = await coll.find_one({})
        client.close()

        sample_fields = []
        if sample:
            sample_clean = _serialize_doc(sample)
            sample_fields = [
                {"field": k, "sample_type": type(v).__name__}
                for k, v in sample_clean.items()
            ]

        return {
            "status": "success",
            "engine": "mongodb",
            "collection": collection_name,
            "document_count": doc_count,
            "fields": sample_fields,
        }
    except Exception as e:
        return {"status": "error", "engine": "mongodb", "message": str(e)}


@mcp.tool()
async def find_mongo_documents(collection_name: str, query_filter: str = "{}", limit: int = 50) -> dict[str, Any]:
    """Safely query documents from a MongoDB collection using a JSON filter with limit enforcement and PII sanitization."""
    try:
        # Enforce max limit of 50
        safe_limit = min(max(1, limit), 50)
        
        # Parse query filter
        filter_dict = json.loads(query_filter) if isinstance(query_filter, str) else query_filter
        
        client, db = _get_mongo_client()
        coll = db[collection_name]
        cursor = coll.find(filter_dict).limit(safe_limit)
        
        docs = []
        async for doc in cursor:
            docs.append(_serialize_doc(doc))
        client.close()

        # Apply PII Data Sanitization Guardrail
        sanitized_docs = sanitize_db_result_guardrail(docs)
        return {
            "status": "success",
            "engine": "mongodb",
            "collection": collection_name,
            "count": len(sanitized_docs),
            "documents": sanitized_docs,
        }
    except Exception as e:
        return {"status": "error", "engine": "mongodb", "message": str(e)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
