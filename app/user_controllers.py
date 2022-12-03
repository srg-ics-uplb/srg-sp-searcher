import math
import sqlite3
import json

# from datetime import datetime
# from time import time
from app import app

# import traceback

def conn_to_db():
  conn = sqlite3.connect(app.config['DB_PATH'] + 'users.db')
  conn.create_function('LOG', 1, math.log)
  return conn

def get_user_by_id(userid):
  try:
    conn = conn_to_db()
    cursor = conn.execute("""
      SELECT * FROM USERS WHERE userid = '{}'
    """.format(userid))
    user_data = cursor.fetchone()
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
    conn.close()
    return user
  except sqlite3.Error as e:
    print(e)
    pass


def upsert_user(credentials):
  try:
    conn = conn_to_db()
    cursor = conn.execute("""
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
      ))
    conn.commit()
    conn.close()
    return get_user_by_id(credentials.get('userid'))
  except sqlite3.Error as e:
    print(e)
    pass

def get_view_history(userid):
  try:
    conn = conn_to_db()
    cursor = conn.execute("""
      SELECT view_history FROM USERS WHERE userid = '{}'
    """.format(
      userid
    ))
    view_history = None
    for row in cursor:
      view_history = row[0]

    conn.close()
    return json.loads(view_history)
  except sqlite3.Error as e:
    print(e)
    pass

def update_view_history(userid, view_history):
  try:
    conn = conn_to_db()
    cursor = conn.execute("""
      UPDATE USERS SET
      view_history = '{}'
      WHERE userid = '{}'
    """.format(
      view_history,
      userid
    ))
    conn.commit()
    conn.close()
    return get_user_by_id(userid)
  except sqlite3.Error as e:
    print(e)
    pass