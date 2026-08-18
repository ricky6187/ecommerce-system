
from fastapi.testclient import TestClient
from app.main import app 

client = TestClient(app)

def test_get_with_no_token_returns_401_or_404():
    """call api without token"""
    response = client.get("/api/products")

    assert response.status_code == 401
    assert "detail" in response.json()

def test_invalid_url_returns_404():
    """call a invalid api"""
    response = client.get("/api/this-url-does-not-exist")
    assert response.status_code == 404
