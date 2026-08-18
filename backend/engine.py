"""Motore agronomico: rischio fungino, dilavamento, scadenza, blocco pioggia, raccomandazioni."""
from datetime import datetime, timezone

REASON = {
    "LEACHING": "Dilavamento", "EXPIRED": "Copertura scaduta", "PHASE_RISK": "Rischio di fase",
    "FUNGAL_RISK": "Rischio fungino", "INSECT_RISK": "Rischio insetti",
    "ACARID_RISK": "Rischio acari", "MANUAL": "Manuale",
}

CATEGORY_FOR_RISK = {
    "fungal": ["rame", "fungicida", "zolfo"],
    "insect": ["insetticida"],
    "acarid": ["acaricida"],
}

SUGGESTION = {
    "fungal": "Consigliato trattamento preventivo con rame o fungicida specifico.",
    "insect": "Consigliato insetticida selettivo o olio di Neem.",
    "acarid": "Consigliato acaricida od olio minerale (contro ragnetto rosso).",
}


def iso_now():
    return datetime.now(timezone.utc).isoformat()


def _parse(dt):
    if not dt:
        return None
    try:
        return datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except Exception:
        return None


def estimate_leaf_wetness(humidity, temp, rainfall_rate):
    """Stima bagnatura fogliare 0-8 quando manca il sensore."""
    if humidity is None:
        return 0
    if (rainfall_rate or 0) > 0:
        return 8
    if humidity >= 90:
        w = 6
    elif humidity >= 80:
        w = 4
    elif humidity >= 70:
        w = 2
    else:
        w = 0
    if temp is not None and temp < 5:
        w = max(0, w - 2)
    return w


def assess_fungal_risk(reading, cfg):
    """Ritorna intensità 0-3 del rischio fungino meteo-dipendente."""
    temp = reading.get("temp_c")
    hum = reading.get("humidity_pct")
    lw = reading.get("leaf_wetness")
    if lw is None:
        lw = estimate_leaf_wetness(hum, temp, reading.get("rainfall_rate_mmh"))
    score = 0
    tmin = float(cfg["temp_fungal_min_c"]); tmax = float(cfg["temp_fungal_max_c"])
    if temp is not None and tmin <= temp <= tmax:
        score += 1
    if hum is not None and hum >= float(cfg["humidity_fungal_threshold"]):
        score += 1
    if lw >= float(cfg["leaf_wetness_threshold"]):
        score += 1
    return score


def is_raining(reading, cfg):
    return (reading.get("rainfall_rate_mmh") or 0) >= float(cfg["rain_block_mmh"])


def irrigation_status(soil, cfg):
    if soil is None:
        return {"status": "no_data", "soil_moisture_pct": None,
                "message": "Sensore umidità non disponibile (connessione GW2000).",
                "advice": "Collega la stazione Ecowitt con sensore di umidità del suolo."}
    low = float(cfg["soil_moisture_low_pct"]); crit = float(cfg["soil_moisture_critical_pct"])
    stop = float(cfg["soil_moisture_stop_pct"])
    if soil <= crit:
        return {"status": "critical", "soil_moisture_pct": soil,
                "message": f"Umidità CRITICA {soil}%: irrigare subito!",
                "advice": "Avviare irrigazione immediata. Priorità: pomacee (Melo/Pero) e peschi."}
    if soil <= low:
        return {"status": "low", "soil_moisture_pct": soil,
                "message": f"Umidità bassa {soil}%: irrigazione consigliata.",
                "advice": "Irrigare nelle prossime ore, preferibilmente mattino presto o sera."}
    if soil >= stop:
        return {"status": "high", "soil_moisture_pct": soil,
                "message": f"Umidità elevata {soil}%: nessuna irrigazione necessaria.",
                "advice": "Terreno ben idratato. Verificare drenaggio se pioggia recente."}
    return {"status": "ok", "soil_moisture_pct": soil,
            "message": f"Umidità ottimale {soil}%.", "advice": "Nessuna azione necessaria."}


