.PHONY: install
install:
	uv sync --group dev --group test
	uv pip install -e .

.PHONY: test
test:
	uv run pytest -x src/hecto tests

.PHONY: lint
lint:
	uv run ruff check src/hecto tests
	uv run ty check

.PHONY: coverage
coverage:
	uv run pytest --cov-config=pyproject.toml --cov-report html --cov hecto src/hecto tests
