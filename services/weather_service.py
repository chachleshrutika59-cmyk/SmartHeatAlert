import logging
import math

import requests


FORECAST_HOURS = (6, 9, 12, 14, 16, 18, 21)
logger = logging.getLogger(__name__)


def _weather_number(value, minimum=None, maximum=None):
    if isinstance(value, bool) or value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None
    if minimum is not None and number < minimum:
        return None
    if maximum is not None and number > maximum:
        return None
    return number


def get_current_weather(latitude, longitude):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature",
        "temperature_unit": "celsius",
        "timezone": "auto"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()
        if not isinstance(data, dict):
            logger.warning("Current weather API returned an invalid response.")
            return None
        current = data.get("current")
        if not isinstance(current, dict):
            logger.warning("Current weather API response omitted current data.")
            return None

        return {
            "temperature": _weather_number(current.get("temperature_2m")),
            "humidity": _weather_number(
                current.get("relative_humidity_2m"),
                minimum=0,
                maximum=100
            ),
            "feels_like": _weather_number(
                current.get("apparent_temperature")
            ),
            "time": (
                current.get("time")
                if isinstance(current.get("time"), str)
                else None
            )
        }

    except requests.RequestException:
        logger.warning("Current weather API request failed.")

        return None


def get_today_forecast(latitude, longitude):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature",
        "forecast_days": 1,
        "temperature_unit": "celsius",
        "timezone": "auto"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            logger.warning("Forecast API returned an invalid response.")
            return []
        hourly = data.get("hourly")
        if not isinstance(hourly, dict):
            logger.warning("Forecast API response omitted hourly data.")
            return []
        times = hourly.get("time", [])
        temperatures = hourly.get("temperature_2m", [])
        humidities = hourly.get("relative_humidity_2m", [])
        feels_like_values = hourly.get("apparent_temperature", [])
        if not all(
            isinstance(values, list)
            for values in (
                times,
                temperatures,
                humidities,
                feels_like_values
            )
        ):
            logger.warning("Forecast API returned invalid hourly values.")
            return []

        forecast = []
        for target_hour in FORECAST_HOURS:
            candidates = []
            for index, time_value in enumerate(times):
                try:
                    hour = int(time_value[11:13])
                except (TypeError, ValueError, IndexError):
                    continue

                if (
                    abs(hour - target_hour) <= 1
                    and index < len(temperatures)
                    and index < len(humidities)
                    and index < len(feels_like_values)
                ):
                    candidates.append((abs(hour - target_hour), index))

            if not candidates:
                continue

            _, index = min(candidates)
            forecast.append({
                "time": (
                    times[index] if isinstance(times[index], str) else None
                ),
                "temperature": _weather_number(temperatures[index]),
                "humidity": _weather_number(
                    humidities[index],
                    minimum=0,
                    maximum=100
                ),
                "feels_like": _weather_number(feels_like_values[index])
            })

        return forecast

    except requests.RequestException:
        logger.warning("Weather forecast API request failed.")
        return []