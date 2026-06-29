import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

def get_admin_token():
    """Get a real JWT token by logging in as admin (mocked)."""
    with patch("app.routers.auth.get_customer_by_email") as mock_get, \
         patch("app.routers.auth.verify_password", return_value=True), \
         patch("app.routers.auth.save_refresh_token"):

        mock_get.return_value = (
            "admin-001",       # customer_id
            "Admin User",      # full_name
            "admin@bank.com",  # email
            "hashed_pw",       # password_hash
            "admin"            # role
        )

        response = client.post("/auth/login", json={
            "email": "admin@bank.com",
            "password": "admin123"
        })
        return response.json()["access_token"]


def get_customer_token():
    """Get a JWT token for a regular customer (mocked)."""
    with patch("app.routers.auth.get_customer_by_email") as mock_get, \
         patch("app.routers.auth.verify_password", return_value=True), \
         patch("app.routers.auth.save_refresh_token"):

        mock_get.return_value = (
            "customer-001",
            "Jane Austen",
            "jane@bank.com",
            "hashed_pw",
            "customer"
        )

        response = client.post("/auth/login", json={
            "email": "jane@bank.com",
            "password": "password123"
        })
        return response.json()["access_token"]


# ──────────────────────────────────────────────
# AUTH TESTS
# ──────────────────────────────────────────────

