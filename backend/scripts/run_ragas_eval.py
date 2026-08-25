"""Benchmark CLI Script: Runs end-to-end Ragas evaluation across candidate resumes and job descriptions."""

import asyncio
import json
from app.eval.ragas_evaluator import ragas_evaluator
from app.services.rag_service import rag_service


SAMPLE_DATASETS = [
    {
        "candidate_id": 101,
        "job_id": 201,
        "candidate_name": "Alice Smith",
        "resume_text": """
Alice Smith - Senior Backend Engineer
Experience:
- 4 years building high-throughput FastAPI and AsyncIO microservices at TechCorp.
- Managed PostgreSQL and Redis caching layers handling 50,000 requests per minute.
- Automated Kubernetes cluster deployments using Helm and Docker containerization.
Skills: Python, FastAPI, PostgreSQL, Redis, Kubernetes, Docker, Microservices, REST APIs.
""",
        "job_description": """
Senior Python Engineer Needed
Requirements:
- 3+ years experience with Python microservices (FastAPI/Flask).
- Expertise in PostgreSQL database design and Redis caching.
- Experience with Docker containerization and Kubernetes orchestration.
""",
        "user_query": "Extract candidate microservices and database experience.",
        "generated_answer": "Alice Smith has 4 years of experience building FastAPI microservices at TechCorp, managing PostgreSQL databases and Redis caching layers.",
        "ground_truth": "Alice Smith worked for 4 years on FastAPI microservices, managing PostgreSQL and Redis caching at TechCorp.",
    },
    {
        "candidate_id": 102,
        "job_id": 202,
        "candidate_name": "Bob Jones",
        "resume_text": """
Bob Jones - Frontend Developer
Experience:
- 3 years experience building responsive web UI using React, Next.js, and Tailwind CSS.
- Integrated REST endpoints and WebSocket live streaming for interactive dashboards.
Skills: JavaScript, TypeScript, React, Next.js, HTML5, CSS3, WebSockets.
""",
        "job_description": """
Full Stack Engineer
Requirements:
- Strong knowledge of React frontend and Python backend.
""",
        "user_query": "Evaluate Bob Jones's Python backend experience.",
        "generated_answer": "Bob Jones is primarily a Frontend Developer with React and Next.js experience. No backend Python experience was found in the resume.",
        "ground_truth": "Bob Jones has React and Next.js frontend experience but lacks backend Python experience.",
    },
]


async def run_benchmark():
    print("=" * 70)
    print("        RAGAS EVALUATION & LLAMAINDEX BENCHMARK RUNNER")
    print("=" * 70)

    total_faithfulness = 0.0
    total_relevance = 0.0
    total_precision = 0.0
    total_recall = 0.0

    eval_results = []

    for idx, sample in enumerate(SAMPLE_DATASETS, 1):
        print(f"\n[Sample {idx}] Evaluating candidate: {sample['candidate_name']}")
        
        # 1. Index document with LlamaIndex
        rag_service.index_resume(sample["candidate_id"], sample["resume_text"])
        
        # 2. Perform LlamaIndex RAG retrieval
        retrieved_contexts = rag_service.retrieve_resume_context(
            candidate_id=sample["candidate_id"],
            query=sample["user_query"],
            top_k=3,
        )
        
        # 3. Execute Ragas evaluation
        eval_res = ragas_evaluator.evaluate_sample(
            question=sample["user_query"],
            contexts=retrieved_contexts,
            answer=sample["generated_answer"],
            ground_truth=sample["ground_truth"],
        )

        total_faithfulness += eval_res.faithfulness
        total_relevance += eval_res.answer_relevancy
        total_precision += eval_res.context_precision
        total_recall += eval_res.context_recall

        sample_summary = {
            "candidate": sample["candidate_name"],
            "query": sample["user_query"],
            "retrieved_chunks": len(retrieved_contexts),
            "metrics": eval_res.model_dump(),
        }
        eval_results.append(sample_summary)

        print(f"  - Faithfulness: {eval_res.faithfulness:.2f}")
        print(f"  - Answer Relevance: {eval_res.answer_relevancy:.2f}")
        print(f"  - Context Precision: {eval_res.context_precision:.2f}")
        print(f"  - Context Recall: {eval_res.context_recall:.2f}")
        print(f"  - Guardrail Passed: {'[PASS]' if eval_res.passed_guardrail else '[FAIL]'}")

    n = len(SAMPLE_DATASETS)
    print("\n" + "=" * 70)
    print("                    OVERALL BENCHMARK SUMMARY")
    print("=" * 70)
    print(f" Mean Faithfulness       : {total_faithfulness / n:.2f}")
    print(f" Mean Answer Relevance   : {total_relevance / n:.2f}")
    print(f" Mean Context Precision  : {total_precision / n:.2f}")
    print(f" Mean Context Recall     : {total_recall / n:.2f}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_benchmark())
