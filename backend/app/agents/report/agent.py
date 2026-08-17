import json

from pydantic import BaseModel, Field

from app.llm.gateway import llm_gateway
from app.mcp.client import MCPClient


class ReportOutput(BaseModel):
    overallScore: int = Field(ge=1, le=10)
    strengths: list[str]
    weaknesses: list[str]
    recommendation: str


REPORT_SYSTEM = """You are a recruiter report generator.
Summarize the interview evaluations into a hiring recommendation.
Respond with JSON only:
{"overallScore": N, "strengths": [...], "weaknesses": [...], "recommendation": "..."}
overallScore is the average score rounded. recommendation is one short sentence."""


async def run_report(state: dict, mcp: MCPClient) -> dict:
    scores_data = await mcp.get_scores(state["interview_id"])
    evaluations = state.get("evaluations", []) or [
        {"skill": s["skill"], "score": s["score"], "feedback": s["feedback"]}
        for s in scores_data.get("scores", [])
    ]

    if evaluations:
        avg = round(sum(e["score"] for e in evaluations) / len(evaluations))
    else:
        avg = 0

    messages = [
        {"role": "system", "content": REPORT_SYSTEM},
        {"role": "user", "content": json.dumps({"evaluations": evaluations, "averageScore": avg})},
    ]

    raw = await llm_gateway.generate(messages, "report", interview_id=state.get("interview_id"))
    try:
        parsed = ReportOutput.model_validate_json(raw)
        report = parsed.model_dump()
    except Exception:
        all_strengths: list[str] = []
        all_weaknesses: list[str] = []
        for e in evaluations:
            all_strengths.extend(e.get("strengths", []))
            all_weaknesses.extend(e.get("weaknesses", []))
        report = {
            "overallScore": avg or 5,
            "strengths": list(dict.fromkeys(all_strengths))[:5],
            "weaknesses": list(dict.fromkeys(all_weaknesses))[:5],
            "recommendation": "Review recommended based on interview performance.",
        }

    state["report"] = report
    state["should_continue"] = False
    return state
