import pytest
from fastapi.testclient import TestClient

from tradingai.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_api_version():
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert "version" in response.json() 