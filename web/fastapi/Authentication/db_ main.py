from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from db_models import *
# https://metanit.com/python/database/3.3.php

# строка подключения
sqlite_database = "sqlite:///main.db"  # sqlite
#postgres_database = "postgresql+psycopg2://admin:password@localhost/db1" # Postgres

# создаем движок SqlAlchemy
engine = create_engine(sqlite_database)
#engine = create_engine(postgres_database)

# создаем класс сессии
Session = sessionmaker(autoflush=False, bind=engine)
# создаем саму сессию базы данных
with Session(autoflush=False, bind=engine) as session:  # Нужна для удобства работы с базой данных
    pass
