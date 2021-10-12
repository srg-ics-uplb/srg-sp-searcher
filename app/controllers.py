import re
import math
import hashlib
import sqlite3
import unicodedata

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

from collections import Counter
#from cStringIO import StringIO
from datetime import datetime
from time import time
from app import app

from io import StringIO
from email.generator import Generator

import traceback
import sys


from nltk import PorterStemmer

stemmer = PorterStemmer()

def lemmatize(word):
    #return stemmer.stem(word, 0, len(word) - 1)
    return stemmer.stem(word)

def conn_to_db(db_name):
    conn = sqlite3.connect(app.config['DB_PATH'] + db_name)
    conn.create_function('LOG', 1, math.log)
    return conn

def pdf_allready_exists(pdf_name):
    # check if a pdf is all ready in the database using the hash
    pdf_hash = hash_file(app.config['PDF_DIR_LOC'] + app.config['PDF_DIR'] + pdf_name)
    conn = conn_to_db('pdf.db')
    cursor = conn.execute("SELECT NAME, HASH, DATE FROM PDF WHERE HASH = '{}'".format(pdf_hash))
    for row in cursor: #just look if it contain one...
        conn.close()
        return True
    conn.close()
    return False

def insert_pdf_to_db(pdf_name,title,authors,year,month):
    # insert a pdf into the database and return his id
    path = app.config['PDF_DIR_LOC'] + app.config['PDF_DIR'] + pdf_name
    conn = conn_to_db('pdf.db')
    cursor = conn.execute("INSERT INTO PDF (NAME, HASH, DATE, TITLE, AUTHORS, YEAR, MONTH ) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                                            pdf_name, hash_file(path), int(time()), title, authors, year, month))
    conn.commit()
    pdf_id = cursor.lastrowid
    conn.close()
    return pdf_id

def insert_word_to_db(pdf_id, word, freq):
    conn = conn_to_db('pdf.db')
    conn.execute("INSERT INTO FREQ (PDF_ID, WORD, W_FREQ) VALUES ({}, '{}', {})".format(
                                    pdf_id, word, str(freq)))
    conn.commit()
    conn.close()

def generate_bibtex(pdf_name):
    conn = conn_to_db('pdf.db')
    cursor = conn.execute("SELECT TITLE, AUTHORS, YEAR FROM PDF WHERE NAME='"+pdf_name+"'")
    
    #fields = pdf_name.split("_")
    #cite_key=fields[len(fields)-1].split(".")[0]

    for row in cursor: 
        fields = row[1].split(",")
        temp1=fields[0].split(" ")
        temp2=temp1[len(temp1)-1]
        temp3=row[0].split(" ")
        cite_key = temp2+row[2]+temp3[0]
        retval = "@techreport{"+cite_key+", title={"+row[0]+"}, author={" +row[1].replace(","," and ")+" }, year={"+row[2]+"}, institution={Institute of Computer Science, University of the Philippines Los Baños}, type={Special Problems and Theses Technical Reports Series}}"

    conn.close()
    return retval
    

def delete_from_db(pdf_name):
    conn = conn_to_db('pdf.db')
    cursor = conn.execute("SELECT ID FROM PDF WHERE NAME='"+pdf_name+"'")

    for row in cursor:
        pdf_id = int(row[0])
    
    print("DELETE FROM PDF WHERE ID="+str(pdf_id))
    print("DELETE FROM FREQ WHERE PDF_ID="+str(pdf_id))
    #cursor = conn.execute("DELETE FROM PDF WHERE ID="+)
    conn.execute("DELETE FROM PDF WHERE ID="+str(pdf_id))
    conn.execute("DELETE FROM FREQ WHERE PDF_ID="+str(pdf_id))

    conn.commit()
    conn.close()
    return 0


def count_pdf():
    conn = conn_to_db('pdf.db')
    cursor = conn.execute("SELECT COUNT(*) FROM PDF")

    for row in cursor: #only one results...
        conn.close()
        return int(row[0])

    conn.close() #just in case...
    return 0

def get_results(words, page=0, nb_max_by_pages=8, nb_min_pdfs=8):
    nb_pdf = count_pdf()
    ws = "'" + "','".join(words) + "'"
    print(list(words))

    conn = conn_to_db('pdf.db')

    start_time = time()
    # a pdf_score is calculated  with sum(tf-idf) of words matched time the number of different words matched on the pdf
    cursor = conn.execute("""
        SELECT PDF_ID, NAME, DATE, WORD, SUM(W_FREQ * LOG(TIDF)) * COUNT(WORD) AS SCORE, TITLE, AUTHORS, YEAR, MONTH
        FROM (SELECT PDF_ID, WORD, W_FREQ
              FROM FREQ
              WHERE WORD IN ({}))
          INNER JOIN
             (SELECT PDF_ID AS P2, WORD AS W2, {} / COUNT(PDF_ID) AS TIDF
              FROM FREQ WHERE W2 IN ({})
              GROUP BY W2) ON WORD = W2
          INNER JOIN
             (SELECT ID, NAME, DATE, TITLE, AUTHORS, YEAR, MONTH
              FROM PDF) ON ID = PDF_ID
        GROUP BY PDF_ID
        ORDER BY SCORE DESC
        LIMIT {} OFFSET {}
      """.format(ws, str(float(nb_pdf)), ws, nb_max_by_pages, nb_max_by_pages * page))
    conn.commit()
    end_time = time()    

    pdfs = []
    for i, row in enumerate(cursor):
        pdfs.append({"pdf_name" : row[1],
                     "date"     : format(datetime.fromtimestamp(row[2]), '%d/%m/%Y'),
                     "score"    : row[4] * 100,
                     "title"     : row[5],
                     "authors"  : row[6],
                     "year"     : row[7],
                     "month"    : row[8]})
    conn.close()

    if len(pdfs) == nb_max_by_pages:
        return pdfs, end_time - start_time, True #pdfs list, time took to process and True for telling to display a "next button"

    conn = conn_to_db('pdf.db')
    cursor = conn.execute("SELECT NAME, DATE, TITLE, AUTHORS, YEAR, MONTH FROM PDF ORDER BY RANDOM() LIMIT {}".format(str(nb_min_pdfs - len(pdfs))))
    conn.commit()

    for row in cursor:
        pdfs.append({   "pdf_name"  : row[0], 
                        "date"      : format(datetime.fromtimestamp(row[1]), '%d/%m/%Y'),
                        "title"     : row[2],
                        "authors"   : row[3],
                        "year"      : row[4],
                        "month"     : row[5],  
                        "score" : 0})

    conn.close()
    return pdfs, end_time - start_time, False #pdfs list, time took to process and False for telling to not display a "next button"

def hash_file(path):
    # return the md5 hash of a file
    BLOCKSIZE = 65536
    hasher = hashlib.md5()

    with open(path, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)

    return hasher.hexdigest()

def normalize_txt(text):
    return re.sub('[^0-9a-zA-Z]+', ' ', unicodedata.normalize('NFKD', unicode(text, 'utf-8')).encode('ASCII', 'ignore'))

def convert_pdf_to_txt(pdfname): # just stollen here : https://gist.github.com/jmcarp/7105045
    rsrcmgr = PDFResourceManager()
    sio = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, sio, codec=codec, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    fp = open(pdfname, 'rb')
    for page in PDFPage.get_pages(fp):
        interpreter.process_page(page)
    fp.close()

    text = sio.getvalue()

    device.close()
    sio.close()

#    return normalize_txt(text)
    return text


def read_as_txt(pdf_path):
    try:
        return convert_pdf_to_txt(pdf_path)
    except:
        print(traceback.format_exc())
        return ''

def get_word_cout(txt):
    words = map(lemmatize, txt.lower().split())
    word_count = Counter(words)
    return word_count 

