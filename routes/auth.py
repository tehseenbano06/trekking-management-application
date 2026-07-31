from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, StaffProfile

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register_trekker():
    """Self-registration for Users (Trekkers). Role is fixed to 'trekker'."""
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
            return redirect(url_for("auth.register_trekker"))

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role="trekker",
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/register-staff", methods=["GET", "POST"])
def register_staff():
    """
    Self-registration for Trek Staff. They get an account AND a
    StaffProfile row with is_approved=False. They cannot log in
    successfully until Admin approves them (checked in login route).
    """
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        contact_number = request.form.get("contact_number", "").strip()

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
            return redirect(url_for("auth.register_staff"))

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role="staff",
        )
        db.session.add(user)
        db.session.flush()  # gives `user` an id before we commit, so we can link it below

        profile = StaffProfile(
            user_id=user.id,
            contact_number=contact_number,
            is_approved=False,
        )
        db.session.add(profile)
        db.session.commit()

        flash("Registration submitted. Please wait for Admin approval before logging in.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_staff.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        if not user.is_active:
            flash("This account has been blacklisted/deactivated. Contact Admin.", "danger")
            return redirect(url_for("auth.login"))

        # Staff must be approved by Admin before they can log in.
        if user.role == "staff":
            if not user.staff_profile or not user.staff_profile.is_approved:
                flash("Your staff account is awaiting Admin approval.", "warning")
                return redirect(url_for("auth.login"))

        # Everything checks out — start the session.
        session["user_id"] = user.id
        session["name"] = user.name
        session["role"] = user.role

        flash(f"Welcome back, {user.name}!", "success")

        if user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif user.role == "staff":
            return redirect(url_for("staff.dashboard"))
        else:
            return redirect(url_for("user.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
