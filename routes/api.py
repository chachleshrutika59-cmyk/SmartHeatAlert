import math

import requests

from flask import Blueprint, current_app, request, jsonify, session

from extensions import db
from models.location import Location


api_bp = Blueprint("api", __name__, url_prefix="/api")
MAX_LOCATION_QUERY_LENGTH = 200


def _coordinates_from(data, latitude_key="latitude", longitude_key="longitude"):
    if not isinstance(data, dict):
        return None

    latitude_value = data.get(latitude_key)
    longitude_value = data.get(longitude_key)
    if isinstance(latitude_value, bool) or isinstance(longitude_value, bool):
        return None

    try:
        latitude = float(latitude_value)
        longitude = float(longitude_value)
    except (TypeError, ValueError):
        return None

    if (
        not math.isfinite(latitude)
        or not math.isfinite(longitude)
        or not -90 <= latitude <= 90
        or not -180 <= longitude <= 180
    ):
        return None

    return latitude, longitude


def get_location_name(latitude, longitude):

    url = "https://nominatim.openstreetmap.org/reverse"

    params = {
        "lat": latitude,
        "lon": longitude,
        "format": "jsonv2",
        "addressdetails": 1,
        "zoom": 18,
        "accept-language": "en"
    }

    headers = {
        "User-Agent": "SmartHeatAlert/1.0"
    }

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()
        if not isinstance(data, dict):
            current_app.logger.warning(
                "Reverse geocoding returned an invalid response."
            )
            return None

        address = data.get("address", {})
        if not isinstance(address, dict):
            address = {}

        # Try to get the most useful local name
        location_name = (
            address.get("neighbourhood")
            or address.get("suburb")
            or address.get("village")
            or address.get("town")
            or address.get("city")
            or address.get("county")
        )

        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
        )

        if location_name and city and location_name != city:
            return f"{location_name}, {city}"

        return location_name or data.get("display_name")

    except requests.RequestException:
        current_app.logger.warning("Reverse geocoding request failed.")

        return None


@api_bp.route("/location", methods=["POST"])
def save_location():

    if not session.get("logged_in") or not session.get("user_id"):
        return jsonify({
            "success": False,
            "message": "User not logged in"
        }), 401

    coordinates = _coordinates_from(request.get_json(silent=True))
    if coordinates is None:
        return jsonify({
            "success": False,
            "message": "Provide valid latitude and longitude values."
        }), 400

    latitude, longitude = coordinates

    user_id = session.get("user_id")

    # Get location name
    location_name = get_location_name(
        latitude,
        longitude
    )

    # Save location
    location = Location(
        user_id=user_id,
        latitude=latitude,
        longitude=longitude,
        location_name=location_name
    )

    db.session.add(location)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Location saved successfully",
        "location_id": location.id,
        "latitude": latitude,
        "longitude": longitude,
        "location_name": location_name
    })

@api_bp.route("/search-location", methods=["POST"])
def search_location():

    if not session.get("logged_in") or not session.get("user_id"):
        return jsonify({
            "success": False,
            "message": "User not logged in"
        }), 401

    data = request.get_json(silent=True)
    search_text = data.get("location") if isinstance(data, dict) else None
    if isinstance(search_text, str):
        search_text = search_text.strip()

    if not isinstance(search_text, str) or not search_text:
        return jsonify({
            "success": False,
            "message": "Please enter a location."
        }), 400
    if len(search_text) > MAX_LOCATION_QUERY_LENGTH:
        return jsonify({
            "success": False,
            "message": "Location search must be 200 characters or fewer."
        }), 400

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": search_text,
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1,
        "accept-language": "en"
    }

    headers = {
        "User-Agent": "SmartHeatAlert/1.0"
    }

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        results = response.json()

        if not isinstance(results, list):
            current_app.logger.warning(
                "Location search returned an invalid response."
            )
            return jsonify({
                "success": False,
                "message": "Location service returned an invalid response."
            }), 502

        if not results:

            return jsonify({
                "success": False,
                "message": "Location not found."
            })

        result = results[0]
        if not isinstance(result, dict):
            return jsonify({
                "success": False,
                "message": "Location service returned an invalid result."
            }), 502

        coordinates = _coordinates_from(
            result,
            latitude_key="lat",
            longitude_key="lon"
        )
        if coordinates is None:
            current_app.logger.warning(
                "Location search returned invalid coordinates."
            )
            return jsonify({
                "success": False,
                "message": "Location service returned invalid coordinates."
            }), 502
        latitude, longitude = coordinates

        location_name = str(result.get("display_name") or search_text)[:200]

        user_id = session.get("user_id")

        location = Location(
            user_id=user_id,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name
        )

        db.session.add(location)
        db.session.commit()

        return jsonify({
            "success": True,
            "latitude": latitude,
            "longitude": longitude,
            "location_name": location_name
        })

    except requests.RequestException:
        current_app.logger.warning("Location search request failed.")

        return jsonify({
            "success": False,
            "message": "Location service unavailable."
        }), 503