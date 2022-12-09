#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import uuid
import time
import datetime
import unittest
from faker import Faker

from hallelujah import create_app, db, User, Article, Media, Resource


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.fake = Faker()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(name=self.fake.user_name(), email=self.fake.email(), password='pwd')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(name=self.fake.user_name(), email=self.fake.email(), password='pwd')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_salts_are_random(self):
        u1 = User(name=self.fake.user_name(), email=self.fake.email(), password='pwd1')
        u2 = User(name=self.fake.user_name(), email=self.fake.email(), password='pwd2')
        self.assertTrue(u1.password_hash != u2.password_hash)

    def test_timestamp(self):
        u = User(name=self.fake.user_name(), email=self.fake.email(), password='pwd')
        db.session.add(u)
        db.session.commit()
        self.assertTrue((datetime.datetime.utcnow() - u.member_since).total_seconds() < 10)
        self.assertTrue((datetime.datetime.utcnow() - u.last_seen).total_seconds() < 10)

    def test_last_seen(self):
        u = User(name=self.fake.user_name(), email=self.fake.email(), password='pwd')
        db.session.add(u)
        db.session.commit()
        time.sleep(1)
        old_last_seen = u.last_seen
        u.update_last_seen()
        self.assertTrue(u.last_seen > old_last_seen)

    def test_gravatar(self):
        u = User(name=self.fake.user_name(), email='test@test.com', password='pwd')
        with self.app.test_request_context('/'):
            gravatar = u.get_gravatar_icon()
            gravatar_256 = u.get_gravatar_icon(size=256)
            gravatar_pg = u.get_gravatar_icon(rating='pg')
            gravatar_retro = u.get_gravatar_icon(default='retro')
        self.assertTrue('https://www.gravatar.com/avatar/' + 
                        'b642b4217b34b1e8d3bd915fc65c4452' in gravatar)
        self.assertTrue('s=256' in gravatar_256)
        self.assertTrue('r=pg' in gravatar_pg)
        self.assertTrue('d=retro' in gravatar_retro)

class ArticleModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_url_html(self):
        a = Article(title='asd /sd\s\tdf\\sdf', content='#Head\n1. first\n2. second\n3. third\n')
        try:
            u = uuid.UUID(a.url)
        except ValueError:
            u = None
        self.assertIsNotNone(a.url)
        self.assertTrue(a.content_html == '<h1>Head</h1>\n<ol>\n<li>first</li>\n<li>second</li>\n<li>third</li>\n</ol>')

class MediaModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_valid_media(self):
        m = Media(user_id=-1, path="", filename="")
        self.assertTrue(m.timestamp == None)
        self.assertTrue(m.uuidname != None)

class ResourceModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.fake = Faker()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_uri(self):
        a = Resource(uri=self.fake.url())
        self.assertTrue(a.uri.startswith('http'))

