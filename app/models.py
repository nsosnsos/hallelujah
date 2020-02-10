# !/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import hashlib
import datetime
from flask import current_app, url_for
from flask_login import UserMixin, AnonymousUserMixin
from flask_sqlalchemy import BaseQuery
from functools import reduce
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2.filters import do_striptags, do_truncate
from itsdangerous import SignatureExpired, TimedJSONWebSignatureSerializer as Serializer

from . import db, loginMgr, whoosh
from .functions import split_key_words, string_to_url, markdown2html, unused_param
from config import Config


rex_more_tag = re.compile(r'<!--more-->', re.I)


class RoleName:
    GUEST = 'GUEST'
    COMMENT = 'COMMENT'
    DIARY = 'DIARY'
    GALLERY = 'GALLERY'
    BLOG = 'BLOG'
    ADMIN = 'ADMIN'


class Permission:
    GUEST = 0x00
    COMMENT = 0x01
    DIARY = 0x02
    GALLERY = 0x04
    BLOG = 0x08
    ADMIN = 0x10


class Role(db.Model):
    __table_name__ = 'role'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    __mapper_args__ = {'order_by': [id.asc()]}
    name = db.Column(db.String(Config.SHORT_STR_LEN), unique=True, nullable=False)
    permission = db.Column(db.Integer, unique=False, nullable=False)
    users = db.relationship('User', backref=db.backref('role', lazy='joined'), lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permission is None:
            self.permission = 0

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permission += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permission -= perm

    def reset_permission(self):
        self.permission = 0

    def has_permission(self, perm):
        return (self.permission & perm) == perm

    @staticmethod
    def insert_roles():
        roles = {
            RoleName.GUEST:   [Permission.GUEST],
            RoleName.COMMENT: [Permission.COMMENT],
            RoleName.DIARY:   [Permission.COMMENT, Permission.DIARY],
            RoleName.GALLERY: [Permission.COMMENT, Permission.DIARY, Permission.GALLERY],
            RoleName.BLOG:     [Permission.COMMENT, Permission.DIARY, Permission.GALLERY, Permission.BLOG],
            RoleName.ADMIN:   [Permission.COMMENT, Permission.DIARY, Permission.GALLERY, Permission.BLOG,
                               Permission.ADMIN]
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if not role:
                role = Role(name=r)
            role.reset_permission()
            for p in roles[r]:
                role.add_permission(p)
            db.session.add(role)
        db.session.commit()


class Follow(db.Model):
    __table_name__ = 'follow'
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    datetime = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.datetime.utcnow)


class User(UserMixin, db.Model):
    __table_name__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    __mapper_args__ = {'order_by': [id.asc()]}
    name = db.Column(db.String(Config.SHORT_STR_LEN), unique=True, nullable=False)
    email = db.Column(db.String(Config.SHORT_STR_LEN), unique=True, nullable=False)
    description = db.Column(db.Text(), unique=False, nullable=True)
    confirmed = db.Column(db.Boolean, unique=False, nullable=False, default=False)
    password_hash = db.Column(db.String(Config.LONG_STR_LEN), unique=False, nullable=False)
    avatar_hash = db.Column(db.String(Config.SHORT_STR_LEN), unique=False, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), unique=False, nullable=False)
    member_since = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.datetime.utcnow)
    diaries = db.relationship('Diary', backref=db.backref('user', lazy='joined'), lazy='dynamic')
    blogs = db.relationship('Blog', backref=db.backref('user', lazy='joined'), lazy='dynamic')
    galleries = db.relationship('Gallery', backref=db.backref('user', lazy='joined'), lazy='dynamic')
    comments = db.relationship('Comment', backref=db.backref('user', lazy='joined'), lazy='dynamic')
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'), lazy='dynamic',
                               cascade='all, delete-orphan')
    follower = db.relationship('Follow', foreign_keys=[Follow.followed_id],
                               backref=db.backref('followed', lazy='joined'), lazy='dynamic',
                               cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.role:
            if self.email == current_app.config['MAIL_ADMIN']:
                self.role = Role.query.filter_by(name=RoleName.ADMIN).first()
            else:
                self.role = Role.query.filter_by(name=RoleName.DIARY).first()
            self.role_id = self.role.id if self.role else 0
        if not self.avatar_hash:
            self.avatar_hash = self.generate_avatar_hash()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'User: id={}, name={}'.format(self.__class__.__name__, self.id, self.name)

    @staticmethod
    def insert_admin():
        user = User(name=current_app.config['SYS_ADMIN'], email=current_app.config['MAIL_ADMIN'],
                    password=current_app.config['SYS_ADMIN'], description=current_app.config['SYS_ADMIN'])
        db.session.add(user)
        db.session.commit()

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
        db.session.commit()

    def generate_avatar_hash(self):
        return hashlib.md5(self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_password_reset_token(self, expiration=Config.EXPIRATION_TIME):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'password_reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except SignatureExpired:
            return False
        user = User.query.get(data.get('password_reset', None))
        if not user:
            return False
        user.password = new_password
        db.session.add(user)
        db.session.commit()
        return True

    def get_confirm_token(self, expiration=Config.EXPIRATION_TIME):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except SignatureExpired:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def get_email_change_token(self, new_email, expiration=Config.EXPIRATION_TIME):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'email_change': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.decode('utf-8'))
        except SignatureExpired:
            return False
        if data.get('email_change') != self.id:
            return False

        new_email = data.get('new_email', None)
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.generate_avatar_hash()
        db.session.add(self)
        return True

    def can(self, perm):
        return self.role and self.role.has_permission(perm)

    def is_admin(self):
        return self.can(Permission.ADMIN)

    def update_last_seen(self):
        self.last_seen = datetime.datetime.utcnow()
        db.session.add(self)

    def get_gravatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        avatar_hash = self.avatar_hash or self.generate_avatar_hash()
        return '{url}/{avatar_hash}?s={size}&d={default}&r={rating}'.format(
            url=url, avatar_hash=avatar_hash, size=size, default=default, rating=rating)

    def is_following(self, user):
        if not user.id:
            return False
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        if not user.id:
            return False
        return self.follower.filter_by(follower_id=user.id).first() is not None

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower_id=self.id, followed_id=user.id)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user).first()
        if f:
            db.session.add(f)

    @property
    def self_diary(self):
        return Diary.query.filter(Diary.user_id == self.id)

    @property
    def self_gallery(self):
        return Gallery.query.filter(Gallery.user_id == self.id)

    @property
    def self_blog(self):
        return Blog.query.filter(Blog.user_id == self.id)

    @property
    def followed_diary(self):
        return Diary.query.join(Follow, Follow.followed_id == Diary.user_id).filter(
            (not Diary.is_private) and Follow.follower_id == self.id)

    @property
    def followed_gallery(self):
        return Gallery.query.join(Follow, Follow.followed_id == Gallery.user_id).filter(
            (not Gallery.is_private) and Follow.follower_id == self.id)

    @property
    def followed_blog(self):
        return Blog.query.join(Follow, Follow.followed_id == Blog.user_id).filter(
            (not Blog.is_private) and Follow.follower_id == self.id)


