# Banking Web Application — Implementation Plan

> **Reference:** [`STEP_BY_STEP_IMPLEMENTATION_GUIDE.md`](STEP_BY_STEP_IMPLEMENTATION_GUIDE.md)  
> **Stack:** HTML + Bootstrap · Python Flask · SQLite  
> **Pattern:** App-factory Flask · Blueprint routing · Service layer · Jinja2 templates  

---

## Overview

Build a full-stack browser-based banking application from scratch inside this workspace. The app allows pre-seeded customers to log in, view their balance on a dashboard, and perform deposits and withdrawals. All code follows the architecture defined in `IMPLEMENTATION_PLAN.md` and the step-by-step decisions in `STEP_BY_STEP_IMPLEMENTATION_GUIDE.md`.

**Folder layout (target):**
```
banking-workshop/
├── FRONTEND/
│   ├── templates/       ← Jinja2 HTML (base, login, dashboard, transactions)
│   └── static/          ← Custom CSS overrides
└── BACKEND/
    ├── app.py           ← Flask app factory; registers blueprints
    ├── config.py        ← SECRET_KEY, DATABASE_PATH, DEBUG
    ├── requirements.txt ← Pinned dependencies
    ├── models/
    │   └── db.py        ← Connection helper, init_db(), seed_db()
    ├── routes/
    │   ├── auth_routes.py
    │   ├── dashboard_routes.py
    │   └── transaction_routes.py
    ├── services/
    │   ├── auth_service.py
    │   ├── account_service.py
    │   └── transaction_service.py
    └── tests/
        ├── test_unit.py
        └── test_integration.py
```

---

## Sub-Task 1 — Project Scaffolding & Flask Entry Point

**Status:** [x] done

### Intent
Create the folder skeleton, install Flask, write `config.py` and a minimal `app.py` that starts the dev server cleanly. This is the foundation every other sub-task builds on.

### Expected Outcomes
- Directories `FRONTEND/templates/`, `FRONTEND/static/`, `BACKEND/routes/`, `BACKEND/services/`, `BACKEND/models/`, `BACKEND/tests/` all exist.
- `BACKEND/requirements.txt` lists `flask` and `werkzeug`.
- `BACKEND/config.py` exposes `SECRET_KEY`, `DATABASE_PATH`, `DEBUG`.
- `BACKEND/app.py` contains a `create_app()` factory that loads config, registers (empty) blueprints, and wires `template_folder` and `static_folder` to the `FRONTEND/` directories.
- Running `python BACKEND/app.py` starts the server without errors.

### Todo List
1. Create all required directories (no placeholder files needed beyond `__init__.py` where Python requires them).
2. Write `BACKEND/config.py` with the three configuration values. Use `os.path` to derive an absolute `DATABASE_PATH` relative to `config.py`'s location.
3. Write `BACKEND/app.py` with a `create_app()` factory. Point `template_folder` to `../FRONTEND/templates` and `static_folder` to `../FRONTEND/static`. Load config from `config.py`. Register placeholder blueprints (stubs to be filled in later sub-tasks). Add `if __name__ == "__main__": app.run()` at the bottom.
4. Create `BACKEND/requirements.txt` with `flask` and `werkzeug`.
5. Add empty `__init__.py` files to `routes/`, `services/`, `models/`, and `tests/` packages.

### Relevant Context
- Guide §1.2–§1.5, §2.1, §2.2, §4.1
- Plan §4 (folder structure table)
- `template_folder` and `static_folder` must be passed to `Flask(...)` constructor since they live outside `BACKEND/`.

---

## Sub-Task 2 — Database Layer (models/db.py)

**Status:** [x] done

### Intent
Build the only file that talks directly to SQLite: connection helper, table creation, and seed data. All other layers will import helpers from here rather than touching `sqlite3` directly.

### Expected Outcomes
- `BACKEND/models/db.py` contains:
  - `get_db()` — opens/returns a per-request connection stored on Flask's `g`, with `row_factory = sqlite3.Row`.
  - `close_db()` — teardown function registered with `@teardown_appcontext`.
  - `init_db()` — creates `customers`, `accounts`, and `transactions` tables with `IF NOT EXISTS`.
  - `seed_db()` — inserts two test customers (e.g., `alice` / `password123` and `bob` / `secret456`) with hashed passwords and a starting balance of `1000.00` each — only when the table is empty.
- `app.py` calls `init_db()` and `seed_db()` inside `create_app()` within the app context.
- `bank.db` is created automatically the first time the app starts.

### Todo List
1. Write `get_db()` using Flask's `g` pattern; store the open connection as `g._database`.
2. Write `close_db(e=None)` and register it via `app.teardown_appcontext` inside `create_app()` (or export it and call from `app.py`).
3. Write `init_db()` with `CREATE TABLE IF NOT EXISTS` for all three tables:
   - `customers(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, full_name TEXT NOT NULL)`
   - `accounts(id INTEGER PRIMARY KEY, customer_id INTEGER UNIQUE NOT NULL REFERENCES customers(id), balance REAL NOT NULL DEFAULT 0.0)`
   - `transactions(id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id), type TEXT NOT NULL, amount REAL NOT NULL, timestamp TEXT NOT NULL)`
