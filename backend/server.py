from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import json
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import List, Optional

import bcrypt
import jwt
import requests
from bson import ObjectId
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr

from phases import PHASE_TEMPLATES, template_for_species, SPECIES_LIST
from engine import run_cycle, irrigation_status, iso_now

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_ALGORITHM = "HS256"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("frutteto")

app = FastAPI(title="Frutteto Agro API")
api = APIRouter(prefix="/api")


# ------------------------------------------------ auth helpers
def hash_password(pw): return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
def verify_password(p, h): return bcrypt.checkpw(p.encode(), h.encode())
def get_secret(): return os.environ["JWT_SECRET"]


def create_access_token(uid, email):
    return jwt.encode({"sub": uid, "email": email, "type": "access",
                       "exp": datetime.now(timezone.utc) + timedelta(days=7)},
                      get_secret(), algorithm=JWT_ALGORITHM)


def set_auth_cookie(response, token):
    response.set_cookie("access_token", token, httponly=True, secure=True,
                        samesite="none", max_age=604800, path="/")


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(401, "Non autenticato")
    try:
        payload = jwt.decode(token, get_secret(), algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(401, "Utente non trovato")
        user["id"] = str(user["_id"]); user.pop("_id", None); user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Sessione scaduta")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token non valido")


def oid(v):
    try:
        return ObjectId(v)
    except Exception:
        raise HTTPException(400, "ID non valido")


def clean(doc):
    doc["id"] = str(doc["_id"]); doc.pop("_id", None); return doc


# ------------------------------------------------ config defaults
DEFAULT_CONFIG = {
    "check_interval_minutes": "30",
    "leaching_threshold_mm": "15",
    "rain_block_mmh": "2",
    "leaf_wetness_threshold": "3",
    "temp_fungal_min_c": "10",
    "temp_fungal_max_c": "30",
    "humidity_fungal_threshold": "80",
    "soil_moisture_low_pct": "35",
    "soil_moisture_critical_pct": "20",
    "soil_moisture_stop_pct": "75",
    "ecowitt_app_key": "",
    "ecowitt_api_key": "",
    "ecowitt_mac": "",
    "liters_per_plant": "10",
}


async def get_user_config(user_id):
    doc = await db.configs.find_one({"user_id": user_id})
    cfg = dict(DEFAULT_CONFIG)
    if doc:
        cfg.update(doc.get("values", {}))
    return cfg


# ------------------------------------------------ models
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
    emoji: Optional[str] = "🌳"
    notes: Optional[str] = ""


class ProductIn(BaseModel):
    name: str
    active_ingredient: Optional[str] = ""
    category: str
    persistence_days: float = 7
    carenza_days: int = 0
    dose_per_hl: Optional[float] = None
    dose_unit: str = "g"
    leaching_threshold_mm: float = 15.0
    max_applications_year: Optional[int] = None
    notes: Optional[str] = ""
    in_stock: bool = True


class CompatibilityIn(BaseModel):
    plant_id: str
    phase_id: str
    priority: int = 5
    recommended: bool = True
    notes: Optional[str] = ""


class TreatmentIn(BaseModel):
    plant_id: str
    product_id: str
    dose_used: Optional[float] = None
    dose_unit: Optional[str] = "g"
    operator: Optional[str] = ""
    notes: Optional[str] = ""
    applied_at: Optional[str] = None


class PhaseSetIn(BaseModel):
    phase_id: str


class ConfigIn(BaseModel):
    values: dict


class AdvisorIn(BaseModel):
    question: str
    plant_id: Optional[str] = None


# ------------------------------------------------ auth routes
@api.post("/auth/register")
async def register(body: RegisterIn, response: Response):
    email = body.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(400, "Email già registrata")
    doc = {"name": body.name, "email": email, "password_hash": hash_password(body.password),
           "role": "user", "plan": "trial",
           "trial_ends": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
           "created_at": iso_now()}
    res = await db.users.insert_one(doc)
    token = create_access_token(str(res.inserted_id), email)
    set_auth_cookie(response, token)
    doc["id"] = str(res.inserted_id); doc.pop("_id", None); doc.pop("password_hash", None)
    doc["token"] = token
    return doc


