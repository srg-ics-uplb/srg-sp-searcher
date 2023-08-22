import math
import sqlite3
import json

# from datetime import datetime
# from time import time
from app import app

# import traceback

def db_execute(sql):
  # print(sql)  
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
  sql = "SELECT userid, email, given_name, family_name, picture, allow_upload, allow_delete, view_history, saved_trs, user_type FROM USERS WHERE userid = '{}'".format(userid)
  user_data = db_execute(sql)[0]
  user = {
    "email"         : user_data[1],
    "given_name"    : user_data[2],
    "family_name"   : user_data[3],
    "picture"       : user_data[4],
    "allow_upload"  : user_data[5],
    "allow_delete"  : user_data[6],
    "view_history"  : user_data[7],
    "saved_trs"     : user_data[8],
    "user_type"     : user_data[9],
  }
  return user

def get_userid_by_email(email):
  sql = "SELECT userid FROM USERS WHERE email = '{}'".format(email)
  userid = db_execute(sql)[0]
  return userid[0]

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
  return get_user_by_id(credentials.get('userid'))
  
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

def get_delete_permission(userid):
  sql = "SELECT allow_delete FROM USERS WHERE userid = '{}'".format(userid)
  data = db_execute(sql)[0]
  return data[0]

def set_delete_permission(userid, permit):
  sql = "UPDATE USERS SET allow_delete = '{}' WHERE userid = '{}'".format(int(permit), userid)
  db_execute(sql)
  return get_delete_permission(userid)

def get_upload_permission(userid):
  sql = "SELECT allow_upload FROM USERS WHERE userid = '{}'".format(userid)
  data = db_execute(sql)[0]
  return data[0]

def set_upload_permission(userid, permit):
  sql = "UPDATE USERS SET allow_upload = '{}' WHERE userid = '{}'".format(int(permit), userid)
  db_execute(sql)
  return get_upload_permission(userid)

def get_user_type(userid):
  sql = f"SELECT user_type FROM users WHERE userid = '{userid}'"
  data = db_execute(sql)[0]
  return data

def set_user_type(userid, userType):
  sql = f"UPDATE users SET user_type = '{userType}' WHERE userid = '{userid}'"
  db_execute(sql)
  return get_user_type(userid)


def list_users():
  users = []
  sql = "SELECT email, given_name, family_name, allow_upload, allow_delete, userid, user_type FROM USERS"
  data = db_execute(sql)
  for row in data:
    users.append({
      "email"             : row[0],
      "name"              : "{} {}".format(row[1], row[2]),
      "allow_upload"      : row[3],
      "allow_delete"      : row[4],
      "id"                : row[5],
      "user_type"         : row[6],
    })
  return users

def get_user_names(users):
  quoteWord = lambda word : "'" + word + "'"
  sql = f"SELECT userid, given_name || ' ' || family_name FROM users WHERE userid IN ({', '.join(map(quoteWord, users))})" 
  rows = db_execute(sql)
  users = []
  if rows and len(rows) > 0:
    for row in rows:
      users.append({
        'id'        : row[0],
        'name'      : row[1],
      })

  return users