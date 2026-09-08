.PHONY: help dev test lint db-up db-down db-seed clean

help:
	@echo "Fiosra MVP Developer Commands:"
	@echo "  make dev       - Run FastAPI dev server with auto-reload"
	@echo "  make test      - Run full PyTest verification suite"
	@echo "  make db-up     - Start PostgreSQL 16 + pgvector container"
	@echo "  make db-down   - Stop PostgreSQL container"
	@echo "  make lint      - Check code style with ruff"
	@echo "  make clean     - Remove python caches and build artifacts"

dev:
	uvicorn fiosra.mvp.app:app --reload --port 8000

test:
	pytest fiosra/tests/ -v

db-up:
	docker compose up -d

db-down:
	docker compose down

lint:
	ruff check fiosra/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
