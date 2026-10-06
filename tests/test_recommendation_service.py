import unittest

from services.recommendation_service import generate_recommendations


class GenerateRecommendationsTests(unittest.TestCase):
    def test_critical_risk_returns_safety_and_hydration_guidance(self):
        result = generate_recommendations(
            temperature=45,
            humidity=90,
            feels_like=49,
            heat_risk_score=92,
            risk_level="Critical Risk",
            activity_level="Heavy Outdoor Work",
            outdoor_exposure="More than 6 hours"
        )

        self.assertEqual(result["risk_level"], "Critical Risk")
        self.assertEqual(result["risk_score"], 92)
        self.assertTrue(result["recommendations"])
        self.assertIn(
            "Avoid unnecessary outdoor exposure",
            result["recommendations"][0]["message"]
        )
        self.assertIn("water", result["hydration"]["message"].lower())
        self.assertIn("not a medical diagnosis", result["disclaimer"])

    def test_moderate_recommendations_reflect_activity_and_exposure(self):
        result = generate_recommendations(
            temperature=34,
            humidity=55,
            feels_like=35,
            heat_risk_score=42,
            risk_level="Moderate Risk",
            activity_level="Outdoor Activity",
            outdoor_exposure="3–6 hours"
        )

        messages = [item["message"] for item in result["recommendations"]]
        self.assertTrue(any("short cooling breaks" in item for item in messages))
        self.assertTrue(any("cooler periods" in item for item in messages))
        self.assertTrue(any("continuous time" in item for item in messages))

    def test_recommendations_include_relevant_weather_factors(self):
        result = generate_recommendations(
            temperature=35,
            humidity=75,
            feels_like=40,
            heat_risk_score=60,
            risk_level="High Risk",
            activity_level="Normal Activity",
            outdoor_exposure="1–3 hours"
        )

        titles = [item["title"] for item in result["recommendations"]]
        self.assertIn("Air temperature", titles)
        self.assertIn("Humidity", titles)
        self.assertIn("Feels-like conditions", titles)
        self.assertIn("cooling breaks", result["hydration"]["message"])

    def test_rejects_invalid_weather_or_profile_data(self):
        with self.assertRaises(ValueError):
            generate_recommendations(
                temperature=35,
                humidity=101,
                feels_like=36,
                heat_risk_score=60,
                risk_level="High Risk",
                activity_level="Normal Activity",
                outdoor_exposure="1–3 hours"
            )


if __name__ == "__main__":
    unittest.main()
