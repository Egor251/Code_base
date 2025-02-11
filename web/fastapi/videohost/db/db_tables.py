"""
Файл с моделями таблиц в базе данных
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

Base = declarative_base()

class VideoDB(Base):
    """
    Модель таблицы Видео в базе данных
    """
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)
    duration = Column(Integer)  # В секундах
    thumbnail_path = Column(String)