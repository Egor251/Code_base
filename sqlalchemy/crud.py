import sqlalchemy
import create_database

with create_database.Session(autoflush=False, bind=create_database.engine) as session:

    # query - запрос к базе данных
    # filter - where
    # first - только первую запись
    test = session.query(create_database.Msg).filter(create_database.Msg.user_id == 'user_id').first()  # Получаем первыу запись подходящую под условие в фильтре. test становится экземпляром класса database.Msg с сответствующими атрибутами

    test.status = 'finished'
    test.status_updated_at = '1'
    session.commit()  # Сохраняем изменения в базе данных. Обязательно!


def insert(data):  # Функция для обновления базы
        with create_database.Session(autoflush=False, bind=create_database.engine) as session:
            request = sqlalchemy.insert(create_database.Msg).values(data)  # Более низкоуровневое заполнение БД. data - словарь с данными, где ключ - название столбца в таблице
            session.execute(request)
            session.commit()

def low_interaction():
    n = 10
    output_list = []  # Список, в который будут записываться данные из базы данных
    with create_database.Session(autoflush=False, bind=create_database.engine) as session:
        stmt = sqlalchemy.select(create_database.Msg).limit(n).order_by(sqlalchemy.desc(create_database.Msg.id))  # Здесь sqlalchemy сама формирует sql запрос. функция print() его выведет
        data = session.execute(stmt) # Выполняем запрос (можно и просто строку запроса написать) и получаем массив подходящих под условие объектов

        # так как в data лежат объекты класса database.Msg, а не данные, то нужно их преобразовать в список
        for item in data:
            output_list.append(item[0].get_list())