@api.post("/auth/login")
async def login(body: LoginIn, response: Response):
    email = body.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Credenziali non valide")
    token = create_access_token(str(user["_id"]), email)
    set_auth_cookie(response, token)
    user["id"] = str(user["_id"]); user.pop("_id", None); user.pop("password_hash", None)
    user["token"] = token
    return user


@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


@api.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user


# ------------------------------------------------ reference
@api.get("/reference/species")
async def species():
    return {"species": SPECIES_LIST,
            "templates": {k: [p["phase_name"] for p in v] for k, v in PHASE_TEMPLATES.items()}}


@api.get("/reference/categories")
async def categories():
    return {"categories": ["rame", "fungicida", "zolfo", "insetticida", "acaricida",
                           "corroborante", "correttore", "fertilizzante", "ammendante"]}


# ------------------------------------------------ plants
@api.get("/plants")
async def list_plants(user: dict = Depends(get_current_user)):
    docs = await db.plants.find({"user_id": user["id"], "active": True}).sort("created_at", -1).to_list(500)
    out = []
    for d in docs:
        d = clean(d)
        if d.get("current_phase_id"):
            ph = await db.phases.find_one({"_id": oid(d["current_phase_id"])})
            if ph:
                d["current_phase"] = {"id": str(ph["_id"]), "phase_name": ph["phase_name"],
                                      "phase_code": ph["phase_code"],
                                      "risk_fungal": ph["risk_fungal"], "risk_insect": ph["risk_insect"],
                                      "risk_acarid": ph["risk_acarid"]}
        out.append(d)
    return out


@api.post("/plants")
async def create_plant(body: PlantIn, user: dict = Depends(get_current_user)):
    doc = body.model_dump()
    doc.update({"user_id": user["id"], "active": True, "current_phase_id": None,
                "created_at": iso_now()})
    res = await db.plants.insert_one(doc)
    plant_id = str(res.inserted_id)
    # auto-generate BBCH phases from template
    template = template_for_species(body.species)
    first_phase_id = None
    for p in template:
        pd = {"user_id": user["id"], "plant_id": plant_id, **p}
        r = await db.phases.insert_one(pd)
        if first_phase_id is None:
            first_phase_id = str(r.inserted_id)
    await db.plants.update_one({"_id": res.inserted_id}, {"$set": {"current_phase_id": first_phase_id}})
    doc = clean(doc); doc["id"] = plant_id
    doc["current_phase_id"] = first_phase_id
    return doc


@api.get("/plants/{plant_id}")
async def get_plant(plant_id: str, user: dict = Depends(get_current_user)):
    p = await db.plants.find_one({"_id": oid(plant_id), "user_id": user["id"]})
    if not p:
        raise HTTPException(404, "Pianta non trovata")
    phases = await db.phases.find({"plant_id": plant_id}).sort("phase_order", 1).to_list(100)
    treatments = await db.treatments.find({"plant_id": plant_id}).sort("applied_at", -1).to_list(20)
    return {"plant": clean(p), "phases": [clean(x) for x in phases],
            "treatments": [clean(x) for x in treatments]}


@api.put("/plants/{plant_id}")
async def update_plant(plant_id: str, body: PlantIn, user: dict = Depends(get_current_user)):
    await db.plants.update_one({"_id": oid(plant_id), "user_id": user["id"]},
                               {"$set": body.model_dump()})
    return {"ok": True}


@api.delete("/plants/{plant_id}")
async def delete_plant(plant_id: str, user: dict = Depends(get_current_user)):
    await db.plants.update_one({"_id": oid(plant_id), "user_id": user["id"]},
                               {"$set": {"active": False}})
    return {"ok": True}


