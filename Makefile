.PHONY: install lint test run docker-up

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .

test:
	pytest --cov=proofthread --cov-report=term-missing

run:
	proofthread

docker-up:
	docker compose up --build

