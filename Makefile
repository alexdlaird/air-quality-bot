.PHONY: all env install

SHELL := /usr/bin/env bash

all: env virtualenv install

env:
	cp -n .env.example .env | true

virtualenv:
	@if [ ! -d ".venv" ]; then \
		python3 -m pip install virtualenv --user; \
		python3 -m virtualenv .venv; \
	fi

install: env virtualenv
	@( \
		source .venv/bin/activate; \
		python -m pip install -r requirements.txt; \
		python -m pip install -r requirements_deploy.txt -t ./lib; \
	)

test: env virtualenv
	@( \
		source .venv/bin/activate; \
		python -m unittest discover -s tests/unit; \
	)

test-e2e: env virtualenv
	@( \
		source .venv/bin/activate; \
		python -m unittest discover -s tests/e2e; \
	)
