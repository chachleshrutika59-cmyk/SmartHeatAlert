from flask import Flask, redirect, url_for
from config import Config
from extensions import db
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.api import api_bp
from routes.settings import settings_bp
from routes.alerts import alerts_bp
from routes.history import history_bp
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Set SECRET_KEY in the environment before starting the app.")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("Set DATABASE_URL in the environment before starting the app.")

    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(history_bp)

    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    @app.cli.command("init-db")
    def init_db():
        """Create any missing tables for a fresh development database."""
        db.create_all()
        print("Database tables created.")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])