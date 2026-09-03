.PHONY: install lint test migrate run docker-up docker-down

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .

test:
	pytest --cov=proofthread --cov-report=term-missing

migrate:
	proofthread-db head

run:
	proofthread

docker-up:
	docker compose up --build

docker-down:
	docker compose down
