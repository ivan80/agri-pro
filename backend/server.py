from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import logging
import secrets
import random
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Annotated

import bcrypt
import jwt
import requests
from bson import ObjectId
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr, BeforeValidator, ConfigDict

# ---------------------------------------------------------------- DB
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_ALGORITHM = "HS256"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("frutteto")

app = FastAPI(title="Frutteto Manager API")
api = APIRouter(prefix="/api")


# ---------------------------------------------------------------- helpers
def PyObjectId():
    return Annotated[str, BeforeValidator(str)]


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def get_secret() -> str:
    return os.environ["JWT_SECRET"]


def create_access_token(uid: str, email: str) -> str:
    payload = {"sub": uid, "email": email, "type": "access",
               "exp": datetime.now(timezone.utc) + timedelta(days=7)}
    return jwt.encode(payload, get_secret(), algorithm=JWT_ALGORITHM)


def set_auth_cookie(response: Response, token: str):
    response.set_cookie(key="access_token", value=token, httponly=True,
                        secure=True, samesite="none", max_age=604800, path="/")


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Non autenticato")
    try:
        payload = jwt.decode(token, get_secret(), algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="Utente non trovato")
        user["id"] = str(user["_id"])
        user.pop("_id", None)
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sessione scaduta")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")


# ---------------------------------------------------------------- models
class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class PlantIn(BaseModel):
    name: str
    species: str
    variety: Optional[str] = ""
    planted_year: Optional[int] = None
    quantity: int = 1
    phase: str = "riposo"
    notes: Optional[str] = ""


class IrrigationIn(BaseModel):
    plant_id: Optional[str] = None
    liters: float
    duration_min: int
    method: str = "goccia"
    date: Optional[str] = None


class WeatherSettingsIn(BaseModel):
    application_key: str
    api_key: str
    mac: str


class AdvisorIn(BaseModel):
    question: str
    plant_id: Optional[str] = None


# ---------------------------------------------------------------- auth routes
@api.post("/auth/register")
async def register(body: RegisterIn, response: Response):
    email = body.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email già registrata")
    doc = {"name": body.name, "email": email, "password_hash": hash_password(body.password),
           "role": "user", "plan": "trial",
           "trial_ends": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
           "created_at": datetime.now(timezone.utc).isoformat()}
    res = await db.users.insert_one(doc)
    token = create_access_token(str(res.inserted_id), email)
    set_auth_cookie(response, token)
    doc["id"] = str(res.inserted_id)
    doc.pop("_id", None); doc.pop("password_hash", None)
    doc["token"] = token
    return doc


@api.post("/auth/login")
async def login(body: LoginIn, response: Response):
    email = body.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    token = create_access_token(str(user["_id"]), email)
    set_auth_cookie(response, token)
    user["id"] = str(user["_id"])
    user.pop("_id", None); user.pop("password_hash", None)
    user["token"] = token
    return user


@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


@api.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user


# ---------------------------------------------------------------- plants
@api.get("/plants")
async def list_plants(user: dict = Depends(get_current_user)):
    docs = await db.plants.find({"user_id": user["id"]}).sort("created_at", -1).to_list(500)
    for d in docs:
        d["id"] = str(d["_id"]); d.pop("_id", None)
    return docs


@api.post("/plants")
async def create_plant(body: PlantIn, user: dict = Depends(get_current_user)):
    doc = body.model_dump()
    doc.update({"user_id": user["id"], "created_at": datetime.now(timezone.utc).isoformat()})
    res = await db.plants.insert_one(doc)
    doc["id"] = str(res.inserted_id); doc.pop("_id", None)
    return doc


