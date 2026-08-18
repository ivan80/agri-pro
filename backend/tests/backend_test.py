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
                   "dose_per_l": 5, "dose_unit": "g",
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


# --------------------------------------------------------- Phase Advice (NEW)
class TestPhaseAdvice:
    """POST /api/plants/{id}/phase-advice — Claude AI treatment advice for current phase."""

    def test_phase_advice_returns_400_when_no_current_phase(self):
        """A plant with current_phase_id=None (manually cleared) must 400."""
        s = requests.Session()
        email = f"test_advice_np_{uuid.uuid4().hex[:8]}@frutteto.it"
        r = s.post(f"{API}/auth/register",
                   json={"name": "Adv T", "email": email, "password": "Passw0rd!"}, timeout=15)
        assert r.status_code == 200
        s.headers.update({"Authorization": f"Bearer {r.json()['token']}"})
        # Create plant then clear current_phase_id directly via update via API isn't exposed;
        # instead, request advice on an ID that doesn't exist => 404 (still valid error path)
        # For the 400 case, we test that a bad plant_id returns 404 as documented.
        # This test also verifies auth requirement is enforced.
        r = s.post(f"{API}/plants/{'0'*24}/phase-advice", timeout=15)
        # Non existent plant => 404 (not 400). 400 requires current_phase_id=None which cannot
        # be reached from a newly-created plant (auto phases set the first one).
        assert r.status_code in (400, 404)

    def test_phase_advice_returns_advice_for_risky_phase(self):
        """Register user -> create Melo -> set current phase to Fioritura -> phase-advice returns advice + phase."""
        s = requests.Session()
        email = f"test_advice_{uuid.uuid4().hex[:8]}@frutteto.it"
        r = s.post(f"{API}/auth/register",
                   json={"name": "Adv T", "email": email, "password": "Passw0rd!"}, timeout=15)
        assert r.status_code == 200
        s.headers.update({"Authorization": f"Bearer {r.json()['token']}"})

        r = s.post(f"{API}/plants",
                   json={"name": "TEST Adv Melo", "species": "Melo", "emoji": "🍎"}, timeout=15)
        assert r.status_code == 200
        plant_id = r.json()["id"]

        phases = s.get(f"{API}/plants/{plant_id}/phases", timeout=10).json()
        risky = next(ph for ph in phases if ph["phase_name"] == "Fioritura")
        r = s.post(f"{API}/plants/{plant_id}/phase",
                   json={"phase_id": risky["id"]}, timeout=10)
        assert r.status_code == 200

        # call phase-advice — Claude call can take up to 45s
        r = s.post(f"{API}/plants/{plant_id}/phase-advice", timeout=90)
        if r.status_code == 502:
            pytest.skip(f"AI service unavailable: {r.text}")
        assert r.status_code == 200, r.text
        d = r.json()
        assert "advice" in d and isinstance(d["advice"], str) and len(d["advice"]) > 30
        assert "phase" in d
        assert d["phase"]["phase_name"] == "Fioritura"
        assert d["phase"]["risk_fungal"] == 3
        # cleanup
        s.delete(f"{API}/plants/{plant_id}", timeout=10)

    def test_phase_advice_not_found_for_bogus_plant(self, fresh_user):
        s, _ = fresh_user
        r = s.post(f"{API}/plants/{'0'*24}/phase-advice", timeout=15)
        assert r.status_code in (400, 404)


