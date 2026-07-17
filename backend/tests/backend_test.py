"""Backend integration tests for Pomario / Frutteto Agro API (agronomic engine).

Coverage:
- Auth (register, login, me, logout, token+cookie dual auth, Bearer fallback)
- Reference (species with BBCH templates, product categories)
- Empty-state (fresh user has zero plants/products)
- Plants CRUD with AUTO-BBCH phase generation (Melo -> pomacee 14 phases)
- Products CRUD + toggle in_stock + compatibility
- Treatments (persistence-based expires_at, supersedes prior category)
- Engine /api/cycle/run — full recommendation pipeline with a risky phase
- Recommendations dismiss/execute
- Alerts list / ack / ack-all
- Weather latest (demo) + history + irrigation status
- Config GET/PUT
- Status counts
- AI phase (re)generation (Claude Sonnet) — flagged slow
"""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@frutteto.it"
ADMIN_PASSWORD = "Frutteto2026!"


# --------------------------------------------------------- fixtures
@pytest.fixture(scope="session")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="session")
def fresh_user():
    """Register a fresh user (empty orchard). Returns (session, user_dict)."""
    s = requests.Session()
    email = f"test_user_{uuid.uuid4().hex[:8]}@frutteto.it"
    payload = {"name": "TEST User", "email": email, "password": "Passw0rd!"}
    r = s.post(f"{API}/auth/register", json=payload, timeout=15)
    assert r.status_code == 200, f"Register failed: {r.status_code} {r.text}"
    data = r.json()
    # Also set Bearer just in case cookies are dropped by requests session
    s.headers.update({"Authorization": f"Bearer {data['token']}"})
    return s, data


