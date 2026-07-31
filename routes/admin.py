from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import User, StaffProfile, Trek, Booking
from utils import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role="trekker").count()
    total_staff = User.query.filter_by(role="staff").count()
    total_bookings = Booking.query.count()
    return render_template(
        "admin/dashboard.html",
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
    )


# ---------- Trek management ----------

@admin_bp.route("/treks")
@role_required("admin")
def treks():
    q = request.args.get("q", "").strip()
    query = Trek.query
    if q:
        query = query.filter(Trek.name.ilike(f"%{q}%"))
    all_treks = query.order_by(Trek.id.desc()).all()
    staff_list = StaffProfile.query.filter_by(is_approved=True).all()
    return render_template("admin/treks.html", treks=all_treks, staff_list=staff_list, q=q)


@admin_bp.route("/treks/create", methods=["POST"])
@role_required("admin")
def create_trek():
    name = request.form["name"].strip()
    location = request.form["location"].strip()
    difficulty = request.form["difficulty"]
    duration_days = int(request.form["duration_days"])
    total_slots = int(request.form["total_slots"])

    # Form fields arrive as plain strings (e.g. "2026-07-12"). SQLite's
    # Date column needs a real Python date object, not text, so we parse
    # it here. If the field was left blank, we store None instead.
    start_date_str = request.form.get("start_date") or None
    end_date_str = request.form.get("end_date") or None
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

    trek = Trek(
        name=name,
        location=location,
        difficulty=difficulty,
        duration_days=duration_days,
        total_slots=total_slots,
        available_slots=total_slots,
        status="Pending",
        start_date=start_date,
        end_date=end_date,
    )
    db.session.add(trek)
    db.session.commit()
    flash("Trek created.", "success")
    return redirect(url_for("admin.treks"))


@admin_bp.route("/treks/<int:trek_id>/edit", methods=["POST"])
@role_required("admin")
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    trek.name = request.form["name"].strip()
    trek.location = request.form["location"].strip()
    trek.difficulty = request.form["difficulty"]
    trek.duration_days = int(request.form["duration_days"])
    trek.total_slots = int(request.form["total_slots"])
    trek.status = request.form["status"]
    db.session.commit()
    flash("Trek updated.", "success")
    return redirect(url_for("admin.treks"))


@admin_bp.route("/treks/<int:trek_id>/delete", methods=["POST"])
@role_required("admin")
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    flash("Trek removed.", "info")
    return redirect(url_for("admin.treks"))


@admin_bp.route("/treks/<int:trek_id>/assign-staff", methods=["POST"])
@role_required("admin")
def assign_staff(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    staff_id = request.form.get("staff_id")
    trek.staff_id = int(staff_id) if staff_id else None
    if trek.status == "Pending":
        trek.status = "Approved"
    db.session.commit()
    flash("Staff assigned to trek.", "success")
    return redirect(url_for("admin.treks"))


# ---------- Staff management ----------

@admin_bp.route("/staff")
@role_required("admin")
def staff_list():
    q = request.args.get("q", "").strip()
    query = User.query.filter_by(role="staff")
    if q:
        query = query.filter(User.name.ilike(f"%{q}%"))
    all_staff = query.order_by(User.id.desc()).all()
    return render_template("admin/staff.html", staff=all_staff, q=q)


@admin_bp.route("/staff/<int:user_id>/approve", methods=["POST"])
@role_required("admin")
def approve_staff(user_id):
    user = User.query.get_or_404(user_id)
    if user.staff_profile:
        user.staff_profile.is_approved = True
        db.session.commit()
        flash(f"{user.name} approved as Trek Staff.", "success")
    return redirect(url_for("admin.staff_list"))


@admin_bp.route("/staff/<int:user_id>/toggle-active", methods=["POST"])
@role_required("admin")
def toggle_staff_active(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"{user.name} is now {'active' if user.is_active else 'blacklisted'}.", "info")
    return redirect(url_for("admin.staff_list"))


# ---------- User management ----------

@admin_bp.route("/users")
@role_required("admin")
def users_list():
    q = request.args.get("q", "").strip()
    query = User.query.filter_by(role="trekker")
    if q:
        query = query.filter(User.name.ilike(f"%{q}%"))
    all_users = query.order_by(User.id.desc()).all()
    return render_template("admin/users.html", users=all_users, q=q)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@role_required("admin")
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"{user.name} is now {'active' if user.is_active else 'blacklisted'}.", "info")
    return redirect(url_for("admin.users_list"))


# ---------- Bookings ----------

@admin_bp.route("/bookings")
@role_required("admin")
def bookings():
    all_bookings = Booking.query.order_by(Booking.id.desc()).all()
    return render_template("admin/bookings.html", bookings=all_bookings)