import os
from datetime import datetime, timedelta, timezone
import jwt
import hashlib
import base64
from dotenv import load_dotenv

load_dotenv()
# this is for password encrypt
# not work has bug
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
TOKEN_BLACKLIST = set()

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    hash_obj = hashlib.sha256(password_bytes).digest()
    return base64.b64encode(hash_obj).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status

security_scheme = HTTPBearer()

def get_current_user_from_token(cred: HTTPAuthorizationCredentials = Depends(security_scheme)) -> str:

    token = cred.credentials

    if token in TOKEN_BLACKLIST:
     raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been logged out! Please login again."
        )
    
    try:
        # decode and check real or fake
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None :
            raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token database payload."
                )
        return {"username": username, "role": role, "token": token}

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired! Please login again."
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature!"
        )

def require_admin_role(current_user: dict = Depends(get_current_user_from_token)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden! Only administrators can access this resource."
        )
    return current_user