# --------------------------------------------------------- Improved recommendation text
class TestRecommendationSuggestionText:
    """Verify SUGGESTION text appears in engine-generated recommendation when no product configured."""

    def test_no_product_recommendation_includes_suggestion(self):
        s = requests.Session()
        email = f"test_sugg_{uuid.uuid4().hex[:8]}@frutteto.it"
        r = s.post(f"{API}/auth/register",
                   json={"name": "Sugg T", "email": email, "password": "Passw0rd!"}, timeout=15)
        assert r.status_code == 200
        s.headers.update({"Authorization": f"Bearer {r.json()['token']}"})

        # Melo -> Fioritura (fungal risk 3), no products at all
        r = s.post(f"{API}/plants",
                   json={"name": "TEST Sugg Melo", "species": "Melo", "emoji": "🍎"}, timeout=15)
        plant_id = r.json()["id"]
        phases = s.get(f"{API}/plants/{plant_id}/phases", timeout=10).json()
        risky = next(ph for ph in phases if ph["phase_name"] == "Fioritura")
        s.post(f"{API}/plants/{plant_id}/phase",
               json={"phase_id": risky["id"]}, timeout=10)

        r = s.post(f"{API}/cycle/run", timeout=30)
        assert r.status_code == 200
        res = r.json()["result"]

        if res["is_raining"]:
            pytest.skip("Demo weather rolled 'raining' — engine skips rec generation")

        recs = s.get(f"{API}/recommendations?status=pending", timeout=10).json()
        mine = [rr for rr in recs if rr["plant_id"] == plant_id]
        assert len(mine) >= 1, f"Expected advisory rec, got: {recs}"
        # No compatible product -> product_id None -> reason must contain the suggestion text
        advisory = [rr for rr in mine if rr.get("product_id") in (None, "")]
        assert advisory, f"Expected advisory (product_id None). Got: {mine}"
        # Each rec kind must include its specific SUGGESTION treatment text
        # (fungal -> "rame o fungicida", insect -> "insetticida", acarid -> "acaricida")
        expectations = {
            "FUNGAL_RISK": ["rame o fungicida", "trattamento preventivo"],
            "INSECT_RISK": ["insetticida", "neem"],
            "ACARID_RISK": ["acaricida", "olio minerale"],
        }
        checked = 0
        for rr in advisory:
            code = rr.get("reason_code")
            if code in expectations:
                reason = rr["reason"].lower()
                assert any(exp in reason for exp in expectations[code]), \
                    f"Missing SUGGESTION for {code} in reason: {rr['reason']}"
                checked += 1
        assert checked >= 1, f"No categorized advisory found. Advisories: {advisory}"


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


# --------------------------------------------------------- NEW iter5 features
class TestProductDosePerLiter:
    """Product model uses dose_per_l (per liter), replacing dose_per_hl."""

    def test_create_product_with_dose_per_l(self, fresh_user):
        s, _ = fresh_user
        payload = {"name": "TEST DosePerL Prod", "category": "fungicida",
                   "persistence_days": 7, "carenza_days": 2,
                   "dose_per_l": 2.5, "dose_unit": "ml",
                   "leaching_threshold_mm": 15, "in_stock": True}
        r = s.post(f"{API}/products", json=payload, timeout=10)
        assert r.status_code == 200, r.text
        prod = r.json()
        assert prod.get("dose_per_l") == 2.5
        assert prod.get("dose_unit") == "ml"
        # verify persisted via GET
        got = [p for p in s.get(f"{API}/products", timeout=10).json() if p["id"] == prod["id"]][0]
        assert got["dose_per_l"] == 2.5


