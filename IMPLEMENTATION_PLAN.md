# Banking Web Application — Implementation Plan

> **Status:** Planning  
> **Type:** High-Level Architecture & Planning Document  
> **Stack:** HTML + Bootstrap (Frontend) · Python Flask (Backend) · SQLite (Database)

---

## 1. Solution Overview

### Objective

Build a lightweight, browser-based banking web application that allows registered customers to log in securely, view their account balance, and perform basic transactions (deposit and withdrawal) through a clean, responsive interface.

### Scope

| In Scope | Out of Scope |
|---|---|
| Customer login and session management | User self-registration / sign-up |
| Dashboard with account summary | Multi-account support per customer |
| View current account balance | Fund transfers between accounts |
| Deposit funds | Scheduled / recurring transactions |
| Withdraw funds | Admin panel or back-office tooling |
| Logout | External payment integrations |

### Users

| User Type | Description |
|---|---|
| **Customer** | The sole end-user persona. A pre-registered bank customer who logs in to view and manage their account. |

### Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | A customer must be able to log in using a username and password. |
| FR-02 | An authenticated customer must be presented with a personal dashboard. |
| FR-03 | The dashboard must display the customer's current account balance. |
| FR-04 | A customer must be able to deposit a positive monetary amount. |
| FR-05 | A customer must be able to withdraw an amount no greater than their current balance. |
| FR-06 | A customer must be able to log out, terminating their session. |
| FR-07 | Unauthenticated users must be redirected to the login page. |

### Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | **Security** — Passwords must be stored as hashed values; sessions must be server-side. |
| NFR-02 | **Responsiveness** — UI must be usable on both desktop and mobile via Bootstrap's grid. |
| NFR-03 | **Simplicity** — No external infrastructure dependencies; SQLite runs embedded in the backend. |
| NFR-04 | **Separation of Concerns** — Frontend and backend are cleanly separated into their own top-level folders. |
| NFR-05 | **Stateless REST-like Routes** — Backend routes follow a predictable, resource-oriented structure. |

### Assumptions

- Customer accounts are pre-seeded in the database (no public registration flow).
- The application is for demonstration / workshop purposes and will run locally.
- A single SQLite database file is sufficient; no production-grade persistence layer is needed.
- Bootstrap is loaded via CDN; no Node.js / npm build step is required for the frontend.
- Flask's built-in development server is the target runtime environment.

---

## 2. High-Level Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      BROWSER                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │              FRONTEND  (FRONTEND/)                │  │
│  │  HTML pages + Bootstrap CSS + Vanilla JS          │  │
│  │  login.html · dashboard.html · transactions.html  │  │
│  └──────────────────┬────────────────────────────────┘  │
└─────────────────────┼───────────────────────────────────┘
                      │  HTTP Request (form POST / fetch)
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   BACKEND  (BACKEND/)                   │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Python Flask App                   │    │
│  │  app.py · routes/ · services/ · models/         │    │
│  │                                                 │    │
│  │  Auth Routes   →  AuthService                   │    │
│  │  Account Routes →  AccountService               │    │
│  │  Transaction Routes → TransactionService        │    │
│  └────────────────────┬────────────────────────────┘    │
└───────────────────────┼─────────────────────────────────┘
                        │  SQLAlchemy ORM / sqlite3
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  DATABASE  (BACKEND/)                   │
│               SQLite  —  bank.db                        │
│          customers · accounts · transactions            │
└─────────────────────────────────────────────────────────┘
```

### Frontend → Backend → Database Interaction

1. **Frontend** serves static HTML files rendered in the browser. Forms and buttons trigger HTTP requests to Flask routes.
2. **Backend** receives requests, validates session state, delegates business logic to service modules, and queries the database via an ORM or the sqlite3 standard library.
3. **Database** persists customer credentials, account balances, and transaction history. All reads and writes are performed exclusively by the backend.

### Request Lifecycle

```
Browser                  Flask Route              Service Layer           SQLite
  │                           │                        │                    │
  │── POST /login ──────────► │                        │                    │
  │                           │── validate input ────► │                    │
  │                           │                        │── query customer ► │
  │                           │                        │◄── customer row ── │
  │                           │◄── auth result ─────── │                    │
  │◄── redirect /dashboard ── │                        │                    │
  │                           │                        │                    │
  │── GET /dashboard ───────► │                        │                    │
  │                           │── check session ─────► │                    │
  │                           │                        │── query balance ─► │
  │                           │                        │◄── balance row ─── │
  │◄── 200 dashboard HTML ─── │                        │                    │