# --------------------------------------------------------- Auth
class TestAuth:
    def test_login_admin_returns_token_and_cookie(self):
        r = requests.post(f"{API}/auth/login",
                          json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        assert "token" in data and len(data["token"]) > 20
        assert "access_token" in r.cookies

    def test_admin_me(self, admin_session):
        r = admin_session.get(f"{API}/auth/me", timeout=10)
        assert r.status_code == 200
        assert r.json()["email"] == ADMIN_EMAIL

    def test_register_returns_trial_user_and_token(self, fresh_user):
        _, user = fresh_user
        assert user["plan"] == "trial"
        assert "trial_ends" in user
        assert user["email"].startswith("test_user_")
        assert "id" in user
        assert "token" in user and len(user["token"]) > 20
        assert "password_hash" not in user

    def test_register_duplicate_email(self):
        s = requests.Session()
        email = f"test_dup_{uuid.uuid4().hex[:8]}@frutteto.it"
        r1 = s.post(f"{API}/auth/register",
                    json={"name": "A", "email": email, "password": "Passw0rd!"}, timeout=15)
        assert r1.status_code == 200
        r2 = requests.post(f"{API}/auth/register",
                           json={"name": "A", "email": email, "password": "Passw0rd!"}, timeout=15)
        assert r2.status_code == 400

    def test_login_invalid_credentials(self):
        r = requests.post(f"{API}/auth/login",
                          json={"email": ADMIN_EMAIL, "password": "wrong"}, timeout=10)
        assert r.status_code == 401

    def test_me_unauthenticated(self):
        r = requests.get(f"{API}/auth/me", timeout=10)
        assert r.status_code == 401

    def test_me_via_bearer_only(self):
        # login, throw away cookies, use only Bearer
        r = requests.post(f"{API}/auth/login",
                          json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=10)
        assert r.status_code == 200
        token = r.json()["token"]
        r2 = requests.get(f"{API}/auth/me",
                          headers={"Authorization": f"Bearer {token}"}, timeout=10)
        assert r2.status_code == 200
        assert r2.json()["email"] == ADMIN_EMAIL

    def test_logout_clears_cookie(self):
        s = requests.Session()
        s.post(f"{API}/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=10)
        r = s.post(f"{API}/auth/logout", timeout=10)
        assert r.status_code == 200
        # Without Bearer (session cookie cleared), /me must 401
        r2 = requests.get(f"{API}/auth/me",
                          cookies=s.cookies, timeout=10)
        assert r2.status_code == 401


# --------------------------------------------------------- Reference
class TestReference:
    def test_species_list(self):
        r = requests.get(f"{API}/reference/species", timeout=10)
        assert r.status_code == 200
        j = r.json()
        assert "species" in j and "templates" in j
        names = [s["name"] for s in j["species"]]
        assert "Melo" in names and "Pesco" in names and "Vite/Uva" in names
        # each species has emoji + template ref
        for s in j["species"]:
            assert "emoji" in s and "template" in s
        # pomacee template should have 14 phases
        assert len(j["templates"].get("pomacee", [])) == 14

    def test_categories(self):
        r = requests.get(f"{API}/reference/categories", timeout=10)
        assert r.status_code == 200
        cats = r.json()["categories"]
        for c in ["rame", "fungicida", "insetticida", "acaricida"]:
            assert c in cats


# --------------------------------------------------------- Empty state
class TestEmptyState:
    def test_fresh_user_has_no_plants(self, fresh_user):
        s, _ = fresh_user
        r = s.get(f"{API}/plants", timeout=10)
        assert r.status_code == 200
        assert r.json() == []

    def test_fresh_user_has_no_products(self, fresh_user):
        s, _ = fresh_user
        r = s.get(f"{API}/products", timeout=10)
        assert r.status_code == 200
        assert r.json() == []

    def test_fresh_user_has_no_treatments(self, fresh_user):
        s, _ = fresh_user
        r = s.get(f"{API}/treatments", timeout=10)
        assert r.status_code == 200
        assert r.json() == []

    def test_fresh_user_status(self, fresh_user):
        s, _ = fresh_user
        r = s.get(f"{API}/status", timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ("plants", "products", "pending_recommendations", "urgent_recommendations",
                  "unread_alerts", "healthy_plants", "is_raining", "weather"):
            assert k in d
        assert d["plants"] == 0
        assert d["products"] == 0
        assert d["pending_recommendations"] == 0


# --------------------------------------------------------- Plants + auto phases
class TestPlantsAndPhases:
    def test_create_plant_generates_pomacee_phases(self, fresh_user):
        s, _ = fresh_user
        r = s.post(f"{API}/plants",
                   json={"name": "TEST Melo", "species": "Melo", "emoji": "🍎", "variety": "Gala"},
                   timeout=15)
        assert r.status_code == 200, r.text
        p = r.json()
        assert p["name"] == "TEST Melo"
        assert p["species"] == "Melo"
        assert "id" in p
        # current phase set to first (Dormienza)
        assert p.get("current_phase_id") is not None

        # phases list
        r2 = s.get(f"{API}/plants/{p['id']}/phases", timeout=10)
        assert r2.status_code == 200
        phases = r2.json()
        assert len(phases) == 14  # Melo -> pomacee
        # Assert ordering + risk fields
        assert phases[0]["phase_name"] == "Dormienza"
        assert phases[0]["risk_fungal"] == 0
        assert any(ph["phase_name"] == "Fioritura" for ph in phases)

        # list plants shows it with current_phase populated
        r3 = s.get(f"{API}/plants", timeout=10)
        assert r3.status_code == 200
        found = [x for x in r3.json() if x["id"] == p["id"]]
        assert len(found) == 1
        assert found[0].get("current_phase") is not None
        assert found[0]["current_phase"]["phase_name"] == "Dormienza"

        # GET /plants/{id} returns plant + phases + treatments
        r4 = s.get(f"{API}/plants/{p['id']}", timeout=10)
        assert r4.status_code == 200
        det = r4.json()
        assert det["plant"]["id"] == p["id"]
        assert len(det["phases"]) == 14
        assert det["treatments"] == []

        # set current phase to a risky one (Fioritura risk_fungal=3)
        risky = next(ph for ph in phases if ph["phase_name"] == "Fioritura")
        r5 = s.post(f"{API}/plants/{p['id']}/phase",
                    json={"phase_id": risky["id"]}, timeout=10)
        assert r5.status_code == 200
        # verify persisted
        r6 = s.get(f"{API}/plants", timeout=10)
        found = [x for x in r6.json() if x["id"] == p["id"]][0]
        assert found["current_phase"]["phase_name"] == "Fioritura"
        assert found["current_phase"]["risk_fungal"] == 3

        # soft delete
        r7 = s.delete(f"{API}/plants/{p['id']}", timeout=10)
        assert r7.status_code == 200
        r8 = s.get(f"{API}/plants", timeout=10)
        assert not any(x["id"] == p["id"] for x in r8.json())

    def test_plants_user_isolation(self, admin_session, fresh_user):
        r = admin_session.post(f"{API}/plants",
                               json={"name": "TEST Admin Pesco", "species": "Pesco",
                                     "emoji": "🍑"}, timeout=15)
        assert r.status_code == 200
        pid = r.json()["id"]
        s, _ = fresh_user
        r2 = s.get(f"{API}/plants", timeout=10)
        assert not any(x["id"] == pid for x in r2.json())
        admin_session.delete(f"{API}/plants/{pid}", timeout=10)

    def test_plants_requires_auth(self):
        r = requests.get(f"{API}/plants", timeout=10)
        assert r.status_code == 401


# --------------------------------------------------------- Products + compatibility
class TestProducts:
    def test_products_crud(self, fresh_user):
        s, _ = fresh_user
        payload = {"name": "TEST Poltiglia Bordolese", "category": "rame",
                   "active_ingredient": "Solfato di rame",
                   "persistence_days": 10, "carenza_days": 3,
                   "dose_per_hl": 500, "dose_unit": "g",
                   "leaching_threshold_mm": 20, "in_stock": True,
                   "notes": "test"}
        r = s.post(f"{API}/products", json=payload, timeout=10)
        assert r.status_code == 200
        prod = r.json()
        assert prod["name"] == payload["name"]
        assert prod["category"] == "rame"
        assert prod["in_stock"] is True
        pid = prod["id"]

        # list
        r = s.get(f"{API}/products", timeout=10)
        assert r.status_code == 200
        assert any(p["id"] == pid for p in r.json())

        # update / toggle stock
        upd = {**payload, "in_stock": False}
        r = s.put(f"{API}/products/{pid}", json=upd, timeout=10)
        assert r.status_code == 200
        r = s.get(f"{API}/products", timeout=10)
        got = [p for p in r.json() if p["id"] == pid][0]
        assert got["in_stock"] is False

        # delete (soft)
        r = s.delete(f"{API}/products/{pid}", timeout=10)
        assert r.status_code == 200
        r = s.get(f"{API}/products", timeout=10)
        assert not any(p["id"] == pid for p in r.json())


# --------------------------------------------------------- Engine cycle & recommendations
class TestEngineCycle:
    """End-to-end: plant + risky phase + compatible product => recommendation."""

    def test_full_cycle_creates_recommendation(self):
        """Fresh user -> Melo -> current phase Fioritura (risk 3) ->
        compatible rame product -> compatibility -> run cycle -> pending rec."""
        s = requests.Session()
        email = f"test_engine_{uuid.uuid4().hex[:8]}@frutteto.it"
        r = s.post(f"{API}/auth/register",
                   json={"name": "Engine T", "email": email, "password": "Passw0rd!"}, timeout=15)
        assert r.status_code == 200
        s.headers.update({"Authorization": f"Bearer {r.json()['token']}"})

        # create plant
        r = s.post(f"{API}/plants",
                   json={"name": "TEST Melo Eng", "species": "Melo", "emoji": "🍎"}, timeout=15)
        assert r.status_code == 200
        plant = r.json()
        plant_id = plant["id"]

        # get phases, set current to "Fioritura" (risk_fungal 3)
        phases = s.get(f"{API}/plants/{plant_id}/phases", timeout=10).json()
        risky = next(ph for ph in phases if ph["phase_name"] == "Fioritura")
        assert risky["risk_fungal"] >= 2
        r = s.post(f"{API}/plants/{plant_id}/phase",
                   json={"phase_id": risky["id"]}, timeout=10)
        assert r.status_code == 200

        # create rame product in stock
        r = s.post(f"{API}/products",
                   json={"name": "TEST Rame Eng", "category": "rame",
                         "persistence_days": 7, "carenza_days": 3,
                         "leaching_threshold_mm": 20, "in_stock": True},
                   timeout=10)
        assert r.status_code == 200
        prod = r.json()

        # add compatibility for plant+phase
        r = s.post(f"{API}/products/{prod['id']}/compatibility",
                   json={"plant_id": plant_id, "phase_id": risky["id"],
                         "priority": 1, "recommended": True}, timeout=10)
        assert r.status_code == 200

        # GET compatibility
        r = s.get(f"{API}/products/{prod['id']}/compatibility", timeout=10)
        assert r.status_code == 200
        assert len(r.json()) >= 1

        # run engine
        r = s.post(f"{API}/cycle/run", timeout=30)
        assert r.status_code == 200, r.text
        result = r.json()
        assert result["ok"] is True
        res = result["result"]
        assert set(["leached", "expired", "new_recommendations", "is_raining", "fungal_risk"]).issubset(res.keys())

        # If it's "raining" in the demo weather, engine skips generation.
        # If not, expect at least one rec to be produced.
        recs = s.get(f"{API}/recommendations?status=pending", timeout=10).json()
        # ensure recommendations endpoint works
        assert isinstance(recs, list)

        if not res["is_raining"]:
            # Now we should have at least 1 pending rec on THIS plant
            mine = [r for r in recs if r["plant_id"] == plant_id]
            assert len(mine) >= 1, f"No recommendations generated. Result={res} recs={recs}"
            rec = mine[0]
            assert rec["status"] == "pending"
            assert rec["reason_code"] in ("FUNGAL_RISK", "PHASE_RISK", "INSECT_RISK", "ACARID_RISK")
            assert "plant_name" in rec

            # Dismiss
            r = s.post(f"{API}/recommendations/{rec['id']}/dismiss", timeout=10)
            assert r.status_code == 200
            recs2 = s.get(f"{API}/recommendations?status=pending", timeout=10).json()
            assert not any(x["id"] == rec["id"] for x in recs2)
            dismissed = s.get(f"{API}/recommendations?status=dismissed", timeout=10).json()
            assert any(x["id"] == rec["id"] for x in dismissed)
        else:
            # rain path: an info alert should exist about rain_block
            alerts = s.get(f"{API}/alerts", timeout=10).json()
            assert any(a["type"] == "rain_block" for a in alerts)

    def test_cycle_with_no_compatible_product_creates_advisory(self):
        """No compatible product => engine still creates an advisory rec/alert about missing product."""
        s = requests.Session()
        email = f"test_engine2_{uuid.uuid4().hex[:8]}@frutteto.it"
        r = s.post(f"{API}/auth/register",
                   json={"name": "Engine T2", "email": email, "password": "Passw0rd!"}, timeout=15)
        assert r.status_code == 200
        s.headers.update({"Authorization": f"Bearer {r.json()['token']}"})

        r = s.post(f"{API}/plants",
                   json={"name": "TEST Vite Eng", "species": "Vite/Uva", "emoji": "🍇"}, timeout=15)
        assert r.status_code == 200
        plant_id = r.json()["id"]

        phases = s.get(f"{API}/plants/{plant_id}/phases", timeout=10).json()
        # pick phase with risk_fungal >=2 (Pre-fioritura)
        risky = next(ph for ph in phases if ph["risk_fungal"] >= 2)
        s.post(f"{API}/plants/{plant_id}/phase",
               json={"phase_id": risky["id"]}, timeout=10)

        r = s.post(f"{API}/cycle/run", timeout=30)
        assert r.status_code == 200
        res = r.json()["result"]

        recs = s.get(f"{API}/recommendations?status=pending", timeout=10).json()
        assert isinstance(recs, list)
        if not res["is_raining"]:
            mine = [rr for rr in recs if rr["plant_id"] == plant_id]
            assert len(mine) >= 1
            # No compatible product -> product_id should be None on the rec
            advisory = [rr for rr in mine if rr.get("product_id") in (None, "")]
            assert len(advisory) >= 1


# --------------------------------------------------------- Treatments
class TestTreatments:
    def test_treatment_lifecycle_and_supersede(self, fresh_user):
        s, _ = fresh_user
        # create plant + product
        pl = s.post(f"{API}/plants",
                    json={"name": "TEST Trat Pesco", "species": "Pesco",
                          "emoji": "🍑"}, timeout=15).json()
        prod = s.post(f"{API}/products",
                      json={"name": "TEST Fung A", "category": "fungicida",
                            "persistence_days": 5, "carenza_days": 2,
                            "leaching_threshold_mm": 15, "in_stock": True},
                      timeout=10).json()
        # first treatment
        r = s.post(f"{API}/treatments",
                   json={"plant_id": pl["id"], "product_id": prod["id"],
                         "dose_used": 300, "dose_unit": "g"}, timeout=15)
        assert r.status_code == 200, r.text
        t1 = r.json()
        assert t1["status"] == "valid"
        assert t1["expires_at"]  # persistence => expiry set
        assert t1["category"] == "fungicida"

        # list treatments
        lst = s.get(f"{API}/treatments", timeout=10).json()
        got = [t for t in lst if t["id"] == t1["id"]][0]
        assert got["plant_name"] == "TEST Trat Pesco"
        assert got["product_name"] == "TEST Fung A"

        # second same-category treatment supersedes first
        prod2 = s.post(f"{API}/products",
                       json={"name": "TEST Fung B", "category": "fungicida",
                             "persistence_days": 6, "carenza_days": 2,
                             "leaching_threshold_mm": 15, "in_stock": True},
                       timeout=10).json()
        r = s.post(f"{API}/treatments",
                   json={"plant_id": pl["id"], "product_id": prod2["id"]}, timeout=15)
        assert r.status_code == 200
        lst = s.get(f"{API}/treatments", timeout=10).json()
        first = [t for t in lst if t["id"] == t1["id"]][0]
        assert first["status"] == "superseded"

        # cleanup
        s.delete(f"{API}/plants/{pl['id']}", timeout=10)


# --------------------------------------------------------- Alerts
class TestAlerts:
    def test_alerts_flow(self, fresh_user):
        s, _ = fresh_user
        # ack-all (should be no-op even if empty)
        r = s.post(f"{API}/alerts/ack-all", timeout=10)
        assert r.status_code == 200
        r = s.get(f"{API}/alerts", timeout=10)
        assert r.status_code == 200
        # any unread alerts should be 0 after ack-all
        assert all(a.get("acknowledged") for a in r.json())


# --------------------------------------------------------- Weather / Irrigation
class TestWeatherIrrigation:
    def test_weather_latest_demo(self, fresh_user):
        s, _ = fresh_user
        r = s.get(f"{API}/weather/latest", timeout=15)
        assert r.status_code == 200
        w = r.json()
        assert w["source"] in ("demo", "ecowitt")
        for k in ("temp_c", "humidity_pct", "rainfall_rate_mmh", "wind_speed_ms"):
            assert k in w

    def test_weather_history_returns_array(self, fresh_user):
        s, _ = fresh_user
        # Trigger at least one read
        s.get(f"{API}/weather/latest", timeout=15)
        r = s.get(f"{API}/weather/history", timeout=10)
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list)
        if arr:
            row = arr[-1]
            for k in ("time", "temp", "humidity"):
                assert k in row

    def test_irrigation_status(self, fresh_user):
        s, _ = fresh_user
        r = s.get(f"{API}/irrigation/status", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "status" in d and "message" in d and "advice" in d
        assert d["status"] in ("no_data", "critical", "low", "ok", "high")


# --------------------------------------------------------- Config
class TestConfig:
    def test_get_and_put_config(self, fresh_user):
        s, _ = fresh_user
        r = s.get(f"{API}/config", timeout=10)
        assert r.status_code == 200
        cfg = r.json()
        for k in ("leaching_threshold_mm", "rain_block_mmh",
                  "soil_moisture_low_pct", "soil_moisture_critical_pct",
                  "ecowitt_app_key", "ecowitt_api_key", "ecowitt_mac"):
            assert k in cfg

        # update
        r = s.put(f"{API}/config",
                  json={"values": {"leaching_threshold_mm": "22",
                                   "ecowitt_mac": "AA:BB:CC:DD:EE:FF"}}, timeout=10)
        assert r.status_code == 200
        r = s.get(f"{API}/config", timeout=10)
        cfg = r.json()
        assert cfg["leaching_threshold_mm"] == "22"
        assert cfg["ecowitt_mac"] == "AA:BB:CC:DD:EE:FF"


# --------------------------------------------------------- AI (slow, one test only)
class TestAI:
    def test_ai_generate_phases(self, admin_session):
        """AI regen — may take up to 60s. Skips on network / LLM error."""
        # create a temporary plant on admin for AI test
        p = admin_session.post(f"{API}/plants",
                               json={"name": "TEST AI Melo", "species": "Melo",
                                     "emoji": "🍎"}, timeout=15).json()
        try:
            r = admin_session.post(f"{API}/plants/{p['id']}/generate-phases", timeout=90)
            if r.status_code == 502:
                pytest.skip(f"AI service unavailable: {r.text}")
            assert r.status_code == 200, r.text
            d = r.json()
            assert d.get("ok") is True
            assert isinstance(d.get("count"), int) and d["count"] >= 6
            # verify phases persisted
            phases = admin_session.get(f"{API}/plants/{p['id']}/phases", timeout=10).json()
            assert len(phases) == d["count"]
        finally:
            admin_session.delete(f"{API}/plants/{p['id']}", timeout=10)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
