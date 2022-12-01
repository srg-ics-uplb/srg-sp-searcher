from flask import Flask, render_template, request, redirect, url_for, abort, session, send_from_directory, send_file, make_response
from werkzeug.utils import secure_filename
from app import app
from time import time
from os import listdir, remove, getcwd
from time import gmtime, strftime
import traceback 
import sys, os
import qrcode
import fitz
import tempfile
import pytz
# import requests

from . controllers import *
from . oauth import *
import json

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


# @app.route('/', methods=['GET'])
# def index_page():

#     rows, speed, next_button = get_recents()

#     if app.config['ALLOW_DELETE']:
#         return render_template('index.html', rows=rows, speed=speed, next_button=next_button, allow_delete=True)

#     return render_template('index.html', rows=rows, speed=speed, next_button=next_button)

@app.route('/search', methods=['GET'])
#@auth.login_required
def search_page():
    query = request.args.get('s')
    page  = request.args.get('p')

    if not query:
        # return render_template('search.html', allow_upload=app.config['ALLOW_UPLOAD'], count_pdf=count_pdf())
        return redirect('/')

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
        # return render_template('index.html')
        return redirect('/')

    rows, speed, next_button = get_results(words, page)

    if next_button:
        next_button = page + 1

    if app.config['ALLOW_DELETE']:
        return render_template('index.html', user_request=query, rows=rows, speed=speed, next_button=next_button, allow_delete=True)

    if session['user']:
        return render_template('index.html', user_request=query, rows=rows, speed=speed, next_button=next_button, user=session['user'])
    return render_template('index.html', user_request=query, rows=rows, speed=speed, next_button=next_button)

@app.route('/upload', methods=['GET'])
@auth.login_required
def upload_page():
    if not app.config['ALLOW_UPLOAD']:
        return render_template('index.html')
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
        abstract = request.form['abstract']
        index_terms = request.form['index_terms']

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
            # txt = read_as_txt(pdf_path) + " " + title + " " + authors + " " + year + " " + month
            txt = abstract + " " + index_terms + " " + title + " " + authors + " " + year + " " + month
            txt_arr = txt.split(' ')
            txt = ""
            for word in txt_arr:
                txt = txt + " " + word.strip(',.')

            if not txt:
                remove(pdf_path)
                return "We cann't extract nothing from this pdf... <a href='/search'>search</a>."

            counter = get_word_cout(txt)

        except:
            remove(pdf_path)
            print(traceback.format_exc())
            return "This is not a pdf... <a href='/search'>search</a>." 

        pdf_id = insert_pdf_to_db(file_name,title,authors,year,month,abstract,index_terms) #add the pdf to the database 
        total_words = sum(counter.values())
        for word in counter: #update the words in database
            insert_word_to_db(pdf_id, word, counter[word] / float(total_words))
        return "File {} successfully uploaded as  {}... <a href='/search'>search</a>.".format(uploaded_file.filename, str(pdf_id))
    except:
        return "Fail to uploadi."


@app.route('/delete/<pdf_name>')
@auth.login_required
def del_pdf(pdf_name):
    if not app.config['ALLOW_DELETE']:
        return "Delete is disabled. Back to <a href='/search'>search</a>." 

    pdf_id=delete_from_db(pdf_name)
    #get the path to the target pdf
    input_file = os.path.join(app.root_path,'static',app.config['PDF_DIR']) + secure_filename(pdf_name)
    os.remove(input_file)
    return pdf_name+" has been deleted. Back to <a href='/search'>search</a>."


@app.route('/bibtex/<pdf_name>')
#@auth.login_required
def bibtex(pdf_name):
    return generate_bibtex(pdf_name)


@app.route('/pdf/<pdf_name>')
@auth.login_required
def return_pdf(pdf_name):
    try:
        #get current date and time in PH
        datetime_ph = datetime.now(pytz.timezone('Asia/Manila'))
        download_date=datetime_ph.strftime("%Y-%m-%d %H:%M:%S %Z %z" )        
        input_data=request.base_url+" "+download_date

        #generate a qr code
        qr = qrcode.QRCode(
            version=1,
            box_size=2,
            border=5)
        qr.add_data(input_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        qrcode_filename=make_temp_file("qrcode.png")
        img.save(qrcode_filename) 

        #get the path to the target pdf
        input_file = os.path.join(app.root_path,'static',app.config['PDF_DIR']) + secure_filename(pdf_name)

        # retrieve the first page of the PDF
        file_handle = fitz.open(input_file)
        first_page = file_handle[0]
        img=open(qrcode_filename, "rb").read()

        # define the position (upper-right corner)
        #image_rectangle = fitz.Rect(530,2,610,82)
        image_rectangle = fitz.Rect(500,2,560,62)
        # add the image
        first_page.insert_image(image_rectangle, stream=img)
        
        return_filename = make_temp_file(secure_filename(pdf_name))
        file_handle.save(return_filename)
        file_handle.close()

        resp = send_file(return_filename,secure_filename(pdf_name))
    
        #remove the temporary files (works only in linux)
        os.remove(qrcode_filename)
        os.remove(return_filename)
        
        return resp
    except:
        print(traceback.format_exc())
        abort(404)

#Utility function to create a temporaty file with suffix
def make_temp_file(suffix):
        temp = tempfile.NamedTemporaryFile()
        return temp.name+"_"+suffix






@app.route('/', methods=['GET'])
def index():
    print('GET /')
    rows, speed, next_button = get_recents(limit=8)
    if not session['user']:
        res = make_response(render_template('index.html', rows=rows, speed=speed, next_button=next_button, client_id = app.config['GOOGLE_CLIENT_ID'], oauth_callback_url = "http://localhost:5000/callback"))
        res.headers.set('Referrer-Policy', 'no-referrer-when-downgrade')
        res.headers.set('Cross-Origin-Opener-Policy', 'same-origin-allow-popups')
        return res

    return render_template('index.html', rows=rows, speed=speed, next_button=next_button, user = session['user'])


@app.route('/callback', methods=['POST', 'GET'])
def callback():
    credential = request.form.get('credential')
    user = verify_token(credential)
    if user:
        session['user'] = json.dumps(user)

        # get view history and saved pdfs
    
    return redirect('/')

@app.route('/logout', methods=['GET'])
def logout():
    session['user'] = None
    return redirect('/')