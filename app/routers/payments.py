from fastapi import APIRouter, HTTPException, Depends
from app.schemas.schemas import PaymentRequest
from app.models.BankAccount import BankAccount
from app.models.Card import DebitCard, CreditCard
from app.models.PaymentProcessor import PaymentProcessor
from app.auth.dependencies import get_current_user
from app.database.connection import get_connection
from datetime import datetime

router = APIRouter(prefix="/payments", tags=["Payments"])
processor = PaymentProcessor()


def load_card_from_db(card_number: str):
    """Reconstructs a DebitCard or CreditCard object from the database."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT card_number, card_holder_name, expiry_date, cvv, is_blocked, card_type, credit_limit, used_credit, account_id FROM cards WHERE card_number = %s",
        (card_number,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None

    account = BankAccount.load_from_db(row[8])
    if not account:
        return None

    expiry = datetime.combine(row[2], datetime.min.time())

    if row[5] == "debit":
        card = DebitCard(row[0], row[1], expiry, row[3], account)
    else:
        card = CreditCard(row[0], row[1], expiry, row[3], account, float(row[6]))
        card.usedCredit = float(row[7])

    card._isBlocked = row[4]
    return card


def get_customers_account_id(customer_id: str):
    """Helper — find which account a customer owns."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT account_id FROM customers WHERE customer_id = %s", (customer_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


@router.post("/pay")
def make_payment(data: PaymentRequest, current_user: dict = Depends(get_current_user)):
    """
    Process a payment.
    Customers can only pay with cards linked to their own account.
    Admins can process any card.
    """
    card = load_card_from_db(data.card_number)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if current_user["role"] == "customer":
        owned_account_id = get_customers_account_id(current_user["customer_id"])
        if owned_account_id != card.account.accountId:
            raise HTTPException(status_code=403, detail="This card does not belong to you")

    result = processor.processPayment(card, data.amount, data.merchant_name)
    return {"result": result}


@router.get("/history")
def get_transaction_history(current_user: dict = Depends(get_current_user)):
    """Admins see every transaction. Customers see only their own."""
    conn = get_connection()
    cur = conn.cursor()

    if current_user["role"] == "admin":
        cur.execute(
            "SELECT transaction_id, amount, currency, date, status, card_number, merchant_name FROM transactions ORDER BY date DESC"
        )
    else:
        cur.execute(
            """
            SELECT t.transaction_id, t.amount, t.currency, t.date, t.status, t.card_number, t.merchant_name
            FROM transactions t
            JOIN cards c ON t.card_number = c.card_number
            JOIN customers cu ON c.account_id = cu.account_id
            WHERE cu.customer_id = %s
            ORDER BY t.date DESC
            """,
            (current_user["customer_id"],)
        )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "transaction_id": r[0], "amount": r[1], "currency": r[2],
            "date": r[3], "status": r[4], "card_number": r[5], "merchant_name": r[6]
        }
        for r in rows
    ]