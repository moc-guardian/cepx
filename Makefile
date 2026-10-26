.DEFAULT_GOAL := help
.PHONY: help setup test unit e2e cov lint fmt fix types pc check bench-local package clean

UV_RUN_CMD = uv run --no-sync

help:
	@echo "Usage: make <target>"
	@echo "  setup        Install deps and git hooks for development"
	@echo "  test         Run the unit suite and collect coverage"
	@echo "  unit         Run unit tests only (no coverage)"
	@echo "  e2e          Run against the live CEP providers (network)"
	@echo "  cov          Report coverage from the last run (no re-run)"
	@echo "  lint         Lint with ruff"
	@echo "  fmt          Format with ruff"
	@echo "  fix          Apply the fixes lint reports, then format"
	@echo "  types        Type check with ty"
	@echo "  pc           Run all pre-commit hooks on all files"
	@echo "  check        Run tests, coverage report, and pre-commit"
	@echo "  bench-local  Benchmark the local provider against cepx-data"
	@echo "               (e.g. make bench-local ARGS=\"--n 200000\")"
	@echo "  package      Build the sdist and wheel into dist/"
	@echo "  clean        Clean development environment"

setup:
	uv venv --clear --python $$(cat .python-version)
	uv sync --all-groups
	$(UV_RUN_CMD) pre-commit install

test:
	$(UV_RUN_CMD) coverage run
	$(UV_RUN_CMD) coverage report

unit:
	$(UV_RUN_CMD) pytest -m unit

# Hits the real provider APIs, so it needs network and is excluded from the
# default run by the `-m "not e2e"` in addopts.
e2e:
	$(UV_RUN_CMD) pytest -m e2e -rs -p no:cacheprovider

cov:
	$(UV_RUN_CMD) coverage report
	$(UV_RUN_CMD) coverage html

lint:
	$(UV_RUN_CMD) ruff check .

fmt:
	$(UV_RUN_CMD) ruff format .

# `fmt` only reformats. Most of what `lint` reports is fixable, but by a
# different command, so this is the loop to run after a red `lint`.
fix:
	$(UV_RUN_CMD) ruff check . --fix
	$(UV_RUN_CMD) ruff format .

types:
	$(UV_RUN_CMD) ty check

pc:
	$(UV_RUN_CMD) pre-commit run --all-files

check: test pc

bench-local:
	uv run --with cepx-data python tools/bench_local.py $(ARGS)

package:
	uv build

clean:
	@for ext in mo pot pyc; do \
		find . -type f -name "*.$$ext" -delete; \
	done
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@rm -rf .coverage .ruff_cache .pytest_cache .ty_cache htmlcov dist
