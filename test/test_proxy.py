#!/usr/bin/env python3
"""test proxy"""

import tempfile

from faker import Faker

from hallelujah import User, db

from .test_base import BaseTestCase


class ProxyTestCase(BaseTestCase):
    """proxy testcase"""

    def setUp(self):
        super().setUp()
        self.app.config["PROXY_VERIFY_SSL"] = False
        self.app.config["PROXY_STORAGE"] = tempfile.mkdtemp(prefix="proxy_test_")
        self.fake = Faker()
        self.user = User(name="proxy_user", email=self.fake.email(), password="password")
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        import shutil

        from hallelujah.proxy.views import collection_manager

        if collection_manager is not None and hasattr(collection_manager, "base_dir"):
            shutil.rmtree(collection_manager.base_dir, ignore_errors=True)
        super().tearDown()

    def _login(self, client):
        """login and return client"""
        with client.session_transaction() as sess:
            sess["_user_id"] = str(self.user.id)

    def test_proxy_requires_login(self):
        """test proxy requires login"""
        with self.app.test_client() as client:
            response = client.get("/proxy")
            self.assertIn(response.status_code, [302, 401])

    def test_proxy_page_loads_when_authenticated(self):
        """test proxy page loads when authenticated"""
        with self.app.test_client() as client:
            self._login(client)
            response = client.get("/proxy")
            self.assertEqual(response.status_code, 200)

    def test_proxy_forwards_request(self):
        """test proxy forwards request"""
        with self.app.test_client() as client:
            self._login(client)
            response = client.get("/proxy", query_string={"url": "https://httpbin.org/anything"})
            self.assertEqual(response.status_code, 200)
            self.assertIn("httpbin", response.data.decode("utf-8", errors="replace"))

    def test_proxy_returns_html_content(self):
        """test proxy returns proxied html content"""
        with self.app.test_client() as client:
            self._login(client)
            response = client.get("/proxy", query_string={"url": "https://httpbin.org/html"})
            self.assertEqual(response.status_code, 200)
            content = response.data.decode("utf-8", errors="replace")
            self.assertIn("Moby-Dick", content)

    def test_proxy_rewrites_links(self):
        """test proxy rewrites absolute links"""
        from hallelujah.proxy.pywb_integration import PywbIntegration

        pi = PywbIntegration()
        rewritten = pi.rewrite_html(
            '<a href="https://example.com/page">link</a>',
            "https://example.com/",
        )
        self.assertIn("/proxy?url=", rewritten)

    def test_collection_isolation(self):
        """test collection isolation between users"""
        from hallelujah.proxy.views import collection_manager

        self.assertIsNotNone(collection_manager)
        u1_dir = collection_manager.ensure_user_collection(self.user.id)
        u2_dir = collection_manager.ensure_user_collection(999999)
        self.assertNotEqual(u1_dir, u2_dir)
        self.assertIn(f"user_{self.user.id}", u1_dir)
        self.assertIn("user_999999", u2_dir)
