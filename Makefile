.PHONY: setup test lint indices verify

setup:
	uv venv && . .venv/bin/activate && uv pip install -e ".[dev]"

test:
	python -m pytest

lint:
	ruff check src tests

indices:
	bi indices VIX VIX3M VIX9D VVIX SKEW

verify:
	bi ledger verify ledger/predictions.jsonl
