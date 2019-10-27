# Spell Check Web Service

[![Build Status](https://travis-ci.com/kratel/nyu_appsec_a2.svg?token=9hqx4ysaqwyc5JJXpgtm&branch=master)](https://travis-ci.com/kratel/nyu_appsec_a2)

A web service to run a spell checker.

## Usage

A user must register using the `/register` form and login. Afterwards they will be able to submit text that will be spell checked.

## Registration - /register

There are a few input fields for this form.
- username - required
- password - required
- 2FA - optional

A username must be unique. If you are already logged in a link for logging out will be returned instead.

## Login - /login

There are a few input fields for this form.
- username - required
- password - required
- 2FA - optional

2FA is required for a successful login if one was used when registering the username. If you are already logged in a link for logging out will be returned instead.

## Spell Checker - /spell_check

There is a textarea box here where you can enter text. This text will then be analyzed by the spell checker and return the misspelled words if any were found.
