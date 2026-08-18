
from fastapi.testclient import TestClient
from app.main import app 
# replace the db and cloudinary result
from unittest.mock import patch
from app import models
from app import auth_service

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

    def mock_get_current_user():
        return {"username": "testuser", "role": "user"}

    app.dependency_overrides[auth_service.get_current_user_from_token] = mock_get_current_user

    try:
        
        payload = {"product_id": test_product.id, "quantity": 3}
        response = client.post("/api/orders", json=payload)
    
        assert response.status_code == 201

        db_session.refresh(test_product)
        assert test_product.stock == 7

    finally:
        # clear so won't affect other test case
        app.dependency_overrides.clear()

def test_create_product_by_admin(db_session):
    def mock_require_admin_role():
        return {"username": "admin_boss", "role": "admin"}
    
    # intercept cloudinary.uploader.upload with mock_upload so it won't ask cloudinary
    app.dependency_overrides[auth_service.require_admin_role] = mock_require_admin_role
    with patch("cloudinary.uploader.upload") as mock_upload:
        
        # the replaced result
        mock_upload.return_value = {"secure_url": "https://cloudinary.com"}
        
        form_data = {"title": "test case", "description": "test description", "original_price": "500", "flash_price": "299", "stock": "50"}
        file_data = {"photo": ("test.jpg", b"fake image bytes", "image/jpeg")}

        try:
            response = client.post("/api/products", data=form_data, files=file_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["product"]["photo_url"] == "https://cloudinary.com"

            product_id = data["product"]["id"]

            # check the function actually called 
            mock_upload.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    db_product = db_session.query(models.Product).filter(models.Product.id == product_id).first()
    assert db_product.photo_url == "https://cloudinary.com"


