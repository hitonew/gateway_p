from fastapi.testclient import TestClient
from app.main import app
from app.adapters.api.dependencies import get_transfer_connector
from app.core.connectors.interface import ConnectorIntegration
from app.core.payments.types import ConnectorResponse, PaymentState


class StubConnector(ConnectorIntegration):
    async def build_request(self, data):
        return {"originId": data.origin_id or "test-origin"}

    async def execute_request(self, request):
        return {"statusCode": 0, "requestEcho": request}

    async def handle_response(self, response):
        return ConnectorResponse(
            status=PaymentState.AUTHORIZED,
            provider_reference_id=response["requestEcho"]["originId"],
            raw_response=response,
        )


def override_connector():
    return StubConnector()


app.dependency_overrides[get_transfer_connector] = override_connector

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


def test_register_transfer_request():
    payload = {
        "source": {
            "addressType": "CBU_CVU",
            "address": "0000000000000000000000",
            "owner": {
                "personIdType": "CUI",
                "personId": "20304050607",
                "personName": "John Doe",
            },
        },
        "destination": {
            "addressType": "CBU_CVU",
            "address": "9999999999999999999999",
            "owner": {
                "personIdType": "CUI",
                "personId": "20987654321",
                "personName": "Jane Roe",
            },
        },
        "body": {
            "amount": "123.45",
            "currency": "ARS",
            "description": "Test transfer",
            "concept": "VAR",
        },
    }

    response = client.post("/api/v1/transfers", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "AUTHORIZED"
    assert body["originId"]
    assert body["paymentId"]

    echoed = body["echoed_request"]
    assert echoed["source"]["addressType"] == payload["source"]["addressType"]
    assert echoed["source"]["address"] == payload["source"]["address"]
    assert echoed["source"]["owner"] == payload["source"]["owner"]
    assert echoed["destination"] == payload["destination"]
    assert echoed["body"]["currency"] == payload["body"]["currency"]
    assert echoed["body"]["description"] == payload["body"]["description"]
    assert echoed["body"]["concept"] == payload["body"]["concept"]
    assert str(echoed["body"]["amount"]) == payload["body"]["amount"]
    assert body["bankResponse"]["statusCode"] == 0

    origin_id = body["originId"]
    status_response = client.get(f"/api/v1/transfers/{origin_id}")
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["origin_id"] == origin_id
    assert status_body["status"] == "AUTHORIZED"
    assert status_body["metadata"]["client_request"]["body"]["amount"] == payload["body"]["amount"]