```

---

## 3. Component Design

### Frontend Responsibilities

| Responsibility | Detail |
|---|---|
| **Rendering** | Deliver HTML pages for login, dashboard, and transaction forms. |
| **Styling** | Apply Bootstrap classes for layout, typography, cards, buttons, and responsive grid. |
| **User Input** | Collect credentials (login), deposit amounts, and withdrawal amounts via HTML forms. |
| **Feedback** | Display success/error flash messages returned by the backend inside styled Bootstrap alerts. |
| **Navigation** | Provide navigation links between dashboard sections and a logout button. |
| **No Business Logic** | The frontend does not validate balances or authenticate users — all logic lives in the backend. |

### Backend Responsibilities

| Responsibility | Detail |
|---|---|
| **Routing** | Map URL paths to handler functions for each feature (login, dashboard, deposit, withdraw, logout). |
| **Authentication** | Verify credentials, hash/verify passwords, and manage server-side Flask sessions. |
| **Session Guard** | Protect every route except login — redirect unauthenticated requests to `/login`. |
| **Business Logic** | Enforce deposit/withdrawal rules (positive amounts, sufficient balance). |
| **Data Access** | Read and write to the SQLite database using a consistent data access pattern. |
| **Response** | Return rendered HTML templates or redirect responses; no separate JSON API needed. |

### Database Responsibilities

| Responsibility | Detail |
|---|---|
| **Persistence** | Store customer credentials, account balances, and a log of all transactions. |
| **Integrity** | Enforce constraints to prevent negative balances at the storage level. |
| **Isolation** | All access is mediated by the backend; no direct database access from the browser. |

---

## 4. Folder Structure

```
banking-workshop/
│
├── IMPLEMENTATION_PLAN.md          ← This document
│
├── FRONTEND/                       ← All browser-facing static files
│   ├── templates/                  ← Jinja2 HTML templates (served by Flask)
│   │   ├── base.html               ← Shared layout: navbar, Bootstrap CDN link
│   │   ├── login.html              ← Login form page
│   │   ├── dashboard.html          ← Customer dashboard with balance summary
│   │   └── transactions.html       ← Deposit / Withdraw forms and feedback
│   └── static/                     ← Optional custom CSS or JS overrides
│       └── style.css               ← Minimal custom styles on top of Bootstrap
│
└── BACKEND/                        ← All server-side Python code and database
    ├── app.py                      ← Flask application factory; registers blueprints
    ├── config.py                   ← App configuration (secret key, DB path)
    ├── bank.db                     ← SQLite database file (auto-created on first run)
    ├── routes/                     ← URL route handlers grouped by feature
    │   ├── auth_routes.py          ← /login, /logout
    │   ├── dashboard_routes.py     ← /dashboard
    │   └── transaction_routes.py   ← /deposit, /withdraw
    ├── services/                   ← Business logic layer
    │   ├── auth_service.py         ← Credential verification, password hashing
    │   ├── account_service.py      ← Balance retrieval
    │   └── transaction_service.py  ← Deposit and withdrawal logic
    └── models/                     ← Data models / database access helpers
        └── db.py                   ← Database connection, table helpers
