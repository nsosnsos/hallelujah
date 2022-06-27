#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import unittest
from flask import current_app

from hallelujah import create_app, db


class BasicTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertTrue(self.app is not None)

    def test_app_test_mode(self):
        self.assertTrue(self.app.config.get('TESTING', True))

