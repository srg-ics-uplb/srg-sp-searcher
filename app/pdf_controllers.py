from flask import session

import math
import sqlite3
import json

from datetime import datetime
from time import time
from app import app

# import traceback

def db_execute(sql):
  # print(sql)
  try:
    data = []

    with sqlite3.connect(app.config['DB_PATH'] + 'pdf.db') as conn:
      conn.create_function('LOG', 1, math.log)
      cursor = conn.execute(sql)
      for row in cursor:
        # print('pdf_controllers.py/db_execute()')
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

def get_pdf_count():
  sql = 'SELECT COUNT(id) FROM PDF'
  data = db_execute(sql)

  return data[0][0]

def get_most_recents(limit=3, page=0):
  sql = """
      SELECT
      NAME, DATE, TITLE, AUTHORS, YEAR, MONTH, ABSTRACT, ID
      FROM PDF
      WHERE status = (SELECT id FROM pdf_status WHERE name = 'APPROVED')
      ORDER BY ID DESC LIMIT {} OFFSET {}
  """.format(limit, page*limit)

  start_time=time()
  data = db_execute(sql)
  end_time=time()

  pdfs = []
  for row in data:
    pdfs.append({ 
      "pdf_name"  : row[0], 
      "date"      : format(datetime.fromtimestamp(row[1]), '%d/%m/%Y'),
      "title"     : row[2],
      "authors"   : row[3],
      "year"      : row[4],
      "month"     : row[5],  
      "abstract"  : row[6],
      "id"        : row[7],
      "score"     : 0
    })

  next_button = set_next_button(get_pdf_count(), page + 1, limit)

  return pdfs, end_time - start_time, next_button #pdfs list, time took to process and False for telling to not display a "next button"

