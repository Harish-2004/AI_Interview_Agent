from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import CandidateCreate, CandidateResponse
from app.db.models import Candidate
from app.db.session import get_db

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post("", response_model=CandidateResponse, status_code=201)
async def create_candidate(payload: CandidateCreate, db: AsyncSession = Depends(get_db)):
    candidate = Candidate(
        name=payload.name,
        email=str(payload.email),
        resume_text=payload.resume_text,
    )
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    return candidate
