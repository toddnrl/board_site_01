from flask import Flask, request, render_template, redirect

app = Flask(__name__)


memos = []

@app.route('/')
def index():
    return render_template('index.html', memos=memos)

@app.route('/create', methods=['POST'])
def create():
    title = request.form.get('title')
    message = request.form.get('message')

    memos.append({
        'id': len(memos) +1,
        'title': title,
        'message' : message
        
    })

    return redirect('/')

@app.route('/delete/<int:memo_id>')
def delete(memo_id):
    global memos
    memos = [memo for memo in memos if memo['id'] != memo_id]
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)




