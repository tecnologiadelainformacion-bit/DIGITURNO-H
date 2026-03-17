# =====================================================
# DIGITURNO SAAS PRO (DEPLOY READY)
# FastAPI + SQLite + WebSockets (Render/Railway/VPS)
# =====================================================

"""
INSTALACIÓN:
pip install fastapi uvicorn sqlalchemy passlib[bcrypt] python-jose

EJECUTAR LOCAL:
uvicorn main:app --reload

EJECUTAR EN PRODUCCIÓN (IMPORTANTE):
uvicorn main:app --host 0.0.0.0 --port ${PORT}

NOTAS DEPLOY:
- Usa la variable de entorno PORT (Render/Railway)
- Cambia API URL en los HTML por tu dominio
- SQLite funciona, pero para SaaS usa PostgreSQL luego
"""

# ================= IMPORTS =================
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime
import os

# ================= CONFIG =================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./digiturno.db")
SECRET = os.getenv("SECRET", "supersecret")

# ================= DB =================
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ================= MODELOS =================
class Empresa(Base):
    __tablename__ = "empresas"
    id = Column(Integer, primary_key=True)
    nombre = Column(String)

class Turno(Base):
    __tablename__ = "turnos"
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer)
    numero = Column(String)
    estado = Column(String)
    prioridad = Column(Integer)
    modulo = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# ================= APP =================
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"])

# ================= WEBSOCKET =================
clientes = []

async def broadcast(msg: str):
    vivos = []
    for c in clientes:
        try:
            await c.send_text(msg)
            vivos.append(c)
        except:
            pass
    clientes[:] = vivos

@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    clientes.append(ws)
    try:
        while True:
            await ws.receive_text()
    except:
        if ws in clientes:
            clientes.remove(ws)

# ================= ENDPOINTS =================
@app.post("/turno")
async def crear_turno(data: dict):
    db = SessionLocal()

    empresa_id = data.get("empresa_id", 1)
    prioridad = data.get("prioridad", 0)

    count = db.query(Turno).filter_by(empresa_id=empresa_id).count()
    numero = "A" + str(count + 1).zfill(3)

    turno = Turno(
        empresa_id=empresa_id,
        numero=numero,
        estado="esperando",
        prioridad=prioridad
    )
    db.add(turno)
    db.commit()

    await broadcast(f"nuevo:{numero}")

    return {"numero": numero}

@app.post("/siguiente")
async def siguiente(data: dict):
    db = SessionLocal()

    empresa_id = data.get("empresa_id", 1)
    modulo = data.get("modulo", "1")

    turno = db.query(Turno).filter_by(
        empresa_id=empresa_id,
        estado="esperando"
    ).order_by(Turno.prioridad.desc(), Turno.id.asc()).first()

    if not turno:
        return {"msg": "sin turnos"}

    turno.estado = "llamado"
    turno.modulo = modulo
    db.commit()

    await broadcast(f"llamado:{turno.numero}:{modulo}")

    return {"numero": turno.numero, "modulo": modulo}

@app.get("/turnos/{empresa_id}")
def lista(empresa_id: int):
    db = SessionLocal()
    return db.query(Turno).filter_by(empresa_id=empresa_id).all()

# =====================================================
# ================= FRONTEND PRO =======================
# =====================================================

# ⚠️ IMPORTANTE: Cambia esta URL por tu dominio cuando despliegues

# ================= cliente.html =================
"""
<!DOCTYPE html>
<html>
<body>
<h1>Sacar Turno</h1>
<button onclick="crear()">Nuevo Turno</button>
<h2 id="t"></h2>
<script>
const API="https://TU-DOMINIO.com";
async function crear(){
 let r=await fetch(API+"/turno",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({})});
 let d=await r.json();
 document.getElementById("t").innerText=d.numero;
}
</script>
</body>
</html>
"""

# ================= admin.html =================
"""
<!DOCTYPE html>
<html>
<body>
<h1>Administrador</h1>
<button onclick="sig()">Llamar siguiente</button>
<h2 id="t"></h2>
<script>
const API="https://TU-DOMINIO.com";
async function sig(){
 let r=await fetch(API+"/siguiente",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({modulo:"1"})});
 let d=await r.json();
 document.getElementById("t").innerText=d.numero+" -> M"+d.modulo;
}
</script>
</body>
</html>
"""

# ================= display.html =================
"""
<!DOCTYPE html>
<html>
<body style="font-size:50px;text-align:center">
<h1>Pantalla</h1>
<h2 id="turno"></h2>
<script>
let ws=new WebSocket("wss://TU-DOMINIO.com/ws");
ws.onmessage=(e)=>{
 let msg=e.data.split(":");
 if(msg[0]=="llamado"){
   document.getElementById("turno").innerText=msg[1]+" -> M"+msg[2];
 }
};
</script>
</body>
</html>
"""

# ================= TESTS =================
def test_turno_creacion():
    db = SessionLocal()
    t = Turno(empresa_id=1, numero="A001", estado="esperando", prioridad=0)
    db.add(t)
    db.commit()
    assert t.id is not None


def test_siguiente_vacio():
    db = SessionLocal()
    res = db.query(Turno).filter_by(empresa_id=999).first()
    assert res is None


# ================= RUN =================
# LOCAL:
# uvicorn main:app --reload

# PRODUCCIÓN:
# uvicorn main:app --host 0.0.0.0 --port ${PORT}
