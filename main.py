from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.responses import FileResponse
import os
import json



# ================= CONFIG & DB =================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./digiturno.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Turno(Base):
    __tablename__ = "turnos"
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, unique=True)
    estado = Column(String, default="esperando")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# ================= GESTOR DE WEBSOCKETS =================
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # Envía el mensaje a todos los conectados
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# ================= APP =================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= ENDPOINTS =================

@app.get("/")
def home():
    return {"msg": "Digiturno Real-Time API"}

@app.post("/turno")
async def crear_turno(db: Session = Depends(get_db)):
    last_turno = db.query(Turno).order_by(Turno.id.desc()).first()
    next_id = (last_turno.id + 1) if last_turno else 1
    nuevo_numero = f"A{str(next_id).zfill(3)}"
    
    t = Turno(numero=nuevo_numero, estado="esperando")
    db.add(t)
    db.commit()
    
    # Notificar a las pantallas que hay un nuevo turno en cola (opcional)
    await manager.broadcast({"evento": "nuevo_turno", "numero": nuevo_numero})
    
    return {"numero": nuevo_numero}

@app.post("/siguiente")
async def llamar_siguiente(db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(Turno.estado == "esperando").order_by(Turno.id.asc()).first()

    if not turno:
        raise HTTPException(status_code=404, detail="No hay turnos")

    turno.estado = "llamado"
    db.commit()

    # 🔥 NOTIFICACIÓN REAL-TIME: La pantalla sonará y mostrará el número
    await manager.broadcast({
        "evento": "llamar_turno",
        "numero": turno.numero,
        "msg": f"Turno {turno.numero}, por favor pase a módulo."
    })

    return {"numero": turno.numero}

# ================= WEBSOCKET ENDPOINT =================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Mantiene la conexión viva
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
async def home():
    if os.path.exists("home.html"):
        return FileResponse("home.html")
    return {"error": "Archivo home.html no encontrado en el servidor"}

@app.get("/pantalla")
async def abrir_pantalla():
    return FileResponse("index.html")

@app.get("/operador")
async def abrir_panel():
    return FileResponse("control.html")
