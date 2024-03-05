.PHONY: all env virtualenv install nopyc clean test run-devserver

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

nopyc:
	find . -name '*.pyc' | xargs rm -f || true
	find . -name __pycache__ | xargs rm -rf || true

clean: nopyc
	rm -rf build .venv

test: install
	@( \
		source .venv/bin/activate; \
		coverage run -m unittest discover -v -b; \
		coverage report && coverage xml && coverage html; \
	)

run-devserver: install
	@( \
		source .venv/bin/activate; \
		FLASK_SKIP_DOTENV=1 FLASK_ENV=development FLASK_APP=devserver.py flask run; \
	)
