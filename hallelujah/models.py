#!/usr/bin/env python3
# -*- coding;utf-8 -*-


import uuid
import hashlib
import datetime
from faker import Faker
from sqlalchemy import exc
from flask import current_app, url_for
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2.filters import do_striptags, do_truncate

from .extensions import db, login_manager
from .utility import markdown_to_html
from .config import Config


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(Config.SHORT_STR_LEN), unique=True, nullable=False, index=True)
    email = db.Column(db.String(Config.SHORT_STR_LEN), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(Config.LONG_STR_LEN), unique=False, nullable=False)
    avatar_hash = db.Column(db.String(Config.SHORT_STR_LEN), unique=False, nullable=False)
    member_since = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.datetime.utcnow)
    articles = db.relationship('Article', backref='author', lazy='dynamic')
    medias = db.relationship('Media', backref='author', lazy='dynamic')
    resources = db.relationship('Resource', backref='author', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.email = self.email.lower()
        self.avatar_hash = self._generate_avatar_hash()

    def __repr__(self):
        return '{}: id={}, name={}, email={}'.format(self.__class__.__name__, self.id, self.name, self.email)

    def __str__(self):
        return self.__repr__()

    def _generate_avatar_hash(self):
        return hashlib.md5(self.email.encode('utf-8')).hexdigest()

    def get_gravatar_icon(self, size=100, default='identicon', rating='g'):
        url = 'https://www.gravatar.com/avatar'
        avatar_hash = self.avatar_hash or self._generate_avatar_hash()
        return '{url}/{avatar_hash}?s={size}&d={default}&r={rating}'.format(
            url=url, avatar_hash=avatar_hash, size=size, default=default, rating=rating)

    def update_last_seen(self):
        self.last_seen = datetime.datetime.utcnow()
        db.session.add(self)
        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            Config.LOGGER.error('update_last_seen: {}'.format(str(e)))

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def to_json(self):
        json_user = {
            'name': self.name,
            'email': self.email,
            'member_since': self.member_since,
            'last_seen': self.last_seen
        }
        return json_user

    @staticmethod
    def add_user(name, email, password):
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            Config.LOGGER.error('add_user: {}'.format(str(e)))
            return None
        return user

    @staticmethod
    def add_fake_users(count=1):
        fake = Faker()
        for i in range(count):
            User.add_user(fake.user_name(), fake.email(), 'password')


class AnonymousUser(AnonymousUserMixin):
    def __init__(self, **kwargs):
        super(AnonymousUser, self).__init__(**kwargs)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=False, nullable=False, index=True)
    timestamp = db.Column(db.DateTime, unique=False, nullable=False, index=True, default=datetime.datetime.utcnow)
    url = db.Column(db.String(Config.MAX_STR_LEN), unique=True, nullable=False, index=True)
    is_public = db.Column(db.Boolean, unique=False, nullable=False, default=True)
    title = db.Column(db.String(Config.SHORT_STR_LEN), unique=False, nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    content_html = db.Column(db.Text, unique=False, nullable=False)

    def __init__(self, **kwargs):
        super(Article, self).__init__(**kwargs)
        self._generate_url_html()

    def __repr__(self):
        return '{}: id={}, user_id={}, url={}'.format(self.__class__.__name__, self.id, self.user_id, self.url)

    def __str__(self):
        return self.__repr__()

    def _generate_url(self):
        while True:
            url = uuid.uuid4().hex
            if not Article.query.filter(Article.url == url).first():
                return url

    def _generate_url_html(self):
        self.url = self._generate_url()
        self.content_html = markdown_to_html(self.content)

    def to_json(self):
        json_article = {
            'author': self.author.name,
            'author_url': url_for('main.user', user_name=self.author.name, _external=True),
            'title': self.title,
            'truncated_content': do_truncate(current_app.jinja_env, do_striptags(self.content_html)),
            'timestamp': self.timestamp,
            'url': url_for('main.article', article_url=self.url, _external=True),
        }
        return json_article

    @staticmethod
    def add_article(user_id, is_public, title, content):
        article = Article(user_id=user_id, is_public=is_public, title=title, content=content)
        db.session.add(article)
        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            Config.LOGGER.error('add_article: {}'.format(str(e)))
            return None
        return article

    @staticmethod
    def edit_article(article_id, is_public, title, content):
        article = Article.query.filter(Article.id==article_id).first()
        if not article:
            return None
        article.is_public = is_public
        article.title = title
        article.content = content
        article.content_html = markdown_to_html(content)
        db.session.add(article)
        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            Config.LOGGER.error('add_article: {}'.format(str(e)))
            return None
        return article

    @staticmethod
    def delete_article(article_id):
        article = Article.query.filter(Article.id==article_id).first()
        if not article:
            return False
        db.session.delete(article)
        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            Config.LOGGER.error('add_article: {}'.format(str(e)))
            return False
        return True

    @staticmethod
    def add_fake_articles(count=1):
        fake = Faker()
        max_length = current_app.config.get('MAX_STR_LEN')
        num_users = User.query.count()
        for i in range(num_users):
            u = User.query.offset(fake.random_int(0, num_users - 1)).first()
            for j in range(count):
                Article.add_article(u.id, fake.pybool(),
                                    fake.text(max_nb_chars=current_app.config.get('SHORT_STR_LEN')),
                                    fake.text(max_nb_chars=current_app.config.get('MAX_STR_LEN')))


class Media(db.Model):
    __tablename__ = 'medias'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=False, nullable=False, index=True)
    timestamp = db.Column(db.DateTime, unique=False, nullable=False, index=True, default=datetime.datetime.utcnow)
    uri = db.Column(db.String(Config.MAX_STR_LEN), unique=True, nullable=False, index=False)
    is_public = db.Column(db.Boolean, unique=False, nullable=False, default=True)
    title = db.Column(db.String(Config.SHORT_STR_LEN), unique=False, nullable=True)

    def __init__(self, **kwargs):
        super(Media, self).__init__(**kwargs)
        self._generate_uri()

    def __repr__(self):
        return '{}: id={}, user_id={}, uri={}'.format(self.__class__.__name__, self.id, self.user_id, self.uri)

    def __str__(self):
        return self.__repr__()

    def _generate_uri(self):
        self.uri = 'IMG_' + self.timestamp.strftime('%Y%m%d_%H%M%S')

    def to_json(self):
        json_media = {
            'author': self.author.name,
            'timestamp': self.timestamp,
            'rui': self.uri,
            'is_public': self.is_public,
            'title': self.title,
        }
        return json_media

    @staticmethod
    def add_media(user_id, uri, is_public=True, title=None):
        media = Media(user_id=user_id, uri=uri, is_public=is_public, title=title)
        db.session.add(media)
        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            Config.LOGGER.error('add_media: {}'.format(str(e)))
            return None
        return media

    @staticmethod
    def delete_media(media_uri):
        media = Media.query.filter(Media.uri==media_uri).first()
        if not media:
            return False
        db.session.delete(media)
        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            Config.LOGGER.error('delete_media: {}'.format(str(e)))
            return False
        return True


