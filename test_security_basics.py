import os
import sys
import time
import unittest
from uuid import uuid4

ROOT = os.path.dirname(__file__)
APP_DIR = os.path.join(ROOT, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import app as app_module


class SecurityBasicsTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def test_admin_login_is_rate_limited_after_repeated_failures(self):
        last_response = None
        for _ in range(6):
            last_response = self.client.post(
                "/api/login",
                json={"username": "bartley_admin", "password": "wrong-password"},
                environ_overrides={"REMOTE_ADDR": "203.0.113.10"},
            )

        self.assertIsNotNone(last_response)
        self.assertEqual(last_response.status_code, 429)
        payload = last_response.get_json()
        self.assertFalse(payload["ok"])
        self.assertIn("too many", payload["error"].lower())

    def test_mobile_register_rejects_weak_password(self):
        response = self.client.post(
            "/api/mobile/register",
            json={
                "username": f"weak_{uuid4().hex[:8]}",
                "password": "abc123",
                "first_name": "Weak",
                "last_name": "Password",
                "club_id": 110,
            },
            environ_overrides={"REMOTE_ADDR": "203.0.113.11"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertFalse(payload["ok"])
        self.assertIn("password", payload["error"].lower())

    def test_cross_site_admin_post_is_rejected(self):
        login = self.client.post(
            "/api/login",
            json={"username": "bartley_admin", "password": "ChangeMe123!"},
            environ_overrides={"REMOTE_ADDR": "203.0.113.12"},
        )
        self.assertEqual(login.status_code, 200)

        response = self.client.post(
            "/api/logout",
            headers={"Origin": "https://evil.example"},
            environ_overrides={"REMOTE_ADDR": "203.0.113.12"},
        )

        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        self.assertFalse(payload["ok"])
        self.assertIn("csrf", payload["error"].lower())


if __name__ == "__main__":
    unittest.main()
