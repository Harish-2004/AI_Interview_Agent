.PHONY: up down migrate dev test lint seed demo

up:
	docker compose up -d

down:
	docker compose down

migrate:
	cd backend && uv run alembic upgrade head

dev:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

test:
	cd backend && uv run pytest -v

lint:
	cd backend && uv run ruff check app tests

seed:
	cd backend && uv run python scripts/seed_demo.py

demo:
	cd backend && uv run python scripts/demo_interview.py
