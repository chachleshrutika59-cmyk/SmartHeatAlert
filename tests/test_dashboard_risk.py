import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from extensions import db
from models.alert import Alert
from models.location import Location
from models.temperature import TemperatureRecord
from models.user import User
from routes.auth import auth_bp
from routes.alerts import alerts_bp
from routes.dashboard import dashboard_bp
from routes.history import history_bp
from routes.settings import settings_bp


class DashboardRiskTests(unittest.TestCase):
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
        self.app.register_blueprint(dashboard_bp)
        self.app.register_blueprint(settings_bp)
        self.app.register_blueprint(alerts_bp)
        self.app.register_blueprint(history_bp)

        self.forecast_patcher = patch(
            "routes.dashboard.get_today_forecast",
            return_value=[]
        )
        self.forecast_patcher.start()
        with self.app.app_context():
            db.create_all()
            self.user = User(
                mobile_number="1234567890",
                activity_level="Outdoor Activity",
                outdoor_exposure="3–6 hours",
                safe_temperature=30
            )
            db.session.add(self.user)
            db.session.flush()
            self.user_id = self.user.id
            db.session.add(Location(
                user_id=self.user_id,
                latitude=12.0,
                longitude=34.0,
                location_name="Test Location"
            ))
            db.session.commit()

        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["logged_in"] = True
            session["user_id"] = self.user_id
            session["mobile_number"] = "1234567890"

    def tearDown(self):
        self.forecast_patcher.stop()
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    @patch("routes.dashboard.get_current_weather")
    def test_dashboard_calculates_personalized_risk(self, get_weather):
        get_weather.return_value = {
            "temperature": 39,
            "humidity": 70,
            "feels_like": 42,
            "time": "2026-10-06T12:00"
        }

        with patch(
            "routes.dashboard.render_template",
            return_value="rendered"
        ) as render:
            response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        context = render.call_args.kwargs
        self.assertEqual(context["weather"]["temperature"], 39)
        self.assertEqual(context["user"].id, self.user_id)
        self.assertEqual(context["heat_risk_score"], 69)
        self.assertEqual(context["heat_risk_level"], "High Risk")
        self.assertEqual(context["heat_risk_icon"], "🟠")
        self.assertIn("Heat risk is high", context["heat_risk_message"])
        self.assertEqual(
            context["recommendations"]["risk_level"],
            "High Risk"
        )
        self.assertIn("hydration", context["recommendations"])
        get_weather.assert_called_once_with(12.0, 34.0)

        rendered_page = self.client.get("/dashboard")
        self.assertEqual(rendered_page.status_code, 200)
        self.assertIn(b"<strong>39</strong>", rendered_page.data)
        self.assertIn(b"<span>\xc2\xb0C</span>", rendered_page.data)
        self.assertIn(b"Test Location", rendered_page.data)
        self.assertIn(b"69", rendered_page.data)
        self.assertIn(b"High Risk", rendered_page.data)
        self.assertIn(b"Heat risk is high", rendered_page.data)
        self.assertIn(b"Safety recommendations", rendered_page.data)
        self.assertIn(b"Hydration", rendered_page.data)
        self.assertIn(b"not a medical diagnosis", rendered_page.data)
        self.assertIn(b"location-search-input", rendered_page.data)
        self.assertIn(b'id="heat-globe"', rendered_page.data)
        self.assertIn(b'data-latitude="12.0"', rendered_page.data)
        self.assertIn(b'data-longitude="34.0"', rendered_page.data)
        self.assertIn(b'class="globe-fallback"', rendered_page.data)
        self.assertIn(b'class="globe-canvas"', rendered_page.data)
        self.assertIn(b"js/heat_globe.js", rendered_page.data)
        with self.app.app_context():
            self.assertEqual(Alert.query.filter_by(user_id=self.user_id).count(), 1)
            self.assertEqual(
                TemperatureRecord.query.filter_by(user_id=self.user_id).count(),
                1
            )

        self.client.get("/dashboard")
        with self.app.app_context():
            self.assertEqual(Alert.query.filter_by(user_id=self.user_id).count(), 1)
            self.assertEqual(
                TemperatureRecord.query.filter_by(user_id=self.user_id).count(),
                1
            )
            record = TemperatureRecord.query.filter_by(
                user_id=self.user_id
            ).one()
            self.assertEqual(record.risk_score, 69)
            self.assertEqual(record.risk_level, "High Risk")

    def test_dashboard_provides_today_forecast_with_personal_risk(self):
        from unittest.mock import patch

        weather = {
            "temperature": 35,
            "humidity": 60,
            "feels_like": 36,
            "time": "2026-10-06T12:00"
        }
        forecast_data = [{
            "time": "2026-10-06T14:00",
            "temperature": 39,
            "humidity": 70,
            "feels_like": 42
        }]
        with (
            patch("routes.dashboard.get_current_weather", return_value=weather),
            patch("routes.dashboard.get_today_forecast", return_value=forecast_data)
        ):
            response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"14:00", response.data)
        self.assertIn(b"39\xc2\xb0", response.data)
        self.assertIn(b"High Risk", response.data)
        self.assertIn(b"69/100", response.data)

    @patch("routes.dashboard.get_current_weather", return_value={
        "temperature": 39,
        "humidity": 70,
        "feels_like": 42,
        "time": "2026-10-06T12:00"
    })
    def test_dashboard_respects_disabled_notifications(self, get_weather):
        with self.app.app_context():
            user = db.session.get(User, self.user_id)
            user.notification_enabled = False
            db.session.commit()

        response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        get_weather.assert_called_once_with(12.0, 34.0)
        with self.app.app_context():
            self.assertEqual(
                Alert.query.filter_by(user_id=self.user_id).count(),
                0
            )

    @patch("routes.dashboard.get_current_weather", return_value=None)
    def test_dashboard_handles_missing_weather(self, get_weather):
        with patch(
            "routes.dashboard.render_template",
            return_value="rendered"
        ) as render:
            response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(render.call_args.kwargs["heat_risk_score"])
        self.assertIsNone(render.call_args.kwargs["recommendations"])
        self.assertEqual(
            render.call_args.kwargs["heat_risk_level"],
            "Unavailable"
        )
        self.assertIn(
            "weather data is available",
            render.call_args.kwargs["heat_risk_message"]
        )
        get_weather.assert_called_once_with(12.0, 34.0)

    @patch("routes.dashboard.get_current_weather")
    def test_dashboard_handles_incomplete_user_settings(self, get_weather):
        get_weather.return_value = {
            "temperature": 33,
            "humidity": 55,
            "feels_like": 33,
            "time": "2026-10-06T12:00"
        }
        with self.app.app_context():
            user = db.session.get(User, self.user_id)
            user.activity_level = None
            db.session.commit()

        with patch(
            "routes.dashboard.render_template",
            return_value="rendered"
        ) as render:
            response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(render.call_args.kwargs["heat_risk_score"])
        self.assertIn(
            "Complete your activity",
            render.call_args.kwargs["heat_risk_message"]
        )

    @patch("routes.dashboard.get_current_weather")
    def test_dashboard_handles_incomplete_weather_fields(self, get_weather):
        get_weather.return_value = {
            "temperature": 33,
            "humidity": None,
            "feels_like": 33,
            "time": "2026-10-06T12:00"
        }

        with patch(
            "routes.dashboard.render_template",
            return_value="rendered"
        ) as render:
            response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(render.call_args.kwargs["heat_risk_score"])
        self.assertIn(
            "weather data is incomplete",
            render.call_args.kwargs["heat_risk_message"]
        )


if __name__ == "__main__":
    unittest.main()
