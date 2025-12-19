from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_and_process_payment():
    # 1. Create Payment
    response = client.post("/api/v1/payments", json={"amount": 100.0, "currency": "USD"})
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 100.0
    assert data["status"] == "PENDING"
    payment_id = data["id"]

    # 2. Process Payment
    response = client.post(f"/api/v1/payments/{payment_id}/process")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"

def test_failed_payment_large_amount():
    # 1. Create Large Payment
    response = client.post("/api/v1/payments", json={"amount": 5000.0, "currency": "USD"})
    assert response.status_code == 200
    payment_id = response.json()["id"]

    # 2. Process Payment (Should fail in mock gateway)
    response = client.post(f"/api/v1/payments/{payment_id}/process")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "FAILED"
