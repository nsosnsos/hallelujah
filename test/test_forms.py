#!/usr/bin/env python3
"""test forms"""

from hallelujah.auth.forms import LoginForm, RegisterForm, SettingForm
from hallelujah.main.forms import ArticleForm, DirectoryForm, ResourceForm

from .test_base import BaseTestCase


class FormTestCase(BaseTestCase):
    """form testcase"""

    def test_article_form_valid(self):
        """test article form valid"""
        form = ArticleForm(
            data={
                "title": "Test Title",
                "content": "Test Content",
                "is_public": True,
            }
        )
        self.assertTrue(form.validate())

    def test_article_form_missing_title(self):
        """test article form missing title"""
        form = ArticleForm(data={"content": "Test Content"})
        self.assertFalse(form.validate())
        self.assertIn("title", form.errors)

    def test_article_form_missing_content(self):
        """test article form missing content"""
        form = ArticleForm(data={"title": "Test Title"})
        self.assertFalse(form.validate())
        self.assertIn("content", form.errors)

    def test_resource_form_valid(self):
        """test resource form valid"""
        form = ResourceForm(data={"uri": "https://example.com", "title": "Test Resource"})
        self.assertTrue(form.validate())

    def test_resource_form_missing_uri(self):
        """test resource form missing uri"""
        form = ResourceForm(data={"title": "Test Resource"})
        self.assertFalse(form.validate())
        self.assertIn("uri", form.errors)

    def test_directory_form_valid(self):
        """test directory form valid"""
        form = DirectoryForm(data={"directory_name": "Test Dir"})
        self.assertTrue(form.validate())

    def test_login_form_valid(self):
        """test login form valid"""
        form = LoginForm(
            data={
                "username": "test",
                "password": "password",
                "remember": False,
            }
        )
        self.assertTrue(form.validate())

    def test_login_form_missing_username(self):
        """test login form missing username"""
        form = LoginForm(data={"password": "password"})
        self.assertFalse(form.validate())
        self.assertIn("username", form.errors)

    def test_login_form_missing_password(self):
        """test login form missing password"""
        form = LoginForm(data={"username": "test"})
        self.assertFalse(form.validate())
        self.assertIn("password", form.errors)

    def test_register_form_valid(self):
        """test register form valid"""
        form = RegisterForm(
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "confirm_password": "password123",
            }
        )
        self.assertTrue(form.validate())

    def test_register_form_short_username(self):
        """test register form short username"""
        form = RegisterForm(
            data={
                "username": "ab",
                "email": "test@example.com",
                "password": "password123",
                "confirm_password": "password123",
            }
        )
        self.assertFalse(form.validate())

    def test_register_form_invalid_email(self):
        """test register form invalid email"""
        form = RegisterForm(
            data={
                "username": "newuser",
                "email": "invalid",
                "password": "password123",
                "confirm_password": "password123",
            }
        )
        self.assertFalse(form.validate())

    def test_register_password_mismatch(self):
        """test register password mismatch"""
        form = RegisterForm(
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "confirm_password": "different",
            }
        )
        self.assertFalse(form.validate())

    def test_setting_form_valid(self):
        """test_ setting form valid"""
        form = SettingForm(
            data={
                "old_password": "password123",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123",
            }
        )
        self.assertTrue(form.validate())

    def test_setting_form_mismatch(self):
        """test setting form mismatch"""
        form = SettingForm(
            data={
                "old_password": "password123",
                "new_password": "newpass1",
                "confirm_password": "newpass2",
            }
        )
        self.assertFalse(form.validate())

    def test_setting_form_wrong_old(self):
        """test setting form wrong old"""
        form = SettingForm(
            data={
                "old_password": "wrongpassword",
                "new_password": "newpass1",
                "confirm_password": "newpass1",
            }
        )
        self.assertTrue(form.validate())
