import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, session
# Flask: 웹앱 생성 
# render_template: HTML 보여주기 
# request: 사용자가 보낸 데이터 받기
# redirect: 다른 주소로 이동
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

app = Flask(__name__)
app.secret_key = 'ask'

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

DB_NAME = 'account.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # DB결과를 딕셔너리처럼 사용할 수 있게 한다
    
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,  
                amount INTEGER NOT NULL,  
                memo TEXT,                
                created_at TEXT NOT NULL
        )
''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
        )
''')
    conn.commit()
    conn.close()


def save_expense(user_id, category, amount, memo):  # 지출 1건을 db에 저장하는 함수
    conn = get_db()
    conn.execute(
        'INSERT INTO expenses (user_id, category, amount, memo, created_at) VALUES (?, ?,?,?,?)',
        (user_id, category, amount, memo, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    conn.commit()
    conn.close()

def analyze_expense(user_text): # 사용자가 입력한 문장을 AI가 분석하는 함수
    tools = [
        {
            'type':'function', # 함수 호출 도구라는 뜻
            'function':{   # 함수 정보 시작
                'name': 'save_expense', # 호출할 함수
                'description':'사용자의 지출 문장에서 카테고리, 금액, 메모를 추출한다',
                'parameters':{ # 함수에 들어갈 인자 규칙을 정함
                    'type':'object', # 객체 형태의 결과를 만들어라
                    'properties':{ # 객체 안에 들어갈 값들을 정의
                        'category':{ 
                            'type':'string',
                            'description':'지출 카테고리. 예: 식비, 교통비, 쇼핑, 카페, 기타'
                        },
                        'amount':{ 
                            'type':'integer',
                            'description':'지출 금액. 원 단위 숫자'
                        },
                        'memo':{ 
                            'type':'string',
                            'description':'지출 내용 요약'
                        }
                    },
                    'required':['category','amount','memo'] # 세 값은 반드시 있어야 함

                }
            }
        } # 도구 하나 끝
    ] # tools 목록 종료

    response = client.chat.completions.create(
        model = 'gpt-4o-mini', 
        messages = [
            {
                # AI에게 역할을 정해준다
                'role':'system',
                'content':'너는 가계부 입력을 분석하는 AI야. 사용자의 문장에서 지출 정보를 추출해'
            },
            {
                'role':'user',
                'content':user_text
            }
        ],
        tools=tools,
        tool_choice={'type':'function','function':{'name':'save_expense'}} 
        # AI에게 반드시 save_expense 형태로 만들라고 강제한다
    )

    tool_call = response.choices[0].message.tool_calls[0]  # AI가 만든 함수 호출 정보를 꺼냄
    args = json.loads(tool_call.function.arguments)  # JSON 문자열을 python 딕셔너리로 바꾼다

    args['category']
    args['amount']
    args['memo']

    return args
        


@app.route('/delete/<int:id>')
def delete(id):

    conn = get_db()

    conn.execute(
        'DELETE FROM expenses WHERE id = ?',
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
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
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db()

        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()

        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/')
        
        return '로그인 실패'
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/', methods=['GET','POST'])
def index():
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST': # 사용자가 입력창에 내용을 쓰고 저장 버튼을 눌렀는지 확인한다.
        user_text = request.form.get('expense_text')

        if user_text: # 입력값이 비어있지 않으면 실행한다
            data = analyze_expense(user_text) # AI에게 문장을 분석시킨다.
            save_expense(
                session['user_id'],
                data['category'],
                data['amount'],
                data['memo']
            )
        return redirect('/')

    conn = get_db()
    expenses = conn.execute(
        'SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC',
        (session['user_id'],)
    ).fetchall()

    total = conn.execute(
        'SELECT SUM(amount) AS total FROM expenses WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()['total']

    conn.close()

    if total is None:
        total = 0
    
    return render_template('index.html', expenses=expenses, total=total)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)