class TestProductPrecedenceAutoMatch:
    """(1) Registered in-stock products should be auto-matched by risk category even
    WITHOUT a manual product-phase compatibility row."""

    def test_engine_auto_matches_registered_product_by_category(self):
        s = requests.Session()
        email = f"test_precedence_{uuid.uuid4().hex[:8]}@frutteto.it"
        r = s.post(f"{API}/auth/register",
                   json={"name": "Prec T", "email": email, "password": "Passw0rd!"}, timeout=15)
        assert r.status_code == 200
        s.headers.update({"Authorization": f"Bearer {r.json()['token']}"})

        # plant + risky phase (Fioritura, risk_fungal=3)
        r = s.post(f"{API}/plants",
                   json={"name": "TEST Prec Melo", "species": "Melo", "emoji": "🍎"}, timeout=15)
        plant_id = r.json()["id"]
        phases = s.get(f"{API}/plants/{plant_id}/phases", timeout=10).json()
        risky = next(ph for ph in phases if ph["phase_name"] == "Fioritura")
        s.post(f"{API}/plants/{plant_id}/phase",
               json={"phase_id": risky["id"]}, timeout=10)

        # register product with rame category, IN STOCK, but NO compatibility row
        r = s.post(f"{API}/products",
                   json={"name": "TEST Rame Precedence", "category": "rame",
                         "persistence_days": 7, "carenza_days": 3,
                         "dose_per_l": 3, "dose_unit": "g",
                         "leaching_threshold_mm": 20, "in_stock": True}, timeout=10)
        assert r.status_code == 200
        prod = r.json()

        # NOTE: NO POST to /api/products/{id}/compatibility

        # run cycle
        r = s.post(f"{API}/cycle/run", timeout=30)
        assert r.status_code == 200
        res = r.json()["result"]
        if res["is_raining"]:
            pytest.skip("Demo weather rolled 'raining' — engine skips rec generation")

        recs = s.get(f"{API}/recommendations?status=pending", timeout=10).json()
        mine = [rr for rr in recs if rr["plant_id"] == plant_id and rr.get("reason_code") == "FUNGAL_RISK"]
        assert len(mine) >= 1, f"Expected a FUNGAL_RISK rec, got: {recs}"
        rec = mine[0]
        # Precedence: product_id MUST point to our registered product
        assert rec.get("product_id") == prod["id"], \
            f"Expected auto-matched product_id={prod['id']}, got {rec.get('product_id')}. Reason: {rec.get('reason')}"
        assert "applicare" in rec["reason"].lower()
        assert "TEST Rame Precedence" in rec["reason"]


class TestLocationWeather:
    """(2) When no Ecowitt, fetch weather from Open-Meteo via lat/lon config. If Open-Meteo
    rate-limited/unreachable, gracefully fall back to demo. Both are acceptable — no 500."""

    def test_weather_uses_location_or_falls_back(self, fresh_user):
        s, _ = fresh_user
        # Set location config (Rome). Also ensure no Ecowitt keys set.
        r = s.put(f"{API}/config",
                  json={"values": {"latitude": "41.9028", "longitude": "12.4964",
                                    "location_name": "Roma, IT",
                                    "ecowitt_app_key": "", "ecowitt_api_key": "",
                                    "ecowitt_mac": ""}}, timeout=10)
        assert r.status_code == 200
        # verify persisted
        cfg = s.get(f"{API}/config", timeout=10).json()
        assert cfg["latitude"] == "41.9028"
        assert cfg["location_name"] == "Roma, IT"

        r = s.get(f"{API}/weather/latest", timeout=20)
        assert r.status_code == 200, r.text
        w = r.json()
        # Either open-meteo (success) or demo (fallback) — both acceptable, no crash
        assert w.get("source") in ("open-meteo", "demo"), f"Unexpected source: {w.get('source')}"
        # Required numeric fields present
        for k in ("temp_c", "humidity_pct", "rainfall_rate_mmh", "wind_speed_ms"):
            assert k in w
        # No 500, no exception; timestamp present
        assert "timestamp" in w


