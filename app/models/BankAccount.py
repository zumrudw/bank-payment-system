import uuid
from app.database.connection import get_connection


class BankAccount:
    def __init__(self, balance, currency, account_id=None, iban=None):
        self.accountId = account_id or str(uuid.uuid4())
        self.iban = iban or str(uuid.uuid4())
        self.__balance = float(balance)   # private attribute, force float to avoid Decimal/float clashes
        self.currency = currency

    def deposit(self, amount):
        self.__balance += amount

    def withdraw(self, amount):
        if amount <= self.__balance:
            self.__balance -= amount
            return True
        return False

    def getBalance(self):
        return self.__balance

    def save_to_db(self):
        """Insert or update this account in PostgreSQL."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO bank_accounts (account_id, iban, balance, currency)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (account_id) DO UPDATE
            SET balance = EXCLUDED.balance
            """,
            (self.accountId, self.iban, self.__balance, self.currency)
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def load_from_db(account_id):
        """Reconstructs a BankAccount object from a database row."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT account_id, iban, balance, currency FROM bank_accounts WHERE account_id = %s",
            (account_id,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return BankAccount(balance=row[2], currency=row[3], account_id=row[0], iban=row[1])
        return None