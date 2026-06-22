from fastapi import APIRouter, HTTPException, Depends
from app.schemas.schemas import DebitCardCreate, CreditCardCreate
from app.models.BankAccount import BankAccount
from app.models.Card import DebitCard, CreditCard
from app.auth.dependencies import require_admin

router = APIRouter(prefix="/cards", tags=["Cards"])


@router.post("/debit", dependencies=[Depends(require_admin)])
def create_debit_card(data: DebitCardCreate):
    """Admin only — issue a debit card linked to an account."""
    account = BankAccount.load_from_db(data.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    card = DebitCard(data.card_number, data.card_holder_name, data.expiry_date, data.cvv, account)
    card.save_to_db(card_type="debit")
    return {"message": "Debit card created", "card_number": card.cardNumber}


@router.post("/credit", dependencies=[Depends(require_admin)])
def create_credit_card(data: CreditCardCreate):
    """Admin only — issue a credit card linked to an account."""
    account = BankAccount.load_from_db(data.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    card = CreditCard(data.card_number, data.card_holder_name, data.expiry_date, data.cvv, account, data.credit_limit)
    card.save_to_db(card_type="credit", credit_limit=data.credit_limit)
    return {"message": "Credit card created", "card_number": card.cardNumber}