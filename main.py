from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import Column, Integer, String, Boolean

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import uuid


from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from Data.database import get_db, engine
from Data import models, crud, schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/truth_dares/", response_model=schemas.TruthDares)
def create_truth_dare(
    truth_dare: schemas.TruthDaresCreate, db: Session = Depends(get_db)
):
    return crud.create_truth_dare(db=db, truth_dare=truth_dare)


@app.get("/truth_dares/", response_model=list[schemas.TruthDares])
def read_truth_dares(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    truth_dares = crud.get_truth_dares(db, skip=skip, limit=limit)
    return truth_dares


@app.get("/truth_dares/{truth_dare_id}", response_model=schemas.TruthDares)
def read_truth_dare(truth_dare_id: int, db: Session = Depends(get_db)):
    db_truth_dare = crud.get_truth_dare(db, truth_dare_id=truth_dare_id)
    if db_truth_dare is None:
        raise HTTPException(status_code=404, detail="TruthDare not found")
    return db_truth_dare


@app.put("/truth_dares/{truth_dare_id}", response_model=schemas.TruthDares)
def update_truth_dare(
    truth_dare_id: int,
    truth_dare: schemas.TruthDaresUpdate,
    db: Session = Depends(get_db),
):
    db_truth_dare = crud.update_truth_dare(
        db=db, truth_dare_id=truth_dare_id, truth_dare=truth_dare
    )
    if db_truth_dare is None:
        raise HTTPException(status_code=404, detail="TruthDare not found")
    return db_truth_dare


@app.delete("/truth_dares/{truth_dare_id}", response_model=schemas.TruthDares)
def delete_truth_dare(truth_dare_id: int, db: Session = Depends(get_db)):
    db_truth_dare = crud.delete_truth_dare(db=db, truth_dare_id=truth_dare_id)
    if db_truth_dare is None:
        raise HTTPException(status_code=404, detail="TruthDare not found")
    return db_truth_dare


app = FastAPI()

# Разрешить CORS для всех источников (для разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        return connection_id

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

    async def send_data(self, data: dict):
        for connection in self.active_connections.values():
            await connection.send_json(data)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    connection_id = await manager.connect(websocket)
    try:
        # Отправляем URL нового соединения при первом подключении
        await websocket.send_json({"new_connection_url": f"/ws/{connection_id}"})
        while True:
            data = await websocket.receive_json()
            print(f"Received data: {data}")
            await manager.send_data(data)
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        manager.disconnect(connection_id)


@app.websocket("/ws/{connection_id}")
async def websocket_with_id(websocket: WebSocket, connection_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received data on {connection_id}: {data}")
            await manager.send_data(data)
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        manager.disconnect(connection_id)


# строка подключения
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# создаем движок SqlAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)


# создаем базовый класс для моделей
class Base(DeclarativeBase):
    pass


# создаем модель, объекты которой будут храниться в бд
class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True)
    body = Column(String)
    isBoy = Column(Boolean)
    timer = Column(Integer)


# создаем таблицы
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autoflush=False, bind=engine)
db = SessionLocal()


db.commit()


# приложение, которое ничего не делает
