.PHONY: dev build test seed migrate

# Docker
up:
	docker compose up --build

down:
	docker compose down

# Development
dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# Database
migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m app.seed

# Testing
test-backend:
	cd backend && python -m pytest tests/ -v

test-frontend:
	cd frontend && npm run test

test: test-backend test-frontend

# Demo data
generate-demo:
	python scripts/generate_demo_data.py
