from flask import Blueprint, render_template, session, redirect, url_for

from models.location import Location
from models.user import User

from services.weather_service import get_current_weather, get_today_forecast
from services.heat_service import classify_heat
from services.risk_service import calculate_heat_risk
from services.recommendation_service import generate_recommendations
from services.alert_service import create_heat_alert_if_needed
from services.history_service import save_temperature_record
from models.alert import Alert


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():

    # Check login
    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))

    user_id = session.get("user_id")
    mobile_number = session.get("mobile_number")

    # Get the authenticated user's profile.
    user = User.query.filter_by(id=user_id).first_or_404()

    # Get latest saved location
    location = (
        Location.query
        .filter_by(user_id=user_id)
        .order_by(Location.created_at.desc())
        .first()
    )

    weather = None
    heat_status = None
    heat_risk = None
    recommendations = None
    forecast = []
    heat_risk_message = "Heat risk is unavailable until weather data is available."

    # Get weather
    if location:

        weather = get_current_weather(
            location.latitude,
            location.longitude
        )
        forecast_data = get_today_forecast(
            location.latitude,
            location.longitude
        )

        for forecast_item in forecast_data:
            item = dict(forecast_item)
            item["risk"] = None
            if (
                user.safe_temperature is not None
                and user.activity_level
                and user.outdoor_exposure
                and all(
                    item.get(key) is not None
                    for key in ("temperature", "humidity", "feels_like")
                )
            ):
                try:
                    item["risk"] = calculate_heat_risk(
                        temperature=item["temperature"],
                        humidity=item["humidity"],
                        feels_like=item["feels_like"],
                        activity_level=user.activity_level,
                        outdoor_exposure=user.outdoor_exposure,
                        safe_temperature=user.safe_temperature
                    )
                except ValueError:
                    item["risk"] = None

            try:
                forecast_temperature = float(item["temperature"])
                item["chart_height"] = round(
                    max(0, min(100, (forecast_temperature + 10) * 100 / 60))
                )
            except (TypeError, ValueError):
                item["chart_height"] = 0

            item["time_label"] = (
                item["time"][11:16]
                if isinstance(item.get("time"), str)
                else "—"
            )
            forecast.append(item)

    if weather:
        weather_values = (
            weather.get("temperature"),
            weather.get("humidity"),
            weather.get("feels_like")
        )
        has_weather_values = all(value is not None for value in weather_values)

        if has_weather_values:
            # Keep the existing threshold-based status where the user's
            # threshold is configured.
            if user.safe_temperature is not None:
                heat_status = classify_heat(
                    weather["temperature"],
                    user.safe_temperature
                )

            if (
                user.safe_temperature is not None
                and user.activity_level
                and user.outdoor_exposure
            ):
                try:
                    heat_risk = calculate_heat_risk(
                        temperature=weather["temperature"],
                        humidity=weather["humidity"],
                        feels_like=weather["feels_like"],
                        activity_level=user.activity_level,
                        outdoor_exposure=user.outdoor_exposure,
                        safe_temperature=user.safe_temperature
                    )
                except ValueError:
                    heat_risk_message = (
                        "Heat risk could not be calculated from the "
                        "available weather or profile data."
                    )
                else:
                    heat_risk_message = heat_risk["message"]
                    recommendations = generate_recommendations(
                        temperature=weather["temperature"],
                        humidity=weather["humidity"],
                        feels_like=weather["feels_like"],
                        heat_risk_score=heat_risk["score"],
                        risk_level=heat_risk["level"],
                        activity_level=user.activity_level,
                        outdoor_exposure=user.outdoor_exposure
                    )
            elif not (
                user.safe_temperature is not None
                and user.activity_level
                and user.outdoor_exposure
            ):
                heat_risk_message = (
                    "Complete your activity, outdoor exposure, and safe "
                    "temperature settings to see your personalized heat risk."
                )
        else:
            heat_risk_message = (
                "Heat risk is unavailable because current weather data "
                "is incomplete."
            )

    heat_risk_score = heat_risk["score"] if heat_risk else None
    heat_risk_level = heat_risk["level"] if heat_risk else "Unavailable"
    heat_risk_icon = heat_risk["icon"] if heat_risk else "⚪"

    if (
        user.notification_enabled
        and weather
        and weather.get("temperature") is not None
        and user.safe_temperature is not None
    ):
        location_label = (
            location.location_name
            or f"{location.latitude:.4f}, {location.longitude:.4f}"
            if location
            else "Unknown location"
        )
        create_heat_alert_if_needed(
            user_id=user.id,
            temperature=weather["temperature"],
            safe_temperature=user.safe_temperature,
            risk_score=heat_risk_score,
            risk_level=heat_risk_level,
            location=location_label
        )

    if (
        location
        and weather
        and weather.get("temperature") is not None
    ):
        save_temperature_record(
            user_id=user.id,
            location_id=location.id,
            weather=weather,
            heat_risk=heat_risk
        )

    unread_alert_count = Alert.query.filter_by(
        user_id=user.id,
        is_read=False
    ).count()

    return render_template(
        "dashboard.html",
        mobile_number=mobile_number,
        location=location,
        weather=weather,
        user=user,
        heat_status=heat_status,
        heat_risk=heat_risk,
        heat_risk_score=heat_risk_score,
        heat_risk_level=heat_risk_level,
        heat_risk_icon=heat_risk_icon,
        heat_risk_message=heat_risk_message,
        recommendations=recommendations,
        unread_alert_count=unread_alert_count,
        forecast=forecast
    )