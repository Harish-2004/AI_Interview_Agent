import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Candidate, Evaluation, InterviewMessage, Job, MessageRole


def _extract_skills_from_text(text: str) -> list[str]:
    known_skills = [
        "FastAPI",
        "Docker",
        "SQL",
        "Python",
        "PostgreSQL",
        "REST",
        "Kubernetes",
        "Redis",
        "AWS",
        "async",
    ]
    text_lower = text.lower()
    found = []
    for skill in known_skills:
        if skill.lower() in text_lower:
            found.append(skill if skill != "REST" else "REST APIs")
    if not found:
        words = re.findall(r"\b[A-Z][a-zA-Z+#]+\b", text)
        found = list(dict.fromkeys(words))[:5]
    return found


class ResumeHandlers:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_resume(self, candidate_id: int) -> dict:
        result = await self.db.execute(select(Candidate).where(Candidate.id == candidate_id))
        candidate = result.scalar_one_or_none()
        if not candidate:
            return {"error": "Candidate not found"}
        return {
            "candidate_id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "resume_text": candidate.resume_text,
        }

    async def extract_skills(self, candidate_id: int) -> dict:
        resume = await self.get_resume(candidate_id)
        if "error" in resume:
            return resume
        skills = _extract_skills_from_text(resume["resume_text"])
        return {"candidate_id": candidate_id, "skills": skills}

    async def get_experience(self, candidate_id: int) -> dict:
        resume = await self.get_resume(candidate_id)
        if "error" in resume:
            return resume
        text = resume["resume_text"]
        sentences = [s.strip() for s in re.split(r"[.\n]", text) if s.strip()]
        return {"candidate_id": candidate_id, "experience_summary": sentences[:5]}


class JDHandlers:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_job_description(self, job_id: int) -> dict:
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return {"error": "Job not found"}
        return {"job_id": job.id, "title": job.title, "description": job.description}

    async def get_required_skills(self, job_id: int) -> dict:
        jd = await self.get_job_description(job_id)
        if "error" in jd:
            return jd
        skills = _extract_skills_from_text(jd["description"])
        return {"job_id": job_id, "required_skills": skills}


class MemoryHandlers:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_answer(
        self,
        interview_id: int,
        question: str,
        answer: str,
        score: int,
    ) -> dict:
        return {
            "interview_id": interview_id,
            "stored": True,
            "question": question,
            "answer": answer,
            "score": score,
        }

    async def get_previous_questions(self, interview_id: int) -> dict:
        result = await self.db.execute(
            select(InterviewMessage)
            .where(
                InterviewMessage.interview_id == interview_id,
                InterviewMessage.role == MessageRole.assistant,
            )
            .order_by(InterviewMessage.timestamp)
        )
        messages = result.scalars().all()
        return {
            "interview_id": interview_id,
            "questions": [m.content for m in messages],
        }

    async def get_scores(self, interview_id: int) -> dict:
        result = await self.db.execute(
            select(Evaluation).where(Evaluation.interview_id == interview_id)
        )
        evaluations = result.scalars().all()
        return {
            "interview_id": interview_id,
            "scores": [
                {"skill": e.skill, "score": e.score, "feedback": e.feedback}
                for e in evaluations
            ],
        }