async def _add_alert(db, user_id, atype, severity, message, plant_id=None):
    # anti-spam: non duplicare alert identico non letto
    exists = await db.alerts.find_one({"user_id": user_id, "type": atype, "message": message,
                                       "acknowledged": False})
    if exists:
        return
    await db.alerts.insert_one({"user_id": user_id, "type": atype, "severity": severity,
                                "message": message, "plant_id": plant_id, "acknowledged": False,
                                "created_at": iso_now()})


async def _add_rec(db, user_id, plant_id, product_id, reason, reason_code, priority):
    dup = await db.recommendations.find_one({"user_id": user_id, "plant_id": plant_id,
                                             "reason_code": reason_code, "status": "pending"})
    if dup:
        return False
    await db.recommendations.insert_one({"user_id": user_id, "plant_id": plant_id,
                                         "product_id": product_id, "reason": reason,
                                         "reason_code": reason_code, "priority": priority,
                                         "status": "pending", "created_at": iso_now()})
    return True


async def check_leaching(db, user_id, reading, cfg):
    """Accumula pioggia sui trattamenti validi; se supera soglia -> dilavato."""
    rain = reading.get("rainfall_event_mm") or reading.get("rainfall_daily_mm") or 0
    if rain <= 0:
        return 0
    count = 0
    treatments = await db.treatments.find({"user_id": user_id, "status": "valid"}).to_list(500)
    for t in treatments:
        prod = await db.products.find_one({"_id": _oid(t.get("product_id"))})
        threshold = float((prod or {}).get("leaching_threshold_mm") or cfg["leaching_threshold_mm"])
        acc = (t.get("rainfall_accumulated_mm") or 0) + rain
        if acc >= threshold:
            await db.treatments.update_one({"_id": t["_id"]},
                {"$set": {"status": "leached", "rainfall_accumulated_mm": acc, "leached_at": iso_now()}})
            pl = await db.plants.find_one({"_id": _oid(t.get("plant_id"))})
            pname = (pl or {}).get("name", "pianta")
            await _add_alert(db, user_id, "leaching", "warning",
                             f"Trattamento su {pname} dilavato ({acc:.0f}mm > {threshold:.0f}mm). Ripetere.",
                             t.get("plant_id"))
            await _add_rec(db, user_id, t.get("plant_id"), t.get("product_id"),
                           f"Copertura dilavata dalla pioggia ({acc:.0f}mm). Rinnovare il trattamento.",
                           "LEACHING", "urgent")
            count += 1
        else:
            await db.treatments.update_one({"_id": t["_id"]},
                                           {"$set": {"rainfall_accumulated_mm": acc}})
    return count


async def check_expiry(db, user_id):
    now = iso_now()
    count = 0
    treatments = await db.treatments.find({"user_id": user_id, "status": "valid",
                                           "expires_at": {"$lt": now}}).to_list(500)
    for t in treatments:
        await db.treatments.update_one({"_id": t["_id"]}, {"$set": {"status": "expired"}})
        pl = await db.plants.find_one({"_id": _oid(t.get("plant_id"))})
        pname = (pl or {}).get("name", "pianta")
        await _add_rec(db, user_id, t.get("plant_id"), t.get("product_id"),
                       f"Copertura scaduta su {pname}. Valutare rinnovo del trattamento.",
                       "EXPIRED", "normal")
        count += 1
    return count


async def has_category_coverage(db, user_id, plant_id, categories):
    now = iso_now()
    tr = await db.treatments.find_one({"user_id": user_id, "plant_id": plant_id, "status": "valid",
                                       "category": {"$in": categories}, "expires_at": {"$gt": now}})
    return bool(tr)


