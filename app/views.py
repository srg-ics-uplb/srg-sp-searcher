from flask import Flask, render_template, request, redirect, url_for, abort, session, send_from_directory, send_file, make_response, jsonify
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
from . user_controllers import *
from . oauth import *
import json

import io
import random
import unicodedata

# @app.route('/static/pdf/<path:filename>')
# def protected(filename):
#     pdf_file=os.path.join(app.root_path,'static',app.config['PDF_DIR'])
#     #pdf_file=os.path.join(app.instance_path,'static',app.config['PDF_DIR'])

#     print(pdf_file,filename)
#     return send_from_directory(pdf_file,filename)

# @app.route('/uploads', methods=['POST'])
# def uploaded_page():
#     # if not app.config['ALLOW_UPLOAD']:
#     #     return render_template('search.html')

#     # FIXME : this function is too long (in lines and speed) !! use a thread ?
#     try:
#         if len(listdir(app.config['PDF_DIR_LOC'] + app.config['PDF_DIR'])) > 200:
#             return "Too many pdf already uploaded...max is 200"

#         title = request.form['title']
#         authors = request.form['authors']
#         year = request.form['year']
#         month = request.form['month']
#         abstract = request.form['abstract']
#         index_terms = request.form['index_terms']
#         userid = session.get('userid')

#         print(userid)

#         uploaded_file = request.files['file']
#         file_name = uploaded_file.filename
        
#         print(file_name)

#         if not file_name:
#             return "No file ?"

#         file_name = str(int(time())) + "_" + secure_filename(file_name)
#         pdf_path = app.config['PDF_DIR_LOC'] + app.config['PDF_DIR'] + file_name
#         print(pdf_path)
#         uploaded_file.save(pdf_path) #temporary save

#         # check if the hash all ready exists in the db
#         if pdf_allready_exists(file_name):
#             #remove the pdf from the directory
#             remove(pdf_path)
#             return "This pdf allready exist in the database... <a href='/search'>search</a>."        

#         # "File temporary uploaded... processing it before adding it to database...</br>"

#         counter = None
#         try:
#             #adding the file name to the text for searching by file name...
#             #norm_filnam = normalize_txt(file_name.replace('_', ' ').replace('.', ' ').replace('-', ' '))
#             #txt = read_as_txt(pdf_path) + " " + norm_filnam
#             # txt = read_as_txt(pdf_path) + " " + title + " " + authors + " " + year + " " + month
#             txt = abstract + " " + index_terms + " " + title + " " + authors + " " + year + " " + month
#             txt_arr = txt.split(' ')
#             txt = ""
#             for word in txt_arr:
#                 txt = txt + " " + word.strip(',.')

#             if not txt:
#                 remove(pdf_path)
#                 return "We cann't extract nothing from this pdf... <a href='/search'>search</a>."

#             counter = get_word_cout(txt)

#         except:
#             remove(pdf_path)
#             print(traceback.format_exc())
#             return "This is not a pdf... <a href='/search'>search</a>." 

#         pdfid = insert_pdf_to_db(file_name,title,authors,year,month,abstract,index_terms,userid) #add the pdf to the database 
#         total_words = sum(counter.values())
#         for word in counter: #update the words in database
#             insert_word_to_db(pdfid, word, counter[word] / float(total_words))
#         return redirect('/')
#         # return "File {} successfully uploaded as  {}... <a href='/search'>search</a>.".format(uploaded_file.filename, str(pdfid))
#     except:
#         abort(408)
#         return "Fail to uploadi."


# @app.route('/delete/<pdf_name>')
# def del_pdf(pdf_name):
#     if not app.config['ALLOW_DELETE']:
#         return "Delete is disabled. Back to <a href='/search'>search</a>." 

#     pdfid=delete_from_db(pdf_name)
#     #get the path to the target pdf
#     input_file = os.path.join(app.root_path,'static',app.config['PDF_DIR']) + secure_filename(pdf_name)
#     os.remove(input_file)
#     return pdf_name+" has been deleted. Back to <a href='/search'>search</a>."


@app.route('/bibtex/<pdf_name>')
def bibtex(pdf_name):
    return generate_bibtex(pdf_name)


@app.route('/pdf/<pdf_name>')
def return_pdf(pdf_name):
    try:
        add_pdf_to_view_history(pdf_name, session['userid'])
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






@app.before_request
def check_auth():
    PUBLIC_PATHS = ['/login', '/callback', '/register', '/logout', '/', '/search']
    if request.path.startswith('/static/styles') or request.path == '/favicon.ico':
        return
    print("{} {}".format(request.method, request.path))
    if request.path.startswith('/admin') and session.get('user', {'user_type': 'STUDENT'})['user_type'] != 'ADMIN':
        return redirect('/')
    if request.path in PUBLIC_PATHS or request.path.startswith('/research_paper'):
        return
    if not session or not session.get('user'):
        return redirect('/login')
    session['user'] = get_user_by_id(session['userid'])
    session['user']['name'] = session['user'].get('given_name') + " " + session['user'].get('family_name')
    session['favorites'] = get_user_favorites(session.get('userid'))
    return



