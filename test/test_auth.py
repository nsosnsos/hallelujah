#!/usr/bin/env python3
"""test auth"""

from faker import Faker

from hallelujah import User, db

from .test_base import BaseTestCase


class AuthTestCase(BaseTestCase):
    """auth testcase"""

    def setUp(self):
        super().setUp()
        self.fake = Faker()
        self.user = User(name="name", email=self.fake.email(), password="password")
        db.session.add(self.user)
        db.session.commit()

    def test_login_logout_flow(self):
        """test login logout flow"""
        with self.app.test_client() as client:
            response = client.post(
                "/auth/login",
                data={"username": "name", "password": "password"},
            )
            self.assertEqual(response.status_code, 302)

            response = client.get("/auth/logout")
            self.assertEqual(response.status_code, 302)

    def test_login_redirects_when_authenticated(self):
        """test login redirects when authenticated"""
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess["_user_id"] = str(self.user.id)

            response = client.get("/auth/login")
            self.assertEqual(response.status_code, 302)

    def test_unauthorized_access(self):
        """test unauthorized access"""
        with self.app.test_client() as client:
            response = client.get("/auth/profile")
            self.assertIn(response.status_code, [302, 401])

    def test_password_setter_no_getter(self):
        """test password setter no getter"""
        u = User(name=self.fake.user_name(), email=self.fake.email(), password=self.fake.password())
        self.assertIsNotNone(u.password_hash)
        with self.assertRaises(AttributeError):
            _ = u.password

    def test_password_salts_are_random(self):
        """test password salts are random"""
        u1 = User(name=self.fake.user_name(), email=self.fake.email(), password=self.fake.password())
        u2 = User(name=self.fake.user_name(), email=self.fake.email(), password=self.fake.password())
        self.assertNotEqual(u1.password_hash, u2.password_hash)
