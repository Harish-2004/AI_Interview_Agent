import json

from pydantic import BaseModel

from app.guardrails import validate_interview_question_guardrail
from app.llm.gateway import llm_gateway
from app.mcp.client import MCPClient


class InterviewerOutput(BaseModel):
    question: str
    isFollowUp: bool = False


INTERVIEWER_SYSTEM = """You are a technical interviewer.
Ask clear, focused questions about the given skill/topic.
Use resume and job context when relevant.
Respond with JSON only: {{"question": "<question>", "isFollowUp": true|false}}
Keep questions concise and professional."""


from langchain_core.prompts import ChatPromptTemplate

interviewer_prompt_template = ChatPromptTemplate.from_messages([
    ("system", INTERVIEWER_SYSTEM),
    ("user", "{context_json}"),
])


async def run_interviewer(state: dict, mcp: MCPClient) -> dict:
    topic = state.get("current_topic", "general")
    resume = await mcp.get_resume(state["candidate_id"])
    jd = await mcp.get_job_description(state["job_id"])
    prev = await mcp.get_previous_questions(state["interview_id"])

    context = {
        "topic": topic,
        "resume_summary": resume.get("resume_text", "")[:500],
        "job_title": jd.get("title", ""),
        "previous_questions": prev.get("questions", []),
        "last_answer": state.get("last_answer"),
    }

    # Format messages using LangChain ChatPromptTemplate
    prompt_value = interviewer_prompt_template.format_messages(context_json=json.dumps(context))
    messages = [
        {"role": "user" if msg.type in ("human", "user") else msg.type, "content": msg.content}
        for msg in prompt_value
    ]

    raw = await llm_gateway.generate(
        messages, "interviewer", interview_id=state.get("interview_id")
    )
    try:
        parsed = InterviewerOutput.model_validate_json(raw)
        raw_question = parsed.question
    except Exception:
        raw_question = f"Tell me about your experience with {topic}."

    # APPLY INTERVIEW QUESTION GUARDRAIL & DEDUPLICATION
    prev_questions = prev.get("questions", [])
    guardrail_res = validate_interview_question_guardrail(
        raw_question, topic=topic, previous_questions=prev_questions
    )
    validated_question = guardrail_res["validated_question"]

    state["current_question"] = validated_question
    state["question_count"] = state.get("question_count", 0) + 1
    return state
