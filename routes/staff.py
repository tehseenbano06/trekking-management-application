from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from models import Trek, Booking, User
from utils import role_required

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


def _current_staff_profile():
    """Helper: get the StaffProfile row belonging to the logged-in staff user."""
    user = User.query.get(session["user_id"])
    return user.staff_profile


@staff_bp.route("/dashboard")
@role_required("staff")
def dashboard():
    profile = _current_staff_profile()
    assigned_treks = Trek.query.filter_by(staff_id=profile.id).all() if profile else []

    # Number of registered (Booked) trekkers per trek, for the dashboard view.
    trek_counts = {
        t.id: Booking.query.filter_by(trek_id=t.id, booking_status="Booked").count()
        for t in assigned_treks
    }
    return render_template("staff/dashboard.html", treks=assigned_treks, trek_counts=trek_counts)


@staff_bp.route("/treks/<int:trek_id>")
@role_required("staff")
def trek_detail(trek_id):
    profile = _current_staff_profile()
    trek = Trek.query.get_or_404(trek_id)

    # Ensure only the assigned staff member can manage this trek.
    if trek.staff_id != profile.id:
        flash("You are not assigned to this trek.", "danger")
        return redirect(url_for("staff.dashboard"))

    bookings = Booking.query.filter_by(trek_id=trek.id, booking_status="Booked").all()
    return render_template("staff/trek_detail.html", trek=trek, bookings=bookings)


@staff_bp.route("/treks/<int:trek_id>/update", methods=["POST"])
@role_required("staff")
def update_trek(trek_id):
    profile = _current_staff_profile()
    trek = Trek.query.get_or_404(trek_id)

    if trek.staff_id != profile.id:
        flash("You are not assigned to this trek.", "danger")
        return redirect(url_for("staff.dashboard"))

    new_status = request.form.get("status")
    new_slots = request.form.get("available_slots")

    if new_status:
        trek.status = new_status

    if new_slots is not None and new_slots != "":
        new_available = int(new_slots)
        # total_slots must always equal (currently booked trekkers) + (available slots),
        # otherwise the "X / Y" display on dashboards goes out of sync with reality.
        # Example: 3 booked, 0 available (full), staff opens 3 more slots ->
        # available becomes 3, and total must become 3 (booked) + 3 (available) = 6.
        booked_count = Booking.query.filter_by(trek_id=trek.id, booking_status="Booked").count()
        trek.available_slots = new_available
        trek.total_slots = booked_count + new_available

    db.session.commit()
    flash("Trek updated.", "success")
    return redirect(url_for("staff.trek_detail", trek_id=trek.id))