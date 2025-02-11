from fastapi import FastAPI, HTTPException, Depends, status, WebSocket
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime
import uuid
import os
import subprocess

# Настройка приложения
app = FastAPI(title="Live Streaming Service")

# Конфигурация базы данных
DATABASE_URL = "sqlite:///./streams.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Директории для HLS
HLS_OUTPUT_DIR = "hls"
os.makedirs(HLS_OUTPUT_DIR, exist_ok=True)


# Модель базы данных для стримов
class StreamDB(Base):
    __tablename__ = "streams"

    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    is_live = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    stream_key = Column(String, unique=True)
    hls_playlist = Column(String)


Base.metadata.create_all(bind=engine)


# Pydantic схемы
class StreamCreate(BaseModel):
    title: str
    description: str


class StreamResponse(StreamCreate):
    id: str
    is_live: bool
    created_at: datetime
    stream_key: str
    hls_playlist: str


# Зависимости
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Эндпоинты
@app.post("/streams/create", response_model=StreamResponse)
def create_stream(stream: StreamCreate, db: Session = Depends(get_db)):
    stream_id = str(uuid.uuid4())
    stream_key = str(uuid.uuid4().hex)
    hls_playlist = f"{stream_id}/playlist.m3u8"

    # Создаем директорию для HLS сегментов
    os.makedirs(os.path.join(HLS_OUTPUT_DIR, stream_id), exist_ok=True)

    new_stream = StreamDB(
        id=stream_id,
        **stream.dict(),
        stream_key=stream_key,
        hls_playlist=hls_playlist
    )

    db.add(new_stream)
    db.commit()
    db.refresh(new_stream)
    return new_stream


@app.get("/streams/live", response_model=list[StreamResponse])
def get_live_streams(db: Session = Depends(get_db)):
    return db.query(StreamDB).filter(StreamDB.is_live == True).all()


@app.post("/streams/start/{stream_id}")
def start_stream(stream_id: str, db: Session = Depends(get_db)):
    stream = db.query(StreamDB).filter(StreamDB.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    # Запуск FFmpeg для трансляции в HLS
    input_url = f"rtmp://localhost/live/{stream.stream_key}"
    output_path = os.path.join(HLS_OUTPUT_DIR, stream.id, "playlist.m3u8")

    ffmpeg_cmd = [
        "ffmpeg",
        "-i", input_url,
        "-c:v", "libx264",
        "-hls_time", "4",
        "-hls_playlist_type", "event",
        "-hls_segment_filename", os.path.join(HLS_OUTPUT_DIR, stream.id, "segment_%03d.ts"),
        output_path
    ]

    try:
        process = subprocess.Popen(ffmpeg_cmd)
        stream.is_live = True
        db.commit()
        return {"message": "Stream started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stream/{stream_id}/hls/{segment}")
async def get_hls_segment(stream_id: str, segment: str):
    segment_path = os.path.join(HLS_OUTPUT_DIR, stream_id, segment)
    if not os.path.exists(segment_path):
        raise HTTPException(status_code=404, detail="Segment not found")
    return FileResponse(segment_path)


# Вебсокет для чата
@app.websocket("/ws/{stream_id}/chat")
async def websocket_chat(websocket: WebSocket, stream_id: str):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # Здесь можно добавить логику обработки сообщений
        await websocket.send_text(f"Message received: {data}")


# HTML пример плеера
@app.get("/player/{stream_id}", response_class=HTMLResponse)
async def video_player(stream_id: str):
    return f"""
    <html>
        <body>
            <video id="video" controls width="640" height="480">
                <source src="/stream/{stream_id}/playlist.m3u8" type="application/x-mpegURL">
            </video>
            <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
            <script>
                var video = document.getElementById('video');
                if(Hls.isSupported()) {{
                    var hls = new Hls();
                    hls.loadSource('/stream/{stream_id}/playlist.m3u8');
                    hls.attachMedia(video);
                    hls.on(Hls.Events.MANIFEST_PARSED, function() {{
                        video.play();
                    }});
                }}
            </script>
        </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)