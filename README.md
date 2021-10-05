# SRG Technical Reports Searcher

Useful for setting up a repository of technical reports for a research group.

Credits to: https://github.com/VieVie31/podofo

## Dependencies
Must be available on the dev/prod box.
1. Python3
2. Pip
3. SQLite3

In Ubuntu 20.04: `sudo apt install python3-pip sqlite3`

## Install

1. `git clone https://github.com/srg-ics-uplb/srg-tr-searcher`
2. `cd srg-tr-searcher`
3. `pip install -r requirements.txt`
4. `export PATH=$PATH:$HOME/.local/bin`
5. `mkdir app/static/pdf`
6. `./reset.sh`

## Populate
1. Set the username and password in `app/creds.py`
2. Enable upload by setting `app.config['ALLOW_UPLOAD'] = True` in `app/__init__.py`
3. `gunicorn -c gunicorn_config.py app:app`
4. Open `http://127.0.0.1:5000` in browser
5. Check `access.log` and `error.log` files 

## Deploy
Docker is the best way to deploy the app.

1.  Set a strong the username and password in `app/creds.py`
2.  Disable upload by setting `app.config['ALLOW_UPLOAD'] = False` in `app/__init__.py`
3. `docker-compose build`
4. `DOCKER_HOST="ssh://remote.docker.host" docker-compose down`
4. `DOCKER_HOST="ssh://remote.docker.host" docker-compose up -d`


