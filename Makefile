.PHONY: all env install

PYTHON_BIN ?= python

all: env install

env:
	cp -n .env.example .env | true

install: env
	$(PYTHON_BIN) -m pip install -r requirements.txt
	$(PYTHON_BIN) -m pip install -r requirements_deploy.txt -t ./lib

test:
	export $$(cat .env | grep -v ^\# | xargs) && $(PYTHON_BIN) -m unittest discover
