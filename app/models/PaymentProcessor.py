from app.models.Transaction import Transaction


class PaymentProcessor:
    """
    The 'brain' that orchestrates a payment.
    External code only needs to call processPayment() — this is abstraction.
    """

    def __init__(self):
        self.transactionHistory = []

    def processPayment(self, card, amount, merchantName):
        valid, message = self.validatePayment(card, amount)
        if "Invalid payment amount" in message:
            return message

        transaction = self.createTransaction(card, amount, merchantName)

        if not valid:
            transaction.reject()
            transaction.save_to_db()
            self.transactionHistory.append(transaction)
            return message

        result = card.pay(amount)
        if "APPROVED" in result:
            transaction.approve()
        elif "FAILED" in result:
            transaction.status = "FAILED"
        else:
            transaction.reject()

        transaction.save_to_db()
        self.transactionHistory.append(transaction)
        return result

    def validatePayment(self, card, amount):
        if amount <= 0:
            return False, "Invalid payment amount"
        valid, message = card.validateCard()
        if not valid:
            return False, message
        return True, "Validation passed"

    def createTransaction(self, card, amount, merchantName):
        return Transaction(amount, card.account.currency, card.cardNumber, merchantName)