# Trekking Management Application

A web-based Trekking Management Application developed.

## Tech Stack

- Flask
- SQLite
- Jinja2
- HTML
- CSS
- Bootstrap

## User Roles

- Admin
- Trek Staff
- Trekker (User)

## Database Schema

4 tables implemented using SQLAlchemy models:
- **User** — Admin / Trek Staff / Trekker, told apart by a `role` column
- **StaffProfile** — one-to-one with User, holds `is_approved` for the staff approval workflow
- **Trek** — name, location, difficulty, slots, status lifecycle (Pending → Approved → Open → Closed → Completed), start/end dates
- **Booking** — links User to Trek, tracks booking status (Booked/Cancelled/Completed)

Admin account is created programmatically via `seed_admin.py` (not through manual DB creation).
