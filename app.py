from flask import Flask
from config import Config
from extensions import db

from models.user import User
from models.location import Location
from models.temperature import TemperatureRecord
from models.alert import Alert


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    @app.route("/")
    def home():
        return "Smart Heat Alert System is running!"

    @app.route("/db-test")
    def db_test():
        try:
            db.session.execute(db.text("SELECT 1"))
            return "PostgreSQL connected successfully!"
        except Exception as e:
            return f"Database connection failed: {e}"

    return app


app = create_app()


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)