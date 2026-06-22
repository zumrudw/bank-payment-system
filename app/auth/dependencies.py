from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.jwt_handler import verify_token

# Tells FastAPI to look for "Authorization: Bearer <token>" in headers
bearer_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """
    Runs before any protected route.
    Extracts the token, verifies it, and returns who the user is.
    """
    token = credentials.credentials
    payload = verify_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please login again."
        )
    return {"customer_id": payload["sub"], "role": payload["role"]}


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Use this on routes only admins should access."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only.")
    return current_user