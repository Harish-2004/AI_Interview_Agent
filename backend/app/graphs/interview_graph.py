from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import interrupt

from app.agents.evaluator.agent import run_evaluator
from app.agents.interviewer.agent import run_interviewer
from app.agents.planner.agent import run_planner
from app.agents.report.agent import run_report
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
    messages: Annotated[list, add_messages]


def build_interview_graph(mcp: MCPClient):
    graph = StateGraph(InterviewState)

    async def planner_node(state: InterviewState) -> InterviewState:
        return await run_planner(dict(state), mcp)

    async def interviewer_node(state: InterviewState) -> InterviewState:
        return await run_interviewer(dict(state), mcp)

    async def wait_for_answer_node(state: InterviewState) -> InterviewState:
        answer = interrupt({"question": state.get("current_question", "")})
        updated = dict(state)
        updated["last_answer"] = answer
        return updated

    async def evaluator_node(state: InterviewState) -> InterviewState:
        return await run_evaluator(dict(state), mcp)

    async def report_node(state: InterviewState) -> InterviewState:
        return await run_report(dict(state), mcp)

    def route_after_evaluator(state: InterviewState) -> str:
        if state.get("should_continue"):
            return "planner"
        return "report"

    graph.add_node("planner", planner_node)
    graph.add_node("interviewer", interviewer_node)
    graph.add_node("wait_for_answer", wait_for_answer_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("report", report_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "interviewer")
    graph.add_edge("interviewer", "wait_for_answer")
    graph.add_edge("wait_for_answer", "evaluator")
    graph.add_conditional_edges("evaluator", route_after_evaluator, {"planner": "planner", "report": "report"})
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
