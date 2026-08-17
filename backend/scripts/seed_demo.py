"""Demo data seed script."""

import asyncio

from app.db.models import Candidate, Job
from app.db.session import async_session_factory

DEMO_CANDIDATE = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "resume_text": (
        "Senior backend engineer with 5 years experience. "
        "Built async REST APIs with FastAPI and Pydantic. "
        "Deployed services using Docker and PostgreSQL."
    ),
}

DEMO_JOB = {
    "title": "Backend Engineer",
    "description": (
        "We need a backend engineer skilled in FastAPI, Docker, and SQL. "
        "You will build microservices and containerized deployments."
    ),
}


async def main() -> None:
    from app.db.models import Base
    from app.db.session import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        candidate = Candidate(**DEMO_CANDIDATE)
        job = Job(**DEMO_JOB)
        db.add(candidate)
        db.add(job)
        await db.commit()
        await db.refresh(candidate)
        await db.refresh(job)
        print(f"Seeded candidate id={candidate.id}, job id={job.id}")



if __name__ == "__main__":
    asyncio.run(main())