class TestAuth:

    def test_login_success(self):
        """Valid credentials should return access and refresh tokens."""
        with patch("app.routers.auth.get_customer_by_email") as mock_get, \
             patch("app.routers.auth.verify_password", return_value=True), \
             patch("app.routers.auth.save_refresh_token"):

            mock_get.return_value = (
                "admin-001", "Admin User", "admin@bank.com", "hashed_pw", "admin"
            )

            response = client.post("/auth/login", json={
                "email": "admin@bank.com",
                "password": "admin123"
            })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "admin"

    def test_login_wrong_password(self):
        """Wrong password should return 401."""
        with patch("app.routers.auth.get_customer_by_email") as mock_get, \
             patch("app.routers.auth.verify_password", return_value=False):

            mock_get.return_value = (
                "admin-001", "Admin User", "admin@bank.com", "hashed_pw", "admin"
            )

            response = client.post("/auth/login", json={
                "email": "admin@bank.com",
                "password": "wrongpassword"
            })

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

    def test_login_user_not_found(self):
        """Non-existent email should return 401."""
        with patch("app.routers.auth.get_customer_by_email", return_value=None):
            response = client.post("/auth/login", json={
                "email": "ghost@bank.com",
                "password": "anypassword"
            })

        assert response.status_code == 401

    def test_logout_success(self):
        """Logout should revoke the refresh token."""
        token = get_admin_token()

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur

        with patch("app.routers.auth.get_connection", return_value=mock_conn):
            response = client.post(
                "/auth/logout",
                json={"refresh_token": "some_refresh_token"},
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"


# ──────────────────────────────────────────────
# CUSTOMERS TESTS
# ──────────────────────────────────────────────

class TestCustomers:

    def test_create_account_as_admin(self):
        """Admin should be able to create a bank account."""
        token = get_admin_token()

        mock_account = MagicMock()
        mock_account.accountId = "acc-123"
        mock_account.iban = "AZ00TEST0000000000000000001"
        mock_account.getBalance.return_value = 1000.00

        with patch("app.routers.customers.BankAccount") as MockAccount:
            MockAccount.return_value = mock_account

            response = client.post(
                "/customers/accounts",
                json={"balance": 1000.00, "currency": "USD"},
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "account_id" in data
        assert "iban" in data

    def test_create_account_without_auth(self):
        """Unauthenticated request should return 401 or 403."""
        response = client.post(
            "/customers/accounts",
            json={"balance": 1000.00, "currency": "USD"}
        )
        assert response.status_code in [401, 403]

    def test_create_customer_as_admin(self):
        """Admin should be able to create a new customer."""
        token = get_admin_token()

        mock_account = MagicMock()
        mock_account.accountId = "acc-123"

        mock_customer = MagicMock()
        mock_customer.customerId = "cust-456"
        mock_customer.fullName = "John Doe"
        mock_customer.email = "john@bank.com"
        mock_customer.phone = "1234567890"

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur

        with patch("app.routers.customers.BankAccount.load_from_db", return_value=mock_account), \
             patch("app.routers.customers.Customer", return_value=mock_customer), \
             patch("app.routers.customers.hash_password", return_value="hashed"), \
             patch("app.routers.customers.get_connection", return_value=mock_conn):

            response = client.post(
                "/customers/",
                json={
                    "full_name": "John Doe",
                    "email": "john@bank.com",
                    "phone": "1234567890",
                    "account_id": "acc-123",
                    "password": "password123",
                    "role": "customer"
                },
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "customer_id" in data
        assert data["role"] == "customer"

    def test_create_customer_account_not_found(self):
        """Creating customer with invalid account_id should return 404."""
        token = get_admin_token()

        with patch("app.routers.customers.BankAccount.load_from_db", return_value=None):
            response = client.post(
                "/customers/",
                json={
                    "full_name": "Ghost User",
                    "email": "ghost@bank.com",
                    "phone": "0000000000",
                    "account_id": "nonexistent-acc",
                    "password": "password123",
                    "role": "customer"
                },
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Account not found"


# ──────────────────────────────────────────────
# CARDS TESTS
# ──────────────────────────────────────────────

class TestCards:

    def test_create_debit_card_as_admin(self):
        """Admin should be able to create a debit card."""
        token = get_admin_token()

        mock_account = MagicMock()
        mock_account.accountId = "acc-123"

        mock_card = MagicMock()
        mock_card.cardNumber = "1111222233334444"

        with patch("app.routers.cards.BankAccount.load_from_db", return_value=mock_account), \
             patch("app.routers.cards.DebitCard", return_value=mock_card), \
             patch.object(mock_card, "save_to_db"):

            response = client.post(
                "/cards/debit",
                json={
                    "card_number": "1111222233334444",
                    "card_holder_name": "Jane Austen",
                    "expiry_date": "2029-06-25",
                    "cvv": "123",
                    "account_id": "acc-123"
                },
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        assert response.json()["message"] == "Debit card created"

    def test_create_debit_card_account_not_found(self):
        """Creating a debit card for invalid account should return 404."""
        token = get_admin_token()

        with patch("app.routers.cards.BankAccount.load_from_db", return_value=None):
            response = client.post(
                "/cards/debit",
                json={
                    "card_number": "1111222233334444",
                    "card_holder_name": "Jane Austen",
                    "expiry_date": "2029-06-25",
                    "cvv": "123",
                    "account_id": "invalid-acc"
                },
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Account not found"

    def test_create_credit_card_as_admin(self):
        """Admin should be able to create a credit card."""
        token = get_admin_token()

        mock_account = MagicMock()
        mock_card = MagicMock()
        mock_card.cardNumber = "5555666677778888"

        with patch("app.routers.cards.BankAccount.load_from_db", return_value=mock_account), \
             patch("app.routers.cards.CreditCard", return_value=mock_card), \
             patch.object(mock_card, "save_to_db"):

            response = client.post(
                "/cards/credit",
                json={
                    "card_number": "5555666677778888",
                    "card_holder_name": "Jane Austen",
                    "expiry_date": "2029-06-25",
                    "cvv": "456",
                    "account_id": "acc-123",
                    "credit_limit": 5000.00
                },
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        assert response.json()["message"] == "Credit card created"

    def test_create_card_without_auth(self):
        """Unauthenticated card creation should return 401 or 403."""
        response = client.post(
            "/cards/debit",
            json={
                "card_number": "1111222233334444",
                "card_holder_name": "Jane Austen",
                "expiry_date": "2029-06-25",
                "cvv": "123",
                "account_id": "acc-123"
            }
        )
        assert response.status_code in [401, 403]


# ──────────────────────────────────────────────
# PAYMENTS TESTS
# ──────────────────────────────────────────────

class TestPayments:

    def test_make_payment_success(self):
        """Customer should be able to pay with their own card."""
        token = get_customer_token()

        mock_card = MagicMock()
        mock_card.account.accountId = "acc-customer-001"

        with patch("app.routers.payments.load_card_from_db", return_value=mock_card), \
             patch("app.routers.payments.get_customers_account_id", return_value="acc-customer-001"), \
             patch("app.routers.payments.processor.processPayment", return_value="Payment successful"):

            response = client.post(
                "/payments/pay",
                json={
                    "card_number": "1111222233334444",
                    "amount": 100.00,
                    "merchant_name": "Amazon"
                },
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        assert response.json()["result"] == "Payment successful"

    def test_make_payment_card_not_found(self):
        """Payment with non-existent card should return 404."""
        token = get_customer_token()

        with patch("app.routers.payments.load_card_from_db", return_value=None):
            response = client.post(
                "/payments/pay",
                json={
                    "card_number": "0000000000000000",
                    "amount": 50.00,
                    "merchant_name": "Amazon"
                },
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Card not found"

    def test_make_payment_wrong_card(self):
        """Customer should not be able to pay with someone else's card."""
        token = get_customer_token()

        mock_card = MagicMock()
        mock_card.account.accountId = "acc-someone-else"

        with patch("app.routers.payments.load_card_from_db", return_value=mock_card), \
             patch("app.routers.payments.get_customers_account_id", return_value="acc-customer-001"):

            response = client.post(
                "/payments/pay",
                json={
                    "card_number": "9999888877776666",
                    "amount": 50.00,
                    "merchant_name": "Amazon"
                },
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 403
        assert response.json()["detail"] == "This card does not belong to you"

    def test_payment_without_auth(self):
        """Unauthenticated payment should return 401 or 403."""
        response = client.post(
            "/payments/pay",
            json={
                "card_number": "1111222233334444",
                "amount": 100.00,
                "merchant_name": "Amazon"
            }
        )
        assert response.status_code in [401, 403]

    def test_get_transaction_history_as_admin(self):
        """Admin should see all transactions."""
        token = get_admin_token()

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = [
            ("txn-001", 100.00, "USD", "2026-06-01", "success", "1111222233334444", "Amazon"),
            ("txn-002", 200.00, "USD", "2026-06-02", "success", "5555666677778888", "Netflix"),
        ]

        with patch("app.routers.payments.get_connection", return_value=mock_conn):
            response = client.get(
                "/payments/history",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["transaction_id"] == "txn-001"

    def test_get_transaction_history_as_customer(self):
        """Customer should only see their own transactions."""
        token = get_customer_token()

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = [
            ("txn-001", 100.00, "USD", "2026-06-01", "success", "1111222233334444", "Amazon"),
        ]

        with patch("app.routers.payments.get_connection", return_value=mock_conn):
            response = client.get(
                "/payments/history",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1