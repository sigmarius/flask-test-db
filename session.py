import datetime

from flask import Flask, render_template, session

app = Flask(__name__)
# генерация ключа => Python Console => import os => os.urandom(20).hex()
app.config['SECRET_KEY'] = '4ed56a824c40ff612ead3f5d224505b878ad8f25'
# изменение времени хранения сессии
app.permanent_session_lifetime = datetime.timedelta(days=10)


@app.route('/')
def index():
    # количество посещений главной страницы
    if 'visits' in session:
        session['visits'] = session.get('visits') + 1  # обновление данных сессии
    else:
        session['visits'] = 1  # запись данных в сессию
    return f"<h1>Working with sessions</h1><p>Число просмотров: {session['visits']}</p>"


data = [1, 2, 3, 4]


@app.route('/session')
def session_data():
    # по умолчанию время жизни сессии 31 день
    session.permanent = False  # сессия не сохраняется
    # session.permanent = True  # сессия сохраняется даже после закрытия браузера
    if 'data' not in session:
        session['data'] = data
    else:
        session['data'][1] += 1
        # в случае с изменяемыми типами данных
        session.modified = True

    return f"<p>session['data']: {session['data']}</p>"


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
