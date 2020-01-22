# !/usr/bin/env python
# -*- coding:utf-8 -*-

import unittest

from app import create_app, db
from app.models import Role, User, AnonymousUser, Permission


class TestModel(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user(self):
        u = User(name='test', email='test@gmail.com', password='test')
        self.assertTrue(u.can(Permission.DIARY))
        self.assertFalse(u.can(Permission.GALLERY))

    def test_anonymous(self):
        u = AnonymousUser()
        self.assertTrue(u.can(Permission.ARTICLE))