4. Write `seed_db()` — check `SELECT COUNT(*) FROM customers`; if zero, insert two rows using `werkzeug.security.generate_password_hash`.
5. Call both from `create_app()` inside `with app.app_context():`.

### Relevant Context
- Guide §2.3, §4.3
- Plan §3 (Database Responsibilities), §5 (Transactions Module)
- Use `sqlite3.Row` row factory for dict-style access (`row["balance"]`).

---

## Sub-Task 3 — Service Layer

**Status:** [x] done

### Intent
Implement all business logic in three service files. Routes will call these; services will never import Flask request/session objects.

### Expected Outcomes
- `BACKEND/services/auth_service.py` — `verify_credentials(username, password)` returns customer row or `None`.
- `BACKEND/services/account_service.py` — `get_account(customer_id)` returns the account row for the given customer.
- `BACKEND/services/transaction_service.py`:
  - `deposit(customer_id, amount_str)` — validates, updates balance, inserts transaction row; returns `(success: bool, message: str, new_balance: float|None)`.
  - `withdraw(customer_id, amount_str)` — same signature; additionally checks for sufficient funds.
- All amount parsing uses `float()` inside a `try/except ValueError` block.
- No Flask imports in any service file — only `db.py` helpers and `werkzeug`.

### Todo List
1. `auth_service.py`: query `customers` by username via `get_db()`; use `check_password_hash` to verify; return row or `None`.
2. `account_service.py`: simple single-row query of `accounts` by `customer_id`; return row.
3. `transaction_service.py`:
   a. Write `_parse_amount(amount_str)` private helper — returns `float` or raises `ValueError`.
   b. `deposit()`: parse amount → validate > 0 → `UPDATE accounts SET balance = balance + ? WHERE customer_id = ?` → `INSERT INTO transactions` → return `(True, success_msg, new_balance)`.
   c. `withdraw()`: parse amount → validate > 0 → fetch current balance → validate `amount <= balance` → `UPDATE` + `INSERT` → return `(True, success_msg, new_balance)`.
   d. All failures return `(False, error_msg, None)` — no exceptions propagate to routes.

