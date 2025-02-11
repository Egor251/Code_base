from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic_models import VideoResponse
import os
import uuid
from db.db_main import get_db
from db.db_tables import VideoDB

# Настройка приложения
app = FastAPI(title="Video Hosting Service")

# Создаем директорию для видео
os.makedirs("videos", exist_ok=True)


# Эндпоинты
@app.post("/upload", response_model=VideoResponse)
async def upload_video(
        title: str = Form(...),
        description: str = Form(...),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    Загрузка видео на сервер

    :param title: Название видео
    :param description: Описание видео
    :param file: Файл видео
    :param db: Сессия базы данных
    """

    # Проверка формата файла
    allowed_formats = ["mp4", "avi", "mov"]
    file_format = file.filename.split(".")[-1].lower()
    if file_format not in allowed_formats:
        raise HTTPException(400, detail="Unsupported file format")

    # Генерация уникального имени файла
    file_uuid = str(uuid.uuid4())
    file_name = f"{file_uuid}.{file_format}"
    file_path = os.path.join("videos", file_name)

    # Сохранение файла
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
            #TODO вынести в minio
    except Exception as e:
        raise HTTPException(500, detail=str(e))

    # Сохранение метаданных в БД
    video_db = VideoDB(
        title=title,
        description=description,
        file_path=file_path,
        file_size=len(contents),
        duration=0,  # Для реального проекта: добавить обработку видео
        thumbnail_path=""  # Можно генерировать превью
    )

    db.add(video_db)
    db.commit()
    db.refresh(video_db)

    return video_db


@app.get("/videos", response_model=list[VideoResponse])
def list_videos(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Возвращает список всех видео

    :param skip: Количество видео, которые нужно пропустить
    :param limit: Количество видео, которые нужно вернуть
    :param db: Сессия базы данных
    """
    return db.query(VideoDB).offset(skip).limit(limit).all()


@app.get("/videos/{video_id}", response_model=VideoResponse)
def get_video_info(video_id: int, db: Session = Depends(get_db)):
    """
    Возвращает информацию о видео

    :param video_id: Идентификатор видео
    :param db: Сессия базы данных
    """
    video = db.query(VideoDB).filter(VideoDB.id == video_id).first()
    if not video:
        raise HTTPException(404, detail="Video not found")
    return video


@app.get("/stream/{video_id}")
async def stream_video(video_id: int, db: Session = Depends(get_db)):
    """
    Возвращает поток видео

    :param video_id: Идентификатор видео
    :param db: Сессия базы данных
    """
    video = db.query(VideoDB).filter(VideoDB.id == video_id).first()
    if not video or not os.path.exists(video.file_path):
        raise HTTPException(404, detail="Video not found")

    return FileResponse(
        video.file_path,
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)