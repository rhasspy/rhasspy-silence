.PHONY: check

check:
	flake8 rhasspysilence/*.py
	pylint rhasspysilence/*.py
