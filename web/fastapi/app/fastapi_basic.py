from typing import List
import asyncio
from fastapi import FastAPI
import uvicorn
from data_structure import *  # Фильтрация входящих данных Pydantic
import platform


if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # На всякий случай чтобы избежать проблем в среде windows

port = 8080


app = FastAPI()  # Объявляем приложение


@app.get("/")
def read_root():
    return {"Use /create or /list "}


@app.post("/post")  # Вот так просто описываем post запросы
async def create(query: List[PostCom]):

    for item in query:  # Парсим POST запрос
        user_id = item.user_id
        target_id = item.target_id
        print('user_id: ', user_id)
        print('target_id: ', target_id)

        return {"status": 200, "response": 'accepted'}  # Возвращаем ответ 200, можно через if возвращать другие статусы


@app.get("/list")  # Вот так просто описываем get запросы
async def list_com(user_id, skip: int, limit: int):
    print(user_id, skip, limit)
    return {"status": 200}


if __name__ == '__main__':
    uvicorn.run("main:app", host='0.0.0.0', port=port, reload=False, workers=3)  # Запуск сервера