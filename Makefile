.PHONY: start


ifeq ($(OS), Windows_NT)
    ENV ?= . $(shell pwd)/env/scripts/activate; \
        PYTHONPATH=$(shell pwd) \
        PATH=/c/Program\ Files\ \(x86\)/NSIS/:$$PATH
else
    ENV ?= . $(shell pwd)/env/bin/activate; \
        PYTHONPATH=$(shell pwd)
endif


env:
	python3 -m venv env
	. env/bin/activate \
		&& pip3 install -r requirements/base.txt \
		|| rm -r env


all: start

build: env
	$(ENV) fbs freeze
	$(ENV) fbs installer

start: env
	$(ENV) fbs run
