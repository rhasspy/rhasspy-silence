.PHONY: check test venv

check:
	flake8 rhasspysilence/*.py
	pylint rhasspysilence/*.py

test:
	python3 -m unittest rhasspysilence.test

venv:
	rm -rf .venv/
	python3 -m venv .venv
	.venv/bin/pip3 install wheel setuptools
	.venv/bin/pip3 install -r requirements_all.txt

dist:
	python3 setup.py sdist