def get_pdfs_by_ids(pdfid_list,limit=5,page=0):
  print(pdfid_list)
  pdfs = []
  start_time = time()

  if len(pdfid_list):
    pdfid_page = pdfid_list
    if limit != 0:
      pdfid_page = [pdfid_list[i * limit:(i + 1) * limit] for i in range((len(pdfid_list) + limit - 1) // limit )][page]
    print(pdfid_page)

    if len(pdfid_page):
      for pdfid in pdfid_page:
        print(pdfid)
        sql = f"""
            SELECT ID, NAME, DATE, TITLE, AUTHORS, YEAR, MONTH, ABSTRACT, status
            FROM PDF
            WHERE ID = '{pdfid}'
            AND status = (SELECT id FROM pdf_status WHERE name = 'APPROVED')
        """
        data = db_execute(sql)

        print(data)

        for row in data:
          pdfs.append({
              "id"        : row[0],
              "pdf_name"  : row[1],
              "date"      : format(datetime.fromtimestamp(row[2]), '%d/%m/%Y'),
              "title"     : row[3],
              "authors"   : row[4],
              "year"      : row[5],
              "month"     : row[6],
              "abstract"  : row[7],
              "status"    : row[8]
          })  
      
  end_time = time()

  next_button = set_next_button(len(pdfid_list), page+1, limit)

  print('haha')
  print(pdfs)

  return pdfs, end_time - start_time, next_button

def get_pdfid_by_name(name):
  sql = "SELECT ID FROM PDF WHERE NAME = '{}'".format(name)
  start_time = time()
  data = db_execute(sql)[0]
  end_time = time()
  pdfid = data[0]
  return pdfid

def get_pdf_name_by_id(pdfid):
  sql = "SELECT NAME FROM PDF WHERE ID = '{}'".format(pdfid)
  data = db_execute(sql)[0]
  pdf_name = data[0]
  return pdf_name

def get_pdfs_by_words(nb_pdf, ws, page=0, nb_max_by_pages=8, nb_min_pdfs=8):
  pdfs = []
  sql = """
        SELECT A.PDF_ID, NAME, DATE, WORD, SUM(W_FREQ * LOG(TIDF)) * COUNT(WORD) AS SCORE, TITLE, AUTHORS, YEAR, MONTH, ABSTRACT, STATUS
        FROM (SELECT PDF_ID, WORD, W_FREQ
              FROM FREQ
              WHERE WORD IN ({})) A
          INNER JOIN
             (SELECT ID AS P2, WORD AS W2, {} / COUNT(ID) AS TIDF
              FROM FREQ WHERE W2 IN ({})
              GROUP BY W2) B ON A.WORD = B.W2
          INNER JOIN
             (SELECT ID, NAME, DATE, TITLE, AUTHORS, YEAR, MONTH, ABSTRACT, STATUS
              FROM PDF) C ON A.PDF_ID = C.ID
        WHERE STATUS = (SELECT id FROM pdf_status WHERE name = 'APPROVED')
        GROUP BY A.PDF_ID
        ORDER BY SCORE DESC
        LIMIT {} OFFSET {}
      """.format(ws, str(float(nb_pdf)), ws, nb_max_by_pages, nb_max_by_pages * page)

  start_time = time()
  data = db_execute(sql)
  end_time = time()

  for row in data:
    pdfs.append({
      "id"       : row[0],
      "pdf_name" : row[1],
      "date"     : format(datetime.fromtimestamp(row[2]), '%d/%m/%Y'),
      "score"    : row[4] * 100,
      "title"    : row[5],
      "authors"  : row[6],
      "year"     : row[7],
      "month"    : row[8],
      "abstract" : row[9]
    })

  sql = "SELECT COUNT(*) FROM FREQ WHERE WORD IN ({})".format(ws)
  count = db_execute(sql)[0][0]

  next_button = set_next_button(count, page + 1, nb_max_by_pages)
  output = pdfs, end_time - start_time, next_button
  return output

def get_recents(limit=5, page=0, nb_max_by_pages=8, nb_min_pdfs=8):
  return get_most_recents(limit, page)

def set_next_button(count, page, limit):
  if count > page * limit:
    return page
  return 0

def get_title_by_name(pdf_name):
  sql = "SELECT title FROM PDF WHERE name = '{}'".format(pdf_name)
  data = db_execute(sql)[0]
  return data[0]

def get_research_paper(pdfid):
  sql = """SELECT
      ID,
      NAME,
      DATE,
      TITLE,
      AUTHORS,
      YEAR,
      MONTH,
      ABSTRACT,
      INDEX_TERMS
    FROM PDF
    WHERE ID = {}""".format(pdfid)
  
  data = db_execute(sql)[0]

  pdf = {
    "id":           data[0],
    "name":         data[1],
    "date":         data[2],
    "title":        data[3],
    "authors":      data[4],
    "year":         data[5],
    "month":        data[6],
    "abstract":     data[7],
    "index_terms":  data[8].split(',')
  }

  return pdf

def get_pdf_value(pdfid, column):
  sql = "SELECT {} FROM PDF WHERE ID = {}".format(column, pdfid)
  data = db_execute(sql)[0]
  return data[0]

def update_pdf_value(pdfid, column, value):
  activity = f"{get_pdf_value(pdfid, 'uploaded_by')} edited pdf#{pdfid}; set {column} from {get_pdf_value(pdfid, column)} to {value}"
  sql = f"INSERT INTO LOGS (userid, pdfid, activity) VALUES ('{session['userid']}','{pdfid}','{activity}')"
  db_execute(sql)
  sql = """UPDATE PDF SET
    {} = "{}"
    WHERE ID = {}
  """.format(column, value, pdfid)
  db_execute(sql)
  return

def get_pdfs_by_status(status):
  sql = f"SELECT id, name, date, title, authors, year, month, abstract, index_terms, status, uploaded_by FROM pdf WHERE status = (SELECT id FROM pdf_status WHERE name = '{status}')"
  rows = db_execute(sql)

  pdfs = []
  if rows and len(rows) > 0:
    for row in rows:
      pdfs.append({
        'id'            : row[0],
        'name'          : row[1],
        'date'          : datetime.utcfromtimestamp(int(row[2])).strftime('%d %b, %Y'),
        'title'         : row[3],
        'authors'       : row[4],
        'year'          : row[5],
        'month'         : row[6],
        'abstract'      : row[7],
        'index_terms'   : row[8],
        'status'    : row[9],
        'uploaded_by'   : row[10]
      })

  return pdfs

def get_pdf_status(pdfid):
  print(pdfid)
  sql = f"SELECT status FROM pdf a JOIN pdf_status b ON a.status = b.id WHERE a.id = '{pdfid}'"
  pdf = db_execute(sql)[0]

  return pdf[0]

def get_status_name(status_id):
  sql = f"SELECT name FROM pdf_status WHERE id = {status_id}"
  status_name = db_execute(sql)[0][0]
  return status_name

def set_pdf_status(pdfid, status):
  activity = f"{session['user']['email']} edited pdf#{pdfid}; set status from {get_status_name(get_pdf_status(pdfid))} to {status}"
  sql = f"INSERT INTO LOGS (userid, pdfid, activity) VALUES ('{session['userid']}','{pdfid}','{activity}')"
  db_execute(sql)
  sql = f"UPDATE pdf SET status = (SELECT id FROM pdf_status WHERE name = '{status}') WHERE id = '{pdfid}'"
  db_execute(sql)
  return

# check for user type; if user is student limit to one pending submission
def user_has_pending_submission(email):
  sql = f"SELECT * FROM pdf WHERE uploaded_by = '{email}' AND status = (SELECT id FROM pdf_status WHERE name = 'SUBMITTED')"
  rows = db_execute(sql)

  print(rows)

  if rows is None or len(rows) == 0:
    return False
  return True