class Resource(db.Model):
    __tablename__ = 'resources'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=False, nullable=False, index=True)
    uri = db.Column(db.String(Config.MAX_STR_LEN), unique=False, nullable=False, index=False)
    rank = db.Column(db.Integer, unique=False, nullable=False, index=False, default=Config.MAX_STR_LEN)
    category = db.Column(db.String(Config.SHORT_STR_LEN), unique=False, nullable=False, index=False, default='default')
    title = db.Column(db.String(Config.SHORT_STR_LEN), unique=False, nullable=True, index=False, default='')

    def __init__(self, **kwargs):
        super(Resource, self).__init__(**kwargs)
        self._uri_adaption()

    def _uri_adaption(self):
        if not self.uri.startswith('http://') or not self.uri.startswith('https://'):
            self.uri = 'https://' + self.uri

    def __repr__(self):
        return '{}: id={}, user_id={}, uri={}'.format(self.__class__.__name__, self.id, self.user_id, self.uri)

    def __str__(self):
        return self.__repr__()

    def to_json(self):
        json_resource = {
            'id': self.id,
            'uri': self.uri,
            'rank': self.rank,
            'category': self.category,
            'title': self.title,
        }
        return json_resource

    @staticmethod
    def add_resource(user_id, uri, rank=None, title=None, category=None):
        resource = Resource(user_id=user_id, uri=uri, rank=rank, title=title, category=category)
        db.session.add(resource)
        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            Config.LOGGER.error('add_resource: {}'.format(str(e)))
            return None
        return resource

    @staticmethod
    def modify_resource(json_data, current_user):
        resource = Resource.query.get(json_data.get('id', -1))
        if not resource or resource.user_id != current_user.id:
            return False
        columns = [column.key for column in Resource.__table__.columns]
        for col in columns:
            if col in json_data:
                setattr(resource, col, json_data[col])
        resource._uri_adaption()
        db.session.add(resource)
        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            Config.LOGGER.error('modify_resource: {}'.format(str(e)))
            return False
        return True

    @staticmethod
    def delete_resource(resource_uri):
        resource = Resource.query.filter(Resource.uri==resource_uri).first()
        if not resource:
            return False
        db.session.delete(resource)
        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            Config.LOGGER.error('delete_resource: {}'.format(str(e)))
            return False
        return True

    @staticmethod
    def add_fake_resources(count=1):
        fake = Faker()
        max_length = current_app.config.get('MAX_STR_LEN')
        num_users = User.query.count()
        for i in range(num_users):
            u = User.query.offset(i).first()
            for j in range(count):
                Resource.add_resource(u.id, fake.url(), fake.random_int(0, u.id),
                                      fake.text(max_nb_chars=current_app.config.get('SHORT_STR_LEN')),
                                      u.name if j % 2 == 0 else u.name[::-1])

