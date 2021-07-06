from flask import url_for
from flask_login import UserMixin
# UserMixin по дефолту содержит => is_authenticated, is_active, is_anonymous

# вспомогательный класс для авторизации пользователей через Flask-Login - состояние текущего пользователя
class UserLogin(UserMixin):
    def fromDB(self, user_id, db):
       self.__user = db.getUser(user_id)
       return self

    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        # уникальный идентификатор пользователя в БД в виде строки!
        return str(self.__user['id'])

    def getName(self):
        return self.__user['name'] if self.__user else "Unknown User :("

    def getEmail(self):
        return self.__user['email'] if self.__user else "Unknown email :("

    def getAvatar(self, app):
        img = None
        if not self.__user['avatar']:
            try:
                with app.open_resource(app.root_path + url_for('static', filename='images/default.png'), "rb") as f:
                    img = f.read()
            except FileNotFoundError as e:
                print("Не найден аватар по умолчанию: " + str(e))
        else:
            img = self.__user['avatar']

        return img

    def verifyExt(self, filename):
        ext = filename.rsplit('.', 1)[1]
        if ext == 'png' or ext == 'PNG':
            return True
        return False