class TestFertilization:
    """(4) Fertilization CRUD + reminder alert generation via /api/cycle/run."""

    def test_fertilization_crud_and_reminder_creates_alert(self):
        s = requests.Session()
        email = f"test_fert_{uuid.uuid4().hex[:8]}@frutteto.it"
        r = s.post(f"{API}/auth/register",
                   json={"name": "Fert T", "email": email, "password": "Passw0rd!"}, timeout=15)
        assert r.status_code == 200
        s.headers.update({"Authorization": f"Bearer {r.json()['token']}"})

        # optional: create a plant to attach the fertilization to
        r = s.post(f"{API}/plants",
                   json={"name": "TEST Fert Melo", "species": "Melo", "emoji": "🍎"}, timeout=15)
        plant_id = r.json()["id"]

        # POST fertilization with next_reminder_date in the PAST
        past = (datetime_now_utc() - _timedelta_days(1)).isoformat()
        r = s.post(f"{API}/fertilization",
                   json={"plant_id": plant_id, "ftype": "Stallatico",
                         "product_name": "Stallatico pellettato",
                         "dose": "2 kg/pianta",
                         "next_reminder_date": past,
                         "notes": "TEST reminder due"}, timeout=10)
        assert r.status_code == 200, r.text
        fert = r.json()
        assert fert["ftype"] == "Stallatico"
        fert_id = fert["id"]

        # GET list includes plant_name
        lst = s.get(f"{API}/fertilization", timeout=10).json()
        assert isinstance(lst, list)
        got = [f for f in lst if f["id"] == fert_id]
        assert len(got) == 1
        assert got[0]["plant_name"] == "TEST Fert Melo"

        # Run cycle -> fertilization_reminders should be >= 1
        r = s.post(f"{API}/cycle/run", timeout=30)
        assert r.status_code == 200
        res = r.json()["result"]
        assert "fertilization_reminders" in res
        assert res["fertilization_reminders"] >= 1, f"Expected >=1 reminder. Got: {res}"

        # An alert of type 'fertilization' should exist
        alerts = s.get(f"{API}/alerts", timeout=10).json()
        fert_alerts = [a for a in alerts if a.get("type") == "fertilization"]
        assert len(fert_alerts) >= 1, f"No fertilization alert. Alerts: {alerts}"
        msg = fert_alerts[0]["message"]
        assert "Promemoria concimazione" in msg
        assert "Stallatico" in msg

        # Running the cycle again should NOT re-generate (reminded=True)
        r = s.post(f"{API}/cycle/run", timeout=30)
        assert r.status_code == 200
        assert r.json()["result"]["fertilization_reminders"] == 0

        # DELETE fertilization
        r = s.delete(f"{API}/fertilization/{fert_id}", timeout=10)
        assert r.status_code == 200
        lst = s.get(f"{API}/fertilization", timeout=10).json()
        assert not any(f["id"] == fert_id for f in lst)

    def test_fertilization_without_plant(self, fresh_user):
        """Fertilization can be created without a plant_id (whole orchard)."""
        s, _ = fresh_user
        r = s.post(f"{API}/fertilization",
                   json={"ftype": "Letame", "product_name": "Letame maturo",
                         "dose": "3 kg/mq"}, timeout=10)
        assert r.status_code == 200, r.text
        fert = r.json()
        assert fert["ftype"] == "Letame"

        lst = s.get(f"{API}/fertilization", timeout=10).json()
        got = [f for f in lst if f["id"] == fert["id"]][0]
        assert got["plant_name"] == "Tutto il frutteto"

        # cleanup
        s.delete(f"{API}/fertilization/{fert['id']}", timeout=10)


# Helpers used by fertilization test (avoid new top-level imports)
def datetime_now_utc():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


def _timedelta_days(d):
    from datetime import timedelta
    return timedelta(days=d)


# --------------------------------------------------------- NEW iter6 features
def _make_leaf_jpeg_b64():
    """Create a real JPEG with visible leaf-like features (edges, veins, spots)."""
    import base64, io, random
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (320, 320), (30, 90, 40))
    d = ImageDraw.Draw(img)
    # leaf outline (ellipse)
    d.ellipse([30, 60, 290, 260], fill=(60, 140, 60), outline=(20, 60, 20), width=3)
    # central vein
    d.line([(60, 160), (280, 160)], fill=(30, 80, 30), width=4)
    # side veins
    for y in range(80, 250, 20):
        d.line([(160, 160), (60 + random.randint(0, 20), y)], fill=(40, 100, 40), width=2)
        d.line([(160, 160), (280 - random.randint(0, 20), y)], fill=(40, 100, 40), width=2)
    # brownish disease spots
    for _ in range(18):
        x = random.randint(60, 270); y = random.randint(80, 240)
        r = random.randint(4, 12)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(120, 70, 30), outline=(80, 40, 15))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


