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