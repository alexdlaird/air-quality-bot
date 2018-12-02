.PHONY: all env install

PYTHON_BIN ?= python

all: env install

env:
	cp -n .env.example .env | true

install: env
	python -m pip install -r requirements.txt

test:
	export $$(cat .env | grep -v ^\# | xargs) && $(PYTHON_BIN) -m unittest discover
