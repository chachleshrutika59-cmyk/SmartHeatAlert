import math


RISK_RECOMMENDATIONS = {
    "Low Risk": (
        "Normal outdoor activity is reasonable; continue to use usual precautions.",
        "Maintain your usual hydration routine."
    ),
    "Moderate Risk": (
        "Drink water regularly and take short cooling breaks.",
        "Choose water regularly, especially during time outdoors."
    ),
    "High Risk": (
        "Reduce prolonged outdoor exposure, stay hydrated, and take frequent cooling breaks.",
        "Drink water regularly and take frequent breaks to cool down."
    ),
    "Critical Risk": (
        "Avoid unnecessary outdoor exposure, move to a cooler environment, and take immediate heat-safety precautions.",
        "Keep water available and sip regularly while moving to a cooler environment."
    )
}

ACTIVITY_RECOMMENDATIONS = {
    "Indoor / Low Activity": "Stay in a cool indoor area when practical.",
    "Normal Activity": "Take breaks if you begin to feel overheated.",
    "Outdoor Activity": "Schedule outdoor activity for cooler periods when possible.",
    "Heavy Outdoor Work": "Break strenuous work into shorter periods and take frequent cooling breaks."
}

EXPOSURE_RECOMMENDATIONS = {
    "Less than 1 hour": "Keep outdoor time brief during the hottest part of the day.",
    "1–3 hours": "Plan shaded or cool-down breaks during outdoor time.",
    "3–6 hours": "Reduce continuous time in the heat and plan regular cooling breaks.",
    "More than 6 hours": "Minimize time in the heat where possible and plan frequent breaks in a cool place."
}

SUPPORTED_RISK_LEVELS = tuple(RISK_RECOMMENDATIONS)


def _finite_number(value, label):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a finite number.") from None

    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number.")

    return number


def generate_recommendations(
    temperature,
    humidity,
    feels_like,
    heat_risk_score,
    risk_level,
    activity_level,
    outdoor_exposure
):
    """Return deterministic, general heat-safety guidance for the given conditions."""
    temperature = _finite_number(temperature, "Temperature")
    humidity = _finite_number(humidity, "Humidity")
    feels_like = _finite_number(feels_like, "Feels-like temperature")
    heat_risk_score = _finite_number(heat_risk_score, "Heat risk score")

    if not 0 <= humidity <= 100:
        raise ValueError("Humidity must be between 0 and 100.")

    if not 0 <= heat_risk_score <= 100:
        raise ValueError("Heat risk score must be between 0 and 100.")

    if risk_level not in RISK_RECOMMENDATIONS:
        raise ValueError("Risk level is not recognized.")

    if activity_level not in ACTIVITY_RECOMMENDATIONS:
        raise ValueError("Activity level is not recognized.")

    if outdoor_exposure not in EXPOSURE_RECOMMENDATIONS:
        raise ValueError("Outdoor exposure is not recognized.")

    base_recommendation, hydration_message = RISK_RECOMMENDATIONS[risk_level]
    recommendations = [
        {"title": "Heat safety", "message": base_recommendation},
        {
            "title": "Activity",
            "message": ACTIVITY_RECOMMENDATIONS[activity_level]
        },
        {
            "title": "Outdoor exposure",
            "message": EXPOSURE_RECOMMENDATIONS[outdoor_exposure]
        }
    ]

    if temperature >= 35:
        recommendations.append({
            "title": "Air temperature",
            "message": (
                "Temperatures are high; avoid strenuous activity during the "
                "hottest part of the day when possible."
            )
        })

    if humidity >= 70:
        recommendations.append({
            "title": "Humidity",
            "message": (
                "High humidity can make it harder for sweat to cool your body; "
                "take cooling breaks in a shaded or air-conditioned place."
            )
        })

    if humidity >= 70 or feels_like >= 38:
        hydration_message = (
            "Choose water regularly, especially during activity, and take "
            "cooling breaks in a shaded or air-conditioned place."
        )

    if feels_like >= temperature + 3:
        recommendations.append({
            "title": "Feels-like conditions",
            "message": (
                "The feels-like temperature is notably above the air "
                "temperature; use the feels-like conditions when planning "
                "outdoor activity."
            )
        })

    return {
        "risk_level": risk_level,
        "risk_score": round(heat_risk_score),
        "recommendations": recommendations,
        "hydration": {
            "title": "Hydration",
            "message": hydration_message
        },
        "disclaimer": (
            "General heat-safety information only; it is not a medical "
            "diagnosis or a substitute for professional advice."
        )
    }
