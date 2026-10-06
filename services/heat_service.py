def classify_heat(temperature, safe_temperature):
    """
    Classify heat level based on the user's safe temperature.
    """

    if temperature is None or safe_temperature is None:
        return {
            "level": "Unknown",
            "color": "gray",
            "icon": "⚪",
            "message": "Temperature information is unavailable."
        }

    difference = temperature - safe_temperature

    # Safe
    if difference <= 0:
        return {
            "level": "Safe",
            "color": "green",
            "icon": "🟢",
            "message": (
                "The current temperature is within "
                "your selected safety range."
            )
        }

    # Moderate Heat
    elif difference <= 2:
        return {
            "level": "Moderate Heat",
            "color": "yellow",
            "icon": "🟡",
            "message": (
                "The temperature is slightly above "
                "your safe temperature. Stay hydrated "
                "and avoid unnecessary heat exposure."
            )
        }

    # High Heat
    elif difference <= 5:
        return {
            "level": "High Heat",
            "color": "orange",
            "icon": "🟠",
            "message": (
                "The temperature is significantly above "
                "your safe temperature. Limit outdoor "
                "exposure and stay hydrated."
            )
        }

    # Extreme Heat
    else:
        return {
            "level": "Extreme Heat",
            "color": "red",
            "icon": "🔴",
            "message": (
                "Extreme heat detected. Avoid unnecessary "
                "outdoor exposure and take immediate "
                "heat-safety precautions."
            )
        }