@api.put("/plants/{plant_id}")
async def update_plant(plant_id: str, body: PlantIn, user: dict = Depends(get_current_user)):
    await db.plants.update_one({"_id": ObjectId(plant_id), "user_id": user["id"]},
                               {"$set": body.model_dump()})
    doc = await db.plants.find_one({"_id": ObjectId(plant_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Pianta non trovata")
    doc["id"] = str(doc["_id"]); doc.pop("_id", None)
    return doc


@api.delete("/plants/{plant_id}")
async def delete_plant(plant_id: str, user: dict = Depends(get_current_user)):
    await db.plants.delete_one({"_id": ObjectId(plant_id), "user_id": user["id"]})
    return {"ok": True}


# ---------------------------------------------------------------- irrigation
@api.get("/irrigation")
async def list_irrigation(user: dict = Depends(get_current_user)):
    docs = await db.irrigation.find({"user_id": user["id"]}).sort("date", -1).to_list(200)
    for d in docs:
        d["id"] = str(d["_id"]); d.pop("_id", None)
    return docs


@api.post("/irrigation")
async def create_irrigation(body: IrrigationIn, user: dict = Depends(get_current_user)):
    doc = body.model_dump()
    doc["date"] = doc.get("date") or datetime.now(timezone.utc).isoformat()
    doc.update({"user_id": user["id"]})
    res = await db.irrigation.insert_one(doc)
    doc["id"] = str(res.inserted_id); doc.pop("_id", None)
    return doc


# ---------------------------------------------------------------- stats
@api.get("/stats")
async def stats(user: dict = Depends(get_current_user)):
    plants = await db.plants.count_documents({"user_id": user["id"]})
    irr = await db.irrigation.find({"user_id": user["id"]}).to_list(1000)
    total_liters = sum(i.get("liters", 0) for i in irr)
    species = await db.plants.distinct("species", {"user_id": user["id"]})
    return {"plants": plants, "species": len(species),
            "irrigation_events": len(irr), "total_liters": round(total_liters, 1)}


# ---------------------------------------------------------------- phenology reference
PHASES = [
    {"key": "riposo", "label": "Riposo Vegetativo", "month": "Dic–Feb", "color": "#8A9A8E",
     "desc": "Le piante sono in dormienza. Ideale per potatura secca e trattamenti con rame."},
    {"key": "gemme", "label": "Rigonfiamento Gemme", "month": "Feb–Mar", "color": "#F57C00",
     "desc": "Le gemme iniziano a gonfiarsi. Monitorare temperature e primi trattamenti."},
    {"key": "fioritura", "label": "Fioritura", "month": "Mar–Apr", "color": "#4FC3F7",
     "desc": "Massima attenzione alle gelate tardive e all'impollinazione."},
    {"key": "allegagione", "label": "Allegagione", "month": "Apr–Mag", "color": "#81C784",
     "desc": "Formazione dei frutticini. Diradamento e concimazione azotata."},
    {"key": "accrescimento", "label": "Accrescimento Frutti", "month": "Mag–Lug", "color": "#4CAF50",
     "desc": "I frutti crescono. Fabbisogno idrico elevato: irrigazione costante."},
    {"key": "maturazione", "label": "Maturazione", "month": "Lug–Ott", "color": "#F57C00",
     "desc": "Invaiatura e raccolta. Ridurre l'irrigazione per migliorare i gradi zuccherini."},
]


@api.get("/phases")
async def phases():
    return PHASES


# ---------------------------------------------------------------- plans
@api.get("/plans")
async def plans():
    return [
        {"id": "trial", "name": "Prova Gratuita", "price": "0€", "period": "14 giorni",
         "highlight": False, "features": ["Fino a 10 piante", "Fasi fenologiche", "1 stazione meteo demo", "Consigli AI limitati"]},
        {"id": "annual", "name": "Abbonamento Annuale", "price": "39€", "period": "/anno",
         "highlight": True, "features": ["Piante illimitate", "Stazione Ecowitt completa", "Storico irrigazioni", "Consigli AI illimitati", "Notifiche fenologiche", "Backup cloud"]},
        {"id": "lifetime", "name": "Licenza a Vita", "price": "129€", "period": "una tantum",
         "highlight": False, "features": ["Tutto dell'annuale", "Aggiornamenti a vita", "Nessun rinnovo", "Supporto prioritario", "Multi-frutteto"]},
    ]


# ---------------------------------------------------------------- weather (Ecowitt)
def _demo_weather():
    now = datetime.now(timezone.utc)
    base_t = 18 + random.uniform(-2, 4)
    history = []
    for h in range(23, -1, -1):
        t = base_t + 6 * random.uniform(-0.4, 0.6) - (h - 12) * 0.05
        history.append({
            "time": (now - timedelta(hours=h)).strftime("%H:00"),
            "temp": round(t + random.uniform(-1.5, 1.5), 1),
            "humidity": round(60 + random.uniform(-15, 20), 0),
            "rain": round(max(0, random.uniform(-0.5, 1.2)), 1),
        })
    return {
        "source": "demo",
        "station": "Frutteto Demo Station (GW2000)",
        "updated": now.isoformat(),
        "current": {
            "temp": round(base_t, 1), "feels_like": round(base_t - 1.2, 1),
            "humidity": round(62 + random.uniform(-10, 15)), "pressure": round(1013 + random.uniform(-6, 6), 1),
            "wind_speed": round(random.uniform(3, 18), 1), "wind_dir": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
            "rain_day": round(random.uniform(0, 6), 1), "rain_rate": round(random.uniform(0, 2), 1),
            "solar": round(random.uniform(120, 850)), "uv": random.randint(0, 8),
            "soil_moisture": round(random.uniform(28, 55)), "soil_temp": round(base_t - 3 + random.uniform(-1, 1), 1),
        },
        "history": history,
    }


def _parse_ecowitt(data: dict):
    d = data.get("data", {})
    def val(section, field, default=0):
        try:
            return float(d.get(section, {}).get(field, {}).get("value", default))
        except (ValueError, TypeError):
            return default
    now = datetime.now(timezone.utc)
    current = {
        "temp": val("outdoor", "temperature"), "feels_like": val("outdoor", "feels_like"),
        "humidity": val("outdoor", "humidity"), "pressure": val("pressure", "relative", 1013),
        "wind_speed": val("wind", "wind_speed"), "wind_dir": str(int(val("wind", "wind_direction"))) + "°",
        "rain_day": val("rainfall", "daily"), "rain_rate": val("rainfall", "rain_rate"),
        "solar": val("solar_and_uvi", "solar"), "uv": val("solar_and_uvi", "uvi"),
        "soil_moisture": val("soil_ch1", "soilmoisture"), "soil_temp": val("temp_and_humidity_ch1", "temperature"),
    }
    return {"source": "ecowitt", "station": "Ecowitt Live", "updated": now.isoformat(),
            "current": current, "history": _demo_weather()["history"]}


@api.get("/weather")
async def weather(user: dict = Depends(get_current_user)):
    settings = await db.weather_settings.find_one({"user_id": user["id"]})
    app_key = (settings or {}).get("application_key") or os.environ.get("ECOWITT_APPLICATION_KEY")
    api_key = (settings or {}).get("api_key") or os.environ.get("ECOWITT_API_KEY")
    mac = (settings or {}).get("mac") or os.environ.get("ECOWITT_MAC")
    if app_key and api_key and mac:
        try:
            r = requests.get("https://api.ecowitt.net/api/v3/device/real_time",
                             params={"application_key": app_key, "api_key": api_key, "mac": mac,
                                     "call_back": "all", "temp_unitid": 1, "pressure_unitid": 3,
                                     "wind_speed_unitid": 7, "rainfall_unitid": 12},
                             timeout=10)
            j = r.json()
            if j.get("code") == 0 and j.get("data"):
                return _parse_ecowitt(j)
            logger.warning("Ecowitt API code=%s msg=%s", j.get("code"), j.get("msg"))
        except Exception as e:
            logger.warning("Ecowitt fetch failed: %s", e)
    return _demo_weather()


@api.get("/weather/settings")
async def get_weather_settings(user: dict = Depends(get_current_user)):
    s = await db.weather_settings.find_one({"user_id": user["id"]})
    if not s:
        return {"configured": False, "mac": ""}
    return {"configured": True, "mac": s.get("mac", "")}


@api.post("/weather/settings")
async def save_weather_settings(body: WeatherSettingsIn, user: dict = Depends(get_current_user)):
    await db.weather_settings.update_one(
        {"user_id": user["id"]},
        {"$set": {"user_id": user["id"], **body.model_dump()}}, upsert=True)
    return {"configured": True, "mac": body.mac}


# ---------------------------------------------------------------- AI advisor
@api.post("/ai/advisor")
async def advisor(body: AdvisorIn, user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    context = ""
    if body.plant_id:
        p = await db.plants.find_one({"_id": ObjectId(body.plant_id)})
        if p:
            context = f"\nPianta selezionata: {p.get('name')} ({p.get('species')} {p.get('variety','')}), fase attuale: {p.get('phase')}."
    system = ("Sei un agronomo esperto in frutticoltura e gestione di frutteti misti. "
              "Rispondi SEMPRE in italiano, in modo pratico, chiaro e accessibile agli appassionati. "
              "Dai consigli concreti su irrigazione, potatura, concimazione, difesa e fasi fenologiche. "
              "Struttura la risposta con brevi punti elenco quando utile. Massimo 200 parole.")
    chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"],
                   session_id=f"advisor-{user['id']}",
                   system_message=system).with_model("anthropic", "claude-sonnet-4-6")
    try:
        reply = await chat.send_message(UserMessage(text=body.question + context))
    except Exception as e:
        logger.error("AI advisor error: %s", e)
        raise HTTPException(status_code=502, detail="Assistente AI non disponibile al momento")
    await db.ai_logs.insert_one({"user_id": user["id"], "q": body.question,
                                 "a": reply, "at": datetime.now(timezone.utc).isoformat()})
    return {"answer": reply}


# ---------------------------------------------------------------- startup
@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@frutteto.it")
    admin_pw = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({"name": "Admin", "email": admin_email,
                                   "password_hash": hash_password(admin_pw), "role": "admin",
                                   "plan": "lifetime", "created_at": datetime.now(timezone.utc).isoformat()})
    elif not verify_password(admin_pw, existing["password_hash"]):
        await db.users.update_one({"email": admin_email},
                                  {"$set": {"password_hash": hash_password(admin_pw)}})
    logger.info("Frutteto API ready.")


@app.on_event("shutdown")
async def shutdown():
    client.close()


app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000"), "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
