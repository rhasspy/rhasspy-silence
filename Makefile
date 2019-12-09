.PHONY: check test

check:
	flake8 rhasspysilence/*.py
	pylint rhasspysilence/*.py

test:
	python3 -m unittest rhasspysilence.test
