import pytest

from app.graphs.interview_graph import compile_interview_graph
from app.mcp.client import MCPClient
from langgraph.types import Command


@pytest.mark.asyncio
async def test_graph_interrupt_and_resume(db_session):
    from app.db.models import Candidate, Job

    candidate = Candidate(
        name="Jane",
        email="j@t.com",
        resume_text="FastAPI developer with Docker experience.",
    )
    job = Job(title="Backend", description="FastAPI and Docker required.")
    db_session.add_all([candidate, job])
    await db_session.commit()
    await db_session.refresh(candidate)
    await db_session.refresh(job)

    mcp = MCPClient(db_session)
    graph = compile_interview_graph(mcp)
    config = {"configurable": {"thread_id": "test-graph-1"}}

    initial = {
        "interview_id": 1,
        "candidate_id": candidate.id,
        "job_id": job.id,
        "covered_skills": [],
        "remaining_skills": ["FastAPI", "Docker"],
        "question_count": 0,
        "evaluations": [],
        "should_continue": True,
    }

    await graph.ainvoke(initial, config)
    snapshot = graph.get_state(config)
    assert snapshot.values.get("current_question")
    assert snapshot.next

    await graph.ainvoke(Command(resume="I use FastAPI for async REST APIs."), config)
    snapshot = graph.get_state(config)
    assert snapshot.values.get("evaluations")
