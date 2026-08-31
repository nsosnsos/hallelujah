#!/usr/bin/env python3
"""base test case"""

import unittest

from hallelujah import create_app, db


class BaseTestCase(unittest.TestCase):
    """base testcase"""

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
