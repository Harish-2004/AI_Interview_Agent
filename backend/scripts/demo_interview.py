"""End-to-end demo: create candidate, job, run interview with mocked LLM."""

import asyncio
import json
import sys

import httpx

BASE_URL = "http://localhost:8000"

DEMO_ANSWERS = [
    "I built async REST APIs with FastAPI, Pydantic validation, and dependency injection.",
    "I use multi-stage Dockerfiles with uvicorn and docker-compose for local development.",
    "I optimize queries with indexes, EXPLAIN ANALYZE, and connection pooling in PostgreSQL.",
]


async def run_demo() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        health = await client.get("/health")
        if health.status_code != 200:
            print("API not running. Start with: make dev")
            sys.exit(1)

        candidate_resp = await client.post(
            "/candidates",
            json={
                "name": "Jane Doe",
                "email": "jane.demo@example.com",
                "resume_text": (
                    "Senior backend engineer with FastAPI, Docker, and PostgreSQL experience."
                ),
            },
        )
        candidate_resp.raise_for_status()
        candidate = candidate_resp.json()
        print(f"Created candidate: {candidate['id']}")

        job_resp = await client.post(
            "/jobs",
            json={
                "title": "Backend Engineer",
                "description": (
                    "Requires FastAPI, Docker, and SQL skills for microservices work."
                ),
            },
        )
        job_resp.raise_for_status()
        job = job_resp.json()
        print(f"Created job: {job['id']}")

        start_resp = await client.post(
            "/interviews",
            json={"candidate_id": candidate["id"], "job_id": job["id"]},
        )
        start_resp.raise_for_status()
        interview = start_resp.json()
        print(f"Started interview: {interview['id']}")
        print(f"Question: {interview['current_question']}")

        answer_idx = 0
        while interview["status"] != "completed" and answer_idx < len(DEMO_ANSWERS):
            answer = DEMO_ANSWERS[answer_idx]
            answer_idx += 1
            msg_resp = await client.post(
                f"/interviews/{interview['id']}/messages",
                json={"content": answer},
            )
            msg_resp.raise_for_status()
            interview = msg_resp.json()
            print(f"Answered. Score skill: {interview.get('last_evaluation')}")
            if interview.get("current_question"):
                print(f"Next question: {interview['current_question']}")

        report_resp = await client.get(f"/interviews/{interview['id']}/report")
        report_resp.raise_for_status()
        report = report_resp.json()
        print("\n=== Final Report ===")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(run_demo())
