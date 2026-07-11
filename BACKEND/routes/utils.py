"""
routes/utils.py — Shared helpers used across route blueprints.
"""

from functools import wraps

from flask import redirect, session, url_for


def login_required(f):
    """Decorator that redirects unauthenticated visitors to /login.

    Apply to any route that must only be accessible after a successful login::

        @dashboard_bp.route("/dashboard")
        @login_required
        def dashboard():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("customer_id"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function
