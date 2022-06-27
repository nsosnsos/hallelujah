#!/usr/bin/env python3
# -*- coding;utf-8 -*-


import hashlib
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin

from . import db, login_manager
from .config import Config
from .utility import string_to_url, markdown_to_html


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(Config.SHORT_STR_LEN), unique=True, nullable=False, index=True)
    email = db.Column(db.String(Config.SHORT_STR_LEN), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(Config.LONG_STR_LEN), unique=False, nullable=False)
    avatar_hash = db.Column(db.String(Config.SHORT_STR_LEN), unique=False, nullable=False)
    member_since = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.datetime.utcnow)
    articles = db.relationship('Article', backref=__tablename__, lazy='dynamic')
    medias = db.relationship('Media', backref=__tablename__, lazy='dynamic')

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
        db.session.commit()

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    @property
    def articles(self):
        return Article.query.filter(Article.user_id == self.id)

    @property
    def medias(self):
        return Media.query.filter(Media.user_id == self.id)

    @staticmethod
    def add_user(name, email, password):
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return user.id


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
    url = db.Column(db.String(Config.SHORT_STR_LEN), unique=True, nullable=False, index=True)
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

    def _generate_url_html(self):
        self.url = string_to_url(self.title)
        self.content_html = markdown_to_html(self.content)


class Media(db.Model):
    __tablename__ = 'medias'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=False, nullable=False, index=True)
    timestamp = db.Column(db.DateTime, unique=False, nullable=False, index=True, default=datetime.datetime.utcnow)
    uri = db.Column(db.String(Config.SHORT_STR_LEN), unique=True, nullable=False, index=False)
    is_public = db.Column(db.Boolean, unique=False, nullable=False, default=True)
    title = db.Column(db.String(Config.SHORT_STR_LEN), unique=False, nullable=True)

    def __init__(self, **kwargs):
        super(Media, self).__init__(**kwargs)
        self._generate_uri()

    def __repr__(self):
        return '{}: id={}, user_id={}, url={}'.format(self.__class__.__name__, self.id, self.user_id, self.url)

    def __str__(self):
        return __repr__()

    def _generate_uri(self):
        self.uri = 'IMG_' + self.timestamp.strftime('%Y%m%d_%H%M%S')

