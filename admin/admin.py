import sqlite3

from flask import Blueprint, request, redirect, url_for, flash, render_template, session, g

# 'admin' - имя блюпринта, исп. как суффикс ко всем именам методов данного модуля
admin = Blueprint('admin', __name__, template_folder='templates', static_folder='static')


def login_admin():
    session['admin_logged'] = 1
    print(session)


def isLogged():
    return True if session.get('admin_logged') else False


def logout_admin():
    session.pop('admin_logged', None)
    print('Admin logged out', session)


menu = [{'url': '.index', 'title': 'Панель'},
        {'url': '.list_articles', 'title': 'Список статей'},
        {'url': '.list_users', 'title': 'Список пользователей'},
        {'url': '.logout', 'title': 'Выйти'}]

# подключение к БД в BluePrint
db = None  # глобальная переменная, ссылается на БД
@admin.before_request
def before_request():
    """ Установление соединения с БД перед выполнением запроса """
    global db
    db = g.get('link_db')  # ссылка на существующее соединение с БД


@admin.teardown_request
def teardown_request(request):
    """ После выполнения запроса """
    global db
    db = None
    return request


# URL: domen/admin/
@admin.route('/')
def index():
    if not isLogged():
        return redirect(url_for('.login'))

    return render_template('admin/index.html', menu=menu, title="Админ-панель")


@admin.route('/login', methods=["POST", "GET"])
def login():
    if isLogged():
        return redirect(url_for('.index'))

    if request.method == "POST":
        if request.form['admin'] == "admin" and request.form['psw'] == "12345":
            login_admin()
            # .index (или admin.index) - берем index из текущего Blueprinta, а не глобального
            return redirect(url_for('.index'))
        else:
            flash("Неверная пара логин/пароль", "error")

    return render_template('admin/login.html', title='Админ-панель')


@admin.route('/logout', methods=["POST", "GET"])
def logout():
    if not isLogged():
        return redirect(url_for('.login'))

    logout_admin()
    print(session)

    return redirect(url_for('.login'))


@admin.route('list-articles')
def list_articles():
    if not isLogged():
        return redirect(url_for('.login'))

    list = []
    if db:
        try:
            cur = db.cursor()
            cur.execute(f"SELECT title, text, url FROM posts")
            list = cur.fetchall()
        except sqlite3.Error as e:
            print("Ошибка получения статей из БД " + str(e))

    return render_template('admin/list-articles.html', title='Список статей', menu=menu, list=list)


@admin.route('list-users')
def list_users():
    if not isLogged():
        return redirect(url_for('.login'))

    list = []
    if db:
        try:
            cur = db.cursor()
            cur.execute(f"SELECT name, email FROM users ORDER BY time DESC")
            list = cur.fetchall()
        except sqlite3.Error as e:
            print("Ошибка получения пользователей из БД " + str(e))

    return render_template('admin/list-users.html', title='Список пользователей', menu=menu, list=list)
