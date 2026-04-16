import os
import sys
import unittest

ROOT = os.path.dirname(__file__)
APP_DIR = os.path.join(ROOT, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import app as app_module


class Phase1AcceptanceSmokeTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def _seed_mobile_session(self):
        with self.client.session_transaction() as sess:
            sess["sailor_user_id"] = "1704"
            sess["sailor_id"] = "1703"
            sess["sailor_club_id"] = "110"
            sess["sailor_username"] = "jling"

    def test_public_intro_and_health(self):
        intro = self.client.get("/")
        self.assertEqual(intro.status_code, 200)

        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        payload = health.get_json()
        self.assertTrue(payload["ok"])

    def test_web_admin_phase1_pages_and_dashboard_endpoints(self):
        login = self.client.post(
            "/api/login",
            json={"username": "bartley_admin", "password": "ChangeMe123!"},
        )
        self.assertEqual(login.status_code, 200)
        login_payload = login.get_json()
        self.assertTrue(login_payload["ok"])
        self.assertEqual(login_payload["club_name"], "Bartley Sailing Club")

        landing = self.client.get("/landing")
        self.assertEqual(landing.status_code, 200)

        dashboard = self.client.get("/club_dashboard")
        self.assertEqual(dashboard.status_code, 200)

        for path in [
            "/api/dashboard/landing-overview",
            "/api/dashboard/series-results",
            "/api/dashboard/results-review-queue",
        ]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            payload = response.get_json()
            self.assertTrue(payload["ok"], path)

    def test_mobile_phase1_core_endpoints(self):
        clubs = self.client.get("/api/mobile/clubs")
        self.assertEqual(clubs.status_code, 200)
        clubs_payload = clubs.get_json()
        self.assertTrue(clubs_payload["ok"])
        self.assertGreater(len(clubs_payload["clubs"]), 0)

        self._seed_mobile_session()

        protected_paths = [
            "/api/mobile/me",
            "/api/mobile/races/upcoming",
            "/api/mobile/dashboard",
            "/api/mobile/series",
            "/api/mobile/series/standings",
            "/api/mobile/series/results",
            "/api/mobile/duties",
        ]

        for path in protected_paths:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            payload = response.get_json()
            self.assertTrue(payload["ok"], path)

        dashboard_payload = self.client.get("/api/mobile/dashboard").get_json()
        self.assertIn("latest_day_results", dashboard_payload)
        self.assertIn("series_positions", dashboard_payload)

        series_payload = self.client.get("/api/mobile/series/results").get_json()
        self.assertIn("series", series_payload)
        self.assertGreater(len(series_payload["series"]), 0)


if __name__ == "__main__":
    unittest.main()
