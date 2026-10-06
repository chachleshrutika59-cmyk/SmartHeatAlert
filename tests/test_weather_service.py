import unittest
from unittest.mock import Mock, patch

from services.weather_service import get_current_weather, get_today_forecast


class TodayForecastTests(unittest.TestCase):
    @patch("services.weather_service.requests.get")
    def test_current_weather_normalizes_invalid_values(self, get):
        get.return_value = Mock(
            json=lambda: {
                "current": {
                    "temperature_2m": "not-a-number",
                    "relative_humidity_2m": 105,
                    "apparent_temperature": 36,
                    "time": 123
                }
            }
        )
        get.return_value.raise_for_status.return_value = None

        weather = get_current_weather(12.5, 77.6)

        self.assertEqual(
            weather,
            {
                "temperature": None,
                "humidity": None,
                "feels_like": 36.0,
                "time": None
            }
        )

    @patch("services.weather_service.requests.get")
    def test_current_weather_rejects_malformed_response_shape(self, get):
        get.return_value = Mock(json=lambda: ["unexpected"])
        get.return_value.raise_for_status.return_value = None

        self.assertIsNone(get_current_weather(12.5, 77.6))

    @patch("services.weather_service.requests.get")
    def test_fetches_and_selects_today_hourly_forecast(self, get):
        times = [f"2026-10-06T{hour:02}:00" for hour in range(24)]
        get.return_value = Mock(
            json=lambda: {
                "hourly": {
                    "time": times,
                    "temperature_2m": list(range(20, 44)),
                    "relative_humidity_2m": [50] * 24,
                    "apparent_temperature": list(range(21, 45))
                }
            }
        )
        get.return_value.raise_for_status.return_value = None

        forecast = get_today_forecast(12.5, 77.6)

        self.assertEqual(
            [item["time"] for item in forecast],
            [
                "2026-10-06T06:00",
                "2026-10-06T09:00",
                "2026-10-06T12:00",
                "2026-10-06T14:00",
                "2026-10-06T16:00",
                "2026-10-06T18:00",
                "2026-10-06T21:00"
            ]
        )
        self.assertEqual(forecast[0]["temperature"], 26)
        self.assertEqual(forecast[0]["humidity"], 50)
        self.assertEqual(forecast[0]["feels_like"], 27)
        params = get.call_args.kwargs["params"]
        self.assertEqual(params["forecast_days"], 1)
        self.assertEqual(params["timezone"], "auto")

    @patch("services.weather_service.requests.get")
    def test_returns_empty_list_when_forecast_api_fails(self, get):
        from requests import RequestException

        get.side_effect = RequestException("forecast unavailable")

        self.assertEqual(get_today_forecast(12.5, 77.6), [])


if __name__ == "__main__":
    unittest.main()
