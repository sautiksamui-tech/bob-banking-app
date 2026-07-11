"""
routes/auth_routes.py — Login and logout HTTP handlers.

Routes:
  GET  /login   — render login form (redirect to dashboard if already logged in)
  POST /login   — verify credentials, set session, redirect
  GET  /logout  — clear session, redirect to login
"""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from services.auth_service import verify_credentials

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    """Root URL — redirect to login or dashboard."""
    if session.get("customer_id"):
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle the login page and form submission."""
    # If already authenticated, skip the login page entirely.
    if session.get("customer_id"):
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Basic presence check before hitting the database.
        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html")

        customer = verify_credentials(username, password)

        if customer is None:
            # Generic message — do not reveal which field was wrong.
            flash("Invalid username or password.", "danger")
            return render_template("login.html")

        # Credentials verified — establish the session.
        session.clear()
        session["customer_id"] = customer["id"]
        session["customer_name"] = customer["full_name"]
        return redirect(url_for("dashboard.dashboard"))

    # GET — render the empty login form.
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Terminate the session and redirect to the login page."""
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("auth.login"))
