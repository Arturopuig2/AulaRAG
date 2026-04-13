import requests
import json
import sqlite3
import os

BASE_URL = "http://localhost:8001"
DB_PATH = "/Users/arturo/Desktop/Aula_RAG/AulaRAG/data/aula_rag.db"

def setup_test_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Ensure arturo@test.com exists as admin with password 'testpass'
    hashed_pwd = "$2b$12$AK8uPKPnibviPlzoMMqry.bdJ6J3MUe9AT74iLLvDELgDPnDGKc/G"
    c.execute("UPDATE users SET hashed_password = ?, is_admin = 1 WHERE email = 'arturo@test.com'", (hashed_pwd,))
    if c.rowcount == 0:
        c.execute("INSERT INTO users (email, name, hashed_password, is_admin) VALUES ('arturo@test.com', 'Arturo Admin', ?, 1)", (hashed_pwd,))
    
    # Create a non-admin user
    c.execute("INSERT OR IGNORE INTO users (email, name, hashed_password, is_admin) VALUES ('user@test.com', 'User', 'nopass', 0)")
    conn.commit()
    conn.close()

def get_token(email, password):
    resp = requests.post(f"{BASE_URL}/auth/token", data={"username": email, "password": password})
    if resp.status_code == 200:
        return resp.json()["access_token"]
    print(f"DEBUG: Token failed with {resp.status_code}: {resp.text}")
    return None

def test_admin_access():
    print("Testing admin access security...")
    
    admin_token = get_token("arturo@test.com", "testpass")
    if not admin_token:
        print("❌ Could not get admin token. Check if server is running on :8001")
        return

    # 1. Check admin can access
    resp = requests.get(f"{BASE_URL}/api/admin/questions", headers={"Authorization": f"Bearer {admin_token}"})
    if resp.status_code == 200:
        print("✅ Admin can access questions API")
    else:
        print(f"❌ Admin access failed: {resp.status_code}")

    # 2. Check CRUD for Explanations
    print("Testing Explanation CRUD...")
    exp_data = {
        "subject": "matematicas",
        "contenido": "Las Divisiones",
        "explanation": "La división es repartir algo en partes iguales. Por ejemplo, si tienes 10 caramelos y 2 amigos..."
    }
    resp = requests.post(f"{BASE_URL}/api/admin/explanations", json=exp_data, headers={"Authorization": f"Bearer {admin_token}"})
    if resp.status_code == 200:
        print("✅ Explanation created/updated")
    else:
        print(f"❌ Explanation creation failed: {resp.status_code}")

    # 3. Check Adaptive Logic
    print("Testing Adaptive Logic (Chat)...")
    chat_data = {
        "message": "Quiero repasar el tema de Las Divisiones",
        "subject": "matematicas"
    }
    # Direct form post to /chat
    resp = requests.post(f"{BASE_URL}/chat", data=chat_data, cookies={"access_token": admin_token})
    if resp.status_code == 200:
        text = resp.json().get("response", "")
        if "repartir" in text.lower() or "caramelos" in text.lower():
            print("✅ AI used DB Explanation for adaptation")
        else:
            print(f"❌ AI did not seem to use DB Explanation. Response: {text[:100]}...")
    else:
        print(f"❌ Chat failed: {resp.status_code}")

if __name__ == "__main__":
    setup_test_users()
    test_admin_access()
