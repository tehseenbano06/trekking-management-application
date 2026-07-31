from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import Trek, Booking, User
from utils import role_required

user_bp = Blueprint("user", __name__, url_prefix="/user")


@user_bp.route("/dashboard")
@role_required("trekker")
def dashboard():
    user_id = session["user_id"]
    booked = (
        Booking.query.filter_by(user_id=user_id, booking_status="Booked")
        .join(Trek)
        .all()
    )
    return render_template("user/dashboard.html", bookings=booked)


@user_bp.route("/treks")
@role_required("trekker")
def browse_treks():
    """Only Open treks can be booked, so we only list Open ones here."""
    difficulty = request.args.get("difficulty", "")
    location = request.args.get("location", "").strip()

    query = Trek.query.filter_by(status="Open")
    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f"%{location}%"))

    treks = query.order_by(Trek.id.desc()).all()

    # Which treks has this user already booked? Used to disable the button
    # in the template so they can't double-book from the UI either.
    user_id = session["user_id"]
    already_booked_ids = {
        b.trek_id
        for b in Booking.query.filter_by(user_id=user_id, booking_status="Booked").all()
    }
    return render_template(
        "user/treks.html",
        treks=treks,
        difficulty=difficulty,
        location=location,
        already_booked_ids=already_booked_ids,
    )


@user_bp.route("/treks/<int:trek_id>/book", methods=["POST"])
@role_required("trekker")
def book_trek(trek_id):
    user_id = session["user_id"]
    trek = Trek.query.get_or_404(trek_id)

    # Rule: can only book Open treks.
    if trek.status != "Open":
        flash("This trek is not open for booking.", "danger")
        return redirect(url_for("user.browse_treks"))

    # Rule: no overbooking beyond available slots.
    if trek.available_slots <= 0:
        flash("No slots available for this trek.", "danger")
        return redirect(url_for("user.browse_treks"))

    # Rule: prevent duplicate active booking for the same trek.
    existing = Booking.query.filter_by(
        user_id=user_id, trek_id=trek_id, booking_status="Booked"
    ).first()
    if existing:
        flash("You have already booked this trek.", "warning")
        return redirect(url_for("user.browse_treks"))

    booking = Booking(user_id=user_id, trek_id=trek_id, booking_status="Booked")
    trek.available_slots -= 1
    db.session.add(booking)
    db.session.commit()

    flash("Trek booked successfully!", "success")
    return redirect(url_for("user.dashboard"))


@user_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@role_required("trekker")
def cancel_booking(booking_id):
    user_id = session["user_id"]
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != user_id:
        flash("You cannot cancel someone else's booking.", "danger")
        return redirect(url_for("user.dashboard"))

    if booking.booking_status == "Booked":
        booking.booking_status = "Cancelled"
        booking.trek.available_slots += 1
        db.session.commit()
        flash("Booking cancelled.", "info")

    return redirect(url_for("user.dashboard"))


@user_bp.route("/history")
@role_required("trekker")
def history():
    user_id = session["user_id"]
    all_bookings = (
        Booking.query.filter_by(user_id=user_id).order_by(Booking.id.desc()).all()
    )
    return render_template("user/history.html", bookings=all_bookings)


@user_bp.route("/profile", methods=["GET", "POST"])
@role_required("trekker")
def profile():
    user = User.query.get(session["user_id"])

    if request.method == "POST":
        user.name = request.form["name"].strip()
        new_password = request.form.get("password", "").strip()
        if new_password:
            user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        session["name"] = user.name
        flash("Profile updated.", "success")
        return redirect(url_for("user.profile"))

    return render_template("user/profile.html", user=user)
