from flask_sqlalchemy import SQLAlchemy

# This single db object is imported by both app.py and models.py.
# Keeping it here (instead of creating it inside app.py) avoids a
# "circular import" error: app.py needs models, models need db,
# and if db lived inside app.py, models.py would need to import
# app.py right back -> a loop. So db lives in its own tiny file.
db = SQLAlchemy()
