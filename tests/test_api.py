import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from flask import Flask

from extensions import db
from models.location import Location
from models.user import User
from routes.api import api_bp


class LocationApiTests(unittest.TestCase):
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
        self.app.register_blueprint(api_bp)

        with self.app.app_context():
            db.create_all()
            self.user = User(mobile_number="1234567890")
            db.session.add(self.user)
            db.session.commit()
            self.user_id = self.user.id

        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["logged_in"] = True
            session["user_id"] = self.user_id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_save_location_rejects_invalid_coordinates_without_server_error(self):
        invalid_coordinates = (
            {"latitude": "not-a-number", "longitude": 20},
            {"latitude": 91, "longitude": 20},
            {"latitude": 20, "longitude": -181},
            {"latitude": "NaN", "longitude": 20},
            {"latitude": True, "longitude": 20},
        )

        for coordinates in invalid_coordinates:
            with self.subTest(coordinates=coordinates):
                response = self.client.post("/api/location", json=coordinates)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(response.json["success"])

        malformed_json = self.client.post(
            "/api/location",
            data="{",
            content_type="application/json"
        )
        self.assertEqual(malformed_json.status_code, 400)
        with self.app.app_context():
            self.assertEqual(Location.query.count(), 0)

    @patch("routes.api.get_location_name", return_value="Test City")
    def test_save_location_accepts_valid_coordinates(self, get_location_name):
        response = self.client.post(
            "/api/location",
            json={"latitude": "12.5", "longitude": 77.6}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["success"])
        get_location_name.assert_called_once_with(12.5, 77.6)
        with self.app.app_context():
            location = Location.query.one()
            self.assertEqual(location.user_id, self.user_id)

    def test_search_location_rejects_invalid_or_oversized_queries(self):
        invalid_bodies = (
            None,
            {"location": []},
            {"location": " "},
            {"location": "x" * 201},
        )

        for body in invalid_bodies:
            with self.subTest(body=body):
                response = self.client.post("/api/search-location", json=body)
                self.assertEqual(response.status_code, 400)

    @patch("routes.api.requests.get")
    def test_search_location_rejects_invalid_geocoder_coordinates(self, get):
        get.return_value = Mock(
            json=lambda: [{"lat": "91", "lon": "12", "display_name": "Bad"}]
        )
        get.return_value.raise_for_status.return_value = None

        response = self.client.post(
            "/api/search-location",
            json={"location": "Test City"}
        )

        self.assertEqual(response.status_code, 502)
        with self.app.app_context():
            self.assertEqual(Location.query.count(), 0)

    @patch("routes.api.requests.get")
    def test_search_location_returns_service_unavailable_on_network_error(self, get):
        from requests import RequestException

        get.side_effect = RequestException("upstream error")
        response = self.client.post(
            "/api/search-location",
            json={"location": "Test City"}
        )

        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json["success"])


if __name__ == "__main__":
    unittest.main()
