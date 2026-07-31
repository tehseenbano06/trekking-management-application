from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """
    Blocks access to a route unless someone is logged in.
    We check session['user_id'] because that's what we set in the
    login route — if it's missing, nobody is logged in.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def role_required(role):
    """
    Blocks access unless the logged-in user's role matches.
    Usage: @role_required("admin")  above a route function.
    This is what implements "restrict dashboard access based on role".
    """
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login"))
            if session.get("role") != role:
                flash("You are not authorized to view that page.", "danger")
                return redirect(url_for("auth.login"))
            return f(*args, **kwargs)
        return decorated
    return wrapper
