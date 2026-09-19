import asyncio
from fastapi.testclient import TestClient
from main import app

def test_auth_flow():
    client = TestClient(app)
    
    print("Testing /api/v1/auth/login with default admin...")
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@ransomguard.io",
        "password": "admin123",
        "remember_me": True
    })
    print("Login Status:", res.status_code)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    token = data["access_token"]
    user = data["user"]
    print("Logged in as:", user["name"], "| Role:", user["role"])
    assert "access_token" in data
    assert user["email"] == "admin@ransomguard.io"
    
    print("\nTesting /api/v1/auth/me with Bearer token...")
    me_res = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    print("Me Status:", me_res.status_code)
    assert me_res.status_code == 200
    me_data = me_res.json()
    print("Me user verified:", me_data["email"], me_data["role"])
    
    print("\nTesting /api/v1/auth/register with a new user...")
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "analyst.test@ransomguard.io",
        "password": "securepassword123",
        "name": "Jane Analyst",
        "role": "SOC Incident Responder"
    })
    print("Register Status:", reg_res.status_code)
    assert reg_res.status_code in [200, 400] # 200 for new, 400 if already exists
    if reg_res.status_code == 200:
        reg_data = reg_res.json()
        print("Registered new user:", reg_data["user"]["name"])
    
    print("\nTesting /api/v1/auth/google...")
    goog_res = client.post("/api/v1/auth/google", json={
        "email": "google.user@ransomguard.io",
        "name": "Google SSO User"
    })
    print("Google SSO Status:", goog_res.status_code)
    assert goog_res.status_code == 200
    
    print("\nTesting invalid credentials rejection...")
    bad_res = client.post("/api/v1/auth/login", json={
        "email": "admin@ransomguard.io",
        "password": "wrongpassword"
    })
    print("Invalid login status:", bad_res.status_code)
    assert bad_res.status_code == 401
    
    print("\nAll auth tests passed successfully!")

if __name__ == "__main__":
    test_auth_flow()