class AnonymousUser(AnonymousUserMixin):
    def can(self, perm):
        if perm:
            return False
        else:
            return self.is_authenticated()

    def is_admin(self):
        return self.is_authenticated()


loginMgr.anonymous_user = AnonymousUser


@loginMgr.user_loader
def load_user(uid):
    return User.query.get(int(uid))


blog_tag_ref = db.Table(
    'blog_tag_ref',
    db.Column('blog_id', db.Integer, db.ForeignKey('blog.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id', ondelete='CASCADE'), primary_key=True))


class TagQuery(BaseQuery):
    def search(self, key_word):
        key_word = '%{}%'.format(key_word.strip())
        return self.filter(Tag.name.ilike(key_word))


class Tag(db.Model):
    __table_name__ = 'tag'
    query_class = TagQuery
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(Config.SHORT_STR_LEN), unique=True, nullable=False, index=True)
    __mapper_args__ = {'order_by': [id.asc()]}

    @property
    def link(self):
        return url_for('main.tag', name=self.name.lower(), _external=True)

    @property
    def count(self):
        return Blog.query.public().filter(Blog.tags.any(id=self.id)).count()


class BlogQuery(BaseQuery):
    def public(self):
        return self.filter_by(is_private=False)

    def search(self, kws):
        query_list = []
        for kw in split_key_words(kws):
            kw_wild_cast = '%{}%'.format(kw)
            query_list.append(db.or_(Blog.title.ilike(kw_wild_cast)))
            query_list.append(db.or_(Blog.content.ilike(kw_wild_cast)))
        q = reduce(db.or_, query_list)
        return self.public().filter(q)

    def archive(self, year, month=None, day=None):
        cond_list = [db.extract('year', Blog.create_datetime) == year]
        if month is not None:
            cond_list.append(db.extract('month', Blog.create_datetime) == month)
        if day is not None:
            cond_list.append(db.extract('day', Blog.create_datetime) == day)

        q = reduce(db.and_, cond_list)
        return self.public().filter(q)


