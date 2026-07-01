.PHONY: install dev dev-backend dev-frontend test lint type format migrate migrate-down migrate-revision run backup

install:
	cd backend && uv sync --all-extras
	cd backend && uv run playwright install chromium
	cd frontend && pnpm install

dev:
	@echo "Starting backend (port 8000) and frontend (port 5173)..."
	@trap 'echo "Shutting down..."; kill 0' EXIT; \
	cd backend && uv run uvicorn main:app --reload --port 8000 & \
	cd frontend && pnpm dev & \
	wait

test:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check .

type:
	cd backend && uv run mypy --explicit-package-bases .

format:
	cd backend && uv run ruff format .

migrate:
	cd backend && uv run alembic upgrade head

migrate-down:
	cd backend && uv run alembic downgrade -1

migrate-revision:
	cd backend && uv run alembic revision --autogenerate -m "$(name)"

run:
	cd backend && uv run uvicorn main:app --port 8000

backup:
	@mkdir -p backend/backups; \
	if [ -f backend/fynd.db ]; then \
		cp backend/fynd.db "backend/backups/fynd-$$(date +%Y%m%d-%H%M%S).db"; \
		echo "Backed up to backend/backups/fynd-$$(date +%Y%m%d-%H%M%S).db"; \
	else \
		echo "No database to back up (backend/fynd.db does not exist)"; \
	fi
