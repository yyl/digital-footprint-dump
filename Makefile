PYTHON_VERSION := $(shell cat .python-version)

.PHONY: test-ci

test-ci:
	uv python install $(PYTHON_VERSION)
	uv sync --python $(PYTHON_VERSION)
	uv run --python $(PYTHON_VERSION) pytest
