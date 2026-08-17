from mcp.server.fastmcp import FastMCP

from app.db.session import async_session_factory
from app.mcp.handlers import MemoryHandlers

mcp = FastMCP("memory-mcp")


@mcp.tool()
async def store_answer(
    interview_id: int,
    question: str,
    answer: str,
    score: int,
) -> dict:
    """Store a candidate answer with evaluation score."""
    async with async_session_factory() as db:
        return await MemoryHandlers(db).store_answer(interview_id, question, answer, score)


@mcp.tool()
async def get_previous_questions(interview_id: int) -> dict:
    """Get all previous interviewer questions for an interview."""
    async with async_session_factory() as db:
        return await MemoryHandlers(db).get_previous_questions(interview_id)


@mcp.tool()
async def get_scores(interview_id: int) -> dict:
    """Get all skill scores for an interview."""
    async with async_session_factory() as db:
        return await MemoryHandlers(db).get_scores(interview_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
