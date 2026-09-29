import pytest
import asyncio
import httpx
from main import app
from services.db_service import init_db

class SimpleTestClient:
    def __init__(self, asgi_app):
        self.transport = httpx.ASGITransport(app=asgi_app)
        self.base_url = "http://testserver"

    def _run(self, coro):
        return asyncio.run(coro)

    def get(self, url, headers=None, follow_redirects=True):
        async def _req():
            async with httpx.AsyncClient(transport=self.transport, base_url=self.base_url) as client:
                return await client.get(url, headers=headers, follow_redirects=follow_redirects)
        return self._run(_req())

    def post(self, url, json=None, data=None, headers=None, follow_redirects=True):
        async def _req():
            async with httpx.AsyncClient(transport=self.transport, base_url=self.base_url) as client:
                return await client.post(url, json=json, data=data, headers=headers, follow_redirects=follow_redirects)
        return self._run(_req())

client = SimpleTestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema is initialized before each test run"""
    init_db()

def test_health_check():
    """Test health and diagnostic endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "PocketSmart AI"
    assert "gemini" in data

def test_landing_and_public_pages():
    """Test public HTML pages load with 200 OK"""
    for path in ["/", "/testimonials", "/home-planner", "/party-planner", "/jewelry-planner", "/login", "/register"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "PocketSmart" in response.text

def test_user_registration_and_login():
    """Test user registration, token generation, and login endpoints"""
    import uuid
    rand_user = f"tester_{uuid.uuid4().hex[:6]}"
    email = f"{rand_user}@example.com"
    pwd = "secretpassword123"

    # 1. Register API
    reg_response = client.post("/register", json={
        "username": rand_user,
        "email": email,
        "full_name": "Test Runner",
        "password": pwd
    }, headers={"Accept": "application/json"})
    assert reg_response.status_code == 200
    reg_data = reg_response.json()
    assert reg_data["status"] == "success"
    assert "access_token" in reg_data
    token = reg_data["access_token"]

    # 2. Login API
    login_response = client.post("/login", json={
        "username": rand_user,
        "password": pwd
    }, headers={"Accept": "application/json"})
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["status"] == "success"
    assert "access_token" in login_data

    # 3. Session info API with bearer token
    session_res = client.get("/session-info", headers={"Authorization": f"Bearer {token}"})
    assert session_res.status_code == 200
    sess_data = session_res.json()
    assert sess_data["authenticated"] is True
    assert sess_data["user"]["username"] == rand_user

def test_generate_home_recommendations_api():
    """Scenario 1: Test Home Interior Planning with Smart Budget Allocation"""
    payload = {
        "total_budget": 75000,
        "currency": "INR",
        "room_types": ["Living Room", "Dining Area"],
        "style_preference": "Modern Minimalist",
        "color_palette": "Beige and Teak",
        "items_needed": [
            {"item_name": "Ceiling Fan", "quantity": 2},
            {"item_name": "Dining Table Set", "quantity": 1}
        ],
        "notes": "Prefer energy efficient appliances"
    }
    response = client.post("/generate-home", json=payload, headers={"Accept": "application/json"})
    assert response.status_code == 200
    data = response.json()
    assert data["plan_type"] == "home"
    assert "total_budget" in data
    assert data["total_budget"] == 75000
    assert "categories" in data
    assert len(data["categories"]) > 0
    assert "all_items" in data
    assert len(data["all_items"]) > 0
    assert data["total_estimated_cost"] <= data["total_budget"] + 1000

def test_generate_party_recommendations_api():
    """Scenario 2: Test AI-Based Party Budget Planning"""
    payload = {
        "total_budget": 35000,
        "currency": "INR",
        "event_type": "Birthday Celebration",
        "guest_count": 30,
        "venue_type": "OYO Townhouse / Party Suite",
        "food_preference": "Multi-Cuisine Buffet",
        "decoration_theme": "Golden Fairy Lights",
        "entertainment_needed": True
    }
    response = client.post("/generate-party", json=payload, headers={"Accept": "application/json"})
    assert response.status_code == 200
    data = response.json()
    assert data["plan_type"] == "party"
    assert data["total_budget"] == 35000
    assert "categories" in data
    assert any("catering" in c["category_name"].lower() or "food" in c["category_name"].lower() for c in data["categories"])
    assert any("venue" in c["category_name"].lower() for c in data["categories"])

def test_generate_jewelry_recommendations_api():
    """Scenario 3: Test Jewelry Recommendations with Style Matching"""
    payload = {
        "total_budget": 25000,
        "currency": "INR",
        "occasion": "Wedding Reception",
        "style_preference": "Antique Temple Gold",
        "jewelry_types": ["Necklace", "Earrings", "Bangles/Bracelets"],
        "outfit_color": "Royal Crimson Red & Gold",
        "outfit_type": "Silk Kanjeevaram Saree"
    }
    response = client.post("/generate-jewelry", json=payload, headers={"Accept": "application/json"})
    assert response.status_code == 200
    data = response.json()
    assert data["plan_type"] == "jewelry"
    assert data["total_budget"] == 25000
    assert "all_items" in data
    assert len(data["all_items"]) > 0

def test_history_and_details():
    """Test recommendations history listing and details view"""
    hist_response = client.get("/api/history")
    assert hist_response.status_code == 200
    hist_data = hist_response.json()
    assert "data" in hist_data
    if len(hist_data["data"]) > 0:
        first_id = hist_data["data"][0]["id"]
        detail_res = client.get(f"/recommendations-details?id={first_id}")
        assert detail_res.status_code == 200
