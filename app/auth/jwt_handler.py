from datetime import datetime, timedelta
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))


def create_access_token(customer_id: str, role: str) -> str:
    """
    Short-lived token (30 min) sent with every request.
    Contains the user's id and role, digitally signed so it can't be tampered with.
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": customer_id,
        "role": role,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(customer_id: str) -> tuple[str, datetime]:
    """
    Long-lived token (7 days) used only to get new access tokens.
    Never sent with normal requests, only to /auth/refresh.
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": customer_id,
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4())  # unique token id, lets us track/revoke it
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, expire


def verify_token(token: str, expected_type: str) -> dict | None:
    """
    Decodes a token and checks it's valid, not expired, and the right type.
    Returns the payload if valid, None if not.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None