from datetime import datetime
from extensions import db


class User(db.Model):
    """
    One table for everyone who can log in: Admin, Trek Staff, Trekker (User).
    We tell them apart using the `role` column instead of making 3 separate
    login tables — simpler to query and simpler to explain in viva.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # role is one of: 'admin', 'staff', 'trekker'
    role = db.Column(db.String(20), nullable=False, default="trekker")

    # Admin can blacklist/deactivate a user or staff member.
    # If is_active is False, that person cannot log in anymore.
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # A trekker can have many bookings. `backref` lets us go the other way
    # too: booking.user will give us the User who made that booking.
    bookings = db.relationship("Booking", backref="user", lazy=True)

    # If this user's role is 'staff', they will have exactly one
    # matching row in staff_profiles. uselist=False makes this a
    # one-to-one relationship instead of one-to-many.
    staff_profile = db.relationship(
        "StaffProfile", backref="user", uselist=False, lazy=True
    )

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class StaffProfile(db.Model):
    """
    Extra information that only Trek Staff need, kept in its own table
    instead of cramming staff-only columns into the User table.
    This also holds the approval workflow: a staff member registers,
    but is_approved stays False until Admin approves them — they can't
    log in and use their dashboard until then.
    """
    __tablename__ = "staff_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    contact_number = db.Column(db.String(20))
    experience_years = db.Column(db.Integer, default=0)

    is_approved = db.Column(db.Boolean, default=False, nullable=False)

    # A staff member can be assigned to many treks over time.
    treks = db.relationship("Trek", backref="staff", lazy=True)

    def __repr__(self):
        return f"<StaffProfile user_id={self.user_id} approved={self.is_approved}>"


class Trek(db.Model):
    """
    A single trek offering (e.g. "Kedarkantha Winter Trek").
    status moves through a fixed lifecycle:
    Pending -> Approved -> Open -> Closed -> Completed
    (Admin approves/creates it, Staff opens it for booking, then closes
    it once slots are full or the date passes, then marks it Completed.)
    """
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)

    # Easy / Moderate / Hard
    difficulty = db.Column(db.String(20), nullable=False, default="Easy")

    duration_days = db.Column(db.Integer, nullable=False, default=1)

    total_slots = db.Column(db.Integer, nullable=False, default=10)
    available_slots = db.Column(db.Integer, nullable=False, default=10)

    # Pending / Approved / Open / Closed / Completed
    status = db.Column(db.String(20), nullable=False, default="Pending")

    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

    # Which staff member is assigned to run this trek.
    # Nullable because Admin might create a trek before assigning staff.
    staff_id = db.Column(db.Integer, db.ForeignKey("staff_profiles.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship("Booking", backref="trek", lazy=True)

    def __repr__(self):
        return f"<Trek {self.name} ({self.status})>"


class Booking(db.Model):
    """
    Links a User to a Trek. One row = one trekker's attempt to join
    one trek. booking_status tracks what happened to that attempt.
    """
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)

    # Booked / Cancelled / Completed
    booking_status = db.Column(db.String(20), nullable=False, default="Booked")

    booking_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Booking user={self.user_id} trek={self.trek_id} ({self.booking_status})>"
