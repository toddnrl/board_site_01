from flask import Flask, request, render_template, redirect, session, flash, url_for
from datetime import timedelta

import sqlite3

app = Flask(__name__)



app.secret_key = 'leesang'
app.permanent_session_lifetime = timedelta(minutes=5)


def get_db():
    conn = sqlite3.connect('memo.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS memos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL
            
        )
    ''')

    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE if NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')




    conn.commit()
    conn.close()



@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db()

    memos = conn.execute('SELECT * FROM memos ORDER BY id DESC').fetchall()
    conn.close()


    return render_template('index.html', memos=memos)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET' :
        return render_template('login.html')
    
    username = request.form.get('username')
    password = request.form.get('password')

    conn = get_db()

    user = conn.execute(
        'SELECT * FROM users WHERE username = ?',
        (username,)
    ).fetchone()

    conn.close()

    if user and user['password'] == password:
        session['user_id'] = user['id']
        session['username'] = user['username']
        return redirect('/')
    
    return '로그인 실패'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    username = request.form.get('username')
    password = request.form.get('password')

    conn = get_db()

    conn.execute(
        'INSERT INTO users (username, password) VALUES (?, ?)',
        (username, password)
    )

    conn.commit()
    conn.close()

    return redirect('/login')

@app.route('/edit/<int:memo_id>', methods=['POST'])
def update(memo_id):
    title = request.form.get('title')
    message = request.form.get('message')

    conn = get_db()

    conn.execute(
        'UPDATE memos SET title = ?, message = ? WHERE id = ?',
        (title, message, memo_id)

    )

    conn.commit()
    conn.close()
    
    return redirect('/')


@app.route('/edit/<int:memo_id>')
def edit(memo_id):
    conn = get_db()

    memo = conn.execute(
        'SELECT * FROM memos WHERE id = ?',
        (memo_id,)
        
    ).fetchone()

    conn.close()

    return render_template('edit.html', memo=memo)


@app.route('/create', methods=['POST'])
def create():
    if 'user_id' not in session:
        return redirect('/login')
    

    title = request.form.get('title')
    message = request.form.get('message')

    conn = get_db()

    conn.execute(
        'INSERT INTO memos (title, message) VALUES (?, ?)',
        (title, message)
    )
    conn.commit()
    conn.close()


    return redirect('/')

@app.route('/delete/<int:memo_id>')
def delete(memo_id):
    if 'user_id' not in session:
        return redirect('/login')
    conn = get_db()

    conn.execute(
        'DELETE FROM memos WHERE id = ?',
        (memo_id,)
    )

    conn.commit()
    conn.close()

    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)




