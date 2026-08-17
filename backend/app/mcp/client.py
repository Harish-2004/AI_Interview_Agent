from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp.handlers import JDHandlers, MemoryHandlers, ResumeHandlers


class MCPClient:
    """In-process MCP client wrapping domain tool handlers."""

    def __init__(self, db: AsyncSession):
        self._resume = ResumeHandlers(db)
        self._jd = JDHandlers(db)
        self._memory = MemoryHandlers(db)

    async def get_resume(self, candidate_id: int) -> dict:
        return await self._resume.get_resume(candidate_id)

    async def extract_skills(self, candidate_id: int) -> dict:
        return await self._resume.extract_skills(candidate_id)

    async def get_experience(self, candidate_id: int) -> dict:
        return await self._resume.get_experience(candidate_id)

    async def get_job_description(self, job_id: int) -> dict:
        return await self._jd.get_job_description(job_id)

    async def get_required_skills(self, job_id: int) -> dict:
        return await self._jd.get_required_skills(job_id)

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
