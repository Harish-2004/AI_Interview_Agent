# ⚡ Daily Developer Starter Guide (`starter.md`)

This guide explains how to start your application daily after initial setup, and answers key questions about Docker and PostgreSQL.

---

## ❓ FAQ: Do I need to recreate Docker containers every time?

**NO! You do NOT need to recreate containers every time.**
* Docker containers and database data are **permanently saved** in Docker volumes.
* Running `docker compose up postgres -d` simply **starts existing containers** in the background in less than 2 seconds.
* You do NOT need to run `alembic upgrade head` every time—only when database schemas change!

---

## 🚀 Daily 3-Step Startup Commands

Follow these 3 simple commands whenever you open your IDE to work on the project:

### Step 1: Start PostgreSQL Database Container (1 Second)
Run from the workspace root directory:
```bash
docker compose up postgres -d
```
*(This starts PostgreSQL on port `5432` without starting MongoDB).*

---

### Step 2: Start the FastAPI Backend & Arize Phoenix UI
Open Terminal 1 and run:
```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```
* **FastAPI Backend:** [http://localhost:8000](http://localhost:8000) (Swagger Docs at `/docs`)
* **Arize Phoenix Tracing Dashboard:** [http://localhost:6006](http://localhost:6006)

---

### Step 3: Start the Frontend UI Server
Open Terminal 2 (from workspace root) and run:
```bash
python -m http.server 3000
```
* **Main Web UI:** [http://localhost:3000/frontend/](http://localhost:3000/frontend/)
* **Voice Demo:** [http://localhost:3000/voice_demo.html](http://localhost:3000/voice_demo.html)
* **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Arize Phoenix UI:** [http://localhost:6006](http://localhost:6006)
* **pgAdmin Database Web UI:** [http://localhost:5050](http://localhost:5050) (Login: `admin@admin.com` / `admin`)

---

## 🛑 How to Stop Services when Finished

When you finish working for the day:

1. Press `Ctrl + C` in Terminal 1 and Terminal 2 to stop the dev servers.
2. Stop the PostgreSQL container:
   ```bash
   docker compose stop postgres
   ```
*(Your data remains completely safe in Docker storage for tomorrow!)*
