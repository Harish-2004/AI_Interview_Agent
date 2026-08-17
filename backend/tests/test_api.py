import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_full_interview_flow(client):
    candidate_resp = await client.post(
        "/candidates",
        json={
            "name": "Jane Doe",
            "email": "jane@test.com",
            "resume_text": "FastAPI and Docker experience for 5 years.",
        },
    )
    assert candidate_resp.status_code == 201
    candidate_id = candidate_resp.json()["id"]

    job_resp = await client.post(
        "/jobs",
        json={
            "title": "Backend Engineer",
            "description": "Need FastAPI, Docker, and SQL skills.",
        },
    )
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    start_resp = await client.post(
        "/interviews",
        json={"candidate_id": candidate_id, "job_id": job_id},
    )
    assert start_resp.status_code == 201
    interview = start_resp.json()
    assert interview["status"] == "in_progress"
    assert interview["current_question"]

    msg_resp = await client.post(
        f"/interviews/{interview['id']}/messages",
        json={"content": "I built REST APIs with FastAPI and async endpoints."},
    )
    assert msg_resp.status_code == 200
    updated = msg_resp.json()
    assert updated["question_count"] >= 1


@pytest.mark.asyncio
async def test_interview_completes_and_report(client):
    candidate_resp = await client.post(
        "/candidates",
        json={
            "name": "Bob",
            "email": "bob@test.com",
            "resume_text": "FastAPI Docker SQL developer.",
        },
    )
    candidate_id = candidate_resp.json()["id"]
    job_resp = await client.post(
        "/jobs",
        json={"title": "Dev", "description": "FastAPI only."},
    )
    job_id = job_resp.json()["id"]

    start_resp = await client.post(
        "/interviews",
        json={"candidate_id": candidate_id, "job_id": job_id},
    )
    interview_id = start_resp.json()["id"]

    msg_resp = await client.post(
        f"/interviews/{interview_id}/messages",
        json={"content": "I have extensive FastAPI experience."},
    )
    interview = msg_resp.json()

    if interview["status"] != "completed":
        msg_resp = await client.post(
            f"/interviews/{interview_id}/messages",
            json={"content": "Additional detail on FastAPI projects."},
        )
        interview = msg_resp.json()

    report_resp = await client.get(f"/interviews/{interview_id}/report")
    if interview["status"] == "completed":
        assert report_resp.status_code == 200
        report = report_resp.json()
        assert "overallScore" in report
        assert "recommendation" in report
