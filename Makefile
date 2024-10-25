.PHONY: all env install nopyc clean test run-devserver

SHELL := /usr/bin/env bash
PYTHON_BIN ?= python
PROJECT_VENV ?= venv

all: test

env:
	cp -n .env.example .env | true
	cp -n .env.dev.example .env.dev | true

venv:
	python -m pip install virtualenv --user
	python -m virtualenv $(PROJECT_VENV)

install: env venv
	@( \
		source $(PROJECT_VENV)/bin/activate; \
		python -m pip install -r requirements.txt -t ./lib; \
		python -m pip install -r requirements.txt -r requirements-dev.txt; \
	)

nopyc:
	find . -name '*.pyc' | xargs rm -f || true
	find . -name __pycache__ | xargs rm -rf || true

clean: nopyc
	rm -rf build $(PROJECT_VENV)

test: install
	@( \
		source $(PROJECT_VENV)/bin/activate; \
		coverage run -m unittest discover -v -b && coverage report && coverage xml && coverage html; \
	)

run-devserver: install
	@( \
		source $(PROJECT_VENV)/bin/activate; \
		FLASK_SKIP_DOTENV=1 FLASK_ENV=development FLASK_APP=devserver.py flask run; \
	)
