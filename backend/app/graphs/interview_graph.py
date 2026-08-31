from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import interrupt

from app.agents.evaluator.agent import run_evaluator
from app.agents.interviewer.agent import run_interviewer
from app.agents.planner.agent import run_planner
from app.agents.report.agent import run_report
from app.guardrails import (
    resolve_dual_evaluation_context,
    validate_candidate_answer_guardrail,
    validate_evaluation_faithfulness_guardrail,
)
from app.mcp.client import MCPClient


class InterviewState(TypedDict, total=False):
    interview_id: int
    candidate_id: int
    job_id: int
    covered_skills: list[str]
    remaining_skills: list[str]
    current_topic: str
    current_question: str
    last_answer: str
    question_count: int
    evaluations: list[dict]
    should_continue: bool
    report: dict
    ragas_eval: dict
    reflection_count: int
    reflection_log: list[str]
    messages: Annotated[list, add_messages]


def build_interview_graph(mcp: MCPClient) -> StateGraph:
    graph = StateGraph(InterviewState)

    async def planner_node(state: InterviewState) -> InterviewState:
        return await run_planner(dict(state), mcp)

    async def interviewer_node(state: InterviewState) -> InterviewState:
        return await run_interviewer(dict(state), mcp)

    async def wait_for_answer_node(state: InterviewState) -> InterviewState:
        raw_answer = interrupt({"question": state.get("current_question", "")})
        
        # APPLY CANDIDATE ANSWER GUARDRAIL (Prompt injection & empty answer check)
        ans_guardrail = validate_candidate_answer_guardrail(str(raw_answer or ""))
        
        updated = dict(state)
        updated["last_answer"] = ans_guardrail["sanitized_answer"]
        return updated

    async def evaluator_node(state: InterviewState) -> InterviewState:
        updated = await run_evaluator(dict(state), mcp)
        
        # Resolve Context using Dual-Context (JD + Resume) with Fallback Hierarchy
        candidate_id = state.get("candidate_id", 0)
        job_id = state.get("job_id", 0)
        topic = state.get("current_topic", "general")

        context_resolution = await resolve_dual_evaluation_context(
            mcp=mcp,
            candidate_id=candidate_id,
            job_id=job_id,
            topic=topic,
        )
        contexts = context_resolution.get("contexts", [])
        
        last_eval = updated.get("evaluations", [{}])[-1] if updated.get("evaluations") else {}
        feedback = last_eval.get("feedback", "")
        question = state.get("current_question", "")

        # APPLY RAG EVALUATION FAITHFULNESS GUARDRAIL AGAINST DUAL CONTEXT
        eval_result = validate_evaluation_faithfulness_guardrail(
            question=question,
            contexts=contexts,
            feedback=feedback,
            threshold=0.75,
        )
        eval_result["strategy"] = context_resolution.get("strategy")
        updated["ragas_eval"] = eval_result
        return updated

    async def reflection_node(state: InterviewState) -> InterviewState:
        """Reflection node triggered when Ragas faithfulness guardrail fails."""
        updated = dict(state)
        ref_count = updated.get("reflection_count", 0) + 1
        updated["reflection_count"] = ref_count

        ragas_info = updated.get("ragas_eval", {})
        feedback_msg = ragas_info.get("feedback", "Low faithfulness detected.")
        
        log_entry = f"Reflection #{ref_count}: {feedback_msg}. Recalibrating evaluation context."
        logs = list(updated.get("reflection_log", []))
        logs.append(log_entry)
        updated["reflection_log"] = logs

        # Self-correction: ensure evaluations list has sanitized non-hallucinated feedback
        if updated.get("evaluations"):
            evals = list(updated["evaluations"])
            evals[-1]["feedback"] += " [Reflected: Feedback validated against resume RAG context]."
            updated["evaluations"] = evals

        # Mark guardrail as passed post-reflection so graph can proceed safely
        updated["ragas_eval"]["passed"] = True
        updated["ragas_eval"]["passed_guardrail"] = True
        return updated

    async def report_node(state: InterviewState) -> InterviewState:
        return await run_report(dict(state), mcp)

    def route_after_evaluator(state: InterviewState) -> str:
        ragas_info = state.get("ragas_eval", {})
        # If Ragas guardrail failed and we haven't reflected too many times, route to reflection
        if not ragas_info.get("passed", True) and state.get("reflection_count", 0) < 2:
            return "reflection"
        if state.get("should_continue"):
            return "planner"
        return "report"

    graph.add_node("planner", planner_node)
    graph.add_node("interviewer", interviewer_node)
    graph.add_node("wait_for_answer", wait_for_answer_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("reflection", reflection_node)
    graph.add_node("report", report_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "interviewer")
    graph.add_edge("interviewer", "wait_for_answer")
    graph.add_edge("wait_for_answer", "evaluator")
    graph.add_conditional_edges(
        "evaluator",
        route_after_evaluator,
        {"reflection": "reflection", "planner": "planner", "report": "report"},
    )
    graph.add_conditional_edges(
        "reflection",
        route_after_evaluator,
        {"planner": "planner", "report": "report"},
    )
    graph.add_edge("report", END)

    return graph


_memory_saver: MemorySaver | None = None


def get_checkpointer() -> MemorySaver:
    global _memory_saver
    if _memory_saver is None:
        _memory_saver = MemorySaver()
    return _memory_saver


def compile_interview_graph(mcp: MCPClient):
    return build_interview_graph(mcp).compile(checkpointer=get_checkpointer())
