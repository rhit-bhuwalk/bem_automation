import pytest
from pytest_asyncio import fixture
from fastapi.testclient import TestClient
from datetime import datetime, UTC
import json
from api.main import app
from api.database.redis.main import redis_db
from api.database.incidents.connection import incident_db

# Sample test data
sample_dtc_data = {
    "data": {
        "id": "test-id-123",
        "timestamp": int(datetime.now(UTC).timestamp() * 1000),
        "account_id": "test-account-123",
        "vehicle_id": "test-vehicle-123",
        "dtcs": [
            {
                "t": int(datetime.now(UTC).timestamp() * 1000),
                "code": "P105C",
                "status": 1
            }
        ],
        "mid": "144",
        "is_sid": True,
        "type": "P105C",
        "status": "active",
        "is_set": True
    },
    "action": "create",
    "entity": "dtcs_change_log"
}

sample_alert_data = {
    "data": {
        "id": "test-id-123",
        "account_id": "test-account-123",
        "vehicle_id": "test-vehicle-123",
        "location": "16.709181666666666,74.28041166666667",
        "timestamp": int(datetime.now(UTC).timestamp() * 1000),
        "vehicle_plate": "AB01CD1234",
        "vehicle_tag": "AB 01 CD 1234",
        "type": "engine_temperature",
        "alert_values": json.dumps({"temperature": 95}),
        "address": "Test Location"
    },
    "action": "create",
    "entity": "alert_log"
}

@fixture(scope="module")
def test_client():
    return TestClient(app)

@fixture(autouse=True)
async def setup_and_cleanup():
    """Setup before and cleanup after each test"""
    # Setup
    await redis_db.connect()
    await incident_db.connect()
    yield
    # Cleanup
    try:
        await redis_db.flushdb()  # Clear Redis
        await incident_db.delete_many({})  # Clear MongoDB collection
    finally:
        await redis_db.close()
        await incident_db.close()

@pytest.mark.asyncio
async def test_dtc_webhook_success(test_client):
    """Test successful DTC webhook submission"""
    response = test_client.post("/api/v1/webhooks/dtc", json=sample_dtc_data)
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    
    # Verify Redis storage
    key = f"incident:{sample_dtc_data['data']['id']}"
    stored_data = await redis_db.hgetall(key)
    assert "dtc_data" in stored_data

@pytest.mark.asyncio
async def test_alert_webhook_success(test_client):
    """Test successful Alert webhook submission"""
    response = test_client.post("/api/v1/webhooks/alert", json=sample_alert_data)
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    
    # Verify Redis storage
    key = f"incident:{sample_alert_data['data']['id']}"
    stored_data = await redis_db.hgetall(key)
    assert "alert_data" in stored_data

@pytest.mark.asyncio
async def test_complete_incident_flow(test_client):
    """Test complete flow with both DTC and Alert data"""
    # Send DTC data
    dtc_response = test_client.post("/api/v1/webhooks/dtc", json=sample_dtc_data)
    assert dtc_response.status_code == 200

    # Send Alert data
    alert_response = test_client.post("/api/v1/webhooks/alert", json=sample_alert_data)
    assert alert_response.status_code == 200

    # Verify data was combined and stored in MongoDB
    event_id = sample_dtc_data['data']['id']
    incident = await incident_db.get_incident_data(event_id)
    assert incident is not None
    
    # Verify Redis key was cleaned up
    key = f"incident:{event_id}"
    stored_data = await redis_db.hgetall(key)
    assert not stored_data  # Should be empty after successful processing

@pytest.mark.asyncio
async def test_invalid_dtc_data(test_client):
    """Test DTC webhook with invalid data"""
    invalid_data = {
        "data": {
            "id": "test-id-123",
            # Missing required fields
        },
        "action": "create",
        "entity": "dtcs_change_log"
    }
    response = test_client.post("/api/v1/webhooks/dtc", json=invalid_data)
    assert response.status_code == 500

@pytest.mark.asyncio
async def test_invalid_alert_data(test_client):
    """Test Alert webhook with invalid data"""
    invalid_data = {
        "data": {
            "id": "test-id-123",
            # Missing required fields
        },
        "action": "create",
        "entity": "alert_log"
    }
    response = test_client.post("/api/v1/webhooks/alert", json=invalid_data)
    assert response.status_code == 500

@pytest.mark.asyncio
async def test_concurrent_webhooks(test_client):
    """Test concurrent webhook submissions"""
    # Create multiple test events
    num_events = 5
    test_events = []
    for i in range(num_events):
        event_id = f"test-event-{i}"
        dtc_data = {
            "data": {
                **sample_dtc_data["data"],
                "id": event_id
            },
            "action": "create",
            "entity": "dtcs_change_log"
        }
        alert_data = {
            "data": {
                **sample_alert_data["data"],
                "id": event_id
            },
            "action": "create",
            "entity": "alert_log"
        }
        test_events.append((dtc_data, alert_data))
    
    # Send webhooks
    for dtc, alert in test_events:
        dtc_response = test_client.post("/api/v1/webhooks/dtc", json=dtc)
        alert_response = test_client.post("/api/v1/webhooks/alert", json=alert)
        assert dtc_response.status_code == 200
        assert alert_response.status_code == 200 