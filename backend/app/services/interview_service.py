from langgraph.types import Command

from app.db.models import Evaluation, Interview, InterviewMessage, InterviewStatus, MessageRole
from app.graphs.interview_graph import compile_interview_graph
from app.mcp.client import get_mcp_client


class InterviewService:
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

        await graph.ainvoke(Command(resume=answer), config)

        snapshot = graph.get_state(config)
        state = dict(snapshot.values)

        if not snapshot.next:
            interview.status = InterviewStatus.completed

        await self._persist_graph_step(interview, state)
        await self.db.commit()
        await self.db.refresh(interview)
        return interview

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
        from sqlalchemy import select

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
        from sqlalchemy import select

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
        import json

        content = json.dumps(report)
        await self._add_message_if_new(interview.id, MessageRole.system, content)

    async def get_graph_state(self, interview_id: int) -> dict:
        graph = compile_interview_graph(self.mcp)
        config = self._thread_config(interview_id)
        state = graph.get_state(config)
        return dict(state.values) if state.values else {}

    async def get_report(self, interview: Interview) -> dict | None:
        state = await self.get_graph_state(interview.id)
        if state.get("report"):
            return state["report"]

        from sqlalchemy import select

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
            import json

            try:
                return json.loads(msg.content)
            except json.JSONDecodeError:
                pass
        return None
