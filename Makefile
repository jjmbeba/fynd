.PHONY: install dev dev-backend dev-frontend test lint type format migrate run backup

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
	cd backend && uv run mypy .

format:
	cd backend && uv run ruff format .

migrate:
	@echo "No migrations yet \342\200\224 add alembic init in Phase 1+"
	@exit 0

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
