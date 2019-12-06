from flask import Flask, render_template, request, Response, make_response, redirect
import psycopg2
import hashlib
import redis

from classes.db_connection import DB_connection

app = Flask(__name__)
redis_instance = redis.Redis(db=4)

@app.route('/')
def auth():
    if 'flask_adminka_authorized_user_id' in request.cookies:
        return redirect('/admin')

    return render_template('auth.html')


@app.route('/admin')
def admin():    
    if 'flask_adminka_authorized_user_id' not in request.cookies:
        return redirect('/', code=404)

    id_auth_user = request.cookies.get('flask_adminka_authorized_user_id')

    admin_forms_values = {
        'firstname': None,
        'lastname': None,
        'notepad': None,
    }

    firstname = redis_instance.get('firstname:' + id_auth_user)
    lastname = redis_instance.get('lastname:' + id_auth_user)
    notepad = redis_instance.get('notepad:' + id_auth_user)

    if firstname and lastname and notepad:
        admin_forms_values['firstname'] = firstname.decode("utf-8")
        admin_forms_values['lastname'] = lastname.decode("utf-8")
        admin_forms_values['notepad'] = notepad.decode("utf-8")      
        return render_template('admin.html', admin_forms_values=admin_forms_values)

    with DB_connection() as db_connect:
        db_cursor = db_connect.cursor()

        try:
            request_form = "select * from options where user_id='" + id_auth_user + "'"
            db_cursor.execute(request_form)
            record = db_cursor.fetchone()
            admin_forms_values['firstname'] = record[1] if record[1] else ''
            admin_forms_values['lastname'] = record[2] if record[2] else ''
            admin_forms_values['notepad'] = record[3] if record[3] else ''
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
    firstname = request.values.get('firstname')
    lastname = request.values.get('lastname')
    id_auth_user = request.cookies.get('flask_adminka_authorized_user_id')

    with redis_instance.pipeline() as pipe:
        pipe.multi()
        pipe.set('firstname:' + id_auth_user, firstname)
        pipe.set('lastname:' + id_auth_user, lastname)
        pipe.execute()
        redis_instance.bgsave()

    with DB_connection() as db_connect:
        db_cursor = db_connect.cursor()
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
        notepad = request.values.get('notepad')
        id_auth_user = request.cookies.get('flask_adminka_authorized_user_id')

        with redis_instance.pipeline() as pipe:
            pipe.multi()
            pipe.set('notepad:' + id_auth_user, notepad)
            pipe.execute()
            redis_instance.bgsave()

        db_cursor = db_connect.cursor()
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