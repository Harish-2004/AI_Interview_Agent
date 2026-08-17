from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import JobCreate, JobResponse
from app.db.models import Job
from app.db.session import get_db

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(payload: JobCreate, db: AsyncSession = Depends(get_db)):
    job = Job(title=payload.title, description=payload.description)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job