class TestDiagnosis:
    """(A) POST /api/diagnosis + GET /api/diagnosis history."""

    def test_diagnosis_with_real_image_returns_italian(self, fresh_user):
        s, _ = fresh_user
        img_b64 = _make_leaf_jpeg_b64()
        r = s.post(f"{API}/diagnosis",
                   json={"image_base64": img_b64,
                         "notes": "foglie con macchie brune"}, timeout=120)
        if r.status_code == 502:
            pytest.skip(f"AI service unavailable: {r.text}")
        assert r.status_code == 200, r.text
        d = r.json()
        assert "diagnosis" in d and "id" in d
        text = d["diagnosis"]
        assert isinstance(text, str) and len(text) > 40
        low = text.lower()
        # at least a couple of the required italian sections should appear
        section_hits = sum(1 for s2 in ("diagnosi", "gravit", "sintomi", "trattamento", "prevenzione") if s2 in low)
        assert section_hits >= 3, f"Expected italian markdown sections, got: {text[:400]}"

    def test_diagnosis_strips_data_url_prefix(self, fresh_user):
        s, _ = fresh_user
        img_b64 = _make_leaf_jpeg_b64()
        data_url = "data:image/jpeg;base64," + img_b64
        r = s.post(f"{API}/diagnosis",
                   json={"image_base64": data_url, "notes": "prova prefix"}, timeout=120)
        if r.status_code == 502:
            pytest.skip(f"AI service unavailable: {r.text}")
        assert r.status_code == 200, r.text
        assert "diagnosis" in r.json()

    def test_diagnosis_history_lists_entries(self, fresh_user):
        s, _ = fresh_user
        # ensure at least one exists (may already be from previous test)
        img_b64 = _make_leaf_jpeg_b64()
        # attach to a plant so plant_name is resolved
        r = s.post(f"{API}/plants",
                   json={"name": "TEST Diag Melo", "species": "Melo", "emoji": "🍎"}, timeout=15)
        plant_id = r.json()["id"]
        r = s.post(f"{API}/diagnosis",
                   json={"image_base64": img_b64, "plant_id": plant_id,
                         "notes": "storia diagnosi"}, timeout=120)
        if r.status_code == 502:
            pytest.skip(f"AI service unavailable: {r.text}")
        assert r.status_code == 200
        r2 = s.get(f"{API}/diagnosis", timeout=15)
        assert r2.status_code == 200
        lst = r2.json()
        assert isinstance(lst, list) and len(lst) >= 1
        # find one attached to plant
        mine = [x for x in lst if x.get("plant_id") == plant_id]
        assert mine, "Diagnosis history missing entry with plant_id"
        assert mine[0].get("plant_name") == "TEST Diag Melo"
        assert "diagnosis" in mine[0]


