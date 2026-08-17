from mcp.server.fastmcp import FastMCP

from app.db.session import async_session_factory
from app.mcp.handlers import JDHandlers

mcp = FastMCP("jd-mcp")


@mcp.tool()
async def get_job_description(job_id: int) -> dict:
    """Get job title and full description."""
    async with async_session_factory() as db:
        return await JDHandlers(db).get_job_description(job_id)


@mcp.tool()
async def get_required_skills(job_id: int) -> dict:
    """Extract required skills from job description."""
    async with async_session_factory() as db:
        return await JDHandlers(db).get_required_skills(job_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
