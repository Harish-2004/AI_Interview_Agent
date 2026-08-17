import json

from pydantic import BaseModel, Field

from app.config import settings
from app.llm.gateway import llm_gateway
from app.mcp.client import MCPClient


class EvaluatorOutput(BaseModel):
    score: int = Field(ge=1, le=10)
    skill: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    feedback: str


EVALUATOR_SYSTEM = """You are a technical interview evaluator.
Score the candidate's answer from 1-10 for the given skill.
Respond with JSON only:
{"score": N, "skill": "...", "strengths": [...], "weaknesses": [...], "feedback": "..."}
Be fair and specific."""


async def run_evaluator(state: dict, mcp: MCPClient) -> dict:
    question = state.get("current_question", "")
    answer = state.get("last_answer", "")
    topic = state.get("current_topic", "")

    messages = [
        {"role": "system", "content": EVALUATOR_SYSTEM},
        {
            "role": "user",
            "content": json.dumps({"skill": topic, "question": question, "answer": answer}),
        },
    ]

    raw = await llm_gateway.generate(
        messages, "evaluator", interview_id=state.get("interview_id")
    )
    try:
        parsed = EvaluatorOutput.model_validate_json(raw)
        evaluation = parsed.model_dump()
    except Exception:
        evaluation = {
            "score": 5,
            "skill": topic,
            "strengths": [],
            "weaknesses": [],
            "feedback": "Unable to parse evaluation.",
        }

    await mcp.store_answer(
        state["interview_id"],
        question,
        answer,
        evaluation["score"],
    )

    evaluations = state.get("evaluations", [])
    evaluations.append(evaluation)
    state["evaluations"] = evaluations

    skill = evaluation["skill"]
    covered = state.get("covered_skills", [])
    if skill not in covered:
        covered.append(skill)
    state["covered_skills"] = covered

    remaining = [s for s in state.get("remaining_skills", []) if s.lower() != skill.lower()]
    state["remaining_skills"] = remaining

    max_q = settings.max_questions
    question_count = state.get("question_count", 0)
    state["should_continue"] = bool(remaining) and question_count < max_q

    return state
