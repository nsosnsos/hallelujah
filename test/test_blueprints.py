#!/usr/bin/env python3
"""test blueprints"""

import unittest

from hallelujah import create_app, db


class BlueprintTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_main_blueprint_routes(self):
        with self.app.test_client() as client:
            response = client.get("/")
            self.assertEqual(response.status_code, 200)

            response = client.get("/about")
            self.assertEqual(response.status_code, 200)

    def test_auth_blueprint_routes(self):
        with self.app.test_client() as client:
            response = client.get("/auth/login")
            self.assertEqual(response.status_code, 200)

            response = client.get("/auth/register")
            self.assertEqual(response.status_code, 200)

            response = client.get("/auth/profile")
            self.assertIn(response.status_code, [302, 401])

    def test_api_blueprint_routes(self):
        with self.app.test_client() as client:
            response = client.get("/api/search?keywords=test")
            self.assertEqual(response.status_code, 200)

            response = client.get("/api/get_articles")
            self.assertEqual(response.status_code, 200)

    def test_theme_routes(self):
        with self.app.test_client() as client:
            response = client.post("/theme", data={"toggle": "true"})
            self.assertIn(response.status_code, [200, 302])

            response = client.get("/theme/United")
            self.assertIn(response.status_code, [200, 302])
