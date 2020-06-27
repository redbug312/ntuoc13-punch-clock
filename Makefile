.PHONY: build start


ifeq ($(OS), Windows_NT)
    PYTHON3 ?= python
    ENV ?= . $(shell pwd)/env/scripts/activate; \
        PYTHONPATH=$(shell pwd) \
        PATH=/c/Program\ Files\ \(x86\)/NSIS/:$$PATH
else
    PYTHON3 ?= python3
    ENV ?= . $(shell pwd)/env/bin/activate; \
        PYTHONPATH=$(shell pwd)
endif


env: $(patsubst %,requirements/%.txt, base $(REQUIREMENTS))
	$(PYTHON3) -m venv env
	$(ENV) $(PYTHON3) -m pip install -r $^
	touch $@  # update timestamp


all: start

build: env
	$(ENV) fbs freeze
	$(ENV) fbs installer

start: env
	$(ENV) fbs run
