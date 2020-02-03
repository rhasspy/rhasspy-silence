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
	scripts/create-venv.sh

dist:
	python3 setup.py sdist
