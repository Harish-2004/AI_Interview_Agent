from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp.db_client import get_db_mcp_client
from app.mcp.handlers import JDHandlers, MemoryHandlers, ResumeHandlers
from app.services.rag_service import rag_service


class MCPClient:
    """In-process MCP client wrapping domain tool handlers, LlamaIndex RAG tools, and Multi-DB MCP operations (Postgres & Mongo)."""

    def __init__(self, db: AsyncSession):
        self._resume = ResumeHandlers(db)
        self._jd = JDHandlers(db)
        self._memory = MemoryHandlers(db)
        self._db_mcp = get_db_mcp_client(db)

    async def list_database_structures(self) -> dict[str, Any]:
        """Discover database structures across PostgreSQL tables and MongoDB collections."""
        return await self._db_mcp.list_database_structures()

    async def describe_database_schema(self, name: str, engine: str = "auto") -> dict[str, Any]:
        """Describe table schema or collection metadata."""
        return await self._db_mcp.describe_database_schema(name, engine)

    async def execute_safe_query(self, query_or_filter: str, target: str | None = None, engine: str = "auto") -> dict[str, Any]:
        """Execute guardrail-validated query on Postgres or Mongo."""
        return await self._db_mcp.execute_safe_query(query_or_filter, target, engine)

    async def get_resume(self, candidate_id: int) -> dict:
        data = await self._resume.get_resume(candidate_id)
        if "resume_text" in data:
            rag_service.index_resume(candidate_id, data["resume_text"])
        return data

    async def extract_skills(self, candidate_id: int) -> dict:
        return await self._resume.extract_skills(candidate_id)

    async def get_experience(self, candidate_id: int) -> dict:
        return await self._resume.get_experience(candidate_id)

    async def search_resume_rag(self, candidate_id: int, query: str, top_k: int = 3) -> dict:
        """Search candidate resume using LlamaIndex RAG retrieval."""
        data = await self._resume.get_resume(candidate_id)
        if "resume_text" in data:
            rag_service.index_resume(candidate_id, data["resume_text"])
        
        context_chunks = rag_service.retrieve_resume_context(candidate_id, query, top_k=top_k)
        return {
            "candidate_id": candidate_id,
            "query": query,
            "context_chunks": context_chunks,
        }

    async def get_job_description(self, job_id: int) -> dict:
        data = await self._jd.get_job_description(job_id)
        if "description" in data:
            rag_service.index_jd(job_id, data["description"])
        return data

    async def get_required_skills(self, job_id: int) -> dict:
        return await self._jd.get_required_skills(job_id)

    async def search_jd_rag(self, job_id: int, query: str, top_k: int = 3) -> dict:
        """Search job description using LlamaIndex RAG retrieval."""
        data = await self._jd.get_job_description(job_id)
        if "description" in data:
            rag_service.index_jd(job_id, data["description"])
        
        context_chunks = rag_service.retrieve_jd_context(job_id, query, top_k=top_k)
        return {
            "job_id": job_id,
            "query": query,
            "context_chunks": context_chunks,
        }

    async def store_answer(
        self, interview_id: int, question: str, answer: str, score: int
    ) -> dict:
        return await self._memory.store_answer(interview_id, question, answer, score)

    async def get_previous_questions(self, interview_id: int) -> dict:
        return await self._memory.get_previous_questions(interview_id)

    async def get_scores(self, interview_id: int) -> dict:
        return await self._memory.get_scores(interview_id)


def get_mcp_client(db: AsyncSession) -> MCPClient:
    return MCPClient(db)
