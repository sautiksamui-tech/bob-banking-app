# Banking Web Application

A lightweight, full-stack banking demo built with **Python Flask**, **SQLite**, and **Bootstrap 5**.

> Implements all requirements from `STEP_BY_STEP_IMPLEMENTATION_GUIDE.md`.

---

## Features

- Customer login with hashed passwords (Werkzeug)
- Session-based authentication with session guard on every protected route
- Dashboard displaying current account balance
- Deposit and withdrawal with server-side validation
- Flash messages (success / error) displayed as dismissible Bootstrap alerts
- Responsive layout (Bootstrap 5 grid — works on mobile and desktop)
- POST-Redirect-GET pattern prevents double-submission on browser refresh

---

## Prerequisites

- Python 3.9 or higher (`python --version`)
- pip (ships with Python 3)

No Node.js, Docker, or external database server required.

---

## Quick Start

```powershell
# 1. Navigate to the BACKEND folder
cd BACKEND

# 2. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate        # Windows PowerShell
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the development server
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

The `bank.db` SQLite file is created automatically on the first run.

---

## Demo Credentials

| Username | Password    | Starting Balance |
|----------|-------------|-----------------|
| alice    | password123 | $1,000.00        |
| bob      | secret456   | $2,500.00        |

---

## Project Structure

```
banking-workshop/
├── FRONTEND/
│   ├── templates/
│   │   ├── base.html           ← Shared layout: navbar, Bootstrap CDN, flash messages
│   │   ├── login.html          ← Login form
│   │   ├── dashboard.html      ← Balance summary + action buttons
│   │   └── transactions.html   ← Deposit / Withdraw forms
│   └── static/
│       └── style.css           ← Minimal CSS overrides
│
└── BACKEND/
    ├── app.py                  ← Flask app factory; registers blueprints
    ├── config.py               ← SECRET_KEY, DATABASE_PATH, DEBUG
    ├── requirements.txt        ← Pinned dependencies
    ├── models/
    │   └── db.py               ← SQLite connection, init_db(), seed_db()
    ├── routes/
    │   ├── auth_routes.py      ← GET/POST /login, GET /logout
    │   ├── dashboard_routes.py ← GET /dashboard
    │   ├── transaction_routes.py  ← GET /transactions, POST /deposit, POST /withdraw
    │   └── utils.py            ← login_required decorator
    └── services/
        ├── auth_service.py         ← verify_credentials()
        ├── account_service.py      ← get_account()
        └── transaction_service.py  ← deposit(), withdraw()
```

---

## Running Tests

```powershell
# From the workspace root (banking-workshop/)
cd BACKEND
.\venv\Scripts\activate

# All tests (unit + integration)
python -m pytest tests/ -v

# Unit tests only
python -m pytest tests/test_unit.py -v

# Integration tests only
python -m pytest tests/test_integration.py -v
```

**34 tests** — 16 unit, 18 integration. Both suites use an in-memory SQLite
database so `bank.db` is never modified by tests.

---

## Architecture

```
Browser → Flask Routes → Service Layer → SQLite (bank.db)
```

| Layer | Location | Responsibility |
|---|---|---|
| Frontend | `FRONTEND/templates/` | Jinja2 HTML + Bootstrap 5 styling |
| Routes | `BACKEND/routes/` | HTTP parsing, session guard, redirect |
| Services | `BACKEND/services/` | All business logic; no Flask imports |
| Database | `BACKEND/models/db.py` | Only file that touches SQLite directly |

---

## Security Notes

- Passwords stored as Werkzeug bcrypt-compatible hashes — never plain text.
- Only `customer_id` (integer) stored in the session cookie.
- Generic "Invalid username or password" message prevents username enumeration.
- All protected routes guarded by the `@login_required` decorator.
- In production: move `SECRET_KEY` to an environment variable and set `DEBUG=False`.
