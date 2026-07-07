.DEFAULT_GOAL := help
.PHONY: help setup test unit cov e2e pc check bench-local package clean

UV_RUN_CMD = uv run --no-sync

help:
	@echo "Usage: make <target>"
	@echo "  setup   Install deps and git hooks for development"
	@echo "  test    Run all tests, unit and e2e (no coverage)"
	@echo "  unit    Run unit tests and collect coverage"
	@echo "  cov     Report coverage from the last run (no re-run)"
	@echo "  e2e     Run end-to-end tests against live providers (network)"
	@echo "  pc      Run all pre-commit hooks on all files"
	@echo "  check   Run unit tests, coverage report, and pre-commit"
	@echo "  bench-local  Benchmark the local provider against cepx-data"
	@echo "               (e.g. make bench-local ARGS=\"--n 200000\")"
	@echo "  package Build the sdist and wheel into dist/"
	@echo "  clean   Clean development environment"

setup:
	uv venv --clear --python 3.14
	uv sync --all-groups
	$(UV_RUN_CMD) pre-commit install

unit:
	$(UV_RUN_CMD) pytest -m unit

e2e:
	$(UV_RUN_CMD) pytest -m e2e --no-cov

test:
	$(UV_RUN_CMD) pytest -m "unit or e2e" --no-cov

cov:
	$(UV_RUN_CMD) coverage report
	$(UV_RUN_CMD) coverage html

pc:
	$(UV_RUN_CMD) pre-commit run --all-files

check: unit cov pc

bench-local:
	uv run --with cepx-data python tools/bench_local.py $(ARGS)

package:
	uv build

clean:
	@for ext in mo pot pyc; do \
		find . -type f -name "*.$$ext" -delete; \
	done
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@rm -rf .coverage .ruff_cache .pytest_cache htmlcov dist
