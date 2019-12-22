get-deps:
	# Assuming Debian or Ubuntu here
	sudo apt-get update
	sudo apt-get install -y python3-pip

.PHONY: test coverage report report-html lint

test:
	tox

lint:
	tox -e flake8

coverage:
	coverage run -m unittest discover -v

report:
	coverage report spellcheckapp/*/*.py

report-html:
	coverage html spellcheckapp/*/*.py
