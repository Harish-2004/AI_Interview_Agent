from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas import (
    EvaluationSchema,
    InterviewCreate,
    InterviewResponse,
    MessageCreate,
    MessageSchema,
    ReportResponse,
)
from app.db.models import Interview, InterviewStatus
from app.db.session import get_db
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interviews", tags=["interviews"])


async def _get_interview_or_404(db: AsyncSession, interview_id: int) -> Interview:
    result = await db.execute(
        select(Interview)
        .options(
            selectinload(Interview.messages),
            selectinload(Interview.evaluations),
        )
        .where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


async def _build_response(db: AsyncSession, interview: Interview) -> InterviewResponse:
    service = InterviewService(db)
    graph_state = await service.get_graph_state(interview.id)

    evaluations = [
        EvaluationSchema(
            skill=e.skill,
            score=e.score,
            feedback=e.feedback,
        )
        for e in interview.evaluations
    ]

    messages = [
        MessageSchema(
            role=m.role.value,
            content=m.content,
            timestamp=m.timestamp.isoformat(),
        )
        for m in interview.messages
    ]

    last_eval = None
    if graph_state.get("evaluations"):
        ev = graph_state["evaluations"][-1]
        last_eval = EvaluationSchema(
            skill=ev.get("skill", ""),
            score=ev.get("score", 0),
            feedback=ev.get("feedback", ""),
            strengths=ev.get("strengths", []),
            weaknesses=ev.get("weaknesses", []),
        )

    current_question = graph_state.get("current_question")
    if interview.status == InterviewStatus.completed:
        current_question = None

    return InterviewResponse(
        id=interview.id,
        candidate_id=interview.candidate_id,
        job_id=interview.job_id,
        status=interview.status.value,
        current_question=current_question,
        covered_skills=graph_state.get("covered_skills", []),
        remaining_skills=graph_state.get("remaining_skills", []),
        question_count=graph_state.get("question_count", 0),
        messages=messages,
        evaluations=evaluations,
        last_evaluation=last_eval,
    )


@router.post("", response_model=InterviewResponse, status_code=201)
async def start_interview(payload: InterviewCreate, db: AsyncSession = Depends(get_db)):
    from app.db.models import Candidate, Job

    candidate = await db.get(Candidate, payload.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    job = await db.get(Job, payload.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    service = InterviewService(db)
    try:
        interview = await service.start_interview(payload.candidate_id, payload.job_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    result = await db.execute(
        select(Interview)
        .options(
            selectinload(Interview.messages),
            selectinload(Interview.evaluations),
        )
        .where(Interview.id == interview.id)
    )
    interview = result.scalar_one()
    return await _build_response(db, interview)


@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(interview_id: int, db: AsyncSession = Depends(get_db)):
    interview = await _get_interview_or_404(db, interview_id)
    return await _build_response(db, interview)


@router.post("/{interview_id}/messages", response_model=InterviewResponse)
async def submit_message(
    interview_id: int,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
):
    interview = await _get_interview_or_404(db, interview_id)
    if interview.status == InterviewStatus.completed:
        raise HTTPException(status_code=409, detail="Interview already completed")

    service = InterviewService(db)
    try:
        await service.submit_answer(interview, payload.content)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    interview = await _get_interview_or_404(db, interview_id)
    return await _build_response(db, interview)


@router.get("/{interview_id}/report", response_model=ReportResponse)
async def get_report(interview_id: int, db: AsyncSession = Depends(get_db)):
    interview = await _get_interview_or_404(db, interview_id)
    if interview.status != InterviewStatus.completed:
        raise HTTPException(status_code=404, detail="Report not available; interview not completed")

    service = InterviewService(db)
    report = await service.get_report(interview)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportResponse(**report)
