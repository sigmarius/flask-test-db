from flask import Blueprint, request, redirect, url_for, flash, render_template, session

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
        {'url': '.logout', 'title': 'Выйти'}]


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
