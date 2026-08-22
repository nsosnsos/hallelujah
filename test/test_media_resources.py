#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import datetime
import unittest

from hallelujah import create_app, db
from hallelujah.models import User, Article, Media, Resource


class MediaTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        u = User(name='testuser', email='test@example.com', password='password123')
        db.session.add(u)
        db.session.commit()
        m = Media(user_id=u.id, path='/path', filename='test.jpg', timestamp=datetime.datetime.now(datetime.timezone.utc))
        db.session.add(m)
        db.session.commit()
        self.media = m

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_media_create_default(self):
        m = Media.query.filter(Media.user_id == self.media.user_id).first()
        self.assertIsNotNone(m.timestamp)

    def test_media_to_json_has_required_fields(self):
        with self.app.test_request_context('/'):
            m = Media.query.filter(Media.user_id == self.media.user_id).first()
            m.width = 100
            m.height = 100
            m.uuidname = 'testuuid123'
            json_data = m.to_json()
            self.assertIn('view_url', json_data)
            self.assertIn('download_url', json_data)
            self.assertIn('uuidname', json_data)
            self.assertIn('author', json_data)
            self.assertIn('thumbnail_url', json_data)


class ResourceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        u = User(name='testuser', email='test@example.com', password='password123')
        db.session.add(u)
        db.session.commit()
        r = Resource(user_id=u.id, uri='https://example.com/res', title='Test', category='cat')
        db.session.add(r)
        db.session.commit()
        self.resource = r

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_resource_uri_starts_with_http(self):
        r = Resource.query.filter(Resource.user_id == self.resource.user_id).first()
        self.assertTrue(r.uri.startswith('https://'))

    def test_resource_uri_auto_prepends_http(self):
        r = Resource(user_id=self.resource.user_id, uri='example.com/resource')
        self.assertTrue(r.uri.startswith('https://'))

    def test_resource_to_json(self):
        with self.app.test_request_context('/'):
            r = Resource.query.filter(Resource.user_id == self.resource.user_id).first()
            json_data = r.to_json()
            self.assertIn('id', json_data)
            self.assertIn('uri', json_data)
            self.assertIn('rank', json_data)
            self.assertIn('category', json_data)
            self.assertIn('title', json_data)
            self.assertIn('delete_uri', json_data)


class ArticleTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        u = User(name='testuser', email='test@example.com', password='password123')
        db.session.add(u)
        db.session.commit()
        a = Article(user_id=u.id, title='Test Article', content='# Head\n1. first\n2. second\n')
        db.session.add(a)
        db.session.commit()
        self.article = a

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_article_generates_url(self):
        a = Article.query.filter(Article.user_id == self.article.user_id).first()
        self.assertIsNotNone(a.url)
        self.assertEqual(len(a.url), 32)

    def test_article_content_html_generated(self):
        a = Article.query.filter(Article.user_id == self.article.user_id).first()
        self.assertIn('<h1>Head</h1>', a.content_html)
        self.assertIn('<ol>', a.content_html)
        self.assertIn('<li>first</li>', a.content_html)
        self.assertIn('<li>second</li>', a.content_html)

    def test_article_is_public_default_true(self):
        a = Article.query.filter(Article.user_id == self.article.user_id).first()
        self.assertTrue(a.is_public)

    def test_article_url_unique(self):
        # Create two articles with different content
        a1 = Article(user_id=self.article.user_id, title='First Article', content='Content #1\n')
        a2 = Article(user_id=self.article.user_id, title='Second Article', content='Content #2\n')
        db.session.add(a1)
        db.session.add(a2)
        db.session.commit()
        self.assertIsNotNone(a1.url)
        self.assertIsNotNone(a2.url)
        self.assertNotEqual(a1.url, a2.url)

