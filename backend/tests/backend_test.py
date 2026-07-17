"""Backend integration tests for Pomario / Frutteto Manager API.

Coverage:
- Auth (register, login, me, logout) with httpOnly cookie
- Plants CRUD (per-user isolation)
- Irrigation create + list
- Stats
- Weather (demo fallback), weather/settings
- Phases (6 phases), Plans (3 plans)
- AI advisor (Emergent LLM / Claude)
"""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://agri-track-pro-3.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@frutteto.it"
ADMIN_PASSWORD = "Frutteto2026!"


# ------------------------------------------------------------- fixtures
@pytest.fixture(scope="session")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="session")
def fresh_user():
    """Register a fresh user and return (session, user_dict)."""
    s = requests.Session()
    email = f"TEST_user_{uuid.uuid4().hex[:8]}@frutteto.it"
    payload = {"name": "TEST User", "email": email, "password": "Passw0rd!"}
    r = s.post(f"{API}/auth/register", json=payload, timeout=15)
    assert r.status_code == 200, f"Register failed: {r.status_code} {r.text}"
    data = r.json()
    return s, data


# ------------------------------------------------------------- Auth
class TestAuth:
    def test_login_admin(self, admin_session):
        r = admin_session.get(f"{API}/auth/me", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == ADMIN_EMAIL
        assert data.get("role") == "admin"
        assert "id" in data
        assert "password_hash" not in data

    def test_register_returns_user_with_trial(self, fresh_user):
        _, user = fresh_user
        assert user["plan"] == "trial"
        assert "trial_ends" in user
        assert user["email"].startswith("test_user_")  # lowercased
        assert "id" in user

    def test_register_sets_cookie(self, fresh_user):
        session, _ = fresh_user
        # After register, cookie should be set → /auth/me works
        r = session.get(f"{API}/auth/me", timeout=10)
        assert r.status_code == 200

    def test_register_duplicate_email(self):
        s = requests.Session()
        email = f"TEST_dup_{uuid.uuid4().hex[:8]}@frutteto.it"
        r1 = s.post(f"{API}/auth/register", json={"name": "A", "email": email, "password": "Passw0rd!"}, timeout=15)
        assert r1.status_code == 200
        s2 = requests.Session()
        r2 = s2.post(f"{API}/auth/register", json={"name": "A", "email": email, "password": "Passw0rd!"}, timeout=15)
        assert r2.status_code == 400

    def test_login_invalid_credentials(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"}, timeout=10)
        assert r.status_code == 401

    def test_me_unauthenticated(self):
        r = requests.get(f"{API}/auth/me", timeout=10)
        assert r.status_code == 401

    def test_logout_clears_cookie(self):
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=10)
        assert r.status_code == 200
        r2 = s.post(f"{API}/auth/logout", timeout=10)
        assert r2.status_code == 200
        # after logout, cookie removed → me should fail
        r3 = s.get(f"{API}/auth/me", timeout=10)
        assert r3.status_code == 401

    # -------- Bearer / token flow (bug fix verification) --------
    def test_login_returns_token_and_cookie(self):
        r = requests.post(
            f"{API}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert "token" in data and isinstance(data["token"], str) and len(data["token"]) > 20
        assert data["email"] == ADMIN_EMAIL
        # httpOnly cookie also set
        assert "access_token" in r.cookies, f"cookies: {r.cookies.items()}"

    def test_register_returns_token(self):
        email = f"TEST_tok_{uuid.uuid4().hex[:8]}@frutteto.it"
        r = requests.post(
            f"{API}/auth/register",
            json={"name": "Tok User", "email": email, "password": "Passw0rd!"},
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert "token" in data and isinstance(data["token"], str) and len(data["token"]) > 20
        assert "access_token" in r.cookies

    def test_me_via_bearer_only_no_cookie(self):
        """Simulate a browser that blocks the SameSite=None cookie: use Bearer only."""
        # Login WITHOUT persisting cookies
        r = requests.post(
            f"{API}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10,
        )
        assert r.status_code == 200
        token = r.json()["token"]

        # Fresh call WITHOUT any cookie jar → only Authorization: Bearer
        r2 = requests.get(
            f"{API}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        assert r2.status_code == 200, r2.text
        assert r2.json()["email"] == ADMIN_EMAIL

    def test_me_with_invalid_bearer(self):
        r = requests.get(
            f"{API}/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
            timeout=10,
        )
        assert r.status_code == 401


# ------------------------------------------------------------- Plants CRUD
class TestPlants:
    def test_plants_crud_flow(self, fresh_user):
        session, _ = fresh_user
        # List starts empty
        r = session.get(f"{API}/plants", timeout=10)
        assert r.status_code == 200
        initial = r.json()
        assert isinstance(initial, list)

        # Create
        payload = {"name": "TEST Melo", "species": "Malus domestica",
                   "variety": "Gala", "planted_year": 2020, "quantity": 3, "phase": "fioritura",
                   "notes": "test note"}
        r = session.post(f"{API}/plants", json=payload, timeout=10)
        assert r.status_code == 200
        created = r.json()
        assert created["name"] == payload["name"]
        assert created["species"] == payload["species"]
        assert "id" in created
        plant_id = created["id"]

        # Get list contains
        r = session.get(f"{API}/plants", timeout=10)
        assert r.status_code == 200
        found = [p for p in r.json() if p["id"] == plant_id]
        assert len(found) == 1
        assert found[0]["name"] == "TEST Melo"

        # Update
        upd = {**payload, "phase": "maturazione", "quantity": 5}
        r = session.put(f"{API}/plants/{plant_id}", json=upd, timeout=10)
        assert r.status_code == 200
        assert r.json()["phase"] == "maturazione"
        assert r.json()["quantity"] == 5

        # Delete
        r = session.delete(f"{API}/plants/{plant_id}", timeout=10)
        assert r.status_code == 200
        r = session.get(f"{API}/plants", timeout=10)
        assert not any(p["id"] == plant_id for p in r.json())

    def test_plants_user_isolation(self, admin_session, fresh_user):
        # admin creates plant, fresh_user should not see it
        r = admin_session.post(f"{API}/plants", json={"name": "TEST Admin Pesco", "species": "Prunus persica", "quantity": 1}, timeout=10)
        assert r.status_code == 200
        admin_plant_id = r.json()["id"]

        user_session, _ = fresh_user
        r = user_session.get(f"{API}/plants", timeout=10)
        assert not any(p["id"] == admin_plant_id for p in r.json())

        # cleanup
        admin_session.delete(f"{API}/plants/{admin_plant_id}", timeout=10)

    def test_plants_requires_auth(self):
        r = requests.get(f"{API}/plants", timeout=10)
        assert r.status_code == 401


# ------------------------------------------------------------- Irrigation & Stats
class TestIrrigation:
    def test_irrigation_create_and_list(self, fresh_user):
        session, _ = fresh_user
        payload = {"liters": 25.5, "duration_min": 30, "method": "goccia"}
        r = session.post(f"{API}/irrigation", json=payload, timeout=10)
        assert r.status_code == 200
        ev = r.json()
        assert ev["liters"] == 25.5
        assert "id" in ev
        assert "date" in ev

        r = session.get(f"{API}/irrigation", timeout=10)
        assert r.status_code == 200
        assert any(x["id"] == ev["id"] for x in r.json())

    def test_stats(self, fresh_user):
        session, _ = fresh_user
        r = session.get(f"{API}/stats", timeout=10)
        assert r.status_code == 200
        data = r.json()
        for key in ("plants", "species", "irrigation_events", "total_liters"):
            assert key in data
        assert isinstance(data["plants"], int)
        assert isinstance(data["total_liters"], (int, float))
        assert data["irrigation_events"] >= 1  # we created one above
        assert data["total_liters"] >= 25.5


# ------------------------------------------------------------- Weather
class TestWeather:
    def test_weather_demo_fallback(self, fresh_user):
        session, _ = fresh_user
        r = session.get(f"{API}/weather", timeout=15)
        assert r.status_code == 200
        w = r.json()
        assert w["source"] == "demo"
        assert "current" in w and "history" in w
        assert isinstance(w["history"], list)
        assert len(w["history"]) == 24
        cur = w["current"]
        for k in ("temp", "humidity", "pressure", "wind_speed"):
            assert k in cur

    def test_weather_settings_lifecycle(self, fresh_user):
        session, _ = fresh_user
        r = session.get(f"{API}/weather/settings", timeout=10)
        assert r.status_code == 200
        assert r.json()["configured"] is False

        r = session.post(f"{API}/weather/settings",
                         json={"application_key": "TEST_app", "api_key": "TEST_api", "mac": "AA:BB:CC:DD:EE:FF"},
                         timeout=10)
        assert r.status_code == 200
        assert r.json()["configured"] is True
        assert r.json()["mac"] == "AA:BB:CC:DD:EE:FF"

        r = session.get(f"{API}/weather/settings", timeout=10)
        assert r.json()["configured"] is True


# ------------------------------------------------------------- Reference data
class TestReference:
    def test_phases(self):
        r = requests.get(f"{API}/phases", timeout=10)
        assert r.status_code == 200
        phases = r.json()
        assert isinstance(phases, list)
        assert len(phases) == 6
        keys = [p["key"] for p in phases]
        assert set(keys) == {"riposo", "gemme", "fioritura", "allegagione", "accrescimento", "maturazione"}

    def test_plans(self):
        r = requests.get(f"{API}/plans", timeout=10)
        assert r.status_code == 200
        plans = r.json()
        assert len(plans) == 3
        ids = [p["id"] for p in plans]
        assert set(ids) == {"trial", "annual", "lifetime"}


# ------------------------------------------------------------- AI Advisor
class TestAdvisor:
    def test_advisor_returns_italian_answer(self, admin_session):
        payload = {"question": "Quando devo potare un melo?"}
        # AI can be slow
        r = admin_session.post(f"{API}/ai/advisor", json=payload, timeout=60)
        assert r.status_code == 200, f"Advisor error: {r.status_code} {r.text}"
        data = r.json()
        assert "answer" in data
        assert isinstance(data["answer"], str)
        assert len(data["answer"].strip()) > 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
