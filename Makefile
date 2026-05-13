.PHONY: help clean test lint format check build

help:
	@echo "ag-os development targets:"
	@echo ""
	@echo "  make clean    Remove build artifacts (dist/, *.egg-info/, build/, .pytest_cache/, .ruff_cache/)"
	@echo "  make test     Run the pytest suite"
	@echo "  make lint     Run ruff check + ruff format --check"
	@echo "  make format   Apply ruff format and ruff check --fix"
	@echo "  make check    Run lint + test + mypy"
	@echo "  make build    Build the sdist + wheel (production releases come from CI, not local)"
	@echo ""

# Wipe local build artifacts. Use this before any manual build to avoid
# accidentally re-uploading a stale version (the audit caught dist/ at
# v1.2.0 while pyproject.toml said v1.4.0). Production releases are
# published by .github/workflows/publish.yml on a release event; do not
# run `twine upload dist/*` from your laptop.
clean:
	rm -rf dist/ build/ *.egg-info/ ag_os.egg-info/ \
		.pytest_cache/ .ruff_cache/ .mypy_cache/ \
		.coverage coverage.xml htmlcov/

test:
	pytest --tb=short -q

lint:
	ruff check .
	ruff format --check .

format:
	ruff format .
	ruff check --fix .

check: lint test
	mypy ag_os

build: clean
	python -m build