class Category(db.Model):
    __table_name__ = 'category'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    __mapper_args__ = {'order_by': [id.asc()]}
    name = db.Column(db.String(Config.SHORT_STR_LEN), unique=True, nullable=False)
    blogs = db.relationship('Blog', backref=db.backref('category', lazy='joined'), lazy='dynamic')

    def __init__(self, **kwargs):
        super(Category, self).__init__(**kwargs)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    @staticmethod
    def insert_categories():
        categories = ['ALGORITHM', 'CODE', 'TOOL', 'LIFE']
        for c in categories:
            if not Category.query.filter_by(name=c).first():
                category = Category(name=c)
                db.session.add(category)
                db.session.commit()


@whoosh.register_model('title', 'content')
class Blog(db.Model):
    __table_name__ = 'blog'
    query_class = BlogQuery
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    __mapper_args__ = {'order_by': [id.asc()]}
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=False, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), unique=False, nullable=False)
    is_private = db.Column(db.Boolean, unique=False, nullable=False, default=False)
    create_datetime = db.Column(db.DateTime, unique=False, nullable=False, index=True, default=datetime.datetime.utcnow)
    modify_datetime = db.Column(db.DateTime, unique=False, nullable=False, index=True, default=datetime.datetime.utcnow)
    title = db.Column(db.String(Config.SHORT_STR_LEN), unique=False, nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    content_html = db.Column(db.Text, unique=False, nullable=True)
    summary = db.Column(db.String(Config.LONG_STR_LEN), unique=False, nullable=True)
    tags = db.relationship(Tag, secondary=blog_tag_ref, backref=db.backref('blogs', lazy=True), lazy='subquery')
    comments = db.relationship('Comment', backref=db.backref('blog', lazy='joined'), lazy='dynamic')

    def generate_html(self, value):
        self.content_html = markdown2html(value)
        if not self.summary or not len(self.summary.strip()):
            rex_more_tag_match = rex_more_tag.search(value)
            if rex_more_tag_match:
                self.summary = markdown2html(value[:rex_more_tag_match.start()])
            else:
                self.summary = do_truncate(do_striptags(self.content_html), length=Config.LONG_STR_LEN)

    @property
    def has_more(self):
        return rex_more_tag.search(self.content)

    @property
    def link(self):
        return url_for('main.blog', name=string_to_url(self.title), _external=True)

    @property
    def next(self):
        _query = db.and_(Blog.id > self.id,)
        return self.query.public().filter(_query).order_by(Blog.id.asc()).first

    @property
    def prev(self):
        _query = db.and_(Blog.id < self.id,)
        return self.query.public().filter(_query).order_by(Blog.id.desc()).first

    @property
    def year(self):
        return self.create_datetime.year

    @property
    def month(self):
        return self.create_datetime.month

    @property
    def day(self):
        return self.create_datetime.day

    @staticmethod
    def before_insert(mapper, connection, target):
        unused_param(mapper, connection)
        value = target.content
        target.generate_html(value)

    @staticmethod
    def on_change_content(target, value, oldvalue, initiator):
        unused_param(oldvalue, initiator)
        target.generate_html(value)


class Gallery(db.Model):
    __table_name__ = 'gallery'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    __mapper_args__ = {'order_by': [id.asc()]}
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=False, nullable=False)
    is_private = db.Column(db.Boolean, unique=False, nullable=False, default=True)
    datetime = db.Column(db.DateTime, unique=False, nullable=False, index=True, default=datetime.datetime.utcnow)
    content = db.Column(db.String(Config.LONG_STR_LEN), unique=False, nullable=False)

    @property
    def link(self):
        return url_for('main.gallery', id=self.id, _external=True)


@whoosh.register_model('content')
class Diary(db.Model):
    __table_name__ = 'diary'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    __mapper_args__ = {'order_by': [id.asc()]}
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=False, nullable=False)
    is_private = db.Column(db.Boolean, unique=False, nullable=False, default=True)
    datetime = db.Column(db.DateTime, unique=False, nullable=False, index=True, default=datetime.datetime.utcnow)
    content = db.Column(db.String(Config.LONG_STR_LEN), unique=False, nullable=False)

    @property
    def link(self):
        return url_for('main.diary', id=self.id, _external=True)


@whoosh.register_model('content')
class Comment(db.Model):
    __table_name__ = 'comment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=False, nullable=False)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), unique=False, nullable=False)
    content = db.Column(db.String(Config.LONG_STR_LEN), unique=False, nullable=False)
    datetime = db.Column(db.DateTime, unique=False, nullable=False, index=True, default=datetime.datetime.utcnow)
    reply_to = db.Column(db.Integer, unique=False, nullable=True)


db.event.listen(Blog, 'before_insert', Blog.before_insert)
db.event.listen(Blog.content, 'set', Blog.on_change_content)