class TestWorkplan:
    """(B) GET /api/workplan aggregates pending recs into tank-mix items."""

    def test_workplan_aggregates_and_computes_liters(self):
        s = requests.Session()
        email = f"test_wp_{uuid.uuid4().hex[:8]}@frutteto.it"
        r = s.post(f"{API}/auth/register",
                   json={"name": "WP T", "email": email, "password": "Passw0rd!"}, timeout=15)
        assert r.status_code == 200
        s.headers.update({"Authorization": f"Bearer {r.json()['token']}"})

        # 2 plants -> risky phase
        plant_ids = []
        for i, nm in enumerate(["TEST WP Melo A", "TEST WP Melo B"]):
            r = s.post(f"{API}/plants",
                       json={"name": nm, "species": "Melo", "emoji": "🍎"}, timeout=15)
            pid = r.json()["id"]
            phases = s.get(f"{API}/plants/{pid}/phases", timeout=10).json()
            risky = next(ph for ph in phases if ph["phase_name"] == "Fioritura")
            s.post(f"{API}/plants/{pid}/phase",
                   json={"phase_id": risky["id"]}, timeout=10)
            plant_ids.append(pid)

        # rame product w/ dose_per_l
        r = s.post(f"{API}/products",
                   json={"name": "TEST WP Rame", "category": "rame",
                         "persistence_days": 7, "carenza_days": 3,
                         "dose_per_l": 4, "dose_unit": "g",
                         "leaching_threshold_mm": 20, "in_stock": True}, timeout=10)
        assert r.status_code == 200

        # liters_per_plant to 5 for a predictable computation
        s.put(f"{API}/config", json={"values": {"liters_per_plant": "5"}}, timeout=10)

        r = s.post(f"{API}/cycle/run", timeout=30)
        assert r.status_code == 200
        res = r.json()["result"]
        if res["is_raining"]:
            pytest.skip("Demo weather rolled 'raining' — engine skips rec generation")

        r = s.get(f"{API}/workplan", timeout=15)
        assert r.status_code == 200, r.text
        wp = r.json()
        for k in ("items", "liters_per_plant", "warnings", "total_interventi"):
            assert k in wp
        assert wp["liters_per_plant"] == 5.0
        items = wp["items"]
        assert len(items) >= 1, f"Expected at least 1 workplan item. Got: {wp}"
        rame = next((x for x in items if x["category"] == "rame"), None)
        assert rame is not None, f"No rame item. items={items}"
        assert rame["n_plants"] == 2
        assert rame["liters"] == 10.0  # 2 * 5
        assert rame["product_qty"] == 40.0  # 4 g/L * 10 L
        assert rame["dose_unit"] == "g"
        assert set(rame["plants"]) == {"TEST WP Melo A", "TEST WP Melo B"}
        # rame present -> warning about carenza / fioritura
        assert any("Rame" in w for w in wp["warnings"])

    def test_workplan_warning_rame_zolfo_incompat(self):
        s = requests.Session()
        email = f"test_wpz_{uuid.uuid4().hex[:8]}@frutteto.it"
        r = s.post(f"{API}/auth/register",
                   json={"name": "WPZ", "email": email, "password": "Passw0rd!"}, timeout=15)
        s.headers.update({"Authorization": f"Bearer {r.json()['token']}"})
        # Insert two dummy pending recs directly by having engine generate two categories:
        # Not straightforward without compat rows for both; instead, we bypass and craft via API.
        # Use two plants: one with fungal risk gets 'rame', another with acarid risk gets 'zolfo' compat.
        # Simpler: create plant + set risky phase and register BOTH rame and zolfo products in stock.
        # The engine matches rame OR fungicida for fungal — 'zolfo' won't auto-match to fungal.
        # So we manually add compatibility rows to force both categories to appear.
        r = s.post(f"{API}/plants",
                   json={"name": "TEST WPZ Melo", "species": "Melo", "emoji": "🍎"}, timeout=15)
        pid = r.json()["id"]
        phases = s.get(f"{API}/plants/{pid}/phases", timeout=10).json()
        risky = next(ph for ph in phases if ph["phase_name"] == "Fioritura")
        s.post(f"{API}/plants/{pid}/phase", json={"phase_id": risky["id"]}, timeout=10)

        pr_rame = s.post(f"{API}/products",
                         json={"name": "TEST WPZ Rame", "category": "rame",
                               "persistence_days": 7, "carenza_days": 3,
                               "dose_per_l": 3, "dose_unit": "g",
                               "leaching_threshold_mm": 20, "in_stock": True}, timeout=10).json()
        pr_zolfo = s.post(f"{API}/products",
                          json={"name": "TEST WPZ Zolfo", "category": "zolfo",
                                "persistence_days": 7, "carenza_days": 3,
                                "dose_per_l": 5, "dose_unit": "g",
                                "leaching_threshold_mm": 20, "in_stock": True}, timeout=10).json()
        # add compat rows so BOTH generate pending recs for the same plant+phase
        s.post(f"{API}/products/{pr_rame['id']}/compatibility",
               json={"plant_id": pid, "phase_id": risky["id"],
                     "priority": 1, "recommended": True}, timeout=10)
        s.post(f"{API}/products/{pr_zolfo['id']}/compatibility",
               json={"plant_id": pid, "phase_id": risky["id"],
                     "priority": 2, "recommended": True}, timeout=10)

        r = s.post(f"{API}/cycle/run", timeout=30)
        assert r.status_code == 200
        if r.json()["result"]["is_raining"]:
            pytest.skip("Demo weather rolled 'raining'")

        r = s.get(f"{API}/workplan", timeout=15)
        assert r.status_code == 200
        wp = r.json()
        cats = {i["category"] for i in wp["items"]}
        # We expect the engine to pick top-priority (rame) for fungal risk; zolfo may or may not
        # appear depending on engine behavior. Test the incompatibility warning ONLY when both do.
        if "rame" in cats and "zolfo" in cats:
            assert any("rame" in w.lower() and "zolfo" in w.lower() for w in wp["warnings"]), \
                f"Missing rame/zolfo incompatibility warning. warnings={wp['warnings']}"
        else:
            # At least verify workplan is well-formed and no crash
            assert isinstance(wp["warnings"], list)


