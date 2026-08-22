#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import unittest

from hallelujah import create_app, db
from hallelujah.main.forms import ArticleForm, ResourceForm, DirectoryForm
from hallelujah.auth.forms import LoginForm, RegisterForm, SettingForm


class FormTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_article_form_valid(self):
        form = ArticleForm(data={'title': 'Test Title', 'content': 'Test Content', 'is_public': True})
        self.assertTrue(form.validate())

    def test_article_form_missing_title(self):
        form = ArticleForm(data={'content': 'Test Content'})
        self.assertFalse(form.validate())
        self.assertIn('title', form.errors)

    def test_article_form_missing_content(self):
        form = ArticleForm(data={'title': 'Test Title'})
        self.assertFalse(form.validate())
        self.assertIn('content', form.errors)

    def test_resource_form_valid(self):
        form = ResourceForm(data={'uri': 'https://example.com', 'title': 'Test Resource'})
        self.assertTrue(form.validate())

    def test_resource_form_missing_uri(self):
        form = ResourceForm(data={'title': 'Test Resource'})
        self.assertFalse(form.validate())
        self.assertIn('uri', form.errors)

    def test_directory_form_valid(self):
        form = DirectoryForm(data={'directory_name': 'Test Dir'})
        self.assertTrue(form.validate())

    def test_login_form_valid(self):
        form = LoginForm(data={'username': 'test', 'password': 'password', 'remember': False})
        self.assertTrue(form.validate())

    def test_login_form_missing_username(self):
        form = LoginForm(data={'password': 'password'})
        self.assertFalse(form.validate())
        self.assertIn('username', form.errors)

    def test_login_form_missing_password(self):
        form = LoginForm(data={'username': 'test'})
        self.assertFalse(form.validate())
        self.assertIn('password', form.errors)

    def test_register_form_valid(self):
        form = RegisterForm(data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertTrue(form.validate())

    def test_register_form_short_username(self):
        form = RegisterForm(data={
            'username': 'ab',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertFalse(form.validate())

    def test_register_form_invalid_email(self):
        form = RegisterForm(data={
            'username': 'newuser',
            'email': 'invalid',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertFalse(form.validate())

    def test_register_password_mismatch(self):
        form = RegisterForm(data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'different'
        })
        self.assertFalse(form.validate())

    def test_setting_form_valid(self):
        form = SettingForm(data={
            'old_password': 'password123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        })
        self.assertTrue(form.validate())

    def test_setting_form_mismatch(self):
        form = SettingForm(data={
            'old_password': 'password123',
            'new_password': 'newpass1',
            'confirm_password': 'newpass2'
        })
        self.assertFalse(form.validate())

    def test_setting_form_wrong_old(self):
        form = SettingForm(data={
            'old_password': 'wrongpassword',
            'new_password': 'newpass1',
            'confirm_password': 'newpass1'
        })
        self.assertTrue(form.validate())

