from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

from sqlalchemy.orm import relationship

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(100), nullable=False)

    description = Column(String(500), nullable=False)

    original_price = Column(Numeric(10,2), nullable=False)

    flash_price = Column(Numeric(10,2), nullable=False)

    stock = Column(Integer, default=0, nullable=False)

    photo_url = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Order(Base):
    __tablename__= "orders"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String(50), nullable=False, index=True)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    quantity = Column(Integer, default=1, nullable=False)

    price_paid = Column(Numeric(10,2), nullable=False)

    status = Column(String(20), default="Pending", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    product = relationship("Product")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(50), unique=True, nullable=False, index=True)

    role = Column(String(20), default="user", nullable=False)

    hashed_password = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
