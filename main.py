# =====================================================
# DIGITURNO SAAS PRO (RENDER READY - FIXED)
# =====================================================

"""
🔥 ESTA VERSIÓN YA ESTÁ CORREGIDA PARA QUE FUNCIONE:
- Local
- Render
- Evita errores comunes (JSON, DB, etc)

ARCHIVOS NECESARIOS:
1) main.py
2) requirements.txt
"""

# ================= IMPORTS =================
from fastapi import FastAPI
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

# ================= HELPERS =================
def db_to_dict(turno):
    return {
        "id": turno.id,
        "numero": turno.numero,
        "estado": turno.estado
    }

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
    db.refresh(t)

    return db_to_dict(t)


@app.post("/siguiente")
def siguiente():
    db = SessionLocal()

    turno = db.query(Turno).filter_by(estado="esperando").first()

    if not turno:
        return {"msg": "sin turnos"}

    turno.estado = "llamado"
    db.commit()

    return db_to_dict(turno)


@app.get("/turnos")
def listar_turnos():
    db = SessionLocal()
    turnos = db.query(Turno).all()
    return [db_to_dict(t) for t in turnos]

# =====================================================
# requirements.txt (CREAR ESTE ARCHIVO)
# =====================================================

"""
fastapi
uvicorn
sqlalchemy
"""

# =====================================================
# EJECUCIÓN LOCAL (OPCIONAL)
# =====================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
