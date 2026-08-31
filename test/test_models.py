#!/usr/bin/env python3
"""test models"""

import datetime
import time
import unittest
import uuid

from faker import Faker

from hallelujah import Article, Media, Resource, User, db

from .test_base import BaseTestCase


class UserModelTestCase(BaseTestCase):
    """user model testcase"""

    def setUp(self):
        super().setUp()
        self.fake = Faker()

    def test_password_setter(self):
        """test password setter"""
        u = User(name=self.fake.user_name(), email=self.fake.email(), password=self.fake.password())
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        """test no password getter"""
        u = User(name=self.fake.user_name(), email=self.fake.email(), password=self.fake.password())
        with self.assertRaises(AttributeError):
            _ = u.password

    def test_password_salts_are_random(self):
        """test assword salts are random"""
        u1 = User(
            name=self.fake.user_name(),
            email=self.fake.email(),
            password="pwd",
        )
        u2 = User(
            name=self.fake.user_name(),
            email=self.fake.email(),
            password="pwd",
        )
        self.assertTrue(u1.password_hash != u2.password_hash)

    def test_timestamp_auto_set(self):
        """test timestamp auto set"""
        u = User(name=self.fake.user_name(), email=self.fake.email(), password=self.fake.password())
        db.session.add(u)
        db.session.commit()
        current_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        self.assertTrue((current_time - u.member_since).total_seconds() < 10)
        self.assertTrue((current_time - u.last_seen).total_seconds() < 10)

    def test_last_seen(self):
        """test last seen"""
        u = User(name=self.fake.user_name(), email=self.fake.email(), password=self.fake.password())
        db.session.add(u)
        db.session.commit()
        old_last_seen = u.last_seen
        time.sleep(1)
        u.update_last_seen()
        self.assertTrue(u.last_seen > old_last_seen)

    def test_gravatar(self):
        """test gravatar"""
        u = User(name=self.fake.user_name(), email="test@test.com", password=self.fake.password())
        with self.app.test_request_context("/"):
            gravatar = u.get_gravatar_icon()
            gravatar_256 = u.get_gravatar_icon(size=256)
            gravatar_pg = u.get_gravatar_icon(rating="pg")
            gravatar_retro = u.get_gravatar_icon(default="retro")
        self.assertTrue("https://www.gravatar.com/avatar/b642b4217b34b1e8d3bd915fc65c4452" in gravatar)
        self.assertTrue("s=256" in gravatar_256)
        self.assertTrue("r=pg" in gravatar_pg)
        self.assertTrue("d=retro" in gravatar_retro)


class ArticleModelTestCase(BaseTestCase):
    """article model testcase"""

    def test_url_html(self):
        """test url html"""
        a = Article(title="test", content="#Head\n1. first\n2. second\n3. third\n")
        self.assertIsNotNone(a.url)

        try:
            uuid.UUID(a.url)
        except ValueError:
            self.fail(f"a.url '{a.url}' is not a valid UUID")

        expected_html = "<h1>Head</h1>\n<ol>\n<li>first</li>\n<li>second</li>\n<li>third</li>\n</ol>"
        self.assertEqual(a.content_html, expected_html)


class MediaModelTestCase(BaseTestCase):
    """media model testcase"""

    def test_valid_media(self):
        """test valid media"""
        m = Media(user_id=-1, path="", filename="")
        self.assertTrue(m.timestamp is None)
        self.assertTrue(m.uuidname is not None)


class ResourceModelTestCase(unittest.TestCase):
    """resource model testcase"""

    def setUp(self):
        super().setUp()
        self.fake = Faker()

    def test_uri(self):
        """test uri"""
        a = Resource(uri=self.fake.url())
        self.assertTrue(a.uri.startswith("http"))
