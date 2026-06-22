-- 1. Bank accounts
CREATE TABLE IF NOT EXISTS bank_accounts (
    account_id   VARCHAR(36) PRIMARY KEY,
    iban         VARCHAR(36) UNIQUE NOT NULL,
    balance      NUMERIC(12, 2) NOT NULL DEFAULT 0,
    currency     VARCHAR(10) NOT NULL
);

-- 2. Customers (also acts as our "users" table for login)
CREATE TABLE IF NOT EXISTS customers (
    customer_id    VARCHAR(36) PRIMARY KEY,
    full_name      VARCHAR(100) NOT NULL,
    email          VARCHAR(100) UNIQUE NOT NULL,
    phone          VARCHAR(20),
    account_id     VARCHAR(36) REFERENCES bank_accounts(account_id),
    password_hash  VARCHAR(255) NOT NULL,
    role           VARCHAR(20) NOT NULL DEFAULT 'customer'
);

-- 3. Cards (debit + credit)
CREATE TABLE IF NOT EXISTS cards (
    card_number       VARCHAR(16) PRIMARY KEY,
    card_holder_name  VARCHAR(100) NOT NULL,
    expiry_date       DATE NOT NULL,
    cvv               VARCHAR(4) NOT NULL,
    is_blocked        BOOLEAN DEFAULT FALSE,
    card_type         VARCHAR(10) NOT NULL,
    credit_limit      NUMERIC(12, 2),
    used_credit       NUMERIC(12, 2) DEFAULT 0,
    account_id        VARCHAR(36) REFERENCES bank_accounts(account_id)
);

-- 4. Transactions
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id  VARCHAR(36) PRIMARY KEY,
    amount          NUMERIC(12, 2) NOT NULL,
    currency        VARCHAR(10) NOT NULL,
    date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status          VARCHAR(20) NOT NULL,
    card_number     VARCHAR(16) REFERENCES cards(card_number),
    merchant_name   VARCHAR(100)
);

-- 5. Refresh tokens (for login sessions)
CREATE TABLE IF NOT EXISTS refresh_tokens (
    token_id      VARCHAR(36) PRIMARY KEY,
    customer_id   VARCHAR(36) REFERENCES customers(customer_id),
    token         TEXT NOT NULL,
    expires_at    TIMESTAMP NOT NULL,
    is_revoked    BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO bank_accounts (account_id, iban, balance, currency)
VALUES ('admin-account-001', 'admin-iban-001', 0, 'USD')
ON CONFLICT DO NOTHING;

INSERT INTO customers (customer_id, full_name, email, phone, account_id, password_hash, role)
VALUES (
    'admin-001',
    'Admin User',
    'admin@bank.com',
    '0000000000',
    'admin-account-001',
    '$2b$12$VoUeo/1mzItj8iJEl7Pw8u5drmn2R9oc919.mZhJZTAcpyUiGqytC',
    'admin'
)
ON CONFLICT DO NOTHING;