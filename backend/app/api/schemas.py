from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CandidateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    resume_text: str = Field(min_length=10, max_length=50000)


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    resume_text: str


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=10, max_length=50000)


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str


class InterviewCreate(BaseModel):
    candidate_id: int
    job_id: int


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class EvaluationSchema(BaseModel):
    skill: str
    score: int
    feedback: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class MessageSchema(BaseModel):
    role: str
    content: str
    timestamp: str


class InterviewResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    status: str
    current_question: str | None = None
    covered_skills: list[str] = Field(default_factory=list)
    remaining_skills: list[str] = Field(default_factory=list)
    question_count: int = 0
    messages: list[MessageSchema] = Field(default_factory=list)
    evaluations: list[EvaluationSchema] = Field(default_factory=list)
    last_evaluation: EvaluationSchema | None = None


class ReportResponse(BaseModel):
    overallScore: int
    strengths: list[str]
    weaknesses: list[str]
    recommendation: str