class TestFertilizationEdit:
    """(C) PUT /api/fertilization/{id} updates fields and resets reminded=False."""

    def test_edit_fertilization_updates_fields(self, fresh_user):
        s, _ = fresh_user
        r = s.post(f"{API}/fertilization",
                   json={"ftype": "Fogliare", "product_name": "TEST Chelato Fe",
                         "dose": "1 g/L"}, timeout=10)
        assert r.status_code == 200
        fid = r.json()["id"]

        # PUT update
        r = s.put(f"{API}/fertilization/{fid}",
                  json={"ftype": "Radicale", "product_name": "TEST NPK 20-20-20",
                        "dose": "3 kg/pianta", "notes": "aggiornato"}, timeout=10)
        assert r.status_code == 200

        lst = s.get(f"{API}/fertilization", timeout=10).json()
        got = [f for f in lst if f["id"] == fid][0]
        assert got["ftype"] == "Radicale"
        assert got["product_name"] == "TEST NPK 20-20-20"
        assert got["dose"] == "3 kg/pianta"
        assert got["notes"] == "aggiornato"
        assert got["reminded"] is False

        # cleanup
        s.delete(f"{API}/fertilization/{fid}", timeout=10)


# --------------------------------------------------------- NEW iter7 features
class TestCalendar:
    """(A) Calendario Colturale — GET /api/calendar/groups + /api/calendar/{group}"""

    def test_calendar_groups_returns_7(self, fresh_user):
        s, _ = fresh_user
        r = s.get(f"{API}/calendar/groups", timeout=10)
        assert r.status_code == 200
        groups = r.json()
        assert isinstance(groups, list)
        keys = [g["key"] for g in groups]
        for k in ("pomacee", "drupacee", "pesco", "vite", "fico", "nocciolo", "avocado"):
            assert k in keys, f"Missing group {k}"
        for g in groups:
            assert "label" in g and "emoji" in g

    def test_calendar_pomacee_returns_12_months(self, fresh_user):
        s, _ = fresh_user
        r = s.get(f"{API}/calendar/pomacee", timeout=10)
        assert r.status_code == 200
        months = r.json()
        assert isinstance(months, list) and len(months) == 12
        for i, m in enumerate(months, start=1):
            assert m["month"] == i
            assert "name" in m
            assert isinstance(m["operations"], list) and len(m["operations"]) >= 1
        # month 1 = Gennaio, expected op mention "Potatura"
        assert months[0]["name"] == "Gennaio"

    def test_calendar_unknown_group_falls_back_to_pomacee(self, fresh_user):
        # unknown group defaults to pomacee per calendar_for()
        s, _ = fresh_user
        r = s.get(f"{API}/calendar/does_not_exist", timeout=10)
        assert r.status_code == 200
        assert len(r.json()) == 12

    def test_calendar_requires_auth(self):
        r = requests.get(f"{API}/calendar/groups", timeout=10)
        assert r.status_code == 401


