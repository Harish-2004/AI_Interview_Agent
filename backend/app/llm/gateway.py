import json
import logging
import time
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

MOCK_RESPONSES: dict[str, str] = {
    "planner": json.dumps({"nextTopic": "FastAPI"}),
    "interviewer": json.dumps(
        {
            "question": "Tell me about your experience with FastAPI.",
            "isFollowUp": False,
        }
    ),
    "evaluator": json.dumps(
        {
            "score": 8,
            "skill": "FastAPI",
            "strengths": ["REST API design", "async endpoints"],
            "weaknesses": ["advanced middleware"],
            "feedback": "Strong practical FastAPI experience.",
        }
    ),
    "report": json.dumps(
        {
            "overallScore": 8,
            "strengths": ["FastAPI", "REST APIs"],
            "weaknesses": ["SQL Optimization"],
            "recommendation": "Proceed to next round",
        }
    ),
}

TOPIC_QUESTIONS = {
    "FastAPI": "Tell me about your experience with FastAPI.",
    "Docker": "How do you containerize FastAPI applications?",
    "SQL": "How do you optimize SQL queries in production?",
}


def _mock_content(messages: list[dict[str, str]], agent_name: str) -> str:
    if agent_name == "interviewer":
        user_msg = messages[-1].get("content", "") if messages else ""
        try:
            ctx = json.loads(user_msg)
            topic = ctx.get("topic", "FastAPI")
            question = TOPIC_QUESTIONS.get(topic, f"Tell me about your experience with {topic}.")
            return json.dumps({"question": question, "isFollowUp": False})
        except json.JSONDecodeError:
            pass
    if agent_name == "evaluator":
        user_msg = messages[-1].get("content", "") if messages else ""
        try:
            ctx = json.loads(user_msg)
            skill = ctx.get("skill", "FastAPI")
            return json.dumps(
                {
                    "score": 8,
                    "skill": skill,
                    "strengths": [f"{skill} fundamentals"],
                    "weaknesses": [],
                    "feedback": f"Solid {skill} knowledge.",
                }
            )
        except json.JSONDecodeError:
            pass
    if agent_name == "planner":
        user_msg = messages[-1].get("content", "") if messages else ""
        try:
            ctx = json.loads(user_msg)
            remaining = ctx.get("remainingSkills", [])
            if remaining:
                return json.dumps({"nextTopic": remaining[0]})
        except json.JSONDecodeError:
            pass
    return MOCK_RESPONSES.get(agent_name, "{}")


class LLMGateway:
    """Single entry point for all LLM calls via LiteLLM."""

    def __init__(self):
        # Enable LiteLLM's LangSmith callback to trace all LLM completions
        if settings.langchain_tracing_v2:
            try:
                import litellm
                litellm.success_callback = ["langsmith"]
                litellm.failure_callback = ["langsmith"]
            except ImportError:
                pass

    async def generate(
        self,
        messages: list[dict[str, str]],
        agent_name: str,
        *,
        interview_id: int | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        model = settings.model_for_agent(agent_name)
        start = time.perf_counter()

        if not settings.use_real_llm:
            content = _mock_content(messages, agent_name)
            logger.info(
                "llm_mock_response",
                extra={
                    "agent": agent_name,
                    "model": model,
                    "interview_id": interview_id,
                    "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                },
            )
            return content

        import litellm

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "num_retries": 2,
            "fallbacks": ["ollama/gemma:2b", "ollama/llama3.2", "ollama/qwen2.5-coder:7b", "gemini/gemini-2.5-flash"],
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = await litellm.acompletion(**kwargs)
            content = response.choices[0].message.content or ""
            logger.info(
                "llm_response",
                extra={
                    "agent": agent_name,
                    "model": model,
                    "interview_id": interview_id,
                    "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                },
            )
            return content
        except Exception as exc:
            logger.error(f"LiteLLM call failed for agent '{agent_name}' with model '{model}': {exc}")
            # Fallback to mock content so application never crashes on API key/network error
            print(f"\n⚠️ LLM API Error ({model}): {exc}. Falling back to mock response for demo.")
            return _mock_content(messages, agent_name)


llm_gateway = LLMGateway()
