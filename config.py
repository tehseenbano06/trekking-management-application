import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # SECRET_KEY is used by Flask to sign session cookies and flash messages.
    # In a real product this would come from an environment variable.
    # For a college project, a hardcoded string is fine.
    SECRET_KEY = "trekking-management-app-secret-key"

    # SQLite database file will be created at trekking_management_app/trekking.db
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "trekking.db")

    # This just turns off a feature we don't need and that prints warnings.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