@api.post("/plants/{plant_id}/phase")
async def set_phase(plant_id: str, body: PhaseSetIn, user: dict = Depends(get_current_user)):
    ph = await db.phases.find_one({"_id": oid(body.phase_id), "plant_id": plant_id})
    if not ph:
        raise HTTPException(404, "Fase non trovata")
    await db.plants.update_one({"_id": oid(plant_id), "user_id": user["id"]},
                               {"$set": {"current_phase_id": body.phase_id}})
    # invalidate obsolete phase recommendations
    await db.recommendations.update_many(
        {"user_id": user["id"], "plant_id": plant_id, "status": "pending",
         "reason_code": {"$in": ["PHASE_RISK", "FUNGAL_RISK", "INSECT_RISK", "ACARID_RISK"]}},
        {"$set": {"status": "superseded"}})
    return {"ok": True, "phase": clean(ph)}


@api.get("/plants/{plant_id}/phases")
async def plant_phases(plant_id: str, user: dict = Depends(get_current_user)):
    phases = await db.phases.find({"plant_id": plant_id}).sort("phase_order", 1).to_list(100)
    return [clean(x) for x in phases]


@api.get("/plants/{plant_id}/coverage")
async def plant_coverage(plant_id: str, user: dict = Depends(get_current_user)):
    now = iso_now()
    products = await db.products.find({"user_id": user["id"], "active": True}).to_list(200)
    out = []
    for prod in products:
        pid = str(prod["_id"])
        tr = await db.treatments.find_one(
            {"plant_id": plant_id, "product_id": pid, "status": "valid",
             "expires_at": {"$gt": now}}, sort=[("applied_at", -1)])
        out.append({"product": {"id": pid, "name": prod["name"], "category": prod["category"]},
                    "covered": bool(tr),
                    "expires_at": tr["expires_at"] if tr else None})
    return out


# ------------------------------------------------ products
@api.get("/products")
async def list_products(user: dict = Depends(get_current_user)):
    docs = await db.products.find({"user_id": user["id"], "active": True}).sort("name", 1).to_list(300)
    return [clean(d) for d in docs]


@api.post("/products")
async def create_product(body: ProductIn, user: dict = Depends(get_current_user)):
    doc = body.model_dump()
    doc.update({"user_id": user["id"], "active": True, "created_at": iso_now()})
    res = await db.products.insert_one(doc)
    doc = clean(doc); doc["id"] = str(res.inserted_id)
    return doc


@api.put("/products/{product_id}")
async def update_product(product_id: str, body: ProductIn, user: dict = Depends(get_current_user)):
    await db.products.update_one({"_id": oid(product_id), "user_id": user["id"]},
                                 {"$set": body.model_dump()})
    return {"ok": True}


@api.delete("/products/{product_id}")
async def delete_product(product_id: str, user: dict = Depends(get_current_user)):
    await db.products.update_one({"_id": oid(product_id), "user_id": user["id"]},
                                 {"$set": {"active": False}})
    return {"ok": True}


@api.get("/products/{product_id}/compatibility")
async def get_compat(product_id: str, user: dict = Depends(get_current_user)):
    docs = await db.compatibility.find({"user_id": user["id"], "product_id": product_id}).to_list(300)
    return [clean(d) for d in docs]


@api.post("/products/{product_id}/compatibility")
async def add_compat(product_id: str, body: CompatibilityIn, user: dict = Depends(get_current_user)):
    doc = body.model_dump()
    doc.update({"user_id": user["id"], "product_id": product_id})
    await db.compatibility.update_one(
        {"user_id": user["id"], "product_id": product_id,
         "plant_id": body.plant_id, "phase_id": body.phase_id},
        {"$set": doc}, upsert=True)
    return {"ok": True}


@api.delete("/products/{product_id}/compatibility/{compat_id}")
async def del_compat(product_id: str, compat_id: str, user: dict = Depends(get_current_user)):
    await db.compatibility.delete_one({"_id": oid(compat_id), "user_id": user["id"]})
    return {"ok": True}


