# Banking Web Application — Step-by-Step Implementation Guide

> **Reference:** [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)  
> **Purpose:** Plain-English instructions explaining *how* to build each part of the application and *why* each decision is made — without raw source code.  
> **Stack:** HTML + Bootstrap · Python Flask · SQLite

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Backend Implementation](#2-backend-implementation)
3. [Frontend Implementation](#3-frontend-implementation)
4. [Integration Steps](#4-integration-steps)
5. [Validation Rules](#5-validation-rules)
6. [Testing](#6-testing)
7. [Deployment](#7-deployment)

---

## 1. Environment Setup

### 1.1 Prerequisites

Before writing a single line of application code, confirm that the following tools are present on your machine:

- **Python 3.9 or higher** — Flask requires a modern Python version. Run `python --version` to confirm.
- **pip** — Python's package manager. It ships with Python 3 by default.
- A **terminal / command prompt** — PowerShell on Windows, Terminal on macOS/Linux.
- A **text editor or IDE** — VS Code is recommended for its Python extension and integrated terminal.

You do not need Node.js, Docker, or any database server. SQLite is part of Python's standard library and requires no installation.

---

### 1.2 Create the Project Folder Structure

Create the top-level project directory and the two main sub-folders that separate concerns:

- `FRONTEND/` — holds all HTML templates and static assets.
- `BACKEND/` — holds all Python source files and the SQLite database.

Inside `FRONTEND/`, create two sub-folders: `templates/` and `static/`.

Inside `BACKEND/`, create three sub-folders: `routes/`, `services/`, and `models/`.

The reason for this split is **separation of concerns** — the browser-facing code never mixes with server-side logic. Keeping them in distinct folders also makes it easy to find files when the project grows.

---

### 1.3 Create and Activate a Virtual Environment

A virtual environment isolates this project's Python packages from the rest of your system. This prevents version conflicts with other Python projects.

- Navigate into the `BACKEND/` folder in your terminal.
- Create a virtual environment in a folder named `venv` using the `python -m venv venv` command.
- Activate it:
  - On **Windows**: run `venv\Scripts\activate`
  - On **macOS / Linux**: run `source venv/bin/activate`

Once activated, your terminal prompt will show `(venv)` as a prefix. All packages you install from this point will be local to this environment.

---

### 1.4 Install Flask and Dependencies

With the virtual environment active, install the required packages using `pip`:

- **Flask** — the web framework. Install with `pip install flask`.
- **Werkzeug** — already included with Flask. It provides the password hashing utilities (`generate_password_hash` and `check_password_hash`) that you will use for secure credential storage.

SQLite support is built into Python via the `sqlite3` module — no additional install needed.

After installing, create a `requirements.txt` file by running `pip freeze > requirements.txt`. This file records exact package versions so any other developer can reproduce your environment with `pip install -r requirements.txt`.

---

### 1.5 Verify the Setup

Create a minimal `app.py` in `BACKEND/` that starts a Flask server and returns a plain "Hello, Bank!" message at the root URL. Run it with `python app.py` and open `http://127.0.0.1:5000` in a browser. If you see the message, your environment is working correctly. Delete or replace the test route before continuing.

---

## 2. Backend Implementation

### 2.1 Application Entry Point — `app.py`

`app.py` is the heart of the Flask application. Its responsibilities are:

1. **Create the Flask app instance** — this is the object that ties everything together.
2. **Load configuration** — tell Flask where to find the secret key, database file, and debug settings by importing from `config.py`.
3. **Register blueprints** — import the route modules for authentication, dashboard, and transactions, and attach them to the app. Blueprints are Flask's way of splitting routes across multiple files without losing the connection to the main app.
4. **Initialise the database** — call the database setup function once when the app starts so that tables are created if they do not already exist.

The app factory pattern (wrapping all of the above in a `create_app()` function) is a best practice that makes the app easier to test. Call `create_app()` at the bottom of `app.py` and pass the result to Flask's development server.

---

### 2.2 Configuration — `config.py`

Store all environment-specific values in one place so they are easy to change without hunting through every file:

- **`SECRET_KEY`** — a long, random string that Flask uses to sign session cookies. Without this, sessions cannot be trusted. In development, a hardcoded string is acceptable. In production, this must come from an environment variable.
- **`DATABASE_PATH`** — the file path to `bank.db`. Using an absolute path (derived from `__file__`) prevents issues when the app is run from different working directories.
- **`DEBUG`** — set to `True` during development so Flask shows detailed error pages and auto-reloads on file changes. Set to `False` for production.

---

### 2.3 Database Layer — `models/db.py`

This file is the only place in the application that talks directly to SQLite. Everything else goes through it.

**Connection helper:** Write a function that opens a connection to `bank.db` and returns it. Use SQLite's `row_factory = sqlite3.Row` setting so that query results can be accessed like dictionaries (e.g., `row["balance"]`) rather than positional tuples.

**Initialisation routine:** Write a function called `init_db()` that creates the three tables if they do not already exist:
- A `customers` table for login credentials (username, hashed password).
- An `accounts` table that links a customer to a balance amount.
- A `transactions` table that records every deposit and withdrawal with a timestamp.

**Seed function:** Write a function that inserts one or two test customers with known credentials so you can log in immediately. Hash the passwords using Werkzeug's `generate_password_hash` before inserting. Only seed data if the `customers` table is empty so re-running the app does not duplicate records.

Call `init_db()` and the seed function from `app.py` when the app starts.

---

### 2.4 Routes

Routes are thin HTTP handlers. Their job is to:
1. Receive an HTTP request.
2. Extract data from the request (form fields, session values).
3. Call the appropriate service function.
4. Return a rendered template or a redirect.

Routes must never contain business logic — that belongs in the service layer.

#### Authentication Routes — `routes/auth_routes.py`

**`GET /login`**  
Render the login HTML template. If the user is already logged in (a customer ID exists in the session), redirect them directly to the dashboard instead of showing the form again.

**`POST /login`**  
Read the `username` and `password` fields from the submitted form. Pass them to `AuthService.verify_credentials()`. If the service returns a valid customer record, store the customer's ID in the Flask session and redirect to `/dashboard`. If verification fails, re-render the login page with a flash message explaining that the username or password was incorrect. Do not specify *which* field was wrong — vague error messages prevent username enumeration attacks.

**`GET /logout`**  
Call `session.clear()` to remove all data from the server-side session, then redirect to `/login`. No service call is needed — this is purely a session operation.

#### Dashboard Route — `routes/dashboard_routes.py`

**`GET /dashboard`**  
Check that `customer_id` is in the session (apply the session guard). Call `AccountService.get_balance()` with the customer ID. Pass the customer's name and balance to the dashboard template and render it.

#### Transaction Routes — `routes/transaction_routes.py`

**`GET /transactions`**  
Apply the session guard. Render the transactions page which contains both the deposit and withdrawal forms side by side.

**`POST /deposit`**  
Apply the session guard. Read the `amount` field from the form. Pass the customer ID and amount to `TransactionService.deposit()`. Flash a success or error message based on the result. Redirect back to the transactions page (use POST-Redirect-GET pattern to prevent double-submission on browser refresh).

**`POST /withdraw`**  
Apply the session guard. Read the `amount` field from the form. Pass the customer ID and amount to `TransactionService.withdraw()`. Flash a success or error message. Redirect back to the transactions page.

---

### 2.5 Services

Services contain all business logic. They know nothing about HTTP — they accept plain Python values and return results or raise exceptions.

#### `services/auth_service.py`

**`verify_credentials(username, password)`**  
Query the `customers` table for a row matching the given username. If no row is found, return `None` immediately (do not reveal whether the username or password was wrong). If a row is found, use Werkzeug's `check_password_hash` to compare the submitted password against the stored hash. Return the customer row if the hash matches, otherwise return `None`.

#### `services/account_service.py`

**`get_balance(customer_id)`**  
Query the `accounts` table for the row linked to the given customer ID. Return the balance value. This function is intentionally simple — it is a single database read.

#### `services/transaction_service.py`

**`deposit(customer_id, amount)`**  
Validate that `amount` is a number greater than zero. If the validation fails, return an error result. Otherwise, add the amount to the customer's current balance in the `accounts` table and insert a new row into the `transactions` table with type "deposit", the amount, and the current timestamp. Return a success result with the new balance.

**`withdraw(customer_id, amount)`**  
Validate that `amount` is a number greater than zero. Fetch the current balance. Check that `amount` is less than or equal to the current balance. If either check fails, return an error result with a descriptive message. Otherwise, subtract the amount from the balance in the `accounts` table and insert a row into `transactions` with type "withdrawal", the amount, and the timestamp. Return a success result with the new balance.

---

### 2.6 Session Management

Flask sessions use a **signed cookie** stored in the browser. The cookie value is tamper-proof because it is signed with the `SECRET_KEY`, but its contents are readable — so never store sensitive data like passwords or full account details in it. Storing only the `customer_id` (an integer) is both safe and sufficient.

**Session guard pattern:** Create a helper function or decorator that checks whether `session.get("customer_id")` exists and is not `None`. If it is missing, redirect to `/login`. Apply this guard at the top of every route that should be protected. This ensures that manually visiting `/dashboard` without logging in is always redirected.

**Session lifetime:** Flask sessions expire when the browser is closed by default. For the workshop scope, this default is acceptable.

---

### 2.7 Error Handling

For this application, two categories of errors need handling:

**User errors (expected):** Invalid login credentials, negative deposit amounts, insufficient funds for a withdrawal. These are not exceptions — handle them with conditional logic in the service layer and communicate them back to the user via Flask's `flash()` mechanism. Flashed messages are stored in the session for exactly one request and displayed as Bootstrap alert boxes in the next rendered page.

**Application errors (unexpected):** Database connection failures, unexpected `None` values. Wrap database calls in try/except blocks within `db.py` and let Flask's built-in error pages handle unrecoverable errors during development. In production, configure a custom 500 error page that shows a friendly message without exposing stack traces.

---

## 3. Frontend Implementation

All HTML templates live in `FRONTEND/templates/`. Flask is configured to look for templates there. All pages extend a shared `base.html` to avoid repeating the Bootstrap CDN link and navbar on every page.

### 3.1 Base Template — `base.html`

The base template defines the outer shell that every other page inherits from. It should contain:

- The standard HTML `<!DOCTYPE html>` declaration and `<html>`, `<head>`, `<body>` tags.
- Inside `<head>`: the Bootstrap CDN `<link>` tag, a `<meta charset>` tag, a `<meta name="viewport">` tag for mobile responsiveness, and a `<title>` block that child templates can override.
- Inside `<body>`: a Bootstrap **navbar** at the top with the bank name on the left and a "Logout" link on the right (only visible when a user is logged in). A main content `<div>` wrapped in Bootstrap's `container` class. A **flash messages block** just above the content area that loops through any flashed messages and renders each one as a Bootstrap dismissible alert.
- A `{% block content %}{% endblock %}` tag where each child page inserts its unique content.

The reason for a base template is DRY (Don't Repeat Yourself) — updating the navbar or Bootstrap version in one place updates every page.

---

### 3.2 Login Page — `login.html`

This page extends `base.html`. Its content block contains:

- A **centered card** using Bootstrap's card component. Cards give a clean, professional look with minimal effort.
- Inside the card: a title ("Sign In to Your Account"), and an HTML `<form>` with `method="POST"` and `action="/login"`.
- Two form groups: one for "Username" (text input) and one for "Password" (password input). Each uses Bootstrap's `form-label` and `form-control` classes for consistent styling.
- A full-width "Login" submit button styled with `btn btn-primary`.
- The flash messages block (inherited from base) will automatically display the "Invalid credentials" error above the card when login fails.

The form uses `POST` rather than `GET` to prevent credentials from appearing in the browser URL bar or server logs.

---

### 3.3 Dashboard Page — `dashboard.html`

This page extends `base.html`. It is what the customer sees immediately after logging in. Its content block contains:

- A **welcome heading** that greets the customer by name using a Jinja2 template variable (e.g., `{{ customer_name }}`).
- A **balance card** — a prominently styled Bootstrap card that displays the current balance in large text with a currency symbol. Use a `text-success` or `text-primary` colour class to make it visually distinct.
- Two **action buttons** below the balance card: "Deposit Funds" and "Withdraw Funds", each linking to the transactions page. Style them as Bootstrap outline buttons to keep the dashboard clean.
- A brief account summary line (e.g., "Account Status: Active") to make the page feel complete.

---

### 3.4 Transactions Page — `transactions.html`

This page extends `base.html`. It contains both the deposit and withdrawal forms. Use Bootstrap's **two-column grid** (`col-md-6`) to place them side by side on desktop and stacked on mobile.

**Deposit Form (left column):**
- A card with the title "Deposit Funds".
- A single number input field labelled "Amount" with a `min="0.01"` attribute and `step="0.01"` for decimal values.
- A "Deposit" submit button styled with `btn btn-success`.
- The form posts to `/deposit`.

**Withdraw Form (right column):**
- A card with the title "Withdraw Funds".
- A single number input field labelled "Amount" with the same constraints as the deposit form.
- A "Withdraw" submit button styled with `btn btn-danger` to visually signal that this action removes money.
- The form posts to `/withdraw`.

**Flash messages** inherited from the base template will appear above both cards, confirming success ("Deposit of $500.00 was successful") or explaining a failure ("Insufficient funds for this withdrawal").

A "Back to Dashboard" link at the top of the page provides easy navigation.

---

### 3.5 Bootstrap Layout Principles

Apply these Bootstrap conventions consistently across all pages:

- **Container:** Wrap all page content in `<div class="container mt-4">` to centre it and add top margin.
- **Grid:** Use `<div class="row">` and `<div class="col-md-X">` to create multi-column layouts that collapse to single-column on small screens.
- **Cards:** Use `.card`, `.card-header`, `.card-body` to group related content visually.
- **Buttons:** Use `btn btn-primary` for the main action, `btn btn-success` for additive actions (deposit), `btn btn-danger` for destructive actions (withdraw), and `btn btn-outline-secondary` for navigation actions.
- **Alerts:** Use `alert alert-success` for positive feedback and `alert alert-danger` for errors. Add `alert-dismissible` and a close button so users can dismiss them.
- **Spacing utilities:** Use Bootstrap's margin (`mt-`, `mb-`, `mx-auto`) and padding (`p-`, `py-`) utility classes instead of writing custom CSS for spacing.

---

## 4. Integration Steps

### 4.1 Connect Flask to the Frontend Templates

Flask needs to know where to find the HTML templates. By default, Flask looks for a `templates/` folder relative to the application's root. Since the templates live in `FRONTEND/templates/`, you must tell Flask explicitly by passing the `template_folder` argument when creating the Flask app instance.

Similarly, if you have a `FRONTEND/static/` folder for CSS or JS files, pass the `static_folder` argument pointing to it.

Once configured, every call to Flask's `render_template("login.html")` will resolve correctly to `FRONTEND/templates/login.html`.

---

### 4.2 Connect Flask Routes to HTML Forms

HTML forms connect to Flask routes through their `action` and `method` attributes.

- The `action` value must exactly match the URL path defined in the corresponding Flask route (e.g., `action="/login"`).
- The `method` must match what the route expects (`GET` for page loads, `POST` for form submissions).
- The `name` attribute on each `<input>` field is what Flask reads on the server side via `request.form.get("field_name")`. Make sure the names in the HTML match the keys the backend expects.

For redirect-after-POST: after a successful deposit or withdrawal, the Flask route should issue a redirect response rather than rendering a template directly. This prevents the browser from resubmitting the form if the user hits the refresh button.

---

### 4.3 Connect Flask to SQLite

Flask connects to SQLite through Python's built-in `sqlite3` module. The connection is opened at the start of a request and closed when the request finishes.

Use Flask's `g` object (a per-request global) to store the database connection. Write a `get_db()` function that checks if a connection already exists on `g` — if yes, return it; if no, open a new one and store it on `g`. Register a teardown function using Flask's `@app.teardown_appcontext` decorator to close the connection at the end of every request automatically.

This pattern avoids opening a new connection on every database call within a single request and ensures connections are not leaked between requests.

---

### 4.4 Pass Data from Backend to Templates

Flask's `render_template()` function accepts keyword arguments that become variables available inside the Jinja2 template. For example, passing `balance=500.00` makes `{{ balance }}` available in the HTML. Pass only the data the template needs — do not pass entire database row objects or raw SQL results. Extract the values you need in the route handler and pass them as named parameters.

For flash messages, call `flash("message text", "category")` in the route before redirecting. In the template, call `get_flashed_messages(with_categories=True)` inside a loop to render each message as a Bootstrap alert with the appropriate colour class based on the category (`"success"` or `"danger"`).

---

## 5. Validation Rules

Validation happens at two levels: the HTML form (client-side, convenience only) and the Flask service layer (server-side, authoritative). The server-side rules are the ones that actually protect the system. Client-side validation only improves the user experience for honest users.

### 5.1 Login Validation

| Rule | Where Enforced | Response on Failure |
|---|---|---|
| Username field must not be empty | HTML `required` attribute + service layer | Re-render login page with flash error |
| Password field must not be empty | HTML `required` attribute + service layer | Re-render login page with flash error |
| Username must exist in the database | `AuthService.verify_credentials()` | Flash "Invalid username or password" (generic) |
| Password must match the stored hash | `AuthService.verify_credentials()` | Flash "Invalid username or password" (generic) |

**Why use a generic error message?** Saying "Username not found" tells an attacker which usernames are valid. A single message for both failures prevents this information leak.

---

### 5.2 Balance Validation

| Rule | Where Enforced | Response on Failure |
|---|---|---|
| Balance must be retrieved for the logged-in customer only | Session ID used as query key | Unauthorised access is blocked by session guard |
| Balance must never go below zero | `TransactionService.withdraw()` pre-check | Flash "Insufficient funds" error |
| Balance display must be formatted as currency | Template rendering (Jinja2 filter or Python formatting) | N/A — display concern only |

---

### 5.3 Deposit Checks

| Rule | Where Enforced | Response on Failure |
|---|---|---|
| Amount field must not be empty | HTML `required` attribute + service layer | Flash error |
| Amount must be a valid number | `float()` conversion with try/except | Flash "Please enter a valid amount" |
| Amount must be greater than zero | Service layer comparison | Flash "Deposit amount must be greater than zero" |
| No upper limit on deposit | Business decision — not enforced | N/A |

After a successful deposit, the service layer updates the account balance and records the transaction. The route then flashes a confirmation message showing the deposited amount and the new balance.

---

### 5.4 Withdrawal Checks

| Rule | Where Enforced | Response on Failure |
|---|---|---|
| Amount field must not be empty | HTML `required` attribute + service layer | Flash error |
| Amount must be a valid number | `float()` conversion with try/except | Flash "Please enter a valid amount" |
| Amount must be greater than zero | Service layer comparison | Flash "Withdrawal amount must be greater than zero" |
| Amount must not exceed current balance | Service layer comparison against current balance | Flash "Insufficient funds. Your balance is $X.XX" |

The withdrawal check fetches the current balance first and then compares. Do not rely on a cached balance value — always read fresh from the database to avoid race conditions or stale data.

---

## 6. Testing

### 6.1 Unit Tests

Unit tests verify individual service functions in isolation, without running a web server or touching a real database. Use Python's built-in `unittest` module (or `pytest` for a friendlier syntax).

**What to unit test:**

- `AuthService.verify_credentials()`:
  - Test that a correct username + correct password returns a customer record.
  - Test that a correct username + wrong password returns `None`.
  - Test that an unknown username returns `None`.

- `TransactionService.deposit()`:
  - Test that depositing a positive amount increases the balance correctly.
  - Test that depositing zero returns an error result.
  - Test that depositing a negative number returns an error result.

- `TransactionService.withdraw()`:
  - Test that withdrawing less than the balance decreases it correctly.
  - Test that withdrawing exactly the balance reduces it to zero.
  - Test that withdrawing more than the balance returns an "insufficient funds" error.
  - Test that withdrawing zero returns an error.

**How to isolate the database:** Use an in-memory SQLite database (`:memory:`) in your test setup so tests do not touch `bank.db`. Create the tables and seed test data in a `setUp()` method and tear them down in `tearDown()`.

---

### 6.2 Integration Tests

Integration tests verify that the Flask routes, service layer, and database work correctly together as a system. Flask provides a built-in **test client** that simulates HTTP requests without starting a real server.

**Set up the test client:** Create a Flask app instance configured with `TESTING = True` and an in-memory database. Use the test client to make requests and inspect the responses.

**What to integration test:**

- `POST /login` with valid credentials: expect a redirect to `/dashboard` and a session cookie.
- `POST /login` with invalid credentials: expect a 200 response (re-rendered login page) and an error flash message in the response body.
- `GET /dashboard` without a session: expect a redirect to `/login`.
- `GET /dashboard` with a valid session: expect a 200 response containing the customer name and balance.
- `POST /deposit` with a valid amount: expect a redirect to `/transactions` and an updated balance on next GET.
- `POST /deposit` with amount = 0: expect a redirect back with an error flash message.
- `POST /withdraw` with a valid amount ≤ balance: expect a redirect and updated balance.
- `POST /withdraw` with amount > balance: expect a redirect and an "insufficient funds" flash message.
- `GET /logout`: expect a redirect to `/login` and the session to be cleared.

---

### 6.3 Manual Testing Checklist

Run through this checklist end-to-end in a browser after every significant change:

**Authentication Flow**
- [ ] Visiting `/dashboard` without logging in redirects to `/login`.
- [ ] Submitting the login form with an incorrect password shows a generic error message.
- [ ] Submitting with correct credentials redirects to `/dashboard`.
- [ ] The dashboard displays the correct customer name.
- [ ] Clicking "Logout" clears the session and redirects to `/login`.
- [ ] After logging out, the browser back button does not grant access to `/dashboard`.

**Balance Display**
- [ ] The balance on the dashboard matches the seeded starting value.
- [ ] After a deposit, the dashboard balance reflects the new amount.
- [ ] After a withdrawal, the dashboard balance reflects the new amount.

**Deposit Flow**
- [ ] Submitting the deposit form with a valid positive amount shows a success message and updates the balance.
- [ ] Submitting with `0` shows a validation error.
- [ ] Submitting with a negative number shows a validation error.
- [ ] Submitting with non-numeric text shows a validation error.
- [ ] Refreshing the page after a deposit does not resubmit the form (POST-Redirect-GET).

**Withdrawal Flow**
- [ ] Submitting the withdrawal form with a valid amount less than the balance succeeds.
- [ ] Submitting with an amount exactly equal to the balance succeeds and leaves balance at $0.00.
- [ ] Submitting with an amount exceeding the balance shows an "insufficient funds" error.
- [ ] Submitting with `0` or a negative number shows a validation error.

**Responsiveness**
- [ ] Resize the browser to mobile width — all forms and cards should stack vertically without horizontal scrolling.
- [ ] All buttons and inputs are easily tappable at mobile size.

---

## 7. Deployment

### 7.1 Run Locally

Running the application locally during development is straightforward:

1. Open a terminal and navigate to the `BACKEND/` folder.
2. Activate the virtual environment (`venv\Scripts\activate` on Windows).
3. Run `python app.py`.
4. Flask's development server starts and prints the local URL (typically `http://127.0.0.1:5000`).
5. Open that URL in a browser. The application is live.

**Important:** Flask's development server is single-threaded and not designed for concurrent users. It is suitable for local development and demos only.

**Auto-reload:** With `DEBUG = True`, Flask automatically restarts the server when it detects a file change. Save a file, switch to the browser, and refresh — no manual restart needed.

---

### 7.2 Production Considerations

If the application were to be deployed beyond a local workshop, the following changes would be required:

| Concern | Development Approach | Production Approach |
|---|---|---|
| **WSGI Server** | Flask's built-in dev server | Use `gunicorn` or `waitress` (Windows-compatible) as a production-grade WSGI server |
| **Secret Key** | Hardcoded string in `config.py` | Read from an environment variable; never commit to source control |
| **Debug Mode** | `DEBUG = True` | `DEBUG = False` — prevents stack traces from being shown to users |
| **Database** | SQLite file in `BACKEND/` | For higher traffic, migrate to PostgreSQL; for this project, SQLite with `WAL` mode enabled is a step up |
| **HTTPS** | HTTP (localhost only) | Serve behind a reverse proxy (nginx) with a TLS certificate (Let's Encrypt) |
| **Static Files** | Served by Flask | Serve directly by nginx for better performance |
| **Password Hashing** | Werkzeug defaults | Werkzeug's defaults are already strong (bcrypt-compatible); no change needed |
| **Session Security** | `SESSION_COOKIE_SECURE = False` | Set `SESSION_COOKIE_SECURE = True`, `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = "Lax"` |

For the workshop scope, only the local setup in Section 7.1 is needed. The production considerations above are provided as awareness for what a real deployment would involve.

---

*This guide describes the logic and decisions behind each implementation step. It is intentionally free of raw code. Refer to [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) for the architecture context behind these steps.*
