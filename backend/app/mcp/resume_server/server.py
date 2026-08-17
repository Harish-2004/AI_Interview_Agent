from mcp.server.fastmcp import FastMCP

from app.db.session import async_session_factory
from app.mcp.handlers import ResumeHandlers

mcp = FastMCP("resume-mcp")


@mcp.tool()
async def get_resume(candidate_id: int) -> dict:
    """Get full resume text and metadata for a candidate."""
    async with async_session_factory() as db:
        return await ResumeHandlers(db).get_resume(candidate_id)


@mcp.tool()
async def extract_skills(candidate_id: int) -> dict:
    """Extract skills from a candidate resume."""
    async with async_session_factory() as db:
        return await ResumeHandlers(db).extract_skills(candidate_id)


@mcp.tool()
async def get_experience(candidate_id: int) -> dict:
    """Get work experience summary from resume."""
    async with async_session_factory() as db:
        return await ResumeHandlers(db).get_experience(candidate_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
