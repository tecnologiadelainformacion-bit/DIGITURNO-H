# =====================================================
# DIGITURNO SAAS PRO (RENDER READY)
# FastAPI + SQLite (listo para deploy en Render)
# =====================================================

"""
🚀 ESTE ARCHIVO YA ESTÁ LISTO PARA RENDER

NECESITAS 2 ARCHIVOS EN TU REPO:

1) main.py  (este archivo)
2) requirements.txt  (abajo te lo dejo)

-----------------------------
RENDER CONFIG:

Build Command:
pip install -r requirements.txt

Start Command:
uvicorn main:app --host 0.0.0.0 --port $PORT
-----------------------------

PROBAR:
https://tu-app.onrender.com/docs
"""

# ================= IMPORTS =================
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# ================= CONFIG =================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./digiturno.db")

# ================= DB =================
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ================= MODELO =================
class Turno(Base):
    __tablename__ = "turnos"
    id = Column(Integer, primary_key=True)
    numero = Column(String)
    estado = Column(String)

Base.metadata.create_all(engine)

# ================= APP =================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ================= RUTA BASE =================
@app.get("/")
def home():
    return {"msg": "Digiturno API funcionando"}

# ================= ENDPOINTS =================
@app.post("/turno")
def crear_turno():
    db = SessionLocal()

    count = db.query(Turno).count()
    numero = "A" + str(count + 1).zfill(3)

    t = Turno(numero=numero, estado="esperando")
    db.add(t)
    db.commit()

    return {"numero": numero}


@app.post("/siguiente")
def siguiente():
    db = SessionLocal()

    turno = db.query(Turno).filter_by(estado="esperando").first()

    if not turno:
        return {"msg": "sin turnos"}

    turno.estado = "llamado"
    db.commit()

    return {"numero": turno.numero}


@app.get("/turnos")
def listar_turnos():
    db = SessionLocal()
    return db.query(Turno).all()

# =====================================================
# requirements.txt (CREAR ESTE ARCHIVO)
# =====================================================

"""
fastapi
uvicorn
sqlalchemy
"""

# =====================================================
# TESTS
# =====================================================

def test_crear_turno():
    db = SessionLocal()
    t = Turno(numero="A001", estado="esperando")
    db.add(t)
    db.commit()
    assert t.id is not None


def test_listar():
    db = SessionLocal()
    data = db.query(Turno).all()
    assert isinstance(data, list)

# =====================================================
# COMANDOS
# =====================================================

"""
LOCAL:
uvicorn main:app --reload

RENDER:
uvicorn main:app --host 0.0.0.0 --port $PORT
"""

