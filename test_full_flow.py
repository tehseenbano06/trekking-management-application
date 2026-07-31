from app import app
from extensions import db
from models import User, StaffProfile, Trek, Booking
from werkzeug.security import generate_password_hash

import os
if os.path.exists("trekking.db"):
    os.remove("trekking.db")

with app.app_context():
    db.create_all()
    admin = User(name="Administrator", email="admin@trek.com",
                 password_hash=generate_password_hash("admin123"), role="admin")
    db.session.add(admin)
    db.session.commit()

client = app.test_client()

def check(label, cond):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}")
    if not cond:
        raise SystemExit(f"Stopping at failed check: {label}")

# ---- Trekker + Staff registration ----
r = client.post("/auth/register", data={"name": "Trekker One", "email": "trekker1@trek.com", "password": "pass123"}, follow_redirects=True)
check("trekker registration", "Registration successful" in r.data.decode())

r = client.post("/auth/register-staff", data={"name": "Staff One", "email": "staff1@trek.com", "contact_number": "123", "password": "pass123"}, follow_redirects=True)
check("staff registration", "Please wait for Admin approval" in r.data.decode())

# ---- Staff cannot log in before approval ----
r = client.post("/auth/login", data={"email": "staff1@trek.com", "password": "pass123"}, follow_redirects=True)
check("staff blocked before approval", "awaiting Admin approval" in r.data.decode())

# ---- Admin logs in ----
admin_client = app.test_client()
r = admin_client.post("/auth/login", data={"email": "admin@trek.com", "password": "admin123"}, follow_redirects=True)
check("admin login", "Admin Dashboard" in r.data.decode())

# ---- Admin approves staff ----
with app.app_context():
    staff_user = User.query.filter_by(email="staff1@trek.com").first()
    staff_id = staff_user.id

r = admin_client.post(f"/admin/staff/{staff_id}/approve", follow_redirects=True)
check("admin approves staff", "approved as Trek Staff" in r.data.decode())

# ---- Staff can now log in ----
staff_client = app.test_client()
r = staff_client.post("/auth/login", data={"email": "staff1@trek.com", "password": "pass123"}, follow_redirects=True)
check("staff login after approval", "My Assigned Treks" in r.data.decode())

# ---- Admin creates a trek ----
r = admin_client.post("/admin/treks/create", data={
    "name": "Kedarkantha Trek", "location": "Uttarakhand", "difficulty": "Moderate",
    "duration_days": "6", "total_slots": "2", "start_date": "", "end_date": ""
}, follow_redirects=True)
check("admin creates trek", "Trek created" in r.data.decode())

with app.app_context():
    trek = Trek.query.filter_by(name="Kedarkantha Trek").first()
    trek_id = trek.id
    staff_profile_id = User.query.filter_by(email="staff1@trek.com").first().staff_profile.id

# ---- Admin assigns staff to trek ----
r = admin_client.post(f"/admin/treks/{trek_id}/assign-staff", data={"staff_id": str(staff_profile_id)}, follow_redirects=True)
check("admin assigns staff", "Staff assigned" in r.data.decode())

# ---- Staff opens the trek ----
r = staff_client.post(f"/staff/treks/{trek_id}/update", data={"status": "Open", "available_slots": "2"}, follow_redirects=True)
check("staff opens trek", "Trek updated" in r.data.decode())

# ---- Trekker logs in and books the trek ----
trekker_client = app.test_client()
r = trekker_client.post("/auth/login", data={"email": "trekker1@trek.com", "password": "pass123"}, follow_redirects=True)
check("trekker login", "My Dashboard" in r.data.decode())

r = trekker_client.get("/user/treks")
check("trek visible in browse (Open status)", "Kedarkantha Trek" in r.data.decode())

r = trekker_client.post(f"/user/treks/{trek_id}/book", follow_redirects=True)
check("trekker books trek", "Trek booked successfully" in r.data.decode())

# ---- Duplicate booking prevention ----
r = trekker_client.post(f"/user/treks/{trek_id}/book", follow_redirects=True)
check("duplicate booking blocked", "already booked" in r.data.decode())

# ---- Second trekker books remaining slot, third should be blocked (slot limit = 2, 1 used) ----
client.post("/auth/register", data={"name": "Trekker Two", "email": "trekker2@trek.com", "password": "pass123"}, follow_redirects=True)
trekker2_client = app.test_client()
trekker2_client.post("/auth/login", data={"email": "trekker2@trek.com", "password": "pass123"}, follow_redirects=True)
r = trekker2_client.post(f"/user/treks/{trek_id}/book", follow_redirects=True)
check("second trekker books (last slot)", "Trek booked successfully" in r.data.decode())

client.post("/auth/register", data={"name": "Trekker Three", "email": "trekker3@trek.com", "password": "pass123"}, follow_redirects=True)
trekker3_client = app.test_client()
trekker3_client.post("/auth/login", data={"email": "trekker3@trek.com", "password": "pass123"}, follow_redirects=True)
r = trekker3_client.post(f"/user/treks/{trek_id}/book", follow_redirects=True)
check("overbooking prevented (slots full)", "No slots available" in r.data.decode())

# ---- Staff sees participant list ----
r = staff_client.get(f"/staff/treks/{trek_id}")
check("staff sees registered trekkers", "Trekker One" in r.data.decode() and "Trekker Two" in r.data.decode())

# ---- Trekker cancels booking, slot freed ----
with app.app_context():
    booking = Booking.query.filter_by(user_id=User.query.filter_by(email="trekker1@trek.com").first().id).first()
    booking_id = booking.id

r = trekker_client.post(f"/user/bookings/{booking_id}/cancel", follow_redirects=True)
check("trekker cancels booking", "Booking cancelled" in r.data.decode())

r = trekker3_client.post(f"/user/treks/{trek_id}/book", follow_redirects=True)
check("slot freed after cancellation, third trekker can now book", "Trek booked successfully" in r.data.decode())

# ---- Trekker history shows cancelled + booked ----
r = trekker_client.get("/user/history")
check("history shows cancelled booking", "Cancelled" in r.data.decode())

# ---- Admin can view all bookings ----
r = admin_client.get("/admin/bookings")
check("admin views all bookings", "Kedarkantha Trek" in r.data.decode())

# ---- Admin blacklists a trekker, they can't log in ----
with app.app_context():
    t2 = User.query.filter_by(email="trekker2@trek.com").first()
    t2_id = t2.id
admin_client.post(f"/admin/users/{t2_id}/toggle-active", follow_redirects=True)
blocked_client = app.test_client()
r = blocked_client.post("/auth/login", data={"email": "trekker2@trek.com", "password": "pass123"}, follow_redirects=True)
check("blacklisted user blocked from login", "blacklisted" in r.data.decode())

# ---- Role-based access: trekker cannot access admin dashboard ----
r = trekker_client.get("/admin/dashboard", follow_redirects=True)
check("trekker blocked from admin dashboard", "not authorized" in r.data.decode())

# ---- Role-based access: staff cannot access another staff's un-assigned trek management ----
r = trekker_client.get("/staff/dashboard", follow_redirects=True)
check("trekker blocked from staff dashboard", "not authorized" in r.data.decode())

print("\\nALL CHECKS PASSED")
