SHELL := bash
SOURCE = rhasspysilence
PYTHON_FILES = $(SOURCE)/*.py tests/*.py setup.py
PIP_INSTALL ?= install

.PHONY: reformat check test venv dist

reformat:
	scripts/format-code.sh $(PYTHON_FILES)

check:
	scripts/check-code.sh $(PYTHON_FILES)

test:
	scripts/run-tests.sh $(SOURCE)

venv:
	scripts/create-venv.sh

dist:
	python3 setup.py sdist
