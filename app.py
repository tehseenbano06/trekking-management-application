from flask import Flask
from config import Config
from extensions import db

# We import models here (even though we don't use them by name) so that
# SQLAlchemy knows these tables exist before we call db.create_all() below.
import models  # noqa: F401


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Connect the db object (created in extensions.py) to this app.
    db.init_app(app)

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.staff import staff_bp
    from routes.user import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(user_bp)

    return app


app = create_app()


@app.route("/")
def home():
    from flask import redirect, url_for
    return redirect(url_for("auth.login"))


if __name__ == "__main__":
    with app.app_context():
        # Creates trekking.db and all tables defined in models.py,
        # if they don't already exist. Safe to run every time.
        db.create_all()

    app.run(debug=True)
