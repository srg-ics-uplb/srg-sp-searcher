# SRG Technical Reports Searcher

based on https://github.com/VieVie31/podofo

## Installation

1. `git clone https://github.com/srg-ics-uplb/srg-tr-searcher`
2. `cd srg-tr-searcher`
3. `sudo apt install python3-pip sqlite3`
4. `pip install -r requirements.txt`
5. `export PATH=$PATH:$HOME/.local/bin`
6. `mkdir app/static/pdf`
7. `./reset.sh`

## Configuration
1. Set the username and password in `app/creds.py`
2. To allow upload set `app.config['ALLOW_UPLOAD'] = True` in `app/__init__.py`

## Running the app locally
Useful for debugging and uploading.

1. `gunicorn -c gunicorn_config.py app:app`
2. Open `http://127.0.0.1:5000` in browser
3. Check the `access.log` and `error.log` files 

## Deploying the app
Docker is the best way to deploy the app.

1. `docker-compose build`
2. `DOCKER_HOST="ssh://dockeri.host.server" docker-compose up -d`


