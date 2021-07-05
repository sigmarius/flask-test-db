from flask import Flask, render_template, request, redirect, flash, session, url_for, abort, g, make_response

app = Flask(__name__)

menu = [{"title": "Главная", "url": "/"},
        {"title": "Войти", "url": "/login"}]


@app.route('/')
def index():
    return "<h1>Working with cookies</h1>"


@app.route('/login')
def login():
    log = ""
    if request.cookies.get('logged'):
        log = request.cookies.get('logged')

    res = make_response(f"<h1>Форма авторизации</h1><p>logged: {log}</p>")
    # сохраняем куки в браузере клиента 30 дней => max_age = 30days * 24hours * 3600sec
    res.set_cookie('logged', 'yes', 30*24*3600)

    return res


@app.route("/logout")
def logout():
    res = make_response("<p>Вы больше не авторизованы!</p>")
    # удаление куков => max_age = 0
    res.set_cookie('logged', "", 0)
    return res


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