# page routes
@app.route('/', methods=['GET'])
@app.route('/search', methods=['GET'])
@app.route('/history', methods=['GET'])
@app.route('/favorites', methods=['GET'])
def list_page():
    pendingUpload = session.get('pendingUpload', False)
    if pendingUpload:
        del session['pendingUpload']
    try:
        page = abs(int(request.args.get('p')))
    except:
        page = 0

    if (session):
        user_favorites = get_user_favorites(session['userid'])
        favorite_pdfs = get_pdfs_by_ids(user_favorites, limit=0)[0]

    if (request.path =='/search'):
        query = request.args.get('s')

        if not query:
            return redirect('/')

        query = query.lower()
        #query = unicodedata.normalize('NFKD', query).encode('ASCII', 'ignore')
        words = query.split()[:5] #max 5 words for querying...

        #words = map(secure_filename, words)

        # query = " ".join(words)
        
        # words = map(lemmatize, words)

        # if not words:
        #     return redirect('/')
        
        # route = '/search?s=' + '+'.join(query.split(' ')) + '&p='
        route = '/search?s=' + '+'.join(words) + '&p='
        title = 'Search'

        result = get_results(words, page)
        rows, speed, next_button = result
        rows = result[0]

    elif (request.path == '/history'):
        title = 'View History'
        rows, speed, next_button = get_history(session['userid'], page=page)
    elif (request.path == '/favorites'):
        title = 'Favorites'
        rows, speed, next_button = get_favorites(session['userid'], page=page)
        print(rows)
    else:
        title = 'Home'
        rows, speed, next_button = get_recents(page=page)

    try:
        route = route
    except:
        route = request.path + '?p='
        
    if session.get('user'):
        return render_template(
            'index.html',
            title = title,
            rows = rows,
            speed = speed,
            next_button = next_button,
            prev_button = page-1,
            user = session.get('user'),
            favorites = session.get('favorites'),
            favorite_pdfs = favorite_pdfs,
            route = route,
            baseURL = app.config['BASE_URL'],
            pendingUpload = pendingUpload
        )
    else:
        res = make_response(
            render_template(
                'index.html',
                title = title,
                rows = rows,
                speed = speed,
                next_button = next_button,
                prev_button = page-1,
                user = None,
                favorites = '[]',
                favorite_pdfs = '[]',
                route = route,
                client_id = app.config['GOOGLE_CLIENT_ID'], 
                oauth_callback_url = '/callback'
            )
        )
        res.headers.set('Referrer-Policy', 'no-referrer-when-downgrade')
        res.headers.set('Cross-Origin-Opener-Policy', 'same-origin-allow-popups')
        return res
    
@app.route('/upload', methods=['GET'])
def upload_page():
    # if get_upload_permission(get_userid_by_email(session['user']['email'])):
    if session['user'] is not None and not (session['user']['user_type'] == 'STUDENT' and user_has_pending_submission(session['user']['email'])):
        return render_template('upload.html', title='Upload', user=session.get('user'))
    session['pendingUpload'] = True
    return redirect('/')

@app.route('/research_paper/<pdf_name>')
def view_pdf(pdf_name):
    pdf_title = get_title_by_name(pdf_name)
    pdf = get_research_paper(get_pdfid_by_name(pdf_name))
    return render_template('pdf.html', title=pdf_title, user=session.get('user', None), pdf = pdf, baseURL = app.config['BASE_URL'])



# api routes
@app.route('/api/user/saved-trs/<pdfid>', methods=['PUT'])
def edit_favorites(pdfid):
    session['favorites'] = toggle_pdf_favorite(int(pdfid), session.get('userid'))
    return jsonify({ 'favorites' : session.get('favorites'), 'status' : 200 })

# @app.route('/api/pdf/<pdfid>', methods=['DELETE'])
# def delete_pdf_endpoint(pdfid):
#     if get_delete_permission(session.get('userid')):
#         pdf_name = get_pdf_name_by_id(pdfid)
#         # delete_from_db(pdf_name)
#         return jsonify({ 'status': 200, 'message': 'PDF {} successfully deleted from database.'.format(pdf_name)})
#     abort(403)

@app.route('/api/pdf/<pdfid>', methods=['PUT'])
def edit_pdf_endpoint(pdfid):
    if get_upload_permission(session.get('userid')):
        pdf = request.json
        for key, value in pdf.items():
            if value != get_pdf_value(pdf.get('id'),key):
                update_pdf_value(pdf.get('id'), key, value)
        pdf = get_research_paper(pdfid)
        return jsonify({
            'status': 200,
            'message': 'Successfully edited research paper',
            'pdf': pdf,
        })
    abort(403)

@app.route('/register', methods=['POST'])
def register_user():
    user = { 
        **(session.get('user')),
        "campus"      : request.form.get('campus'),
        "college"     : request.form.get('college'),
        "department"  : request.form.get('department'),
        "user_type"   : request.form.get('user_type')
    }
    upsert_user({**user, "userid": session.get('userid')})
    session['user'] = user
    session['favorites'] = get_user_favorites(session.get('userid'))
    return redirect('/')

