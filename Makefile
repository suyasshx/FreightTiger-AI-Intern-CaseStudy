# RouteGuard AI — Operational Makefile

.PHONY: help install test run-cli run-api run-frontend reproducibility eval docker-build docker-up clean

help:
	@echo "RouteGuard AI — Available Commands:"
	@echo "  make install         Install backend and frontend dependencies"
	@echo "  make test            Run complete pytest test suite (28 tests)"
	@echo "  make run-cli         Execute batch analysis pipeline and generate CSV"
	@echo "  make run-api         Start FastAPI production backend on port 8000"
	@echo "  make run-frontend    Start Vite React dev server on port 5173"
	@echo "  make reproducibility Run 3 untouched runs and verify SHA-256 match"
	@echo "  make eval            Execute evaluation harness and generate metrics"
	@echo "  make docker-build    Build Docker image"
	@echo "  make docker-up       Start containerized service via docker-compose"
	@echo "  make clean           Clean cache files and build artifacts"

install:
	pip install -r requirements.txt
	cd frontend && npm install

test:
	python -m pytest tests/ -v

run-cli:
	python cli.py

run-api:
	python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

reproducibility:
	python evaluation/reproducibility_check.py

eval:
	python evaluation/run_evaluation.py

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf frontend/dist
