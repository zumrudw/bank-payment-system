import uuid


class Customer:
    def __init__(self, fullName, email, phoneNumber, account, customer_id=None):
        self.customerId = customer_id or str(uuid.uuid4())
        self.fullName = fullName
        self.email = email
        self.phone = phoneNumber
        self.account = account
        self.cards = []

    def addCard(self, newCard):
        self.cards.append(newCard)

    def removeCard(self, cardNum):
        self.cards = [card for card in self.cards if card.cardNumber != cardNum]

    def getCustomerInfo(self):
        return f"Customer name: {self.fullName} (Customer ID: {self.customerId})"