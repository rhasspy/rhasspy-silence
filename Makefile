SHELL := bash
SOURCE = rhasspysilence
PYTHON_FILES = $(SOURCE)/*.py tests/*.py setup.py
PIP_INSTALL ?= install

.PHONY: reformat check test venv dist

reformat:
	black .
	isort $(PYTHON_FILES)

check:
	flake8 $(PYTHON_FILES)
	pylint $(PYTHON_FILES)
	mypy $(PYTHON_FILES)
	black --check .
	isort --check-only $(PYTHON_FILES)
	yamllint .
	pip list --outdated

test:
	coverage run --source=$(SOURCE) -m pytest
	coverage report -m
	coverage xml

venv:
	rm -rf .venv/
	python3 -m venv .venv
	.venv/bin/pip3 $(PIP_INSTALL) --upgrade pip
	.venv/bin/pip3 $(PIP_INSTALL) wheel setuptools
	.venv/bin/pip3 $(PIP_INSTALL) -r requirements.txt
	.venv/bin/pip3 $(PIP_INSTALL) -r requirements_dev.txt

dist:
	python3 setup.py sdist
