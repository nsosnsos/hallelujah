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

from . import db, login_manager
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
        return __repr__()

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
    def add_fake_articles(count=1):
        fake = Faker()
        max_length = current_app.config.get('MAX_STR_LEN')
        num_users = User.query.count()
        for i in range(count):
            u = User.query.offset(fake.random_int(0, num_users - 1)).first()
            Article.add_article(user_id=u.id, is_public=fake.pybool(),
                                title=fake.text(max_nb_chars=current_app.config.get('SHORT_STR_LEN')),
                                content=fake.text(max_nb_chars=current_app.config.get('MAX_STR_LEN')))

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
        return __repr__()

    def _generate_uri(self):
        self.uri = 'IMG_' + self.timestamp.strftime('%Y%m%d_%H%M%S')