async def generate_phase_recommendations(db, user_id, reading, cfg):
    fungal_intensity = assess_fungal_risk(reading, cfg)
    count = 0
    plants = await db.plants.find({"user_id": user_id, "active": True}).to_list(500)
    for pl in plants:
        phase_id = pl.get("current_phase_id")
        if not phase_id:
            continue
        ph = await db.phases.find_one({"_id": _oid(phase_id)})
        if not ph:
            continue
        risks = [("fungal", ph.get("risk_fungal", 0), "FUNGAL_RISK"),
                 ("insect", ph.get("risk_insect", 0), "INSECT_RISK"),
                 ("acarid", ph.get("risk_acarid", 0), "ACARID_RISK")]
        for kind, base_risk, code in risks:
            effective = base_risk
            if kind == "fungal":
                effective = min(3, base_risk + (1 if fungal_intensity >= 2 else 0))
            if effective < 2:
                continue
            cats = CATEGORY_FOR_RISK[kind]
            if await has_category_coverage(db, user_id, str(pl["_id"]), cats):
                continue
            # cerca prodotto compatibile per pianta+fase, ordinato per priorità
            compat = await db.compatibility.find(
                {"user_id": user_id, "plant_id": str(pl["_id"]), "phase_id": phase_id,
                 "recommended": True}).sort("priority", 1).to_list(50)
            chosen = None
            for c in compat:
                prod = await db.products.find_one({"_id": _oid(c["product_id"]), "active": True,
                                                   "in_stock": True})
                if prod and prod.get("category") in cats:
                    chosen = prod
                    break
            # precedenza ai prodotti registrati: auto-match per categoria se nessuna compatibilità
            if not chosen:
                chosen = await db.products.find_one({"user_id": user_id, "active": True,
                                                     "in_stock": True, "category": {"$in": cats}})
            priority = "urgent" if effective >= 3 else "normal"
            if chosen:
                created = await _add_rec(db, user_id, str(pl["_id"]), str(chosen["_id"]),
                    f"{REASON[code]} (livello {effective}/3) in fase «{ph['phase_name']}»: "
                    f"applicare {chosen['name']}.", code, priority)
            else:
                created = await _add_rec(db, user_id, str(pl["_id"]), None,
                    f"{REASON[code]} livello {effective}/3 in fase «{ph['phase_name']}» su "
                    f"{pl['name']}. {SUGGESTION[kind]} (Aggiungi il prodotto in magazzino "
                    f"o chiedi all'Assistente AI.)",
                    code, priority)
            if created:
                count += 1
    return count


async def expire_old_recommendations(db, user_id):
    # le raccomandazioni di fase più vecchie di 14 giorni scadono
    return 0


def _oid(v):
    from bson import ObjectId
    try:
        return ObjectId(v)
    except Exception:
        return ObjectId("000000000000000000000000")


async def check_fertilization_reminders(db, user_id):
    now = iso_now()
    due = await db.fertilizations.find({"user_id": user_id, "reminded": False,
                                        "next_reminder_date": {"$lte": now, "$ne": None}}).to_list(200)
    count = 0
    for f in due:
        pname = ""
        if f.get("plant_id"):
            pl = await db.plants.find_one({"_id": _oid(f["plant_id"])})
            pname = f" su {pl['name']}" if pl else ""
        label = f.get("ftype") or "concime"
        await _add_alert(db, user_id, "fertilization", "info",
                         f"Promemoria concimazione: {label}{pname}. È il momento di concimare.",
                         f.get("plant_id"))
        await db.fertilizations.update_one({"_id": f["_id"]}, {"$set": {"reminded": True}})
        count += 1
    return count


async def run_cycle(db, user_id, reading, cfg):
    leached = await check_leaching(db, user_id, reading, cfg)
    expired = await check_expiry(db, user_id)
    fert_reminders = await check_fertilization_reminders(db, user_id)
    raining = is_raining(reading, cfg)
    new_recs = 0
    if raining:
        await _add_alert(db, user_id, "rain_block", "info",
                         "Pioggia in corso: nuove raccomandazioni di trattamento sospese.")
    else:
        new_recs = await generate_phase_recommendations(db, user_id, reading, cfg)
    fungal = assess_fungal_risk(reading, cfg)
    if fungal >= 3:
        await _add_alert(db, user_id, "fungal", "critical",
                         "Rischio fungino CRITICO: condizioni meteo altamente favorevoli alle infezioni.")
    return {"leached": leached, "expired": expired, "new_recommendations": new_recs,
            "fertilization_reminders": fert_reminders, "is_raining": raining,
            "fungal_risk": fungal, "ran_at": iso_now()}
