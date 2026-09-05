import json

from pydantic import BaseModel

from app.llm.gateway import llm_gateway
from app.mcp.client import MCPClient


class PlannerOutput(BaseModel):
    nextTopic: str


PLANNER_SYSTEM = """You are a technical interview planner.
Given covered and remaining skills, pick the next skill to assess.
Respond with JSON only: {{"nextTopic": "<skill>"}}
Pick from remaining_skills. If none remain, pick the most important uncovered topic."""


from langchain_core.prompts import ChatPromptTemplate

planner_prompt_template = ChatPromptTemplate.from_messages([
    ("system", PLANNER_SYSTEM),
    ("user", "{skills_payload}"),
])


async def run_planner(state: dict, mcp: MCPClient) -> dict:
    covered = state.get("covered_skills", [])
    remaining = state.get("remaining_skills", [])

    if not remaining and state.get("job_id"):
        jd_skills = await mcp.get_required_skills(state["job_id"])
        if "required_skills" in jd_skills:
            remaining = [s for s in jd_skills["required_skills"] if s not in covered]
            state["remaining_skills"] = remaining

    payload = json.dumps({"coveredSkills": covered, "remainingSkills": remaining})
    prompt_value = planner_prompt_template.format_messages(skills_payload=payload)
    messages = [
        {"role": "user" if msg.type in ("human", "user") else msg.type, "content": msg.content}
        for msg in prompt_value
    ]

    if remaining:
        next_topic = remaining[0]
    else:
        raw = await llm_gateway.generate(
            messages, "planner", interview_id=state.get("interview_id")
        )
        try:
            parsed = PlannerOutput.model_validate_json(raw)
            next_topic = parsed.nextTopic
        except Exception:
            next_topic = "general"

    state["current_topic"] = next_topic
    return state
