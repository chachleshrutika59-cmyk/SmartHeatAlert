import unittest

from services.risk_service import calculate_heat_risk


class CalculateHeatRiskTests(unittest.TestCase):
    def test_low_temperature(self):
        result = calculate_heat_risk(
            temperature=24,
            humidity=30,
            feels_like=24,
            activity_level="Indoor / Low Activity",
            outdoor_exposure="Less than 1 hour",
            safe_temperature=35
        )

        self.assertEqual(result["score"], 0)
        self.assertEqual(result["level"], "Low Risk")

    def test_moderate_heat(self):
        result = calculate_heat_risk(
            temperature=33,
            humidity=55,
            feels_like=33,
            activity_level="Normal Activity",
            outdoor_exposure="1–3 hours",
            safe_temperature=30
        )

        self.assertEqual(result["score"], 29)
        self.assertEqual(result["level"], "Moderate Risk")

    def test_high_heat(self):
        result = calculate_heat_risk(
            temperature=39,
            humidity=70,
            feels_like=42,
            activity_level="Outdoor Activity",
            outdoor_exposure="3–6 hours",
            safe_temperature=30
        )

        self.assertEqual(result["score"], 69)
        self.assertEqual(result["level"], "High Risk")

    def test_critical_heat(self):
        result = calculate_heat_risk(
            temperature=45,
            humidity=90,
            feels_like=45,
            activity_level="Heavy Outdoor Work",
            outdoor_exposure="More than 6 hours",
            safe_temperature=30
        )

        self.assertEqual(result["score"], 100)
        self.assertEqual(result["level"], "Critical Risk")


if __name__ == "__main__":
    unittest.main()
