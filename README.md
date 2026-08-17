# AI Interview Agent

An industry-standard AI-powered technical interview platform. A FastAPI backend orchestrates multi-agent interviews via LangGraph, routes LLM calls through LiteLLM, and exposes domain data through custom MCP servers.

## Architecture

```
Next.js Frontend (future)
        |
        v
FastAPI API Layer
        |
        v
LangGraph Orchestrator
        |
  +-----+-----+-----+
  |           |     |
  v           v     v
Planner   Interviewer  Evaluator
Agent      Agent        Agent
        |
        v
LiteLLM Gateway  -->  GPT / Claude / Gemini
        |
  +-----+-----+-----+
  |           |     |
  v           v     v
Resume MCP   JD MCP   Interview Memory MCP
        |
        v
   PostgreSQL
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for agent I/O schemas, graph flow, and LiteLLM routing.

## Quick Demo Scenario

1. Upload a resume (mentions FastAPI experience).
2. Upload a job description (requires FastAPI, Docker, SQL).
3. Start an interview.
4. **Planner** picks the next skill (e.g. FastAPI).
5. **Interviewer** asks a question; candidate answers via API.
6. **Evaluator** scores the answer and marks the skill covered.
7. Loop until all skills are covered or max questions reached.
8. **Report** agent returns recruiter summary JSON.

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker Desktop (only required if running with PostgreSQL)

### 1. Environment

```bash
cp .env.example .env
# Add at least one LLM provider key (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
```

### 2. Database Setup

You can choose to run with SQLite (no Docker/Postgres setup needed) or PostgreSQL.

#### Option A: SQLite (No Docker required)
1. Open the `.env` file you created in step 1.
2. Uncomment the SQLite connection string and comment out the PostgreSQL one:
   ```env
   DATABASE_URL=sqlite+aiosqlite:///./interview_agent.db
   ```

#### Option B: PostgreSQL (Docker required)
Start the PostgreSQL container:
```bash
docker compose up -d
```

### 3. Backend

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for Swagger UI.

### 4. Demo script

```bash
cd backend
uv run python scripts/demo_interview.py
```

Uses mocked LLM by default; set `USE_REAL_LLM=1` in `.env` for live providers.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Async PostgreSQL URL | `postgresql+asyncpg://postgres:postgres@localhost:5432/interview_agent` |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `ANTHROPIC_API_KEY` | Anthropic API key | — |
| `GOOGLE_API_KEY` | Google Gemini key | — |
| `PLANNER_MODEL` | LiteLLM model for planner | `openai/gpt-4o-mini` |
| `INTERVIEWER_MODEL` | LiteLLM model for interviewer | `openai/gpt-4o` |
| `EVALUATOR_MODEL` | LiteLLM model for evaluator | `anthropic/claude-sonnet-4-20250514` |
| `REPORT_MODEL` | LiteLLM model for report | `openai/gpt-4o` |
| `MAX_QUESTIONS` | Max interview questions | `10` |
| `USE_REAL_LLM` | Use real LLM in demo/tests | `0` |

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| POST | `/candidates` | Create candidate with resume |
| POST | `/jobs` | Create job description |
| POST | `/interviews` | Start interview |
| GET | `/interviews/{id}` | Get interview state |
| POST | `/interviews/{id}/messages` | Submit candidate answer |
| GET | `/interviews/{id}/report` | Get final report |

Full request/response examples: [docs/API.md](docs/API.md).

## MCP Servers

Custom in-repo MCP servers (no external ATS required initially):

- **Resume MCP** — `get_resume`, `extract_skills`, `get_experience`
- **JD MCP** — `get_job_description`, `get_required_skills`
- **Interview Memory MCP** — `store_answer`, `get_previous_questions`, `get_scores`

Details: [docs/MCP.md](docs/MCP.md).

## Project Structure

```
backend/
├── app/
│   ├── agents/       # planner, interviewer, evaluator, report
│   ├── graphs/       # LangGraph interview flow
│   ├── mcp/          # MCP servers + client
│   ├── llm/          # LiteLLM gateway
│   ├── db/           # SQLAlchemy models
│   ├── api/          # FastAPI routers
│   └── services/     # Business logic
├── alembic/
└── scripts/
frontend/             # Next.js (future milestone)
docs/
```

## Development

```bash
make up          # Start PostgreSQL
make migrate     # Run Alembic migrations
make dev         # Start FastAPI with reload
make test        # Run pytest
make lint        # ruff check
```

## License

MIT