# ------------------------------------------------ treatments
@api.get("/treatments")
async def list_treatments(plant_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    q = {"user_id": user["id"]}
    if plant_id:
        q["plant_id"] = plant_id
    docs = await db.treatments.find(q).sort("applied_at", -1).to_list(300)
    out = []
    for d in docs:
        d = clean(d)
        pl = await db.plants.find_one({"_id": oid(d["plant_id"])}) if d.get("plant_id") else None
        pr = await db.products.find_one({"_id": oid(d["product_id"])}) if d.get("product_id") else None
        d["plant_name"] = pl["name"] if pl else "—"
        d["product_name"] = pr["name"] if pr else "—"
        out.append(d)
    return out


@api.post("/treatments")
async def create_treatment(body: TreatmentIn, user: dict = Depends(get_current_user)):
    prod = await db.products.find_one({"_id": oid(body.product_id), "user_id": user["id"]})
    if not prod:
        raise HTTPException(404, "Prodotto non trovato")
    applied = body.applied_at or iso_now()
    applied_dt = datetime.fromisoformat(applied.replace("Z", "+00:00"))
    expires = (applied_dt + timedelta(days=float(prod.get("persistence_days", 7)))).isoformat()
    latest = await db.weather.find_one({"user_id": user["id"]}, sort=[("timestamp", -1)])
    snap = None
    if latest:
        snap = json.dumps({"temp_c": latest.get("temp_c"), "humidity_pct": latest.get("humidity_pct")})
    # invalidate previous valid treatments of same category on same plant
    await db.treatments.update_many(
        {"user_id": user["id"], "plant_id": body.plant_id, "category": prod.get("category"),
         "status": "valid"}, {"$set": {"status": "superseded"}})
    doc = {"user_id": user["id"], "plant_id": body.plant_id, "product_id": body.product_id,
           "category": prod.get("category"), "applied_at": applied, "expires_at": expires,
           "dose_used": body.dose_used, "dose_unit": body.dose_unit or prod.get("dose_unit"),
           "operator": body.operator or user.get("name"), "notes": body.notes,
           "status": "valid", "rainfall_accumulated_mm": 0.0, "weather_snapshot": snap,
           "created_at": iso_now()}
    res = await db.treatments.insert_one(doc)
    doc = clean(doc); doc["id"] = str(res.inserted_id)
    return doc


@api.delete("/treatments/{treatment_id}")
async def delete_treatment(treatment_id: str, user: dict = Depends(get_current_user)):
    await db.treatments.delete_one({"_id": oid(treatment_id), "user_id": user["id"]})
    return {"ok": True}


# ------------------------------------------------ recommendations
@api.get("/recommendations")
async def list_recs(status: str = "pending", user: dict = Depends(get_current_user)):
    docs = await db.recommendations.find({"user_id": user["id"], "status": status}).sort("created_at", -1).to_list(200)
    out = []
    for d in docs:
        d = clean(d)
        pl = await db.plants.find_one({"_id": oid(d["plant_id"])}) if d.get("plant_id") else None
        pr = await db.products.find_one({"_id": oid(d["product_id"])}) if d.get("product_id") else None
        d["plant_name"] = pl["name"] if pl else "—"
        d["plant_emoji"] = pl.get("emoji", "🌳") if pl else "🌳"
        d["product_name"] = pr["name"] if pr else None
        out.append(d)
    return out


@api.post("/recommendations/{rec_id}/dismiss")
async def dismiss_rec(rec_id: str, user: dict = Depends(get_current_user)):
    await db.recommendations.update_one({"_id": oid(rec_id), "user_id": user["id"]},
                                        {"$set": {"status": "dismissed"}})
    return {"ok": True}


@api.post("/recommendations/{rec_id}/execute")
async def execute_rec(rec_id: str, body: TreatmentIn, user: dict = Depends(get_current_user)):
    rec = await db.recommendations.find_one({"_id": oid(rec_id), "user_id": user["id"]})
    if not rec:
        raise HTTPException(404, "Raccomandazione non trovata")
    tr = await create_treatment(body, user)
    await db.recommendations.update_one({"_id": oid(rec_id)},
                                        {"$set": {"status": "executed", "related_treatment_id": tr["id"]}})
    return {"ok": True, "treatment_id": tr["id"]}


# ------------------------------------------------ alerts
@api.get("/alerts")
async def list_alerts(unread: Optional[str] = None, user: dict = Depends(get_current_user)):
    q = {"user_id": user["id"]}
    if unread == "1":
        q["acknowledged"] = False
    docs = await db.alerts.find(q).sort("created_at", -1).to_list(200)
    return [clean(d) for d in docs]


@api.post("/alerts/{alert_id}/ack")
async def ack_alert(alert_id: str, user: dict = Depends(get_current_user)):
    await db.alerts.update_one({"_id": oid(alert_id), "user_id": user["id"]},
                               {"$set": {"acknowledged": True, "ack_at": iso_now()}})
    return {"ok": True}


@api.post("/alerts/ack-all")
async def ack_all(user: dict = Depends(get_current_user)):
    await db.alerts.update_many({"user_id": user["id"], "acknowledged": False},
                                {"$set": {"acknowledged": True, "ack_at": iso_now()}})
    return {"ok": True}


# ------------------------------------------------ weather / ecowitt
def _demo_weather(cfg):
    now = datetime.now(timezone.utc)
    base_t = 18 + random.uniform(-3, 5)
    hum = round(60 + random.uniform(-12, 25))
    rain_rate = round(max(0, random.uniform(-1.5, 2.5)), 1)
    return {
        "source": "demo", "timestamp": now.isoformat(),
        "temp_c": round(base_t, 1), "humidity_pct": hum,
        "soil_moisture_pct": round(random.uniform(22, 62), 1),
        "rainfall_rate_mmh": rain_rate,
        "rainfall_event_mm": round(rain_rate * random.uniform(0, 2), 1),
        "rainfall_daily_mm": round(random.uniform(0, 8), 1),
        "wind_speed_ms": round(random.uniform(0.5, 6), 1),
        "pressure_hpa": round(1013 + random.uniform(-8, 8), 1),
        "leaf_wetness": None,
    }


async def fetch_and_store_weather(user):
    cfg = await get_user_config(user["id"])
    app_key = cfg.get("ecowitt_app_key") or os.environ.get("ECOWITT_APPLICATION_KEY")
    api_key = cfg.get("ecowitt_api_key") or os.environ.get("ECOWITT_API_KEY")
    mac = cfg.get("ecowitt_mac") or os.environ.get("ECOWITT_MAC")
    reading = None
    if app_key and api_key and mac:
        try:
            r = requests.get("https://api.ecowitt.net/api/v3/device/real_time",
                             params={"application_key": app_key, "api_key": api_key, "mac": mac,
                                     "call_back": "all", "temp_unitid": 1, "pressure_unitid": 3,
                                     "wind_speed_unitid": 6, "rainfall_unitid": 12}, timeout=10)
            j = r.json()
            if j.get("code") == 0 and j.get("data"):
                d = j["data"]
                def gv(sec, f, dft=None):
                    try:
                        return float(d.get(sec, {}).get(f, {}).get("value"))
                    except (TypeError, ValueError):
                        return dft
                reading = {"source": "ecowitt", "timestamp": iso_now(),
                           "temp_c": gv("outdoor", "temperature"),
                           "humidity_pct": gv("outdoor", "humidity"),
                           "soil_moisture_pct": gv("soil_ch1", "soilmoisture"),
                           "rainfall_rate_mmh": gv("rainfall", "rain_rate", 0),
                           "rainfall_event_mm": gv("rainfall", "event", 0),
                           "rainfall_daily_mm": gv("rainfall", "daily", 0),
                           "wind_speed_ms": gv("wind", "wind_speed", 0),
                           "pressure_hpa": gv("pressure", "relative", 1013),
                           "leaf_wetness": gv("leaf_ch1", "leaf_wetness")}
        except Exception as e:
            logger.warning("Ecowitt fetch failed: %s", e)
    if reading is None:
        reading = _demo_weather(cfg)
    reading["user_id"] = user["id"]
    await db.weather.insert_one(dict(reading))
    return reading, cfg


@api.get("/weather/latest")
async def weather_latest(user: dict = Depends(get_current_user)):
    reading, cfg = await fetch_and_store_weather(user)
    reading.pop("_id", None); reading.pop("user_id", None)
    return reading


@api.get("/weather/history")
async def weather_history(hours: int = 24, user: dict = Depends(get_current_user)):
    docs = await db.weather.find({"user_id": user["id"]}).sort("timestamp", -1).to_list(500)
    docs = list(reversed(docs))
    out = [{"time": datetime.fromisoformat(d["timestamp"]).strftime("%d/%m %H:%M"),
            "temp": d.get("temp_c"), "humidity": d.get("humidity_pct"),
            "soil": d.get("soil_moisture_pct"), "rain": d.get("rainfall_daily_mm")}
           for d in docs[-200:]]
    return out


@api.get("/irrigation/status")
async def irrigation(user: dict = Depends(get_current_user)):
    latest = await db.weather.find_one({"user_id": user["id"]}, sort=[("timestamp", -1)])
    cfg = await get_user_config(user["id"])
    if not latest:
        reading, cfg = await fetch_and_store_weather(user)
        latest = reading
    return irrigation_status(latest.get("soil_moisture_pct"), cfg)


# ------------------------------------------------ config
@api.get("/config")
async def get_config(user: dict = Depends(get_current_user)):
    cfg = await get_user_config(user["id"])
    return cfg


@api.put("/config")
async def update_config(body: ConfigIn, user: dict = Depends(get_current_user)):
    existing = await db.configs.find_one({"user_id": user["id"]})
    values = (existing or {}).get("values", {})
    values.update(body.values)
    await db.configs.update_one({"user_id": user["id"]},
                                {"$set": {"user_id": user["id"], "values": values}}, upsert=True)
    return {"ok": True}


# ------------------------------------------------ engine cycle + status
@api.post("/cycle/run")
async def cycle_run(user: dict = Depends(get_current_user)):
    reading, cfg = await fetch_and_store_weather(user)
    result = await run_cycle(db, user["id"], reading, cfg)
    return {"ok": True, "result": result, "weather": {k: reading[k] for k in
            ("temp_c", "humidity_pct", "soil_moisture_pct", "rainfall_rate_mmh") if k in reading}}


@api.get("/status")
async def status(user: dict = Depends(get_current_user)):
    latest = await db.weather.find_one({"user_id": user["id"]}, sort=[("timestamp", -1)])
    plants = await db.plants.count_documents({"user_id": user["id"], "active": True})
    products = await db.products.count_documents({"user_id": user["id"], "active": True})
    pending = await db.recommendations.count_documents({"user_id": user["id"], "status": "pending"})
    urgent = await db.recommendations.count_documents({"user_id": user["id"], "status": "pending", "priority": "urgent"})
    unread = await db.alerts.count_documents({"user_id": user["id"], "acknowledged": False})
    treatments = await db.treatments.count_documents({"user_id": user["id"]})
    cfg = await get_user_config(user["id"])
    is_raining = bool(latest and (latest.get("rainfall_rate_mmh") or 0) >= float(cfg["rain_block_mmh"]))
    return {"plants": plants, "products": products, "pending_recommendations": pending,
            "urgent_recommendations": urgent, "unread_alerts": unread, "treatments": treatments,
            "healthy_plants": max(0, plants - pending), "is_raining": is_raining,
            "weather": ({k: latest.get(k) for k in ("temp_c", "humidity_pct", "soil_moisture_pct",
                        "rainfall_rate_mmh", "wind_speed_ms", "pressure_hpa", "source", "timestamp")}
                        if latest else None)}


# ------------------------------------------------ AI
@api.post("/plants/{plant_id}/generate-phases")
async def ai_generate_phases(plant_id: str, user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    p = await db.plants.find_one({"_id": oid(plant_id), "user_id": user["id"]})
    if not p:
        raise HTTPException(404, "Pianta non trovata")
    system = ("Sei un agronomo esperto. Genera le fasi fenologiche (scala BBCH) per una pianta da frutto. "
              "Rispondi SOLO con un array JSON valido, senza testo extra. Ogni elemento: "
              '{"phase_code":"A","phase_name":"...","phase_order":1,"description":"...",'
              '"risk_fungal":0,"risk_insect":0,"risk_acarid":0}. I rischi sono interi 0-3. In italiano.')
    chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"phases-{plant_id}",
                   system_message=system).with_model("anthropic", "claude-sonnet-4-6")
    try:
        reply = await chat.send_message(UserMessage(
            text=f"Pianta: {p['name']} {p.get('variety','')} (specie {p['species']}). Genera 10-14 fasi."))
        txt = reply.strip()
        if "```" in txt:
            txt = txt.split("```")[1].replace("json", "", 1).strip()
        phases = json.loads(txt)
    except Exception as e:
        logger.error("AI phases error: %s", e)
        raise HTTPException(502, "Generazione fasi AI non riuscita")
    await db.phases.delete_many({"plant_id": plant_id})
    first_id = None
    for ph in phases:
        pd = {"user_id": user["id"], "plant_id": plant_id,
              "phase_code": ph.get("phase_code", ""), "phase_name": ph.get("phase_name", ""),
              "phase_order": int(ph.get("phase_order", 0)), "description": ph.get("description", ""),
              "risk_fungal": int(ph.get("risk_fungal", 0)), "risk_insect": int(ph.get("risk_insect", 0)),
              "risk_acarid": int(ph.get("risk_acarid", 0))}
        r = await db.phases.insert_one(pd)
        if first_id is None:
            first_id = str(r.inserted_id)
    await db.plants.update_one({"_id": oid(plant_id)}, {"$set": {"current_phase_id": first_id}})
    return {"ok": True, "count": len(phases)}


@api.post("/ai/advisor")
async def advisor(body: AdvisorIn, user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    context = ""
    if body.plant_id:
        p = await db.plants.find_one({"_id": oid(body.plant_id)})
        if p:
            context = f"\nPianta: {p.get('name')} ({p.get('species')} {p.get('variety','')})."
    system = ("Sei un agronomo esperto in frutticoltura e difesa integrata. Rispondi SEMPRE in italiano, "
              "pratico e accessibile. Consigli su irrigazione, potatura, concimazione, difesa e fasi "
              "fenologiche. Usa brevi punti elenco. Max 200 parole.")
    chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"advisor-{user['id']}",
                   system_message=system).with_model("anthropic", "claude-sonnet-4-6")
    try:
        reply = await chat.send_message(UserMessage(text=body.question + context))
    except Exception as e:
        logger.error("AI advisor error: %s", e)
        raise HTTPException(502, "Assistente AI non disponibile")
    return {"answer": reply}


# ------------------------------------------------ startup
@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@frutteto.it")
    admin_pw = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({"name": "Admin", "email": admin_email,
                                   "password_hash": hash_password(admin_pw), "role": "admin",
                                   "plan": "lifetime", "created_at": iso_now()})
    elif not verify_password(admin_pw, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_pw)}})
    logger.info("Frutteto Agro API ready.")


@app.on_event("shutdown")
async def shutdown():
    client.close()


app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000"), "http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
