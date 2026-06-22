from abc import ABC, abstractmethod
from datetime import datetime
from app.database.connection import get_connection


class Card(ABC):
    """Abstract base class — you can never create a plain Card(), only DebitCard or CreditCard."""

    def __init__(self, cardNumber, cardHolderName, expiryDate, cvv, account):
        self.cardNumber = cardNumber
        self.cardHolderName = cardHolderName
        self.expiryDate = expiryDate
        self.cvv = cvv
        self._isBlocked = False
        self.account = account

    def validateCard(self):
        if self._isBlocked:
            return False, "Blocked card"
        if self.expiryDate < datetime.now():
            return False, "Expired card"
        return True, "Valid"

    def blockCard(self):
        self._isBlocked = True

    def unblockCard(self):
        self._isBlocked = False

    def getCardInfo(self):
        return f"Card number: {self.cardNumber}\nCard holder: {self.cardHolderName}\nExpiry date: {self.expiryDate}"

    @abstractmethod
    def pay(self, amount):
        """Every subclass MUST implement this — that's the abstraction contract."""
        pass

    def save_to_db(self, card_type, credit_limit=None, used_credit=0):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO cards (card_number, card_holder_name, expiry_date, cvv, is_blocked, card_type, credit_limit, used_credit, account_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (card_number) DO UPDATE
            SET is_blocked = EXCLUDED.is_blocked,
                used_credit = EXCLUDED.used_credit
            """,
            (self.cardNumber, self.cardHolderName, self.expiryDate.date(), self.cvv,
             self._isBlocked, card_type, credit_limit, used_credit, self.account.accountId)
        )
        conn.commit()
        cur.close()
        conn.close()


class DebitCard(Card):
    """Pays only if the linked bank account has enough balance."""

    def pay(self, amount):
        valid, message = self.validateCard()
        if not valid:
            return message
        if amount <= 0:
            return "Invalid payment amount"
        if self.account.getBalance() >= amount:
            self.account.withdraw(amount)
            self.account.save_to_db()
            self.save_to_db(card_type="debit")
            return "Payment (Debit) APPROVED"
        return "Payment FAILED - Insufficient balance"


class CreditCard(Card):
    """Pays only if available credit (limit - used) is enough."""

    def __init__(self, cardNumber, cardHolderName, expiryDate, cvv, account, creditLimit):
        super().__init__(cardNumber, cardHolderName, expiryDate, cvv, account)
        self.creditLimit = float(creditLimit)
        self.usedCredit = 0

    def getAvailableCredit(self):
        return self.creditLimit - self.usedCredit

    def pay(self, amount):
        valid, message = self.validateCard()
        if not valid:
            return message
        if amount <= 0:
            return "Invalid payment amount"
        if self.getAvailableCredit() >= amount:
            self.usedCredit += amount
            self.save_to_db(card_type="credit", credit_limit=self.creditLimit, used_credit=self.usedCredit)
            return "Payment (Credit) APPROVED"
        return "Payment FAILED - Credit limit exceeded"