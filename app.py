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

# configuration
DATABASE = '/tmp/okbsqlite.db'
DEBUG = True
SECRET_KEY = 'olM2rtRbg0kzDmdCheQawgDeT0'

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(DATABASE=os.path.join(app.root_path, 'okbsqlite.db')))


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
def showPost(alias):
    title, post = dbase.getPost(alias)
    if not title:
        abort(404)

    return render_template('post.html', menu=dbase.getMenu(), title=title, post=post)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'userLogged' in session:
        return redirect(url_for('profile', username=session['userLogged']))
    elif request.method == 'POST' and request.form['login-username'] == "admin" and request.form['login-password'] == "Qq1234":
        session['userLogged'] = request.form['login-username']
        return redirect(url_for('profile', username=session['userLogged']))

    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        if len(request.form['name']) > 4 and len(request.form['email']) > 4 and len(request.form['password']) > 4 and request.form['password'] == request.form['password2']:
            hash = generate_password_hash(request.form['password'])
            res = dbase.addUser(request.form['name'], request.form['email'], hash)
            if res:
                flash('Вы успешно зарегистрированы!', category='success')
                return redirect(url_for('login'))
            else:
                flash('Ошибка при регистрации - невозожно добавить в БД', category='error')
        else:
            flash('Неверно заполнены поля', category='error')

    return render_template('register.html')


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


@app.route('/profile/<int:username>')
@app.route('/profile/<path:username>')
def profile(username):
    if 'userLogged' not in session or session['userLogged'] != username:
        abort(401)

    return f"Привет, пользователь: {username}"


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
