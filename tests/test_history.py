import unittest
from pathlib import Path

from flask import Flask

from extensions import db
from models.location import Location
from models.temperature import TemperatureRecord
from models.user import User
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.history import history_bp


class HistoryRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(
            __name__,
            template_folder=Path(__file__).resolve().parents[1] / "templates"
        )
        self.app.config.update(
            SECRET_KEY="history-test",
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite://"
        )
        db.init_app(self.app)
        for blueprint in (auth_bp, dashboard_bp, history_bp):
            self.app.register_blueprint(blueprint)

        with self.app.app_context():
            db.create_all()
            first_user = User(mobile_number="1111111111")
            second_user = User(mobile_number="2222222222")
            db.session.add_all([first_user, second_user])
            db.session.flush()
            self.user_id = first_user.id

            first_location = Location(
                user_id=first_user.id,
                latitude=10,
                longitude=20,
                location_name="First Location"
            )
            second_location = Location(
                user_id=second_user.id,
                latitude=30,
                longitude=40,
                location_name="Second Location"
            )
            db.session.add_all([first_location, second_location])
            db.session.flush()
            db.session.add_all([
                TemperatureRecord(
                    user_id=first_user.id,
                    location_id=first_location.id,
                    temperature=39,
                    humidity=70,
                    feels_like=42,
                    risk_score=69,
                    risk_level="High Risk"
                ),
                TemperatureRecord(
                    user_id=second_user.id,
                    location_id=second_location.id,
                    temperature=45,
                    humidity=90,
                    feels_like=49,
                    risk_score=95,
                    risk_level="Critical Risk"
                )
            ])
            db.session.commit()

        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["logged_in"] = True
            session["user_id"] = self.user_id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_history_lists_only_current_users_records(self):
        response = self.client.get("/history")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"First Location", response.data)
        self.assertIn(b"High Risk", response.data)
        self.assertIn(b"69/100", response.data)
        self.assertNotIn(b"Second Location", response.data)
        self.assertNotIn(b"Critical Risk", response.data)
        self.assertIn(b"Temperature and heat risk", response.data)

    def test_history_requires_login(self):
        with self.client.session_transaction() as session:
            session.clear()

        response = self.client.get("/history")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/login"))


if __name__ == "__main__":
    unittest.main()