@app.route('/api/user/<username>/delete-permit', methods=['PUT'])
def toggle_delete_permission(username):
    # check if current user has admin privileges
    userid = get_userid_by_email(session.get('user').get('email'))

    set_user = get_userid_by_email("{}@up.edu.ph".format(username))
    allow_delete = set_delete_permission(set_user, not int(get_delete_permission(set_user)))

    return jsonify({ 'status': 200, 'message': 'User delete permit changed.', 'deletePermit': allow_delete })

@app.route('/api/user/<username>/upload-permit', methods=['PUT'])
def toggle_upload_permission(username):
    set_user = get_userid_by_email("{}@up.edu.ph".format(username))
    allow_upload = set_upload_permission(set_user, not int(get_upload_permission(set_user)))

    return jsonify({ 'status': 200, 'message': 'User upload permit changed.', 'uploadPermit': allow_upload })

@app.route('/api/user/<userid>/userType/<newUserType>', methods=['PUT'])
def edit_user_type(userid, newUserType):
    print(userid)
    print(newUserType)
    userType = set_user_type(userid, newUserType)

    return jsonify({
        'status'        : 200,
        'message'       : 'User type changed.',
        'userType'      : userType,
    })

@app.route('/api/pdf/<pdfid>', methods=['DELETE'])
@app.route('/api/pdf/<pdfid>/status/<pdf_status>', methods=['PUT'])
def edit_pdf_status(pdfid, pdf_status):
    set_pdf_status(pdfid, pdf_status)

    return jsonify({
        'status'        : 200,
        'message'       : 'Successfully changed paper status.'
    })


# auth routes
@app.route('/login', methods=['GET'])
def login():
    res = make_response(render_template('login.html', client_id = app.config['GOOGLE_CLIENT_ID'], oauth_callback_url = app.config['BASE_URL'] + '/callback'))
    res.headers.set('Referrer-Policy', 'no-referrer-when-downgrade')
    res.headers.set('Cross-Origin-Opener-Policy', 'same-origin-allow-popups')
    return res

@app.route('/callback', methods=['POST', 'GET'])
def callback():
    credential = request.form.get('credential')
    user_google_data = verify_token(credential)
    if user_google_data:
        user = upsert_user(user_google_data)
        session['user'] = { **user, "name" : user.get('given_name') + " " + user.get('family_name') }
        session['userid'] = user_google_data['userid']
        session['favorites'] = get_user_favorites(user_google_data['userid'])

    return redirect('/')

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/')



# admin routes
@app.route('/admin', methods=['GET'])
@app.route('/admin/users', methods=['GET'])
def user_management_page():
    users = list_users()
    new_users = []
    for user in users:
        new_user = { **user, 'username': user.get('email')[:-10] }
        new_users.append(new_user)
    
    return render_template('users.html', title="User Management", users = new_users, user=session.get('user'))

@app.route('/admin/pdfs', methods=['GET'])
def pdf_management_page():
    submitted_pdfs = get_pdfs_by_status('SUBMITTED')
    return render_template('/pdfs.html', title="TR Management", pdfs=submitted_pdfs, user = session.get('user'))



@app.route('/upload', methods=['POST'])
def uploading_page():
    try:
        data = request.form.to_dict()

        uploaded_file = request.files['file']
        file_name = uploaded_file.filename

        if not file_name:
            return "No file ?"
        
        file_name = str(int(time())) + "_" + secure_filename(file_name)
        pdf_path = f'./app/static/pdf/{file_name}'
        uploaded_file.save(pdf_path) #temporary save

        # # check if the hash all ready exists in the db
        # if pdf_allready_exists(file_name):
        #     #remove the pdf from the directory
        #     remove(pdf_path)
        #     return "This pdf allready exist in the database... <a href='/search'>search</a>."        


        # print(data)
        # print(session['userid'])
        # print(session['user'])

        data['name'] = file_name
        data['uploaded_by'] = session['user']['email']

         # "File temporary uploaded... processing it before adding it to database...</br>"

        counter = None
        try:
            #adding the file name to the text for searching by file name...
            #norm_filnam = normalize_txt(file_name.replace('_', ' ').replace('.', ' ').replace('-', ' '))
            #txt = read_as_txt(pdf_path) + " " + norm_filnam
            # txt = read_as_txt(pdf_path) + " " + title + " " + authors + " " + year + " " + month
            txt = data['abstract'] + " " + data['index_terms'] + " " + data['title'] + " " + data['authors'] + " " + data['year'] + " " + data['month']
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

        pdfid = insert_pdf(data) #add the pdf to the database 
        print(pdfid)
        total_words = sum(counter.values())
        for word in counter: #update the words in database
            insert_word_to_db(pdfid, word, counter[word] / float(total_words))

        return jsonify({
            'status'        : 200,
            'message'       : 'Succesfully submitted paper'
        })
        # return redirect('/')
        # return "File {} successfully uploaded as  {}... <a href='/search'>search</a>.".format(uploaded_file.filename, str(pdfid))
    except:
        abort(408)
        return "Fail to uploadi."