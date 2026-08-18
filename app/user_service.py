import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import models
from app import auth_service

logger = logging.getLogger(__name__)

def register_new_user(username: str, plain_password: str, db: Session):
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        return "EXISTS"
    
    try:
        secret_hashed_password = auth_service.hash_password(plain_password)
        
        new_user = models.User(
            username=username,
            hashed_password=secret_hashed_password
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except IntegrityError as ie:
        db.rollback()
        logger.warning(f"account {username} trigger unique field error.")
        return "EXISTS"

    except Exception as e:
        db.rollback()
        logger.error(f"register failed: {str(e)}", exc_info=True)
        return "FAILED"

def authenticate_user(username: str, plain_password: str, db: Session):
    try:
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            return False
            
        is_password_correct = auth_service.verify_password(plain_password, user.hashed_password)
        
        if not is_password_correct:
            return False
            
        return user
        
    except Exception as e:
        logger.error(f"login failed: {str(e)}", exc_info=True)
        return "ERROR"
