lint:
	pyflakes *.py && pylint -E *.py

test:
	nosetests -sv loans_test.py