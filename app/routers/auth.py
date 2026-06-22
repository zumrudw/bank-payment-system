from fastapi import APIRouter, HTTPException, Depends
from app.schemas.schemas import LoginRequest, RefreshRequest
from app.database.connection import get_connection
from app.auth.hashing import verify_password
from app.auth.jwt_handler import create_access_token, create_refresh_token, verify_token
from app.auth.dependencies import get_current_user
import uuid

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_customer_by_email(email: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT customer_id, full_name, email, password_hash, role FROM customers WHERE email = %s",
        (email,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def save_refresh_token(customer_id: str, token: str, expires_at):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO refresh_tokens (token_id, customer_id, token, expires_at) VALUES (%s, %s, %s, %s)",
        (str(uuid.uuid4()), customer_id, token, expires_at)
    )
    conn.commit()
    cur.close()
    conn.close()


@router.post("/login")
def login(data: LoginRequest):
    """Login with email + password. Returns access_token + refresh_token."""
    customer = get_customer_by_email(data.email)

    if not customer or not verify_password(data.password, customer[3]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    customer_id, role = customer[0], customer[4]

    access_token = create_access_token(customer_id, role)
    refresh_token, expires_at = create_refresh_token(customer_id)
    save_refresh_token(customer_id, refresh_token, expires_at)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": role
    }


@router.post("/refresh")
def refresh(data: RefreshRequest):
    """Exchange a valid refresh token for a new access token."""
    payload = verify_token(data.refresh_token, "refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT customer_id, is_revoked FROM refresh_tokens WHERE token = %s", (data.refresh_token,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or row[1]:
        raise HTTPException(status_code=401, detail="Refresh token is invalid or has been revoked")

    customer_id = row[0]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT role FROM customers WHERE customer_id = %s", (customer_id,))
    role = cur.fetchone()[0]
    cur.close()
    conn.close()

    new_access_token = create_access_token(customer_id, role)
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(data: RefreshRequest, current_user: dict = Depends(get_current_user)):
    """Revoke a refresh token so it can't be reused."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE refresh_tokens SET is_revoked = TRUE WHERE token = %s", (data.refresh_token,))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Logged out successfully"}