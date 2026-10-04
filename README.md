# AI Butler: Personal Finance Assistant

An AI-powered personal finance assistant for students. **Your financial information is entered
manually by you. This application does not connect to your bank account.**

It analyses, calculates, explains, warns, suggests and forecasts. It never moves money, buys,
sells, pays bills, takes loans or connects to any account. It is an educational tool, not
financial advice.

## Stack
React (Vite) · FastAPI · PostgreSQL · an LLM API (key supplied through `AI_API_KEY`)

## Features
Manual transaction entry · end-of-day balance check · dashboard with health indicator ·
safe daily spending · analytics and charts · spending forecast (labelled as an estimate) ·
EMI affordability · emergency fund · goals · AI Butler chat

## Prerequisites
Python 3.11+, Node.js 18+, PostgreSQL 14+

## 1. Database
```bash
createdb ai_butler
psql -d ai_butler -f database/schema.sql
```
This creates all tables plus fictional demo data. Demo login: `demo@aibutler.demo` / `Demo@1234`.
If `CREATE EXTENSION pgcrypto` fails, install your distribution's `postgresql-contrib` package.

## 2. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     # set DATABASE_URL, SECRET_KEY, AI_API_KEY
uvicorn app.main:app --reload --port 8000
```
Check http://localhost:8000/api/health and the API docs at http://localhost:8000/docs.
Without `AI_API_KEY` the Butler still answers with the app's own calculations.

## 3. Frontend
```bash
cd frontend
npm install
npm run dev              # http://localhost:5173
```
Optional `frontend/.env`: `VITE_API_URL=http://localhost:8000`

## 4. Verify the data rule
```bash
python scripts/verify_no_external_data.py
cd backend && pytest
```

## Known limitations
- Logout discards the token in the browser. The token itself stays valid until it expires
  (default 12 hours) because tokens are stateless.
- Forecasts and health labels are simple estimates, not official scores.
- Add rate limiting before any public deployment.
