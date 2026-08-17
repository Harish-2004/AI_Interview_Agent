# API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

## Candidates

### Create candidate

```http
POST /candidates
Content-Type: application/json
```

**Request:**
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "resume_text": "Senior backend engineer with 5 years FastAPI experience. Built REST APIs, async endpoints, and PostgreSQL integrations."
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "Jane Doe",
  "email": "jane@example.com",
  "resume_text": "Senior backend engineer..."
}
```

## Jobs

### Create job

```http
POST /jobs
Content-Type: application/json
```

**Request:**
```json
{
  "title": "Backend Engineer",
  "description": "We need a backend engineer skilled in FastAPI, Docker, and SQL. You will build microservices and containerized deployments."
}
```

**Response (201):**
```json
{
  "id": 1,
  "title": "Backend Engineer",
  "description": "We need a backend engineer..."
}
```

## Interviews

### Start interview

```http
POST /interviews
Content-Type: application/json
```

**Request:**
```json
{
  "candidate_id": 1,
  "job_id": 1
}
```

**Response (201):**
```json
{
  "id": 1,
  "candidate_id": 1,
  "job_id": 1,
  "status": "in_progress",
  "current_question": "Tell me about your experience with FastAPI.",
  "covered_skills": [],
  "remaining_skills": ["FastAPI", "Docker", "SQL"],
  "question_count": 1
}
```

### Get interview

```http
GET /interviews/{id}
```

**Response (200):**
```json
{
  "id": 1,
  "candidate_id": 1,
  "job_id": 1,
  "status": "in_progress",
  "current_question": "How do you containerize FastAPI applications?",
  "covered_skills": ["FastAPI"],
  "remaining_skills": ["Docker", "SQL"],
  "question_count": 2,
  "messages": [
    {"role": "assistant", "content": "Tell me about your FastAPI experience.", "timestamp": "2026-06-15T10:00:00Z"},
    {"role": "user", "content": "I built async REST APIs with Pydantic validation.", "timestamp": "2026-06-15T10:01:00Z"}
  ],
  "evaluations": [
    {"skill": "FastAPI", "score": 8, "feedback": "Strong practical experience."}
  ]
}
```

### Submit candidate answer

```http
POST /interviews/{id}/messages
Content-Type: application/json
```

**Request:**
```json
{
  "content": "I use multi-stage Dockerfiles with uvicorn and docker-compose for local dev."
}
```

**Response (200):**
```json
{
  "id": 1,
  "status": "in_progress",
  "current_question": "How do you optimize SQL queries in production?",
  "covered_skills": ["FastAPI", "Docker"],
  "remaining_skills": ["SQL"],
  "question_count": 3,
  "last_evaluation": {
    "skill": "Docker",
    "score": 7,
    "strengths": ["containerization"],
    "weaknesses": ["orchestration at scale"],
    "feedback": "Solid Docker fundamentals."
  }
}
```

When the interview completes, `status` becomes `"completed"` and `current_question` is `null`.

### Get report

```http
GET /interviews/{id}/report
```

**Response (200):**
```json
{
  "overallScore": 8,
  "strengths": ["FastAPI", "REST APIs"],
  "weaknesses": ["SQL Optimization"],
  "recommendation": "Proceed to next round"
}
```

**Response (404):** Interview not completed or report not generated.

## Health

```http
GET /health
```

**Response:**
```json
{"status": "ok"}
```

## Error Responses

```json
{
  "detail": "Interview not found"
}
```

Status codes: `400` validation, `404` not found, `409` invalid state (e.g. message on completed interview), `500` server error.

## Swagger Walkthrough

1. `POST /candidates` — create demo candidate.
2. `POST /jobs` — create demo job.
3. `POST /interviews` — start; note `current_question`.
4. `POST /interviews/{id}/messages` — paste an answer; repeat until `status` is `completed`.
5. `GET /interviews/{id}/report` — fetch recruiter summary.
