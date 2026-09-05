# 🚀 Developer Onboarding & Step-by-Step Setup Guide

Welcome to the **AI Interview Agent** codebase! This onboarding guide is designed to help new developers get up and running from scratch, understand how data flows through the application, and quickly locate the key modules to start building or debugging.

---

## 📋 Table of Contents

1. [Prerequisites](#-prerequisites)
2. [Step-by-Step Quickstart (Zero to Running)](#-step-by-step-quickstart-zero-to-running)
   - [1. Environment Setup](#1-environment-setup)
   - [2. Install Backend Dependencies](#2-install-backend-dependencies)
   - [3. Database Setup & Migrations](#3-database-setup--migrations)
   - [4. Launch Backend API Server](#4-launch-backend-api-server)
   - [5. Launch Frontend UI](#5-launch-frontend-ui)
   - [6. Run Interactive Demo & Test Suite](#6-run-interactive-demo--test-suite)
3. [Architecture & Request Lifecycle Walkthrough](#-architecture--request-lifecycle-walkthrough)
4. [Codebase Map & Key Components](#-codebase-map--key-components)
5. [How MCP & Database Mapping Work](#-how-mcp--database-mapping-work)
6. [Testing & Verification Workflow](#-testing--verification-workflow)

---

## 🛠 Prerequisites

Before starting, ensure you have installed:
* **Python 3.11+**
* **[`uv`](https://docs.astral.sh/uv/)** (recommended fast Python package manager) or standard `pip`
* **Node.js / Python HTTP server** (to serve the frontend static app)
* **Docker Desktop** *(Optional: only needed if using PostgreSQL or MongoDB instead of SQLite)*

---

## 🏁 Step-by-Step Quickstart (Zero to Running)

Follow these exact terminal commands to launch the entire application locally from scratch.

### 1. Environment Setup

Copy the example `.env` file in the `backend/` directory:

```bash
# From workspace root
cd backend
cp .env.example .env
```

Open `backend/.env` and set your LLM credentials (or leave defaults for mocked demo mode):
```env
# Database Choice (SQLite default, or Postgres)
DATABASE_URL=sqlite+aiosqlite:///./interview_agent.db

# LLM Keys
GOOGLE_API_KEY=your_gemini_api_key_here

# Active Gemini Models
PLANNER_MODEL=gemini/gemini-3.6-flash
INTERVIEWER_MODEL=gemini/gemini-3.6-flash
EVALUATOR_MODEL=gemini/gemini-3.6-flash
REPORT_MODEL=gemini/gemini-3.6-flash

USE_REAL_LLM=1
```

---

### 2. Install Backend Dependencies

Inside the `backend/` folder, run:

```bash
cd backend
uv sync
```
*(If using standard pip: `pip install -r requirements.txt`)*

---

### 3. Database Setup & Migrations

#### Option A: SQLite (Default — Quickest, no Docker required)
No extra configuration needed! SQLite auto-creates `interview_agent.db` on launch. Run migrations:
```bash
cd backend
uv run alembic upgrade head
```

#### Option B: PostgreSQL (Docker required)
Start PostgreSQL container from workspace root:
```bash
docker compose up -d
```
Then run Alembic migrations in `backend/`:
```bash
cd backend
uv run alembic upgrade head
```

---

### 4. Launch Backend API Server

Start the FastAPI backend with auto-reload enabled:

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

* **Swagger API Documentation:** Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.
* **Healthcheck:** Verify backend is active at [http://localhost:8000/health](http://localhost:8000/health).
* **Arize Phoenix Open-Source Tracing Dashboard:** Open [http://localhost:6006](http://localhost:6006) for real-time local LangGraph node & LLM trace visualization.

---

### 5. Launch Frontend UI

The frontend consists of vanilla HTML, CSS, and JS web interfaces.

From the workspace root directory, start a simple HTTP server:

```bash
# Run from workspace root
python -m http.server 3000
```

Now open in your browser:
* **Main Interview Application:** [http://localhost:3000/frontend/](http://localhost:3000/frontend/)
* **Voice Interactive Demo:** [http://localhost:3000/voice_demo.html](http://localhost:3000/voice_demo.html)

---

### 6. Run Interactive Demo & Test Suite

#### Run CLI Simulation Demo:
```bash
cd backend
uv run python scripts/demo_interview.py
```

#### Run Full Test Suite:
```bash
cd backend
uv run pytest
```

---

## 📐 Architecture & Request Lifecycle Walkthrough

```
┌─────────────────┐       ┌──────────────────────┐       ┌────────────────────────┐
│   Frontend UI   │ ──►   │ FastAPI REST Routes │ ──►   │   InterviewService     │
│ (app.js / HTML) │       │ (app/api/routes.py)  │       │ (interview_service.py) │
└─────────────────┘       └──────────────────────┘       └───────────┬────────────┘
                                                                     │
                                                                     ▼
┌─────────────────┐       ┌──────────────────────┐       ┌────────────────────────┐
│ PostgreSQL /    │ ◄───  │    MCP Client        │ ◄───  │  LangGraph Multi-Agent │
│ SQLite Database │       │  (app/mcp/client.py) │       │ (interview_graph.py)   │
└─────────────────┘       └──────────────────────┘       └────────────────────────┘
```

### End-to-End Flow When a Candidate Takes an Interview:

1. **Candidate & Job Creation:**
   - Client sends candidate details & resume text to `POST /candidates`. Backend creates `Candidate` record with auto-increment ID (`candidate_id = 1`).
   - Client sends job description to `POST /jobs`. Backend creates `Job` record (`job_id = 1`).

2. **Starting Interview (`POST /interviews`):**
   - [`InterviewService.start_interview()`](../backend/app/services/interview_service.py) initializes interview state.
   - It queries required skills via `MCPClient.get_required_skills(job_id)`.
   - Compiles and executes the **LangGraph** flow ([`interview_graph.py`](../backend/app/graphs/interview_graph.py)).

3. **Question & Answer Loop (`POST /interviews/{id}/messages`):**
   - Candidate submits an answer.
   - **Interviewer Agent** ([`interviewer/agent.py`](../backend/app/agents/interviewer/agent.py)) uses candidate resume context & JD context via MCP RAG to pick the next uncovered skill and construct the next question.
   - **Evaluator Agent** ([`evaluator/agent.py`](../backend/app/agents/evaluator/agent.py)) asynchronously scores answers (1-5) based on **Dual-Context Fallback Hierarchy** (Resume + JD Context).

4. **Report Generation:**
   - Once all skills are covered or max questions reached, **Report Agent** ([`report/agent.py`](../backend/app/agents/report/agent.py)) produces candidate performance summary JSON.

---

## 🗺 Codebase Map & Key Components

Here is where to go when making changes:

| Path | Purpose | Key Files |
| :--- | :--- | :--- |
| **Backend API** | Handles REST requests | [`main.py`](../backend/app/main.py), [`interviews.py`](../backend/app/api/interviews.py), [`candidates.py`](../backend/app/api/candidates.py) |
| **Database & Models** | SQLAlchemy ORM Models | [`models.py`](../backend/app/db/models.py), [`session.py`](../backend/app/db/session.py) |
| **Business Logic** | Interview execution & RAG | [`interview_service.py`](../backend/app/services/interview_service.py), [`rag_service.py`](../backend/app/services/rag_service.py) |
| **LangGraph Agents** | Multi-agent orchestration | [`interview_graph.py`](../backend/app/graphs/interview_graph.py), [`interviewer/agent.py`](../backend/app/agents/interviewer/agent.py) |
| **MCP Abstraction** | Model Context Protocol Tools | [`client.py`](../backend/app/mcp/client.py), [`handlers.py`](../backend/app/mcp/handlers.py) |
| **Guardrails & Safety**| Answer relevance & prompt injection | [`rules.py`](../backend/app/guardrails/rules.py) |
| **Frontend Web App** | Web UI & Voice Demo | [`app.js`](../frontend/app.js), [`index.html`](../frontend/index.html), [`voice_demo.html`](../voice_demo.html) |

---

## 🔌 How MCP & Database Mapping Work

### Why MCP?
MCP (Model Context Protocol) decouples AI agents from direct database dependencies:
* Agents call clean MCP tools: `mcp.get_resume(candidate_id=1)`, `mcp.search_resume_rag(...)`.
* MCP handlers process database connections, RAG indexing, and guardrails internally.
* If database schemas change or an external ATS is added, **agents don't change**, only MCP handlers change.

---

## 🧪 Testing & Verification Workflow

Always run verification commands after editing code:

```bash
cd backend

# 1. Run all unit & integration tests
uv run pytest

# 2. Run Guardrail verification specifically
uv run pytest tests/test_guardrails.py

# 3. Test multi-database MCP capabilities
uv run pytest tests/test_db_mcp.py

# 4. Test RAG and evaluation pipeline
uv run pytest tests/test_rag_and_ragas.py
```

Happy Coding! 🚀 If you have any questions, check [`ARCHITECTURE.md`](ARCHITECTURE.md) or [`LANGCHAIN_FLOW.md`](LANGCHAIN_FLOW.md) for deeper technical specifications.
