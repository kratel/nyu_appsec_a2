# Spell Check Web Service

[![Build Status](https://travis-ci.com/kratel/nyu_appsec_a2.svg?token=9hqx4ysaqwyc5JJXpgtm&branch=master)](https://travis-ci.com/kratel/nyu_appsec_a2)

[![codecov](https://codecov.io/gh/kratel/nyu_appsec_a2/branch/master/graph/badge.svg?token=S6tquPAh6H)](https://codecov.io/gh/kratel/nyu_appsec_a2)

A web service to run a spell checker.

## Usage

A user must register using the `/register` form and login. Afterwards they will be able to submit text that will be spell checked.

### Registration - /register

There are a few input fields for this form.
- username - required
- password - required
- 2FA - optional

A username must be unique. If you are already logged in a link for logging out will be returned instead.

### Login - /login

There are a few input fields for this form.
- username - required
- password - required
- 2FA - optional

2FA is required for a successful login if one was used when registering the username. If you are already logged in a link for logging out will be returned instead.

### Spell Checker - /spell_check

There is a textarea box here where you can enter text. This text will then be analyzed by the spell checker and return the misspelled words if any were found.

## Setup

This repo has been structured in a way so that you can run the application by calling `flask run` from the root level of the repo. Please make sure to install the requirements with `pip install -r requirements.txt`

### Configuration

This project will have limited functionality without a spell check executable and a wordlist. These are not provided in the repo. Calling `flask run` will still provide registration and login functionality but text submission will not work. To use your own executable and wordlist simply add their paths to the instance `config.py`

Sample Config:
```
SECRET_KEY='asupersecretkey'
DATABASE='instance/mydb.sqlite'
SPELLCHECK='/path/to/spellcheck_executable'
WORDLIST='/path/to/wordlist.txt'
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE='Lax'
REMEMBER_COOKIE_HTTPONLY=True
```

*Note: This web service also assumes that the spell check executable provided is called with the wordlist as the first argument. e.g. `./a.out wordlist.txt input.txt`*

### Testing

This project uses [tox](https://tox.readthedocs.io/en/latest/), [Beutiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/), and [unittest](https://docs.python.org/3.7/library/unittest.html) for integration tests.
To run tests you can simply call `tox` or `make test`.

### Code Coverage
This project uses the [coverage](https://coverage.readthedocs.io/en/v4.5.x/) library to check code coverage.
To issue a report you can call `make coverage` followed by `make report`.

If you would like to create html pages from your reports you may then call `make report-html`.
