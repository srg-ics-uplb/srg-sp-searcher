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
  pdfs = []
  start_time = time()

  if len(pdfid_list):
    pdfid_page = pdfid_list
    if limit != 0:
      pdfid_page = [pdfid_list[i * limit:(i + 1) * limit] for i in range((len(pdfid_list) + limit - 1) // limit )][page]

    if len(pdfid_page):
      for pdfid in pdfid_page:
        sql = """
            SELECT ID, NAME, DATE, TITLE, AUTHORS, YEAR, MONTH, ABSTRACT
            FROM PDF
            WHERE ID = ({})
        """.format(
            pdfid
        )
        data = db_execute(sql)

        for row in data:
          pdfs.append({
              "id"        : row[0],
              "pdf_name"  : row[1],
              "date"      : format(datetime.fromtimestamp(row[2]), '%d/%m/%Y'),
              "title"     : row[3],
              "authors"   : row[4],
              "year"      : row[5],
              "month"     : row[6],
              "abstract"  : row[7]
          })  
      
  end_time = time()

  next_button = set_next_button(len(pdfid_list), page+1, limit)

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
        SELECT A.PDF_ID, NAME, DATE, WORD, SUM(W_FREQ * LOG(TIDF)) * COUNT(WORD) AS SCORE, TITLE, AUTHORS, YEAR, MONTH, ABSTRACT
        FROM (SELECT PDF_ID, WORD, W_FREQ
              FROM FREQ
              WHERE WORD IN ({})) A
          INNER JOIN
             (SELECT ID AS P2, WORD AS W2, {} / COUNT(ID) AS TIDF
              FROM FREQ WHERE W2 IN ({})
              GROUP BY W2) B ON A.WORD = B.W2
          INNER JOIN
             (SELECT ID, NAME, DATE, TITLE, AUTHORS, YEAR, MONTH, ABSTRACT
              FROM PDF) C ON A.PDF_ID = C.ID
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
  sql = """UPDATE PDF SET
    {} = "{}"
    WHERE ID = {}
  """.format(column, value, pdfid)
  db_execute(sql)
  return