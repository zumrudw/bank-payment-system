from datetime import datetime
import uuid
from app.database.connection import get_connection


class Transaction:
    def __init__(self, amount, currency, cardNumber, merchantName, transaction_id=None):
        self.transactionId = transaction_id or str(uuid.uuid4())
        self.amount = amount
        self.currency = currency
        self.date = datetime.now()
        self.status = "PENDING"
        self.cardNumber = cardNumber
        self.merchantName = merchantName

    def approve(self):
        self.status = "APPROVED"

    def reject(self):
        self.status = "REJECTED"

    def getTransactionDetails(self):
        return (f"Transaction ID: {self.transactionId}\n"
                f"Amount: {self.amount}\nStatus: {self.status}\n"
                f"Merchant name: {self.merchantName}")

    def save_to_db(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO transactions (transaction_id, amount, currency, date, status, card_number, merchant_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (transaction_id) DO UPDATE
            SET status = EXCLUDED.status
            """,
            (self.transactionId, self.amount, self.currency, self.date,
             self.status, self.cardNumber, self.merchantName)
        )
        conn.commit()
        cur.close()
        conn.close()