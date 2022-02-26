.PHONY: build start

ifeq ($(OS), Windows_NT)
    PYTHON3 ?= python
    ENV ?= . $(shell pwd)/venv/scripts/activate; \
        PYTHONPATH=$(shell pwd) \
        PATH=/c/Program\ Files\ \(x86\)/NSIS/:$$PATH
else
    PYTHON3 ?= python3.6
    ENV ?= . $(shell pwd)/venv/bin/activate; \
        PYTHONPATH=$(shell pwd)
endif

venv: $(patsubst %,requirements/%.txt, base $(REQUIREMENTS))
	virtualenv -p $(PYTHON3) venv
	for requirement in $^; do \
		$(ENV) $(PYTHON3) -m pip install -r $$requirement; \
	done
	touch $@  # update timestamp

all: start

build: venv
	$(ENV) fbs freeze
	$(ENV) fbs installer

start: venv
	$(ENV) fbs run
