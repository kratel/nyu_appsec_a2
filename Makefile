get-deps:
	# Assuming Debian or Ubuntu here
	sudo apt-get update
	sudo apt-get install -y python3-pip

test:
	tox

coverage:
	coverage run -m unittest discover -v

report:
	coverage report spellcheckapp/*.py
