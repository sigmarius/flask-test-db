import sqlite3
import os
from flask import Flask, render_template, request, redirect, flash, session, url_for, abort, g, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from cloudipsp import Api, Checkout
from FDataBase import FDataBase
# PBKDF2 (Password-Based Key Derivation Function) from Werkzeug => шифрование паролей
# generate_password_hash() from Werkzeug.security => кодирует строку по протоколу PBKDF2
# check_password_hash() from Werkzeug.security => проверяет данные на соответствие хеша
from werkzeug.security import generate_password_hash, check_password_hash
# для авторизации пользователей => pip install flask-login
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from UserLogin import UserLogin
# WTForms => Для работы с формами => pip install flask_wtf, pip install email_validator
from forms import LoginForm, RegisterForm

# configuration
DATABASE = '/tmp/okbsqlite.db'
DEBUG = True
SECRET_KEY = 'olM2rtRbg0kzDmdCheQawgDeT0'
# max объем в байтах файла, загружаемого на сервер
MAX_CONTENT_LENGTH = 1024 * 1024  # 1Mb

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'okbsqlite.db')))


# авторизация и связь с приложением
login_manager = LoginManager(app)
# если неавторизованный пользователь посещает закрытую страницу => он перенаправляется на страницу авторизации
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "success"


# формирует экземпляр класса при каждом запросе
@login_manager.user_loader
def load_user(user_id):
    print('load_user')
    return UserLogin().fromDB(user_id, dbase)


def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    """ Вспомогательная функция для создания таблиц БД """
    db_lite = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db_lite.cursor().executescript(f.read())
    db_lite.commit()
    db_lite.close()


def get_db():
    """ Соединение с БД, если оно еще не установлено """
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    print('True connection!')
    return g.link_db


# глобальная переменная для связи с БД
dbase = None


@app.before_request
def before_request():
    """ Установление соединения с БД перед выполнением запроса """
    global dbase
    db_lite = get_db()
    dbase = FDataBase(db_lite)


@app.teardown_appcontext
def close_db(error):
    """ Закрываем соединение с БД, если оно было установлено """
    if hasattr(g, 'link_db'):
        g.link_db.close()


@app.route('/database')
@login_required  # доступ только авторизованным пользователям
def database():
    content = render_template('database.html', menu=dbase.getMenu(), posts=dbase.getPostsAnonce())

    res = make_response(content)
    # res.headers['Content-Type'] = 'text/plain'
    # res.headers['Server'] = 'flasksite'
    return res


@app.route('/transfer')
def transfer():
    return redirect(url_for('database'), 301)


@app.route('/add_post', methods=["POST", "GET"])
def addPost():
    if request.method == "POST":
        if len(request.form['name']) > 4 and len(request.form['post']) > 5:
            res = dbase.addPost(request.form['name'], request.form['post'], request.form['url'])
            print('True story')
            if not res:
                flash('if not res - Ошибка добавления статьи', category='error')
            else:
                flash('Статья добавлена успешно', category='success')
        else:
            flash('Some problem with inputs - Ошибка добавления статьи', category='error')

    return render_template('add_post.html', menu=dbase.getMenu(), title="Добавление статьи")


@app.route("/post/<alias>")
@login_required  # доступ только авторизованным пользователям
def showPost(alias):
    title, post = dbase.getPost(alias)
    if not title:
        abort(404)

    return render_template('post.html', menu=dbase.getMenu(), title=title, post=post)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    form = LoginForm()
    if form.validate_on_submit():
        user = dbase.getUserByEmail(form.email.data)
        if user and check_password_hash(user['password'], form.password.data):
            userlogin = UserLogin().create(user)
            # запомнить меня в форме
            rm = form.remember.data
            # авторизуем пользователя
            login_user(userlogin, remember=rm)
            # переход на страницу, с которой изначально осуществлялся запрос неавторизованного пользователя
            return redirect(request.args.get("next") or url_for('profile'))

        flash('Неверная пара логин/пароль', category='error')

    return render_template('login.html', form=form)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hash = generate_password_hash(form.password.data)
        res = dbase.addUser(form.name.data, form.email.data, hash)
        if res:
            flash('Вы успешно зарегистрированы!', category='success')
            return redirect(url_for('login'))
        else:
            flash('Ошибка при регистрации - невозожно добавить в БД', category='error')

    return render_template('register.html', form=form)


# рабочий код, закомментирован чтобы посмотреть на работу SQLite
# app.config['SECRET_KEY'] = 'olM2rtRbg0kzDmdCheQawgDeT0'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///okb.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    isActive = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'Запись: {self.title} по цене {self.price}'


@app.route('/')
def index():
    items = Item.query.order_by(Item.price).all()
    return render_template('index.html', data=items)


@app.route('/about', methods=['POST', 'GET'])
def about():
    if request.method == 'POST':
        if len(request.form['about-user']) > 2:
            flash('Спасибо за ваше сообщение! Мы свяжемся с вами в самое ближайшее время!', category='success')
        else:
            flash('Что-то пошло не так :(', category='error')

    return render_template('about.html')


@app.route('/profile')
@login_required
def profile():
    return render_template("profile.html")


@app.route('/avatar')
@login_required
def avatar():
    img = current_user.getAvatar(app)
    if not img:
        return ""

    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h


@app.route('/upload', methods=["POST", "GET"])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
                res = dbase.updateUserAvatar(img, current_user.get_id())
                if not res:
                    flash("Ошибка обновления аватара", "error")
                flash("Аватар обновлен", "success")
            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "error")
        else:
            flash("Ошибка обновления аватара", "error")

    return redirect(url_for('profile'))


@app.route('/logout')
@login_required
def logout():
    # функция из модуля Flask-Login
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route('/buy/<int:id>')
def item_buy(id):
    item = Item.query.get(id)

    api = Api(merchant_id=1396424,
              secret_key='test')
    checkout = Checkout(api=api)
    data = {
        "currency": "RUB",
        "amount": str(item.price) + "00"
    }
    url = checkout.url(data).get('checkout_url')
    return redirect(url)


@app.route('/create', methods=['POST', 'GET'])
def create():
    if request.method == "POST":
        title = request.form['title']
        price = request.form['price']

        item = Item(title=title, price=price)

        try:
            db.session.add(item)
            db.session.commit()
            return redirect('/')
        except:
            return "Получилась ошибка :("
    else:
        return render_template('create.html')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
