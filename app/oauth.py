# import google.oauth2.credentials
# import google_auth_oauthlib.flow
from google.oauth2 import id_token
from google.auth.transport.requests import Request

# from flask import redirect, session, url_for
from app import app

# CLIENT_SECRETS_FILE = 'client_secret.json'
# SCOPES=['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'openid']

# def login_prompt():
#   print('Login prompt')

#   flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
#     CLIENT_SECRETS_FILE,
#     scopes=SCOPES
#   )

#   flow.redirect_uri = 'http://localhost:5000/callback'

#   authorization_url, state = flow.authorization_url(
#     access_type = 'offline',
#     prompt = 'select_account',
#     include_granted_scopes = 'true'
#   )
#   session['state'] = state
#   return redirect(authorization_url)

# def get_tokens(code):
#   state=session['state']
#   flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
#     CLIENT_SECRETS_FILE,
#     scopes=SCOPES,
#     state=state
#   )
#   flow.redirect_uri = url_for('callback', _external=True)
#   flow.fetch_token(code=code)
#   session['credentials'] = credentials_to_dict(flow.credentials)
#   return

# def credentials_to_dict(credentials):
#   return {'token': credentials.token,
#           'refresh_token': credentials.refresh_token,
#           'token_uri': credentials.token_uri,
#           'client_id': credentials.client_id,
#           'client_secret': credentials.client_secret,
#           'scopes': credentials.scopes}

# CLIENT_ID = "696707186269-vusumn77j1l0gur6ulkkf1orgvskinok.apps.googleusercontent.com"

def verify_token(token):
  try:

    # Specify the CLIENT_ID of the app that accesses the backend:
    idinfo = id_token.verify_oauth2_token(token, Request(), app.config['GOOGLE_CLIENT_ID'], clock_skew_in_seconds=10000)

    # Or, if multiple clients access the backend server:
    # idinfo = id_token.verify_oauth2_token(token, requests.Request())
    # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
    #     raise ValueError('Could not verify audience.')

    # If auth request is from a G Suite domain:
    # GSUITE_DOMAIN_NAME = 'up.edu.ph'
    # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
    #     raise ValueError('Wrong hosted domain.')

    # ID token is valid. Get the user's Google Account ID from the decoded token.
    user = {
      'userid': idinfo['sub'],
      'email': idinfo['email'],
      'given_name': idinfo['given_name'],
      'family_name': idinfo['family_name'],
      'picture': idinfo['picture']
    }
    return user
  except ValueError as ve:
    # Invalid token
    print(ve)
    pass