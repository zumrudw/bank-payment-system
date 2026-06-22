from fastapi import APIRouter, HTTPException, Depends
from app.schemas.schemas import BankAccountCreate, CustomerCreate
from app.models.BankAccount import BankAccount
from app.models.Customer import Customer
from app.auth.hashing import hash_password
from app.auth.dependencies import require_admin
from app.database.connection import get_connection

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("/accounts", dependencies=[Depends(require_admin)])
def create_account(data: BankAccountCreate):
    """Admin only — create a new bank account."""
    account = BankAccount(balance=data.balance, currency=data.currency)
    account.save_to_db()
    return {"account_id": account.accountId, "iban": account.iban, "balance": account.getBalance()}


@router.post("/", dependencies=[Depends(require_admin)])
def create_customer(data: CustomerCreate):
    """Admin only — register a new customer with hashed password."""
    account = BankAccount.load_from_db(data.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    customer = Customer(data.full_name, data.email, data.phone, account)
    hashed = hash_password(data.password)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO customers (customer_id, full_name, email, phone, account_id, password_hash, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (customer.customerId, customer.fullName, customer.email,
         customer.phone, account.accountId, hashed, data.role)
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"customer_id": customer.customerId, "name": customer.fullName, "role": data.role}