.PHONY: all env virtualenv install test run-devserver

SHELL := /usr/bin/env bash

all: env virtualenv install

env:
	cp -n .env.example .env | true
	cp -n .env.dev.example .env.dev | true

virtualenv:
	@if [ ! -d ".venv" ]; then \
		python3 -m pip install virtualenv --user; \
		python3 -m virtualenv .venv; \
	fi

install: env virtualenv
	@( \
		source .venv/bin/activate; \
		python -m pip install -r requirements.txt -t ./lib; \
		python -m pip install -r requirements.txt -r requirements-dev.txt; \
	)

test: env virtualenv
	@( \
		source .venv/bin/activate; \
		python -m coverage run -m unittest discover -v -b && python -m coverage xml -o _build/coverage/coverage.xml; \
	)

run-devserver: env virtualenv
	@( \
		source .venv/bin/activate; \
		FLASK_SKIP_DOTENV=1 FLASK_ENV=development FLASK_APP=devserver.py flask run; \
	)
