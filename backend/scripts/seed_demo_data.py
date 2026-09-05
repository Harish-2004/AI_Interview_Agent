"""Script to seed initial demo Candidate #1 and Job #1 into PostgreSQL for voice_demo.html and testing."""

import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.db.models import Candidate, Job
from app.db.session import async_session_factory


async def seed():
    async with async_session_factory() as db:
        # 1. Seed Candidate #1
        c_stmt = select(Candidate).where(Candidate.id == 1)
        candidate = (await db.execute(c_stmt)).scalar_one_or_none()
        if not candidate:
            candidate = Candidate(
                id=1,
                name="Demo Candidate (Alex Chen)",
                email="alex.chen@example.com",
                resume_text="Experienced Senior Full-Stack Engineer with 5+ years of experience in Python, FastAPI, Docker, PostgreSQL, and React. Built scalable microservices and async APIs.",
            )
            db.add(candidate)
            print("Seeded Candidate #1 (Alex Chen)")
        else:
            print("Candidate #1 already exists.")

        # 2. Seed Job #1
        j_stmt = select(Job).where(Job.id == 1)
        job = (await db.execute(j_stmt)).scalar_one_or_none()
        if not job:
            job = Job(
                id=1,
                title="Senior Backend Engineer (Python & FastAPI)",
                description="We are seeking a Senior Backend Engineer to build high-performance async APIs with Python, FastAPI, Docker, and PostgreSQL. Must have experience with unit testing and database optimization.",
            )
            db.add(job)
            print("Seeded Job #1 (Senior Backend Engineer)")
        else:
            print("Job #1 already exists.")

        await db.commit()
        print("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
