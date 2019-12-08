# Spell Check Web Service

[![Build Status](https://travis-ci.com/kratel/nyu_appsec_a2.svg?token=9hqx4ysaqwyc5JJXpgtm&branch=master)](https://travis-ci.com/kratel/nyu_appsec_a2)

[![codecov](https://codecov.io/gh/kratel/nyu_appsec_a2/branch/master/graph/badge.svg?token=S6tquPAh6H)](https://codecov.io/gh/kratel/nyu_appsec_a2)

A web service to run a spell checker. There are two files that are not included in this repo which are necessary. One is a spell check executable and the other is a wordlist.txt file that will be used as a valid dictionary of words to check against. They can be placed at the root level of the repo. The configration should be updated to point to these files accordingly.

Example:
If a spell check executable called `spell_check.out` is placed at the root level of the repo then the following pair should be in the config:
```
SPELLCHECK='./spell_check.out'
```
If a wordlist called `wordlist.txt` is placed at the root level of the repo then the following pair should be in the config:
```
WORDLIST='wordlist.txt'
```

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

*Note: This web service also assumes that the spell check executable provided is called with the input text as the first argument. e.g. `./a.out input.txt wordlist.txt`*

### Testing

This project uses [tox](https://tox.readthedocs.io/en/latest/), [Beutiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/), and [unittest](https://docs.python.org/3.7/library/unittest.html) for integration tests.
To run tests you can simply call `tox` or `make test`.

### Code Coverage
This project uses the [coverage](https://coverage.readthedocs.io/en/v4.5.x/) library to check code coverage.
To issue a report you can call `make coverage` followed by `make report`.

If you would like to create html pages from your reports you may then call `make report-html`.

## Docker

In the root directory of this repo you can see the [Dockerfile](Dockerfile) and [docker-compose.yaml](docker-compose.yaml) files. These can be used to build a docker image of this app. This image will be defaulting to the sqlite database and have a default admin account setup using the dev credentials. **Be sure to note the additional files to include that are listed at the top of this README.** If you want to configure the app in this image (and don't plan to use kubernetes) do the following:
To use your own config create a `config.py` file in the root directory and uncomment line 16 in [Dockerfile](Dockerfile#L16) for it to be copied over in the docker image.

If you plan to use this image as part of a kubernetes deployment the configuration will be implemented differently, and you can keep reading below.

## Kubernetes

This project has been updated to support postgres and some kubernetes yaml files were added in the [kubernetes](kubernetes) directory.

In order for this project to be deployed successfully there are some other files not included in this repo. They will be discussed in the following sections.

*Note: The following sections and the files provided will be built on the default namespace in minikube.*

*Disclaimer: The following sections utilize secrets to accomplish certain tasks. There are a few ways for this to have been implemented (using configmaps in combination with secrets), this may not be the best way. The reason I chose secrets is because either the information was sensitive or pieces of the information were sensitive.*

### Local Development

For local development I used [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/), [minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/), and [docker](https://www.docker.com/). Although I used docker to test a basic docker compose file and ensure my container was being built correctly, minikube also has docker. I also switched to minikube's `docker` to build my images after my initial tests. 

### Postgres

In order for the app to function correctly, the database was separated from the app. That way these two services can be in their own containers. In order for this to work, the configuration for the app will have to have an updated `SQLALCHEMY_DATABASE_URI` value containing the postgres connection string. Before you can apply the postgres kubernetes yamls you will need to create a few secrets that these files rely on.

#### postgres password

The first secret will need to contain the password for the postgres super user.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
data:
  pgpasssuper: <BASE64-of-password>
```

Make sure to replace the value of `pgpasssuper` with the base64 encoded password. Apply with kubectl.

#### init-script

The second secret is a script containing the password for the user that the app will use. This script was obtained from the [postgres docker page](https://hub.docker.com/_/postgres)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-init-secret
type: Opaque
stringData:
  init-user-db.sh: |-
    #!/bin/bash
    set -e

    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        CREATE USER <spellcheck-app-user> WITH PASSWORD '<replace-me-with-plaintext-secret>';
        CREATE DATABASE <spellcheck-app-database-name>;
        GRANT ALL PRIVILEGES ON DATABASE <spellcheck-app-database-name> TO <spellcheck-app-user>;
    EOSQL
```

Make sure to replace values wrapped in `<` and `>`. Apply with kubectl.

#### Deploying postgres

After the secrets have been applied we can now use the files in this repo under [kubernetes/database](kubernetes/database). I made use of the minikube machine for storage.

I ran the following commands:
```
minikube ssh

cd /mnt/

sudo mkdir data
```

Apply the yamls in the following order:
1. pv-volume.yaml
2. pv-claim.yaml
3. postgres-deployment.yaml
4. postgres-service.yaml

The first 2 are used to create a peristent volume and a persistent volume claim. Make sure you created the directory otherwise you might get a false positive and think you successfully created a persistent volume when in fact minikube created a short-lived temporary one. Double check with the following commands:

```
kubectl get pv

kubectl get pvc
```

There should only be one volume called `postgres-pv-volume` and our claim shoud be bound to it.

*Note: This won't break the behaviour of the app but you will lose all data upon restarting minikube.*

The third yaml belongs to the actual deployment. This is used to generate the deployment that will create our postgres pod. There is a lifecycle hook included here which is used to copy the initialization script we stored as a secret. It will copy it to the directory where the docker entrypoint will look in during startup. This is only executed once and won't be rerun if a database is detected. 

The fourth yaml is the definition for the service. This is created so that our app can connect to this pod.

### Spellcheckapp on kubernetes!

Before we can do anything we need to make sure that minikube will be able to find our docker image for the app. To accomplish this we can run `eval $(minikube docker-env)` to switch to using minikube's docker. Running `docker ps` should show a bunch of containers already running. This is only tied to the current terminal session you ran the `eval` command on. Now we can run `docker build -t spellcheckapp:latest .` to build our image locally within minikube.

Before we can apply the [spellcheckapp kubernetes files](kubernetes/web_service) we need to create the secret the deployment relies on.

#### Spellcheckapp secret

This secret is actually the configuration file that flask will use. This file contains many sensitive values which is why a secret was used.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: spellcheckapp-secret
type: Opaque
stringData:
  config.py: |-
    SECRET_KEY='<some-very-secret-key>'
    SQLALCHEMY_DATABASE_URI='postgres://<spellcheck-app-user>:<replace-me-with-plaintext-secret>@postgres:5432/<spellcheck-app-database-name>'
    SQLALCHEMY_TRACK_MODIFICATIONS=True
    SPELLCHECK='</path/to/spell_check_executable>'
    WORDLIST='</path/to/wordlist.txt>'
    SESSION_COOKIE_HTTPONLY=True
    SESSION_COOKIE_SAMESITE='Lax'
    REMEMBER_COOKIE_HTTPONLY=True
    ADMIN_USERNAME='<admin-username>'
    ADMIN_PASSWORD='<secret-admin-password>'
    ADMIN_MFA=<secret-MFA-must-be-integer-not-string>
```

Be sure to replace the values wrapped in `<` and `>`. Apply this secret with kubectl

#### Spellcheckapp deployment

Now we can apply the spellcheckapp yamls in the following order:
1. spellcheckapp_wb.yaml
2. spellcheckapp_service.yaml

The first yaml will be used to deploy our app with 4 replicas. These will all be using the same config so the secret key and database connection will be synced between all replicas that this deployment creates.

The second yaml will be used to create a loadbalancer service that will be in charge of directing requests to an available pod. Since all these spellcheckapp pods will be connecting to the same database, this should let our app behave correctly.


### Using the app

Now we can run `minikube service list` to see the url and port that our app is serving on. We can just paste this into our browser to check out our app.