```

### Responsibility of Each Folder

| Folder / File | Responsibility |
|---|---|
| `FRONTEND/templates/` | HTML pages rendered server-side via Jinja2 and styled with Bootstrap. |
| `FRONTEND/static/` | Custom CSS or client-side JavaScript that supplements Bootstrap defaults. |
| `BACKEND/app.py` | Entry point — creates the Flask app, sets config, registers all route blueprints. |
| `BACKEND/config.py` | Centralised configuration values (secret key, database URI, debug flag). |
| `BACKEND/routes/` | Thin HTTP handlers — parse request data, call service layer, return responses. |
| `BACKEND/services/` | All business rules live here, keeping routes clean and testable in isolation. |
| `BACKEND/models/` | Database initialisation and query helpers; hides raw SQL from the rest of the app. |
| `BACKEND/bank.db` | SQLite database file — created automatically; not committed to source control. |

---

## 5. Module Breakdown

### Authentication Module

**Goal:** Verify a customer's identity and maintain session state across requests.

| Concern | Description |
|---|---|
| Login flow | Customer submits username + password → backend verifies hash → session cookie issued |
| Session guard | A decorator/helper checks `session["customer_id"]` before every protected route |
| Logout flow | Session is cleared server-side; customer is redirected to login |
| Password storage | Passwords are stored as hashed values (e.g. `werkzeug.security`) — never plain text |

**Key files:** `auth_routes.py`, `auth_service.py`

---

### Dashboard Module

**Goal:** Present a personalised landing page to the authenticated customer.

| Concern | Description |
|---|---|
| Account summary | Fetches and displays the customer's name and current balance |
| Navigation | Provides links to the deposit and withdrawal pages and the logout action |
| Session awareness | Reads `session["customer_id"]` to scope all data fetches to the logged-in customer |

**Key files:** `dashboard_routes.py`, `account_service.py`, `dashboard.html`

---

### Account Management Module

**Goal:** Provide the customer with a real-time view of their account balance.

| Concern | Description |
|---|---|
| Balance retrieval | Queries the account record linked to the current session's customer ID |
| Display | Balance is shown prominently on the dashboard with currency formatting |

**Key files:** `account_service.py`, `db.py`

---

### Transactions Module

**Goal:** Allow the customer to modify their balance through deposit and withdrawal actions.

| Concern | Description |
|---|---|
| Deposit | Accepts a positive amount, adds it to the balance, and records the transaction |
| Withdrawal | Accepts a positive amount ≤ current balance, deducts it, and records the transaction |
| Validation | Backend enforces that amounts are positive numbers and withdrawals do not exceed balance |
| Feedback | Success or error messages are flashed back to the UI via Flask's `flash()` mechanism |
| Audit trail | Each transaction is persisted with amount, type, and timestamp for record-keeping |

**Key files:** `transaction_routes.py`, `transaction_service.py`, `transactions.html`

---

## 6. Implementation Roadmap

### Development Phases

```
Phase 1 — Project Scaffolding
├── Create FRONTEND/ and BACKEND/ folder structures
├── Initialise Flask app with config and blueprint registration
├── Create base HTML template with Bootstrap CDN
└── Verify the development server starts cleanly

Phase 2 — Database Initialisation
├── Define database connection helper in models/db.py
├── Write initialisation routine to create tables on first run
└── Seed one or more test customer accounts

Phase 3 — Authentication
├── Build login route (GET form + POST handler)
├── Implement AuthService credential verification and password hashing
├── Set up Flask session on successful login
├── Implement session guard decorator
├── Implement logout route
└── Build login.html template with Bootstrap form and error alerts

Phase 4 — Dashboard
├── Build dashboard route with session guard
├── Implement AccountService balance retrieval
└── Build dashboard.html template showing customer name and balance

Phase 5 — Transactions
├── Build deposit route and TransactionService deposit method
├── Build withdrawal route and TransactionService withdrawal method
├── Enforce validation rules (positive amounts, sufficient balance)
├── Record each transaction in the database
└── Build transactions.html template with forms and flash message display

Phase 6 — Integration & Polish
├── End-to-end manual walkthrough of all user flows
├── Apply consistent Bootstrap styling across all pages
├── Verify session guard redirects unauthenticated access
└── Confirm balance updates correctly after deposit and withdrawal
```

### Estimated Effort

| Phase | Relative Effort |
|---|---|
| Phase 1 — Scaffolding | Low |
| Phase 2 — Database Initialisation | Low |
| Phase 3 — Authentication | Medium |
| Phase 4 — Dashboard | Low |
| Phase 5 — Transactions | Medium |
| Phase 6 — Integration & Polish | Low |

### Dependencies

| Dependency | Reason |
|---|---|
| Phase 1 must precede all others | Folder structure and Flask app must exist before any feature work |
| Phase 2 must precede Phase 3 | Auth service needs the customer table to exist before querying it |
| Phase 3 must precede Phase 4 & 5 | Dashboard and transactions require a working session guard |
| Phase 4 must precede Phase 5 | Dashboard provides the balance context that transactions update |
| Phase 5 must precede Phase 6 | All features must be built before integration testing begins |

---

*This document is intentionally kept at the planning level. It does not include database schemas, SQL scripts, API contracts, or step-by-step implementation code.*
