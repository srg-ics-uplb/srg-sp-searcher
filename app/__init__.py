from flask import Flask, render_template, request, redirect, url_for, abort, session
from flask_session import Session
import json

app = Flask(__name__)

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# app.config.from_pyfile('creds.py')
app.config.from_pyfile('configs.py')

app.config['DEBUG'] = True
app.config['PDF_DIR_LOC'] = './app/static/'
app.config['PDF_DIR'] = './pdf/' 
app.config['DB_PATH'] = './app/sql/'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 #10 Mo size max for upload

#
app.config['RESEARCH_GROUP'] = ""
app.config['INSTITUTION'] = "Institute of Computer Science, University of the Philippines Los Baños"
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


CLIENT_SECRETS_FILE = open('client_secret.json')
CLIENT_SECRETS = json.load(CLIENT_SECRETS_FILE)
CLIENT_SECRETS_FILE.close()

app.config['GOOGLE_API_CLIENT_SECRETS'] = CLIENT_SECRETS['web']
app.config['GOOGLE_CLIENT_ID'] = CLIENT_SECRETS['web'].get('client_id')

print("Server listening on " + app.config['BASE_URL'])

from app import views

