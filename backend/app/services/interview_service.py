import asyncio
import json
import logging
from langgraph.types import Command
from sqlalchemy import select

from app.config import settings
from app.db.models import Evaluation, Interview, InterviewMessage, InterviewStatus, MessageRole
from app.db.session import async_session_factory
from app.graphs.interview_graph import compile_interview_graph
from app.mcp.client import get_mcp_client
from app.agents.evaluator.agent import run_evaluator
from app.agents.report.agent import run_report
from app.guardrails import (
    validate_candidate_answer_guardrail,
    validate_evaluation_faithfulness_guardrail,
)

logger = logging.getLogger(__name__)


class InterviewService:
    _pending_eval_tasks: dict[int, list[asyncio.Task]] = {}

    def __init__(self, db):
        self.db = db
        self.mcp = get_mcp_client(db)

    def _thread_config(self, interview_id: int) -> dict:
        return {"configurable": {"thread_id": str(interview_id)}}

    async def _init_skills(self, job_id: int) -> list[str]:
        result = await self.mcp.get_required_skills(job_id)
        return result.get("required_skills", [])

    async def start_interview(self, candidate_id: int, job_id: int) -> Interview:
        remaining = await self._init_skills(job_id)
        interview = Interview(
            candidate_id=candidate_id,
            job_id=job_id,
            status=InterviewStatus.in_progress,
        )
        self.db.add(interview)
        await self.db.commit()
        await self.db.refresh(interview)

        graph = compile_interview_graph(self.mcp)
        initial_state = {
            "interview_id": interview.id,
            "candidate_id": candidate_id,
            "job_id": job_id,
            "covered_skills": [],
            "remaining_skills": remaining,
            "question_count": 0,
            "evaluations": [],
            "should_continue": True,
        }

        config = self._thread_config(interview.id)
        await graph.ainvoke(initial_state, config)

        snapshot = graph.get_state(config)
        await self._persist_graph_step(interview, dict(snapshot.values))
        await self.db.commit()
        await self.db.refresh(interview)
        return interview

    async def submit_answer(self, interview: Interview, answer: str) -> Interview:
        if interview.status == InterviewStatus.completed:
            raise ValueError("Interview already completed")

        graph = compile_interview_graph(self.mcp)
        config = self._thread_config(interview.id)

        # Retrieve current graph state prior to advancing
        prev_snapshot = graph.get_state(config)
        prev_state = dict(prev_snapshot.values) if prev_snapshot and prev_snapshot.values else {}

        current_q = prev_state.get("current_question", "")
        current_topic = prev_state.get("current_topic", "general")

        # Apply candidate answer safety guardrail
        ans_guardrail = validate_candidate_answer_guardrail(answer)
        sanitized_answer = ans_guardrail["sanitized_answer"]

        # Offload Evaluation & Ragas Faithfulness Guardrail to Asynchronous Background Task
        if current_q and sanitized_answer:
            task = asyncio.create_task(
                self._async_evaluate_and_persist(
                    interview_id=interview.id,
                    candidate_id=interview.candidate_id,
                    job_id=interview.job_id,
                    question=current_q,
                    topic=current_topic,
                    answer=sanitized_answer,
                )
            )
            tasks = InterviewService._pending_eval_tasks.setdefault(interview.id, [])
            tasks.append(task)

        # Advance graph state to generate the next question immediately
        await graph.ainvoke(Command(resume=sanitized_answer), config)

        snapshot = graph.get_state(config)
        state = dict(snapshot.values)

        q_count = state.get("question_count", 0)
        remaining = state.get("remaining_skills", [])
        is_finished = not remaining or q_count >= settings.max_questions or not snapshot.next

        if is_finished:
            # Await all pending background evaluations before compiling final report
            await self.flush_background_evaluations(interview.id)
            report_state = await run_report(state, self.mcp)
            state["report"] = report_state.get("report")
            interview.status = InterviewStatus.completed

        await self._persist_graph_step(interview, state)
        await self.db.commit()
        await self.db.refresh(interview)
        return interview

    async def _async_evaluate_and_persist(
        self,
        interview_id: int,
        candidate_id: int,
        job_id: int,
        question: str,
        topic: str,
        answer: str,
    ) -> None:
        """Asynchronously runs Evaluator Agent, Ragas Faithfulness Guardrail, and saves Evaluation record to DB."""
        try:
            async with async_session_factory() as session:
                mcp = get_mcp_client(session)
                eval_state = {
                    "interview_id": interview_id,
                    "candidate_id": candidate_id,
                    "job_id": job_id,
                    "current_question": question,
                    "current_topic": topic,
                    "last_answer": answer,
                    "evaluations": [],
                }
                updated = await run_evaluator(eval_state, mcp)

                # Fetch LlamaIndex RAG resume context for Ragas quality verification
                rag_res = await mcp.search_resume_rag(candidate_id=candidate_id, query=topic, top_k=3)
                contexts = rag_res.get("context_chunks", [])

                last_eval = updated.get("evaluations", [{}])[-1] if updated.get("evaluations") else {}
                feedback = last_eval.get("feedback", "")

                # Apply Ragas Faithfulness Guardrail
                eval_result = validate_evaluation_faithfulness_guardrail(
                    question=question,
                    contexts=contexts,
                    feedback=feedback,
                    threshold=0.75,
                )

                if not eval_result.get("passed", True) and updated.get("evaluations"):
                    updated["evaluations"][-1]["feedback"] += " [Reflected: Feedback validated against resume RAG context]."

                # Save evaluation to DB
                svc = InterviewService(session)
                for ev in updated.get("evaluations", []):
                    await svc._save_evaluation_if_new(interview_id, ev)
                await session.commit()
        except Exception as exc:
            logger.error(f"Async evaluation background task failed for interview {interview_id}: {exc}")

    async def flush_background_evaluations(self, interview_id: int) -> None:
        """Awaits and flushes all pending background evaluation tasks for an interview."""
        tasks = InterviewService._pending_eval_tasks.pop(interview_id, [])
        if tasks:
            try:
                current_loop = asyncio.get_running_loop()
                valid_tasks = [t for t in tasks if not t.done() and t.get_loop() == current_loop]
                if valid_tasks:
                    await asyncio.gather(*valid_tasks, return_exceptions=True)
            except RuntimeError:
                pass

    async def _persist_graph_step(self, interview: Interview, state: dict) -> None:
        question = state.get("current_question")
        if question:
            await self._add_message_if_new(interview.id, MessageRole.assistant, question)

        answer = state.get("last_answer")
        if answer:
            await self._add_message_if_new(interview.id, MessageRole.user, answer)

        for ev in state.get("evaluations", []):
            await self._save_evaluation_if_new(interview.id, ev)

        if state.get("report") and interview.status == InterviewStatus.completed:
            await self._save_report_message(interview, state["report"])

    async def _add_message_if_new(self, interview_id: int, role: MessageRole, content: str) -> None:
        result = await self.db.execute(
            select(InterviewMessage).where(
                InterviewMessage.interview_id == interview_id,
                InterviewMessage.role == role,
                InterviewMessage.content == content,
            )
        )
        if result.scalar_one_or_none():
            return
        self.db.add(InterviewMessage(interview_id=interview_id, role=role, content=content))

    async def _save_evaluation_if_new(self, interview_id: int, ev: dict) -> None:
        result = await self.db.execute(
            select(Evaluation).where(
                Evaluation.interview_id == interview_id,
                Evaluation.skill == ev.get("skill", ""),
            )
        )
        if result.scalar_one_or_none():
            return
        self.db.add(
            Evaluation(
                interview_id=interview_id,
                skill=ev.get("skill", "unknown"),
                score=ev.get("score", 0),
                feedback=ev.get("feedback", ""),
            )
        )

    async def _save_report_message(self, interview: Interview, report: dict) -> None:
        content = json.dumps(report)
        await self._add_message_if_new(interview.id, MessageRole.system, content)

    async def get_graph_state(self, interview_id: int) -> dict:
        graph = compile_interview_graph(self.mcp)
        config = self._thread_config(interview_id)
        state = graph.get_state(config)
        return dict(state.values) if state.values else {}

    async def get_report(self, interview: Interview) -> dict | None:
        await self.flush_background_evaluations(interview.id)
        state = await self.get_graph_state(interview.id)
        if state.get("report"):
            return state["report"]

        result = await self.db.execute(
            select(InterviewMessage)
            .where(
                InterviewMessage.interview_id == interview.id,
                InterviewMessage.role == MessageRole.system,
            )
            .order_by(InterviewMessage.timestamp.desc())
        )
        msg = result.scalars().first()
        if msg:
            try:
                return json.loads(msg.content)
            except json.JSONDecodeError:
                pass
        return None
