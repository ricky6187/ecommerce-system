from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

from app import user_service
from app import auth_service

import cloudinary
import cloudinary.uploader

import logging

load_dotenv()

BACKEND_URL = "http://127.0.0.1:8000"

cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure = True
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="sale system api")

@app.post("/api/products", status_code=status.HTTP_201_CREATED)
def create_product(
    title: str = Form(...),
    description: str = Form(...),
    original_price: float = Form(...),
    flash_price: float = Form(...),
    stock: int = Form(...),
    photo: UploadFile = File(None), 
    db: Session = Depends(get_db),
    current_admin: dict = Depends(auth_service.require_admin_role)
):
    photo_url = None

    if photo:
        try:
            upload_result = cloudinary.uploader.upload(
                photo.file, 
                folder="ecommerce_products"
            )
            # public url
            photo_url = upload_result.get("secure_url")
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cloud image upload failed."
            )

    db_product = models.Product(
        title=title,
        description=description,
        original_price=original_price,
        flash_price=flash_price,
        stock=stock,
        photo_url=photo_url
    )

    try:
        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        return {"message": "upload successfully!", "product": db_product}

    except Exception as e:

        db.rollback()

        logger.error(f"/api/products failed: {str(e)}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="upload failed!"
        )

class ProductOrder(BaseModel):
    product_id: int
    quantity: int

@app.post("/api/orders", status_code=status.HTTP_201_CREATED)
def create_order(
    req: ProductOrder,
    db: Session = Depends(get_db),
    current_user: str = Depends(auth_service.get_current_user_from_token)
    ):

    user_name = current_user.get("username")

    product = db.query(models.Product).\
                filter(models.Product.id == req.product_id).\
                with_for_update().\
                first()

    if not product:
        logger.warning(f"order failed! User {user_name} try to buy item that not exist! ID: {req.product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found!"
        )

    if product.stock < req.quantity:
        logger.warning(f"order failed! User {user_name} bought item has not enough quantity! ID: {req.product_id}. Remaining: {product.stock} ")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product out of stock!"
        )

    try:
        product.stock -= req.quantity

        new_order = models.Order(
            user_id=user_name,
            product_id=req.product_id,
            quantity=req.quantity,
            price_paid=product.flash_price,
            status="PAID"
        )

        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        logger.info(f"User {user_name} successfully bought {req.product_id}! Order id: {new_order.id}")

        # lazy loading, build relationship when called this code
        return {
            "message": "Order placed successfully!",
            "order_id": new_order.id,
            "product_title": new_order.product.title,
            "price_paid": float(new_order.price_paid),
            "status": new_order.status
        }

    except Exception as e:
        db.rollback()
        logger.error(f"/api/orders failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Order processing failed!"
        )

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/register", status_code=status.HTTP_201_CREATED)
def register(req: LoginRequest, db: Session = Depends(get_db) ):
    username = req.username
    password = req.password
    result = user_service.register_new_user(username, password, db)

    if result == "EXISTS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken!"
        )
    elif result == "FAILED":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error."
        )
        
    return {
        "message": "User registered successfully!",
        "user_id": result.id,
        "username": result.username
    }

@app.post("/api/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    username = req.username
    password = req.password
    user = user_service.authenticate_user(username, password, db)
    
    if user == "ERROR":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to database issue."
        )
    elif not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password!"
        )

    access_token = auth_service.create_access_token(data={"sub": user.username, "role": user.role})
    
    return {
        "message": "Login successfully!",
        "access_token": access_token,
        "token_type": "bearer", # indicate it's jwt
        "role_identity": user.role
    }

@app.post("/api/logout")
def logout(
    current_user: str = Depends(auth_service.get_current_user_from_token)
):
    token_to_invalidate = current_user.get("token")

    auth_service.TOKEN_BLACKLIST.add(token_to_invalidate)

    logger.info("token logouted!")

    return {
        "message": "Logged out successfully! Your token has been invalidated."
    }

@app.get("/api/products")
def get_product(
    db: Session = Depends(get_db),
    current_user: str = Depends(auth_service.get_current_user_from_token)
    ):
    
    products = db.query(models.Product).order_by(models.Product.id.asc()).all()

    return products