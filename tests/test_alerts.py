import unittest
from pathlib import Path
from flask import Flask

from extensions import db
from models.alert import Alert
from models.user import User
from routes.alerts import alerts_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp


class AlertsRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(
            __name__,
            template_folder=Path(__file__).resolve().parents[1] / "templates"
        )
        self.app.config.update(
            SECRET_KEY="test-secret",
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite://"
        )
        db.init_app(self.app)
        self.app.register_blueprint(auth_bp)
        self.app.register_blueprint(alerts_bp)
        self.app.register_blueprint(dashboard_bp)

        with self.app.app_context():
            db.create_all()
            self.first_user = User(mobile_number="1111111111")
            self.second_user = User(mobile_number="2222222222")
            db.session.add_all([self.first_user, self.second_user])
            db.session.flush()
            self.first_user_id = self.first_user.id
            self.second_user_id = self.second_user.id
            self.first_alert = Alert(
                user_id=self.first_user_id,
                temperature=41,
                threshold=38,
                risk_score=82,
                heat_level="Critical Risk",
                location="First user location",
                condition_key="Critical Risk|above_safe=1",
                message="First user's heat alert"
            )
            self.second_alert = Alert(
                user_id=self.second_user_id,
                temperature=42,
                threshold=39,
                risk_score=90,
                heat_level="Critical Risk",
                location="Second user location",
                condition_key="Critical Risk|above_safe=1",
                message="Second user's heat alert"
            )
            db.session.add_all([self.first_alert, self.second_alert])
            db.session.commit()
            self.first_alert_id = self.first_alert.id
            self.second_alert_id = self.second_alert.id

        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["logged_in"] = True
            session["user_id"] = self.first_user_id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_alert_page_only_shows_logged_in_users_alerts(self):
        response = self.client.get("/alerts")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"First user&#39;s heat alert", response.data)
        self.assertNotIn(b"Second user&#39;s heat alert", response.data)
        self.assertIn(b"82", response.data)
        self.assertIn(b"First user location", response.data)
        self.assertIn(b"Unread", response.data)

    def test_user_can_mark_own_alert_read(self):
        response = self.client.post(
            f"/alerts/{self.first_alert_id}/read",
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Read", response.data)
        with self.app.app_context():
            alert = db.session.get(Alert, self.first_alert_id)
            self.assertTrue(alert.is_read)

    def test_user_cannot_mark_another_users_alert_read(self):
        response = self.client.post(
            f"/alerts/{self.second_alert_id}/read"
        )

        self.assertEqual(response.status_code, 404)
        with self.app.app_context():
            alert = db.session.get(Alert, self.second_alert_id)
            self.assertFalse(alert.is_read)

    def test_alert_page_requires_login(self):
        with self.client.session_transaction() as session:
            session.clear()

        response = self.client.get("/alerts")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/login"))


if __name__ == "__main__":
    unittest.main()
