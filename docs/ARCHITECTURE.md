# Architecture

## Overview

The backend follows a layered design: **API → Services → LangGraph → Agents → LiteLLM / MCP → Database**.

Each agent owns a single responsibility with a small system prompt and Pydantic I/O models. No monolithic prompt files.

## LangGraph Flow

For a comprehensive, step-by-step breakdown of how the agents, memory, checkpointers, and human-in-the-loop lifecycle are orchestrated, see the detailed [LANGCHAIN_FLOW.md](file:///c:/Users/chint/Music/AI%20Interview%20Agent/docs/LANGCHAIN_FLOW.md) guide.

```
START → planner → interviewer → [interrupt: wait for answer]
     → evaluator → (continue?) → planner | report → END
```

### Graph State

| Field | Type | Description |
|-------|------|-------------|
| `interview_id` | int | Database interview PK |
| `candidate_id` | int | Candidate FK |
| `job_id` | int | Job FK |
| `covered_skills` | list[str] | Skills already assessed |
| `remaining_skills` | list[str] | Skills left to assess |
| `current_topic` | str | Skill being interviewed |
| `current_question` | str | Latest interviewer question |
| `last_answer` | str | Latest candidate answer |
| `question_count` | int | Questions asked so far |
| `evaluations` | list[dict] | Per-answer evaluation records |
| `should_continue` | bool | Loop control flag |
| `report` | dict | Final report (set by report node) |

## Agents

### Planner Agent

**Input:** covered and remaining skills from graph state.

**Output:**
```json
{
  "nextTopic": "fastapi"
}
```

**Responsibility:** Decide which skill to assess next based on JD requirements and coverage.

### Interviewer Agent

**Input:** current topic, resume context, previous Q&A, job requirements.

**Output:**
```json
{
  "question": "Tell me about your FastAPI experience.",
  "isFollowUp": false
}
```

**Responsibility:** Generate questions and follow-ups; maintain conversational tone.

### Evaluator Agent

**Input:** question, answer, skill being assessed.

**Output:**
```json
{
  "score": 8,
  "skill": "FastAPI",
  "strengths": ["REST API design"],
  "weaknesses": ["async patterns"],
  "feedback": "Strong practical experience."
}
```

**Responsibility:** Score answers, identify strengths/weaknesses, mark skill covered.

### Report Agent

**Input:** all evaluations, interview metadata.

**Output:**
```json
{
  "overallScore": 8,
  "strengths": ["FastAPI", "REST APIs"],
  "weaknesses": ["SQL Optimization"],
  "recommendation": "Proceed to next round"
}
```

## LiteLLM Gateway

All LLM calls go through `app/llm/gateway.py`:

```python
response = await llm.generate(messages, agent_name="interviewer")
```

Per-agent model routing via environment variables. Swap providers without code changes:

```env
INTERVIEWER_MODEL=gemini/gemini-2.0-flash
EVALUATOR_MODEL=anthropic/claude-sonnet-4-20250514
```

## MCP Integration

Agents access domain data through an MCP client that connects to three in-repo servers:

```
MCP Client
  ├── Resume MCP      (candidate data, skill extraction)
  ├── JD MCP          (job description, required skills)
  └── Memory MCP      (Q&A history, scores)
```

When ATS integration arrives, add **ATS MCP** as a fourth server — no agent code changes required.

## Database Schema

| Table | Purpose |
|-------|---------|
| `candidate` | Resume and contact info |
| `job` | Job title and description |
| `interview` | Interview session (status, FKs) |
| `interview_message` | Transcript (role: user/assistant/system) |
| `evaluation` | Per-skill scores and feedback |

## Human-in-the-Loop

LangGraph uses `interrupt_before=["wait_for_answer"]` after the interviewer node. The FastAPI `POST /interviews/{id}/messages` endpoint resumes the graph with the candidate's answer.

## Observability

Structured JSON logging with `interview_id` correlation. Resume/JD content is not logged by default.
