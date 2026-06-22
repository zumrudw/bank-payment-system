from pydantic import BaseModel
from datetime import datetime


# --- Auth ---
class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str


# --- Accounts & Customers ---
class BankAccountCreate(BaseModel):
    balance: float
    currency: str

class CustomerCreate(BaseModel):
    full_name: str
    email: str
    phone: str
    account_id: str
    password: str
    role: str = "customer"   # defaults to customer if not specified


# --- Cards ---
class DebitCardCreate(BaseModel):
    card_number: str
    card_holder_name: str
    expiry_date: datetime
    cvv: str
    account_id: str

class CreditCardCreate(BaseModel):
    card_number: str
    card_holder_name: str
    expiry_date: datetime
    cvv: str
    account_id: str
    credit_limit: float


# --- Payments ---
class PaymentRequest(BaseModel):
    card_number: str
    amount: float
    merchant_name: str