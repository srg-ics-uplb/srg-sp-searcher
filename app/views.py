from flask import Flask, render_template, request, redirect, url_for, abort, session, send_from_directory, send_file
from werkzeug.utils import secure_filename
from app import app
from time import time
from os import listdir, remove, getcwd
from . controllers import *
import traceback 
import sys, os

from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

import io
import random
import unicodedata


auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if username in users:
        return check_password_hash(users.get(username), password)
    return False

user = app.config["USERNAME"]
pw = app.config["PASSWORD"]

users = {
    user: generate_password_hash(pw)
}


@app.route('/static/pdf/<path:filename>')
@auth.login_required
def protected(filename):
    pdf_file=os.path.join(app.root_path,'static',app.config['PDF_DIR'])
    #pdf_file=os.path.join(app.instance_path,'static',app.config['PDF_DIR'])

    print(pdf_file,filename)
    return send_from_directory(pdf_file,filename)


@app.route('/', methods=['GET'])
@app.route('/search', methods=['GET'])
@auth.login_required
def search_page():
    query = request.args.get('s')
    page  = request.args.get('p')

    if not query:
        return render_template('search.html', allow_upload=app.config['ALLOW_UPLOAD'], count_pdf=count_pdf())

    try:
        page = abs(int(page))
    except:
        page = 0

    query = query.lower()
    #query = unicodedata.normalize('NFKD', query).encode('ASCII', 'ignore')
    words = query.split()[:5] #max 5 words for querying...

    #words = map(secure_filename, words)

    query = " ".join(words)
    

    #words = map(lemmatize, words)
    
    print(words)

    if not words:
        return render_template('search.html')

    rows, speed, next_button = get_results(words, page)

    if next_button:
        next_button = page + 1

    return render_template('results.html', user_request=query, rows=rows, speed=speed, next_button=next_button)

@app.route('/upload', methods=['GET'])
@auth.login_required
def upload_page():
    if not app.config['ALLOW_UPLOAD']:
        return render_template('search.html')
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
@auth.login_required
def uploaded_page():
    if not app.config['ALLOW_UPLOAD']:
        return render_template('search.html')

    # FIXME : this function is too long (in lines and speed) !! use a thread ?
    try:
        if len(listdir(app.config['PDF_DIR_LOC'] + app.config['PDF_DIR'])) > 200:
            return "Too many pdf already uploaded...max is 200"

        title = request.form['title']
        authors = request.form['authors']
        year = request.form['year']
        month = request.form['month']

        uploaded_file = request.files['file']
        file_name = uploaded_file.filename

        if not file_name:
            return "No file ?"

        file_name = str(int(time())) + "_" + secure_filename(file_name)
        pdf_path = app.config['PDF_DIR_LOC'] + app.config['PDF_DIR'] + file_name
        print(pdf_path)
        uploaded_file.save(pdf_path) #temporary save

        # check if the hash all ready exists in the db
        if pdf_allready_exists(file_name):
            #remove the pdf from the directory
            remove(pdf_path)
            return "This pdf allready exist in the database... <a href='/search'>search</a>."        

        # "File temporary uploaded... processing it before adding it to database...</br>"

        counter = None
        try:
            #adding the file name to the text for searching by file name...
            #norm_filnam = normalize_txt(file_name.replace('_', ' ').replace('.', ' ').replace('-', ' '))
            #txt = read_as_txt(pdf_path) + " " + norm_filnam
            txt = read_as_txt(pdf_path) + " " + title + " " + authors + " " + year + " " + month

            if not txt:
                remove(pdf_path)
                return "We cann't extract nothing from this pdf... <a href='/search'>search</a>."

            counter = get_word_cout(txt)

        except:
            remove(pdf_path)
            print(traceback.format_exc())
            return "This is not a pdf... <a href='/search'>search</a>." 

        pdf_id = insert_pdf_to_db(file_name,title,authors,year,month) #add the pdf to the database 
        total_words = sum(counter.values())
        for word in counter: #update the words in database
            insert_word_to_db(pdf_id, word, counter[word] / float(total_words))
        return "File {} successfully uploaded as  {}... <a href='/search'>search</a>.".format(uploaded_file.filename, str(pdf_id))
    except:
        return "Fail to uploadi."


@app.route('/pdf/<pdf_name>')
@auth.login_required
def return_pdf(pdf_name):
    try:
        return redirect(url_for('static', filename=app.config['PDF_DIR'] + secure_filename(pdf_name)))
    except:
        abort(404)


