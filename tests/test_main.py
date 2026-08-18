
from fastapi.testclient import TestClient
from app.main import app 
# replace the db and cloudinary result
from unittest.mock import patch
from app import models

client = TestClient(app)

def test_get_with_no_token_returns_401():
    """call api without token"""
    response = client.get("/api/products")

    assert response.status_code == 401
    assert "detail" in response.json()

def test_invalid_url_returns_404():
    """call a invalid api"""
    response = client.get("/api/this-url-does-not-exist")
    assert response.status_code == 404

def test_create_order_success(db_session):
    test_product = models.Product(
        title="test case",
        description="test description",
        stock=10,
        flash_price=800.0,
        original_price=1000.0
    )
    db_session.add(test_product)
    db_session.commit()
    db_session.refresh(test_product)

    # use patch so no need check jwt
    mock_user = {"username": "testuser", "role": "user"}
    with patch("app.auth_service.get_current_user_from_token", return_value=mock_user):
        
        payload = {"product_id": test_product.id, "quantity": 3}
        response = client.post("/api/orders", json=payload)
    
        assert response.status_code == 201

        db_session.refresh(test_product)
        assert test_product.stock == 7

def test_create_product_by_admin(db_session):
    mock_admin = {"username": "admin_boss", "role": "admin"}
    
    # intercept cloudinary.uploader.upload with mock_upload so it won't ask cloudinary
    with patch("app.auth_service.require_admin_role", return_value=mock_admin), \
         patch("cloudinary.uploader.upload") as mock_upload:
        
        # the replaced result
        mock_upload.return_value = {"secure_url": "https://cloudinary.com"}
        
        form_data = {"title": "test case", "description": "test description", "original_price": "500", "flash_price": "299", "stock": "50"}
        file_data = {"photo": ("test.jpg", b"fake image bytes", "image/jpeg")}
        
        response = client.post("/api/products", data=form_data, files=file_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["product"]["photo_url"] == "https://cloudinary.com"

        product_id = data["product"]["id"]

        # check the function actually called 
        mock_upload.assert_called_once()

    db_product = db_session.query(models.Product).filter(models.Product.id == product_id).first()
    assert db_product.photo_url == "https://cloudinary.com"


