import math
import sqlite3
import json

from datetime import datetime
from time import time
from app import app

# import traceback

def db_execute(sql):
  print(sql)
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

  return pdfs, end_time - start_time, False #pdfs list, time took to process and False for telling to not display a "next button"

def get_pdfs_by_ids(pdfid_list,limit=8,page=0):
  pdfs = []
  start_time = time()
  if len(pdfid_list):
    pdfid_list.reverse()
    for pdfid in pdfid_list:
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

  return pdfs, end_time - start_time, False

def get_pdfid_by_name(name):
  sql = "SELECT ID FROM PDF WHERE NAME = '{}'".format(name)
  start_time = time()
  data = db_execute(sql)[0]
  end_time = time()
  pdfid = data[0]
  return pdfid

def get_pdfs_by_words(nb_pdf, ws, page=0, nb_max_by_pages=8, nb_min_pdfs=8):
  pdfs = []
  sql = """
        SELECT PDF_ID, NAME, DATE, WORD, SUM(W_FREQ * LOG(TIDF)) * COUNT(WORD) AS SCORE, TITLE, AUTHORS, YEAR, MONTH, ABSTRACT
        FROM (SELECT PDF_ID, WORD, W_FREQ
              FROM FREQ
              WHERE WORD IN ({}))
          INNER JOIN
             (SELECT PDF_ID AS P2, WORD AS W2, {} / COUNT(PDF_ID) AS TIDF
              FROM FREQ WHERE W2 IN ({})
              GROUP BY W2) ON WORD = W2
          INNER JOIN
             (SELECT ID, NAME, DATE, TITLE, AUTHORS, YEAR, MONTH, ABSTRACT
              FROM PDF) ON ID = PDF_ID
        GROUP BY PDF_ID
        ORDER BY SCORE DESC
        LIMIT {} OFFSET {}
      """.format(ws, str(float(nb_pdf)), ws, nb_max_by_pages, nb_max_by_pages * page)

  start_time = time()
  data = db_execute(sql)
  end_time = time()

  for row in data:
    pdfs.append({
      "pdf_name" : row[1],
      "date"     : format(datetime.fromtimestamp(row[2]), '%d/%m/%Y'),
      "score"    : row[4] * 100,
      "title"    : row[5],
      "authors"  : row[6],
      "year"     : row[7],
      "month"    : row[8],
      "abstract" : row[9]
    })

  return pdfs, end_time - start_time, False