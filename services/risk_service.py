import math


ACTIVITY_RISK = {
    "Indoor / Low Activity": 0,
    "Normal Activity": 100 / 3,
    "Outdoor Activity": 200 / 3,
    "Heavy Outdoor Work": 100
}

EXPOSURE_RISK = {
    "Less than 1 hour": 0,
    "1–3 hours": 100 / 3,
    "3–6 hours": 200 / 3,
    "More than 6 hours": 100
}

RISK_LEVELS = (
    (25, "Low Risk", "🟢", "Heat conditions are low risk. Continue normal precautions."),
    (50, "Moderate Risk", "🟡", "Heat may affect you. Stay hydrated and take breaks in a cool place."),
    (75, "High Risk", "🟠", "Heat risk is high. Limit outdoor exertion and seek shade or a cool place."),
    (100, "Critical Risk", "🔴", "Heat risk is critical. Avoid strenuous outdoor activity and cool down now.")
)


def _finite_number(value, label):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a finite number.") from None

    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number.")

    return number


def _heat_normalized(value, safe_temperature):
    return min(100.0, max(0.0, (value - safe_temperature) * (100.0 / 15.0)))


def calculate_heat_risk(
    temperature,
    humidity,
    feels_like,
    activity_level,
    outdoor_exposure,
    safe_temperature
):
    """Calculate a deterministic 0-100 heat risk score for a user."""
    temperature = _finite_number(temperature, "Temperature")
    humidity = _finite_number(humidity, "Humidity")
    feels_like = _finite_number(feels_like, "Feels-like temperature")
    safe_temperature = _finite_number(safe_temperature, "Safe temperature")

    if not 0 <= humidity <= 100:
        raise ValueError("Humidity must be between 0 and 100.")

    if activity_level not in ACTIVITY_RISK:
        raise ValueError("Activity level is not recognized.")

    if outdoor_exposure not in EXPOSURE_RISK:
        raise ValueError("Outdoor exposure is not recognized.")

    temperature_score = _heat_normalized(temperature, safe_temperature)
    humidity_score = min(100.0, max(0.0, (humidity - 30.0) * 2.0))
    feels_like_score = _heat_normalized(feels_like, safe_temperature)

    weighted_score = (
        temperature_score * 0.40
        + humidity_score * 0.20
        + feels_like_score * 0.20
        + ACTIVITY_RISK[activity_level] * 0.10
        + EXPOSURE_RISK[outdoor_exposure] * 0.10
    )
    score = min(100, max(0, round(weighted_score)))

    for maximum, level, icon, message in RISK_LEVELS:
        if score <= maximum:
            return {
                "score": score,
                "level": level,
                "icon": icon,
                "message": message
            }

    raise RuntimeError("Heat risk score fell outside the expected range.")
