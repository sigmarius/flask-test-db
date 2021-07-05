# вспомогательный класс для авторизации пользователей через Flask-Login - состояние текущего пользователя
class UserLogin():
    def fromDB(self, user_id, db):
       self.__user = db.getUser(user_id)
       return self

    def create(self, user):
        self.__user = user
        return self

    def is_authenticated(self):
        # проверка авторизации пользователя => True если авторизован
        return True

    def is_active(self):
        # проверка активности пользователя => True для активного
        return True

    def is_anonymous(self):
        # определение неавторизованных пользователей => True для неавторизованных, False для авторизованных
        return False

    def get_id(self):
        # уникальный идентификатор пользователя в БД в виде строки!
        return str(self.__user['id'])