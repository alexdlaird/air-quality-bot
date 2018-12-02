.PHONY: all env install

all: env install

env:
	cp -n .env.example .env | true

install: env
