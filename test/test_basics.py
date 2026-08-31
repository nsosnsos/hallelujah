#!/usr/bin/env python3
"""test basics"""

from .test_base import BaseTestCase


class BasicTestCase(BaseTestCase):
    """basic testcase"""

    def test_app_exists(self):
        """test app exists"""
        self.assertTrue(self.app is not None)

    def test_app_test_mode(self):
        """test app test mode"""
        self.assertTrue(self.app.config.get("TESTING", True))
