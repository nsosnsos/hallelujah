#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import time
import datetime
import unittest

from hallelujah import create_app, db, User


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.user = User(
            name="testuser", email="test@example.com", password="password123"
        )
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login_logout_flow(self):
        with self.app.test_client() as client:
            response = client.post(
                "/auth/login",
                data={"username": "testuser", "password": "password123"},
            )
            self.assertEqual(response.status_code, 302)

            response = client.get("/auth/logout")
            self.assertEqual(response.status_code, 302)

    def test_login_redirects_when_authenticated(self):
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess["_user_id"] = str(self.user.id)

            response = client.get("/auth/login")
            self.assertEqual(response.status_code, 302)

    def test_unauthorized_access(self):
        with self.app.test_client() as client:
            response = client.get("/auth/profile")
            self.assertIn(response.status_code, [302, 401])

    def test_password_setter_no_getter(self):
        u = User(name="test", email="test@test.com", password="pwd")
        self.assertIsNotNone(u.password_hash)
        with self.assertRaises(AttributeError):
            u.password

    def test_password_salts_are_random(self):
        u1 = User(name="user1", email="user1@test.com", password="pwd1")
        u2 = User(name="user2", email="user2@test.com", password="pwd2")
        self.assertNotEqual(u1.password_hash, u2.password_hash)

    def test_timestamp_auto_set(self):
        u = User(name="test", email="test@test.com", password="pwd")
        db.session.add(u)
        db.session.commit()
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        self.assertAlmostEqual(
            (now - u.member_since).total_seconds(), 0, delta=5
        )
        self.assertAlmostEqual((now - u.last_seen).total_seconds(), 0, delta=5)

    def test_last_seen_updates(self):
        u = User(name="test", email="test@test.com", password="pwd")
        db.session.add(u)
        db.session.commit()
        time.sleep(1)
        old_last_seen = u.last_seen
        u.update_last_seen()
        db.session.commit()
        self.assertGreater(u.last_seen, old_last_seen)

    def test_gravatar_url(self):
        u = User(name="test", email="test@test.com", password="pwd")
        with self.app.test_request_context("/"):
            gravatar = u.get_gravatar_icon()
            gravatar_256 = u.get_gravatar_icon(size=256)
            gravatar_pg = u.get_gravatar_icon(rating="pg")
            gravatar_retro = u.get_gravatar_icon(default="retro")
        self.assertTrue(
            "https://www.gravatar.com/avatar/b642b4217b34b1e8d3bd915fc65c4452"
            in gravatar
        )
        self.assertTrue("s=256" in gravatar_256)
        self.assertTrue("r=pg" in gravatar_pg)
        self.assertTrue("d=retro" in gravatar_retro)
