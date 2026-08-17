import json

import pytest

from app.agents.planner.agent import run_planner
from app.mcp.client import MCPClient


@pytest.mark.asyncio
async def test_planner_picks_first_remaining_skill(db_session):
    from app.db.models import Candidate, Job

    candidate = Candidate(name="Test", email="t@t.com", resume_text="FastAPI developer")
    job = Job(title="Dev", description="FastAPI and Docker required")
    db_session.add_all([candidate, job])
    await db_session.commit()
    await db_session.refresh(candidate)
    await db_session.refresh(job)

    mcp = MCPClient(db_session)
    state = {
        "interview_id": 1,
        "candidate_id": candidate.id,
        "job_id": job.id,
        "covered_skills": [],
        "remaining_skills": ["FastAPI", "Docker"],
    }
    result = await run_planner(state, mcp)
    assert result["current_topic"] == "FastAPI"


@pytest.mark.asyncio
async def test_evaluator_output_structure(db_session, monkeypatch):
    from app.agents.evaluator.agent import run_evaluator

    async def mock_generate(messages, agent_name, **kwargs):
        return json.dumps(
            {
                "score": 8,
                "skill": "FastAPI",
                "strengths": ["API design"],
                "weaknesses": [],
                "feedback": "Good answer.",
            }
        )

    monkeypatch.setattr("app.agents.evaluator.agent.llm_gateway.generate", mock_generate)

    mcp = MCPClient(db_session)
    state = {
        "interview_id": 1,
        "current_question": "Tell me about FastAPI.",
        "last_answer": "I use FastAPI daily.",
        "current_topic": "FastAPI",
        "covered_skills": [],
        "remaining_skills": ["FastAPI", "Docker"],
        "question_count": 1,
        "evaluations": [],
    }
    result = await run_evaluator(state, mcp)
    assert result["evaluations"][-1]["score"] == 8
    assert "FastAPI" in result["covered_skills"]
