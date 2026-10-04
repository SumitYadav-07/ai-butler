-- AI Butler schema. All data is entered manually by the user.
-- No bank, UPI, SMS, email or card data is stored or fetched.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DROP TABLE IF EXISTS ai_conversations, daily_balances, financial_goals,
  emergency_funds, savings, emis, income, expenses, transactions,
  financial_profiles, users CASCADE;

CREATE TABLE users (
  id            SERIAL PRIMARY KEY,
  name          VARCHAR(100) NOT NULL,
  email         VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Nullable money fields: NULL means "user has not entered this yet",
-- so the Butler can say "I don't have enough information".
CREATE TABLE financial_profiles (
  id                     SERIAL PRIMARY KEY,
  user_id                INT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  monthly_income         NUMERIC(12,2) CHECK (monthly_income >= 0),
  opening_balance        NUMERIC(12,2),
  monthly_fixed_expenses NUMERIC(12,2) CHECK (monthly_fixed_expenses >= 0),
  monthly_savings_target NUMERIC(12,2) CHECK (monthly_savings_target >= 0),
  emergency_fund_target  NUMERIC(12,2) CHECK (emergency_fund_target >= 0),
  emergency_reserve      NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (emergency_reserve >= 0),
  setup_completed        BOOLEAN NOT NULL DEFAULT FALSE,
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- The ledger: every row is typed in by the user.
CREATE TABLE transactions (
  id             SERIAL PRIMARY KEY,
  user_id        INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type           VARCHAR(10) NOT NULL CHECK (type IN ('income','expense')),
  amount         NUMERIC(12,2) NOT NULL CHECK (amount > 0),
  category       VARCHAR(30) NOT NULL CHECK (category IN (
                   'Food','Transport','Shopping','Entertainment','Bills','Education',
                   'Healthcare','Rent','EMI','Travel','Investments','Other',
                   'Salary','Allowance','Other Income')),
  description    VARCHAR(255) NOT NULL DEFAULT '',
  txn_date       DATE NOT NULL,
  payment_method VARCHAR(30),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_txn_user_date     ON transactions(user_id, txn_date);
CREATE INDEX idx_txn_user_category ON transactions(user_id, category);

-- Recurring fixed expenses (rent, subscriptions) -> used for "upcoming expenses"
CREATE TABLE expenses (
  id        SERIAL PRIMARY KEY,
  user_id   INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name      VARCHAR(100) NOT NULL,
  category  VARCHAR(30) NOT NULL DEFAULT 'Bills',
  amount    NUMERIC(12,2) NOT NULL CHECK (amount > 0),
  due_day   SMALLINT NOT NULL CHECK (due_day BETWEEN 1 AND 31),
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX idx_expenses_user ON expenses(user_id);

-- Recurring income sources entered by the user
CREATE TABLE income (
  id        SERIAL PRIMARY KEY,
  user_id   INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source    VARCHAR(100) NOT NULL,
  amount    NUMERIC(12,2) NOT NULL CHECK (amount > 0),
  pay_day   SMALLINT NOT NULL CHECK (pay_day BETWEEN 1 AND 31),
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX idx_income_user ON income(user_id);

CREATE TABLE emis (
  id               SERIAL PRIMARY KEY,
  user_id          INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name             VARCHAR(100) NOT NULL,
  monthly_amount   NUMERIC(12,2) NOT NULL CHECK (monthly_amount > 0),
  due_day          SMALLINT NOT NULL CHECK (due_day BETWEEN 1 AND 31),
  remaining_months INT CHECK (remaining_months >= 0),
  is_active        BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX idx_emis_user ON emis(user_id);

CREATE TABLE savings (
  id       SERIAL PRIMARY KEY,
  user_id  INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount   NUMERIC(12,2) NOT NULL CHECK (amount > 0),
  saved_on DATE NOT NULL,
  note     VARCHAR(255) NOT NULL DEFAULT ''
);
CREATE INDEX idx_savings_user ON savings(user_id);

CREATE TABLE emergency_funds (
  id                         SERIAL PRIMARY KEY,
  user_id                    INT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  current_amount             NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (current_amount >= 0),
  monthly_essential_expenses NUMERIC(12,2) CHECK (monthly_essential_expenses >= 0),
  target_months              INT CHECK (target_months BETWEEN 1 AND 60),
  updated_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE financial_goals (
  id            SERIAL PRIMARY KEY,
  user_id       INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name          VARCHAR(100) NOT NULL,
  target_amount NUMERIC(12,2) NOT NULL CHECK (target_amount > 0),
  saved_amount  NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (saved_amount >= 0),
  target_date   DATE NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_goals_user ON financial_goals(user_id);

-- End-of-day check: what the app calculated vs what the user says they have.
CREATE TABLE daily_balances (
  id                 SERIAL PRIMARY KEY,
  user_id            INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  balance_date       DATE NOT NULL,
  calculated_balance NUMERIC(12,2) NOT NULL,
  reported_balance   NUMERIC(12,2) NOT NULL,
  difference         NUMERIC(12,2) GENERATED ALWAYS AS (reported_balance - calculated_balance) STORED,
  note               VARCHAR(255) NOT NULL DEFAULT '',
  UNIQUE (user_id, balance_date)
);

CREATE TABLE ai_conversations (
  id         SERIAL PRIMARY KEY,
  user_id    INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role       VARCHAR(10) NOT NULL CHECK (role IN ('user','assistant')),
  message    TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_ai_user_time ON ai_conversations(user_id, created_at);

-- ---------------------------------------------------------------
-- DEMO DATA (fictional). Login: demo@aibutler.demo / Demo@1234
-- pgcrypto's bcrypt hash is compatible with the app's bcrypt check.
-- ---------------------------------------------------------------
DO $$
DECLARE uid INT;
BEGIN
  INSERT INTO users(name, email, password_hash)
  VALUES ('Demo Student', 'demo@aibutler.demo', crypt('Demo@1234', gen_salt('bf')))
  RETURNING id INTO uid;

  INSERT INTO financial_profiles(user_id, monthly_income, opening_balance,
    monthly_fixed_expenses, monthly_savings_target, emergency_fund_target,
    emergency_reserve, setup_completed)
  VALUES (uid, 40000, 25000, 18000, 8000, 120000, 5000, TRUE);

  INSERT INTO expenses(user_id, name, category, amount, due_day) VALUES
    (uid, 'Rent', 'Rent', 10000, 1),
    (uid, 'Phone and internet', 'Bills', 800, 12);
  INSERT INTO emis(user_id, name, monthly_amount, due_day, remaining_months)
    VALUES (uid, 'Laptop EMI', 5000, 5, 8);
  INSERT INTO income(user_id, source, amount, pay_day) VALUES (uid, 'Salary', 40000, 1);
  INSERT INTO savings(user_id, amount, saved_on, note) VALUES (uid, 8000, CURRENT_DATE - 20, 'Demo savings');
  INSERT INTO emergency_funds(user_id, current_amount, monthly_essential_expenses, target_months)
    VALUES (uid, 30000, 20000, 6);
  INSERT INTO financial_goals(user_id, name, target_amount, saved_amount, target_date)
    VALUES (uid, 'New laptop', 60000, 15000, CURRENT_DATE + 240);

  INSERT INTO transactions(user_id, type, amount, category, description, txn_date, payment_method) VALUES
    (uid, 'income',  40000, 'Salary',   'Demo salary',     CURRENT_DATE - 3, 'Bank transfer'),
    (uid, 'expense', 10000, 'Rent',     'Demo rent',       CURRENT_DATE - 3, 'Bank transfer'),
    (uid, 'expense',  5000, 'EMI',      'Laptop EMI',      CURRENT_DATE - 2, 'Auto-debit'),
    (uid, 'expense',   250, 'Food',     'Lunch',           CURRENT_DATE - 2, 'Cash'),
    (uid, 'expense',   600, 'Transport','Metro card top-up',CURRENT_DATE - 1, 'Cash'),
    (uid, 'expense',  1200, 'Shopping', 'T-shirts',        CURRENT_DATE - 1, 'Card'),
    (uid, 'expense',   180, 'Food',     'Snacks',          CURRENT_DATE,     'Cash');
END $$;