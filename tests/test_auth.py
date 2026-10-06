import unittest
from pathlib import Path

from flask import Flask

from extensions import db
from models.user import User
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp


class OtpAuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(
            __name__,
            template_folder=Path(__file__).resolve().parents[1] / "templates"
        )
        self.app.config.update(
            SECRET_KEY="test-secret",
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite://",
            APP_ENV="local",
            LOCAL_DEMO_MODE=True,
            DEMO_OTP_ENABLED=True
        )
        db.init_app(self.app)
        self.app.register_blueprint(auth_bp)
        self.app.register_blueprint(dashboard_bp)

        with self.app.app_context():
            db.create_all()

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_production_mode_disables_demo_login(self):
        self.app.config.update(
            APP_ENV="production",
            LOCAL_DEMO_MODE=False,
            DEMO_OTP_ENABLED=False
        )
        response = self.client.post(
            "/login",
            data={"mobile_number": "1234567890"}
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn(b"Local demo OTP is disabled", response.data)
        with self.client.session_transaction() as session:
            self.assertNotIn("otp", session)
            self.assertNotIn("demo_otp", session)

    def test_local_demo_otp_login_works_and_clears_challenge(self):
        response = self.client.post(
            "/login",
            data={"mobile_number": "1234567890"}
        )

        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as session:
            otp = session["otp"]
            self.assertEqual(session["demo_otp"], otp)
            self.assertEqual(len(otp), 6)
            self.assertTrue(otp.isdigit())

        response = self.client.post("/otp", data={"otp": otp})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/dashboard"))
        with self.client.session_transaction() as session:
            self.assertTrue(session["logged_in"])
            self.assertEqual(session["mobile_number"], "1234567890")
            self.assertNotIn("otp", session)
            self.assertNotIn("demo_otp", session)

        with self.app.app_context():
            self.assertIsNotNone(
                User.query.filter_by(mobile_number="1234567890").first()
            )

    def test_demo_otp_is_visible_only_in_local_demo_mode(self):
        with self.client.session_transaction() as session:
            session["mobile_number"] = "1234567890"
            session["otp"] = "314159"
            session["demo_otp"] = "314159"
            session["otp_created_at"] = "2026-10-06T10:00:00"
            session["otp_attempts"] = 0

        local_response = self.client.get("/otp")
        self.assertIn(b"Development OTP", local_response.data)
        self.assertIn(b"314159", local_response.data)

        self.app.config.update(
            APP_ENV="production",
            LOCAL_DEMO_MODE=False,
            DEMO_OTP_ENABLED=False
        )
        production_response = self.client.get("/otp")
        self.assertEqual(production_response.status_code, 503)
        self.assertNotIn(b"Development OTP", production_response.data)
        self.assertNotIn(b"314159", production_response.data)

        production_verify_response = self.client.post(
            "/otp",
            data={"otp": "314159"}
        )
        self.assertEqual(production_verify_response.status_code, 503)
        self.assertNotIn(b"314159", production_verify_response.data)

    def test_otp_expires_and_blocks_after_three_attempts(self):
        with self.client.session_transaction() as session:
            session["mobile_number"] = "1234567890"
            session["otp"] = "314159"
            session["demo_otp"] = "314159"
            session["otp_created_at"] = "2020-01-01T00:00:00"
            session["otp_attempts"] = 0

        expired_response = self.client.post("/otp", data={"otp": "314159"})
        self.assertIn(b"OTP has expired", expired_response.data)

        with self.client.session_transaction() as session:
            session["otp_created_at"] = "2099-01-01T00:00:00"
            session["otp_attempts"] = 0

        for _ in range(3):
            response = self.client.post("/otp", data={"otp": "000000"})
            self.assertEqual(response.status_code, 200)

        blocked_response = self.client.post(
            "/otp",
            data={"otp": "314159"}
        )
        self.assertIn(b"Maximum attempts reached", blocked_response.data)
        with self.client.session_transaction() as session:
            self.assertEqual(session["otp_attempts"], 3)


if __name__ == "__main__":
    unittest.main()