### Relevant Context
- Guide §2.5, §5.1–§5.4
- Plan §5 (each module's concern table)
- Timestamps: use `datetime.utcnow().isoformat()` for the `transactions.timestamp` column.

---

## Sub-Task 4 — Backend Routes (Blueprints)

**Status:** [x] done

### Intent
Wire up the HTTP layer: three blueprint files that handle request parsing and delegate to services. Routes stay thin — no business logic, just parse → call service → respond.

### Expected Outcomes
- `BACKEND/routes/auth_routes.py` — Blueprint `auth_bp`, prefix none:
  - `GET /login` — renders `login.html`; redirects to `/dashboard` if already logged in.
  - `POST /login` — calls `verify_credentials`; sets `session["customer_id"]`; redirects or flashes.
  - `GET /logout` — clears session; redirects to `/login`.
- `BACKEND/routes/dashboard_routes.py` — Blueprint `dashboard_bp`:
  - `GET /dashboard` — session guard → `get_account()` → renders `dashboard.html` with name + balance.
- `BACKEND/routes/transaction_routes.py` — Blueprint `transaction_bp`:
  - `GET /transactions` — session guard → renders `transactions.html`.
  - `POST /deposit` — session guard → `deposit()` → flash result → redirect `/transactions`.
  - `POST /withdraw` — session guard → `withdraw()` → flash result → redirect `/transactions`.
- A shared `_login_required()` helper (in a common utility or inline per blueprint) enforces the session guard.
- All blueprints registered in `create_app()`.

### Todo List
1. Write `BACKEND/routes/auth_routes.py` with the three routes.
2. Write a `login_required` helper (can live in `BACKEND/routes/utils.py` or be replicated; keep it simple for workshop scope).
3. Write `BACKEND/routes/dashboard_routes.py`.
4. Write `BACKEND/routes/transaction_routes.py`.
5. Register all three blueprints in `app.py`'s `create_app()`.
6. Ensure POST-Redirect-GET pattern is used in deposit and withdraw routes.

### Relevant Context
- Guide §2.4, §2.6, §4.2
- Plan §3 (Backend Responsibilities), §5 (Auth and Transactions modules)
- `flash(message, "success")` / `flash(message, "danger")` — categories map to Bootstrap alert colours in templates.

---

## Sub-Task 5 — Frontend Templates

**Status:** [x] done

### Intent
Build the four Jinja2 HTML templates using Bootstrap 5 via CDN. No custom build step; all styling from Bootstrap utility classes.

### Expected Outcomes
- `FRONTEND/templates/base.html` — DOCTYPE, `<head>` with Bootstrap CDN, viewport meta, title block, navbar with conditional Logout link, flash messages loop, `{% block content %}` placeholder.
- `FRONTEND/templates/login.html` — extends `base.html`; centered card with username + password fields, POST to `/login`, Bootstrap form styles.
- `FRONTEND/templates/dashboard.html` — extends `base.html`; welcome heading, large balance card (`text-success`), two action buttons linking to `/transactions`.
- `FRONTEND/templates/transactions.html` — extends `base.html`; two-column grid (`col-md-6`) with Deposit card (green button) and Withdraw card (red button); "Back to Dashboard" link.
- `FRONTEND/static/style.css` — minimal overrides only (e.g., body background colour, balance font size).

### Todo List
1. Write `base.html` — include Bootstrap 5 CDN link, flash messages `{% for category, message in get_flashed_messages(with_categories=True) %}` loop, `{% block content %}` tag, navbar.
2. Write `login.html` — centered card, two inputs, submit button, extends base.
3. Write `dashboard.html` — greeting, balance display, two nav buttons.
4. Write `transactions.html` — two-column deposit/withdraw layout with amount inputs and submit buttons.
5. Write `FRONTEND/static/style.css` with minimal additions.

### Relevant Context
- Guide §3.1–§3.5, §4.4
- Plan §3 (Frontend Responsibilities)
- Bootstrap 5 CDN: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css`
- Jinja2 variables from routes: `customer_name`, `balance` (dashboard); no variables needed for transactions (all feedback via flash).
- Balance formatting: use `"${:.2f}".format(balance)` in the route before passing to template, or a Jinja2 `| round(2)` filter.

---

## Sub-Task 6 — Testing

**Status:** [x] done

### Intent
Write unit tests for the service layer and integration tests for the Flask routes. Both suites use an in-memory SQLite database so `bank.db` is never touched.

### Expected Outcomes
- `BACKEND/tests/test_unit.py` — `unittest.TestCase` subclass; in-memory DB setup/teardown; tests for `verify_credentials`, `deposit`, and `withdraw` covering all cases from Guide §6.1.
- `BACKEND/tests/test_integration.py` — Flask test client; tests for all route scenarios from Guide §6.2.
- All tests pass when run with `python -m pytest BACKEND/tests/` from the workspace root.

### Todo List
1. Write `test_unit.py`:
   - `setUp`: create `:memory:` SQLite DB, run `init_db()`, seed one test customer.
   - Auth tests: correct credentials → returns row; wrong password → `None`; unknown user → `None`.
   - Deposit tests: positive amount increases balance; zero returns error; negative returns error.
   - Withdraw tests: valid amount decreases balance; exact balance → zero; over-balance → insufficient funds error; zero → error.
2. Write `test_integration.py`:
   - Configure app with `TESTING=True` and in-memory DB.
   - Route tests per checklist in Guide §6.2.
3. Add `pytest` to `requirements.txt`.

### Relevant Context
- Guide §6.1, §6.2
- Services must accept an optional `db` connection parameter (or the app context must supply it via `g`) for testability — review how `get_db()` is implemented and adjust if needed.

---

## Sub-Task 7 — Final Integration & Validation

**Status:** [x] done

### Intent
Do a final end-to-end pass: verify the app starts cleanly, all routes work, flash messages display correctly, POST-Redirect-GET prevents double submission, and the manual testing checklist from Guide §6.3 passes.

### Expected Outcomes
- `python BACKEND/app.py` starts without errors; `bank.db` is created automatically.
- Full login → dashboard → deposit → withdrawal → logout flow works in a browser.
- Unauthenticated access to `/dashboard` or `/transactions` redirects to `/login`.
- Flash messages appear correctly (success in green, error in red) and are dismissible.
- Responsive layout verified at narrow width.
- All automated tests pass.
- A concise `README.md` at the workspace root with startup instructions is created.

### Todo List
1. Walk through every route and confirm request/response cycle (manual trace).
2. Fix any import paths, blueprint registration issues, or template variable mismatches found.
3. Confirm `bank.db` is **not** committed — add it to `.gitignore`.
4. Write `README.md` with: Prerequisites, virtual-env setup steps, how to run, and the two test user credentials.
5. Run `python -m pytest BACKEND/tests/` — all tests must pass.

### Relevant Context
- Guide §6.3 (manual testing checklist), §7.1 (run locally)
- Plan §6 (Phase 6 — Integration & Polish)

---

## Implementation Notes

- **No external DB server** — SQLite only; `sqlite3` is stdlib.
- **No Node / npm** — Bootstrap loaded from CDN.
- **Password hashing** — `werkzeug.security` only; never store plain-text passwords.
- **Session data** — store only `customer_id` (integer) in the Flask session cookie.
- **Balance precision** — store as `REAL` in SQLite; format as `$X.XX` at display time.
- **Error boundary** — service layer never raises to routes; always returns a `(bool, str, value|None)` tuple.