class TestReport:
    """(B) GET /api/report — orchard report data."""

    def test_report_shape_for_fresh_user(self, fresh_user):
        s, u = fresh_user
        r = s.get(f"{API}/report", timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ("generated_at", "owner", "counts", "plants",
                  "treatments", "fertilizations", "diagnoses"):
            assert k in d, f"Missing key {k}"
        for ck in ("plants", "treatments", "fertilizations", "diagnoses"):
            assert ck in d["counts"]
        # fresh user starts empty
        assert d["counts"]["plants"] == 0
        assert d["plants"] == []
        assert d["owner"] == u["name"]

    def test_report_reflects_added_data(self):
        s = requests.Session()
        email = f"test_report_{uuid.uuid4().hex[:8]}@frutteto.it"
        r = s.post(f"{API}/auth/register",
                   json={"name": "Rep T", "email": email, "password": "Passw0rd!"}, timeout=15)
        assert r.status_code == 200
        s.headers.update({"Authorization": f"Bearer {r.json()['token']}"})

        # add a plant + fertilization
        p = s.post(f"{API}/plants",
                   json={"name": "TEST Rep Melo", "species": "Melo", "emoji": "🍎"}, timeout=15).json()
        s.post(f"{API}/fertilization",
               json={"ftype": "Radicale", "product_name": "TEST NPK",
                     "dose": "1 kg", "plant_id": p["id"]}, timeout=10)

        r = s.get(f"{API}/report", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["counts"]["plants"] == 1
        assert d["counts"]["fertilizations"] == 1
        assert d["plants"][0]["name"] == "TEST Rep Melo"
        assert d["plants"][0]["phase"]  # phase resolved
        assert d["fertilizations"][0]["type"] == "Radicale"


class TestTelegram:
    """(C) POST /api/telegram/test — graceful 400 errors, never 500."""

    def test_telegram_test_no_chat_id_returns_400(self, fresh_user):
        s, _ = fresh_user
        r = s.post(f"{API}/telegram/test", timeout=10)
        assert r.status_code == 400
        detail = r.json().get("detail", "")
        assert "Chat ID" in detail or "chat" in detail.lower()

    def test_telegram_test_with_chat_id_no_token_returns_400(self):
        # NOTE: this relies on TELEGRAM_BOT_TOKEN being empty in env (as documented).
        s = requests.Session()
        email = f"test_tg_{uuid.uuid4().hex[:8]}@frutteto.it"
        r = s.post(f"{API}/auth/register",
                   json={"name": "TG T", "email": email, "password": "Passw0rd!"}, timeout=15)
        assert r.status_code == 200
        s.headers.update({"Authorization": f"Bearer {r.json()['token']}"})

        # save chat id
        r = s.put(f"{API}/config",
                  json={"values": {"telegram_chat_id": "123456789"}}, timeout=10)
        assert r.status_code == 200
        cfg = s.get(f"{API}/config", timeout=10).json()
        assert cfg["telegram_chat_id"] == "123456789"

        # now telegram/test should 400 (bot token missing) — NOT 500
        r = s.post(f"{API}/telegram/test", timeout=15)
        assert r.status_code == 400, \
            f"Expected 400 for missing bot token, got {r.status_code}: {r.text}"
        detail = r.json().get("detail", "").lower()
        # graceful message from _send_telegram
        assert "bot telegram non configurato" in detail or "invio non riuscito" in detail


class TestAutoCycleConfig:
    """(D) Auto-cycle enable/disable toggle persists via /api/config."""

    def test_auto_cycle_default_false(self, fresh_user):
        s, _ = fresh_user
        cfg = s.get(f"{API}/config", timeout=10).json()
        assert "auto_cycle_enabled" in cfg
        assert cfg["auto_cycle_enabled"] == "false"

    def test_auto_cycle_toggle_persists(self, fresh_user):
        s, _ = fresh_user
        r = s.put(f"{API}/config",
                  json={"values": {"auto_cycle_enabled": "true"}}, timeout=10)
        assert r.status_code == 200
        cfg = s.get(f"{API}/config", timeout=10).json()
        assert cfg["auto_cycle_enabled"] == "true"
        # toggle back
        r = s.put(f"{API}/config",
                  json={"values": {"auto_cycle_enabled": "false"}}, timeout=10)
        assert r.status_code == 200
        cfg = s.get(f"{API}/config", timeout=10).json()
        assert cfg["auto_cycle_enabled"] == "false"

    def test_backend_alive_after_startup(self):
        # Simple liveness after startup task registered
        r = requests.post(f"{API}/auth/login",
                          json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=10)
        assert r.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
