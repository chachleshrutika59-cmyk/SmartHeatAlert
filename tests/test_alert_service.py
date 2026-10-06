import unittest
from datetime import datetime, timedelta, timezone

from flask import Flask

from extensions import db
from models.alert import Alert
from models.user import User
from services.alert_service import create_heat_alert_if_needed


class CreateHeatAlertTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            SECRET_KEY="test-secret",
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite://"
        )
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            self.user = User(mobile_number="1234567890", safe_temperature=38)
            db.session.add(self.user)
            db.session.commit()
            self.user_id = self.user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_high_risk_alert_created_only_once_during_cooldown(self):
        with self.app.app_context():
            first = create_heat_alert_if_needed(
                user_id=self.user_id,
                temperature=39,
                safe_temperature=38,
                risk_score=70,
                risk_level="High Risk",
                location="Example location"
            )
            repeated = create_heat_alert_if_needed(
                user_id=self.user_id,
                temperature=39,
                safe_temperature=38,
                risk_score=70,
                risk_level="High Risk",
                location="Example location"
            )

            self.assertIsNotNone(first)
            self.assertEqual(first.id, repeated.id)
            self.assertEqual(
                Alert.query.filter_by(user_id=self.user_id).count(),
                1
            )
            self.assertEqual(first.risk_score, 70)
            self.assertEqual(first.threshold, 38)
            self.assertFalse(first.is_read)

    def test_critical_level_escalation_creates_a_new_alert(self):
        with self.app.app_context():
            create_heat_alert_if_needed(
                user_id=self.user_id,
                temperature=39,
                safe_temperature=38,
                risk_score=70,
                risk_level="High Risk",
                location="Example location"
            )
            critical = create_heat_alert_if_needed(
                user_id=self.user_id,
                temperature=43,
                safe_temperature=38,
                risk_score=90,
                risk_level="Critical Risk",
                location="Example location"
            )

            self.assertEqual(critical.heat_level, "Critical Risk")
            self.assertEqual(
                Alert.query.filter_by(user_id=self.user_id).count(),
                2
            )

    def test_temperature_threshold_alert_created_without_risk_score(self):
        with self.app.app_context():
            alert = create_heat_alert_if_needed(
                user_id=self.user_id,
                temperature=39,
                safe_temperature=38,
                risk_score=None,
                risk_level="Unavailable",
                location="Example location"
            )

            self.assertIsNone(alert.risk_score)
            self.assertEqual(alert.heat_level, "Unavailable")
            self.assertIn("exceeds your safe temperature", alert.message)

    def test_no_alert_when_temperature_and_risk_are_low(self):
        with self.app.app_context():
            alert = create_heat_alert_if_needed(
                user_id=self.user_id,
                temperature=30,
                safe_temperature=38,
                risk_score=12,
                risk_level="Low Risk",
                location="Example location"
            )

            self.assertIsNone(alert)
            self.assertEqual(Alert.query.count(), 0)

    def test_same_condition_can_alert_again_after_cooldown(self):
        with self.app.app_context():
            old_alert = Alert(
                user_id=self.user_id,
                temperature=39,
                threshold=38,
                risk_score=70,
                heat_level="High Risk",
                location="Example location",
                condition_key="High Risk|above_safe=1",
                message="Old heat alert",
                created_at=(
                    datetime.now(timezone.utc).replace(tzinfo=None)
                    - timedelta(hours=7)
                )
            )
            db.session.add(old_alert)
            db.session.commit()

            new_alert = create_heat_alert_if_needed(
                user_id=self.user_id,
                temperature=39,
                safe_temperature=38,
                risk_score=70,
                risk_level="High Risk",
                location="Example location"
            )

            self.assertNotEqual(old_alert.id, new_alert.id)
            self.assertEqual(Alert.query.filter_by(user_id=self.user_id).count(), 2)


if __name__ == "__main__":
    unittest.main()
