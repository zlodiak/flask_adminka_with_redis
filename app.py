from flask import Flask, render_template, request, Response, make_response, redirect
import psycopg2
import hashlib

from classes.db_connection import DB_connection

app = Flask(__name__)

@app.route('/')
def auth():
    if 'flask_adminka_authorized_user_id' in request.cookies:
        return redirect('/admin')

    return render_template('auth.html')


@app.route('/admin')
def admin():    
    if 'flask_adminka_authorized_user_id' not in request.cookies:
        return redirect('/', code=404)

    admin_forms_values = {
        'firstname': None,
        'lastname': None,
        'notepad': None,
    }

    with DB_connection() as db_connect:
        db_cursor = db_connect.cursor()
        id_auth_user = request.cookies.get('flask_adminka_authorized_user_id')

        try:
            request_form = "select * from options where user_id='" + id_auth_user + "'"
            db_cursor.execute(request_form)
            record = db_cursor.fetchone()
            admin_forms_values['firstname'] = record[1]
            admin_forms_values['lastname'] = record[2]
            admin_forms_values['notepad'] = record[3]
            print('log: successfull retrieve admin_forms_values', admin_forms_values)
        except:
            print('log: failed retrieve admin_forms_values', admin_forms_values)
        
        return render_template('admin.html', admin_forms_values=admin_forms_values)


@app.route('/auth_request', methods=['POST'])
def auth_request():
    with DB_connection() as db_connect:
        db_cursor = db_connect.cursor()

        pasword = request.values.get('password')
        password_hash = hashlib.sha1(pasword.encode('ASCII')).hexdigest()
        email = request.values.get('email')
        req = "select * from users where password_hash='" + password_hash + "' and email='" + email + "' and active=TRUE"

        try:
            db_cursor.execute(req)
            user = db_cursor.fetchone() 
            resp = Response('authorized')
            resp.headers['Set-Cookie'] = 'flask_adminka_authorized_user_id=' + str(user[0])
            return resp
        except:
            resp = Response('not authorized')
            return resp


@app.route('/submit_profile_request', methods=['POST'])
def submit_profile_request():
    with DB_connection() as db_connect:
        db_cursor = db_connect.cursor()

        firstname = request.values.get('firstname')
        lastname = request.values.get('lastname')
        id_auth_user = request.cookies.get('flask_adminka_authorized_user_id')

        req = "select * from options where user_id=" + id_auth_user
        db_cursor.execute(req)
        record = db_cursor.fetchone() 

        if record:
            try: 
                req = "UPDATE options SET firstname='" + firstname + "', lastname='" + lastname + "' WHERE user_id=" + str(id_auth_user)
                db_cursor.execute(req);
                db_connect.commit()
                resp = Response('submit profile is complete')
                return resp
            except:
                resp = Response('failed')
                return resp


@app.route('/submit_notepad_request', methods=['POST'])
def submit_notepad_request():
    with DB_connection() as db_connect:
        db_cursor = db_connect.cursor()

        notepad = request.values.get('notepad')
        id_auth_user = request.cookies.get('flask_adminka_authorized_user_id')

        req = "select * from options where user_id=" + id_auth_user
        db_cursor.execute(req)
        record = db_cursor.fetchone() 

        if record:
            try: 
                req = "UPDATE options SET notepad='" + notepad + "' WHERE user_id=" + str(id_auth_user)
                db_cursor.execute(req);
                db_connect.commit()
                resp = Response('submit notepad is complete')
                return resp
            except:
                resp = Response('failed')
                return resp


if __name__ == '__main__':
    app.run()