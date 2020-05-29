.PHONY: start


ifeq ($(OS), Windows_NT)
    PYTHON3 ?= python
    ACTIVATE ?= env/Scripts/activate
    ENV ?= . $(shell pwd)/env/scripts/activate; \
        PYTHONPATH=$(shell pwd) \
        PATH=/c/Program\ Files\ \(x86\)/NSIS/:$$PATH
else
    PYTHON3 ?= python3
    ACTIVATE ?= env/bin/activate
    ENV ?= . $(shell pwd)/env/bin/activate; \
        PYTHONPATH=$(shell pwd)
endif


env: requirements/base.txt
	test -d env || $(PYTHON3) -m venv env
	. $(ACTIVATE) \
		&& $(PYTHON3) -m pip install -r $< \
		|| rm -r env


all: start

build: env
	$(ENV) fbs freeze
	$(ENV) fbs installer

start: env
	$(ENV) fbs run
