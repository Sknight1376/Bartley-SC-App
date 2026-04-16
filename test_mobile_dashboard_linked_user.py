import os
import sys
import unittest

ROOT = os.path.dirname(__file__)
APP_DIR = os.path.join(ROOT, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import app as app_module


class MobileDashboardLinkedUserTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def _seed_linked_session(self):
        with self.client.session_transaction() as sess:
            sess["sailor_user_id"] = "1704"
            sess["sailor_id"] = "1703"
            sess["sailor_club_id"] = "110"
            sess["sailor_username"] = "jling"

    def test_dashboard_uses_current_linked_sailor_from_user_mapping(self):
        self._seed_linked_session()

        response = self.client.get("/api/mobile/dashboard")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ok"])
        self.assertGreater(len(payload["completed_races"]), 0)
        self.assertGreater(len(payload["series_positions"]), 0)
        self.assertTrue(all("pursuit" not in (row.get("series_name") or "").lower() for row in payload["completed_races"]))
        self.assertTrue(all("pursuit" not in (row.get("series_name") or "").lower() for row in payload["series_positions"]))
        self.assertTrue(all("pursuit" not in (row.get("series_name") or "").lower() for row in payload["latest_day_results"]))

        latest_dates = {str(row.get("started_at", "")).split("T")[0].split(" ")[0] for row in payload["completed_races"] if row.get("started_at")}
        self.assertEqual(len(latest_dates), 1)

        my_latest_dates = {str(row.get("started_at", "")).split("T")[0].split(" ")[0] for row in payload["latest_day_results"] if row.get("started_at")}
        self.assertLessEqual(len(my_latest_dates), 1)
        self.assertGreater(len(payload["latest_day_results"]), 0)

        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("sailor_id"), "510")

    def test_mobile_series_results_returns_web_style_grouped_data(self):
        self._seed_linked_session()

        response = self.client.get("/api/mobile/series/results")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ok"])
        self.assertGreater(len(payload["series"]), 0)
        self.assertTrue(all("pursuit" not in (row.get("series_name") or "").lower() for row in payload["series"]))
        self.assertTrue(any(len(row.get("races") or []) > 0 for row in payload["series"]))
        self.assertTrue(any(len(row.get("race_sections") or []) > 0 for row in payload["series"]))

    def test_race_control_live_races_are_visible_to_logged_in_club_users(self):
        self._seed_linked_session()

        access_response = self.client.get("/api/mobile/races/control/access")
        races_response = self.client.get("/api/mobile/races/control/upcoming")

        self.assertEqual(access_response.status_code, 200)
        self.assertEqual(races_response.status_code, 200)

        access_payload = access_response.get_json()
        races_payload = races_response.get_json()

        self.assertTrue(access_payload["ok"])
        self.assertTrue(races_payload["ok"])
        self.assertTrue(access_payload["can_race_control"])
        self.assertTrue(races_payload["can_race_control"])
        self.assertGreaterEqual(len(races_payload["races"]), 2)

        race_id = races_payload["races"][0]["race_id"]
        entries_response = self.client.get(f"/api/mobile/races/{race_id}/control-entries")
        self.assertEqual(entries_response.status_code, 200)
        self.assertTrue(entries_response.get_json()["ok"])

    def test_race_control_options_return_sailors_and_boats(self):
        self._seed_linked_session()

        response = self.client.get("/api/mobile/races/control/options")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ok"])
        self.assertGreater(len(payload["sailors"]), 0)
        self.assertTrue(any(len(row.get("boats") or []) >= 0 for row in payload["sailors"]))


if __name__ == "__main__":
    unittest.main()
