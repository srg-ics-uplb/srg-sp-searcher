import math
import sqlite3
import json

# from datetime import datetime
# from time import time
from app import app

# import traceback

def db_execute(sql):
  print(sql)  
  try:
    data = []

    with sqlite3.connect(app.config['DB_PATH'] + 'users.db') as conn:
      conn.create_function('LOG', 1, math.log)
      cursor = conn.execute(sql)
      for row in cursor:
        # print('user_controllers.py/db_execute()')
        # print(row)
        data.append(row)
      conn.commit()

    return data
  except sqlite3.Error as e:
    conn.rollback()
    print(e)
    pass
  finally:
    conn.close()

def get_user_by_id(userid):
  sql = "SELECT * FROM USERS WHERE userid = '{}'".format(userid)
  user_data = db_execute(sql)[0]
  user = {
    "userid"        : user_data[0],
    "email"         : user_data[1],
    "given_name"    : user_data[2],
    "family_name"   : user_data[3],
    "picture"       : user_data[4],
    "allow_upload"  : user_data[5],
    "allow_delete"  : user_data[6],
    "view_history"  : user_data[7],
    "saved_trs"     : user_data[8]
  }
  return user

def upsert_user(credentials):
  sql = """
      INSERT INTO USERS(userid, email, given_name, family_name, picture)
      VALUES ('{userid}', '{email}', '{given_name}', '{family_name}', '{picture}')
      ON CONFLICT (userid) DO UPDATE SET
      given_name = excluded.given_name,
      family_name = excluded.family_name,
      picture = excluded.picture
      WHERE userid = '{userid}'
    """.format(
      userid = credentials.get('userid'),
      email = credentials.get('email'),
      given_name = credentials.get('given_name'),
      family_name = credentials.get('family_name'),
      picture = credentials.get('picture')
    )
  db_execute(sql)
  return
  
def get_view_history(userid):
  sql = "SELECT view_history FROM USERS WHERE userid = '{}'".format(userid)
  data = db_execute(sql)[0]
  view_history = []
  if len(data):
    for row in data:
      view_history = row
  return json.loads(view_history)

def update_view_history(userid, view_history):
  sql = """
      UPDATE USERS SET
      view_history = '{}'
      WHERE userid = '{}'
    """.format(
      view_history,
      userid
    )
  db_execute(sql)
  return

def get_user_favorites(userid):
  sql = "SELECT saved_trs FROM USERS WHERE userid = '{}'".format(userid)
  data = db_execute(sql)[0]
  favorites = []
  if len(data):
    for row in data:
      favorites = row
  return json.loads(favorites)
  
def update_user_favorites(userid, favorites):
  sql = """
      UPDATE USERS SET
      saved_trs = '{}'
      WHERE userid = '{}'
    """.format(
      favorites,
      userid
    )
  db_execute(sql)
  return