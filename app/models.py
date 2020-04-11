# !/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import hashlib
import datetime
from functools import reduce
from flask import current_app, url_for
from flask_login import UserMixin, AnonymousUserMixin
from flask_sqlalchemy import BaseQuery
from wtforms import ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2.filters import do_striptags
from itsdangerous import SignatureExpired, TimedJSONWebSignatureSerializer as Serializer

from config import Config
from . import db, loginMgr, whoosh
from .utilities import Permission, split_key_words, markdown2html, unused_param


class RoleName:
    GUEST = 'GUEST'
    COMMENT = 'COMMENT'
    DIARY = 'DIARY'
    GALLERY = 'GALLERY'
    BLOG = 'BLOG'
    ADMIN = 'ADMIN'


class Role(db.Model):
    __table_name__ = 'role'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    __mapper_args__ = {'order_by': [id.asc()]}
    name = db.Column(db.String(Config.SHORT_STR_LEN), unique=True, nullable=False)
    permission = db.Column(db.Integer, unique=False, nullable=False)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permission is None:
            self.permission = 0

    def __repr__(self):
        return '{}: id={}, name={}'.format(self.__class__.__name__, self.id, self.name)

    def __str__(self):
        return self.__repr__()

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
            RoleName.BLOG:    [Permission.COMMENT, Permission.DIARY, Permission.GALLERY, Permission.BLOG],
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
    name = db.Column(db.String(Config.SHORT_STR_LEN), unique=True, nullable=False, index=True)
    email = db.Column(db.String(Config.SHORT_STR_LEN), unique=True, nullable=False, index=True)
    description = db.Column(db.Text(), unique=False, nullable=True)
    confirmed = db.Column(db.Boolean, unique=False, nullable=False, default=False)
    password_hash = db.Column(db.String(Config.LONG_STR_LEN), unique=False, nullable=False)
    avatar_hash = db.Column(db.String(Config.SHORT_STR_LEN), unique=False, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), unique=False, nullable=False)
    member_since = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.datetime.utcnow)
    categories = db.relationship('Category', backref='user', lazy='dynamic')
    blogs = db.relationship('Blog', backref='user', lazy='dynamic')
    galleries = db.relationship('Gallery', backref='user', lazy='dynamic')
    diaries = db.relationship('Diary', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    tags = db.relationship('Tag', backref='user', lazy='dynamic')
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'), lazy='dynamic',
                               cascade='all, delete-orphan')
    follower = db.relationship('Follow', foreign_keys=[Follow.followed_id],
                               backref=db.backref('followed', lazy='joined'), lazy='dynamic',
                               cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.role:
            if self.email == current_app.config['MAIL_USERNAME']:
                self.role = Role.query.filter_by(name=RoleName.ADMIN).first()
            else:
                self.role = Role.query.filter_by(name=RoleName.DIARY).first()
            self.role_id = self.role.id if self.role else 0
        if not self.avatar_hash:
            self.avatar_hash = self.generate_avatar_hash()

    def __repr__(self):
        return '{}: id={}, name={}'.format(self.__class__.__name__, self.id, self.name)

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def insert_admin():
        user = User(name=current_app.config['SYS_ADMIN'], email=current_app.config['MAIL_USERNAME'],
                    password=current_app.config['SYS_ADMIN'], description=current_app.config['SYS_ADMIN'])
        db.session.add(user)
        db.session.commit()
        return user.id

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
        except (SignatureExpired, Exception) as e:
            Config.LOGGER.error('reset_password exception: {}'.format(str(e)))
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
        except (SignatureExpired, Exception) as e:
            Config.LOGGER.error('confirm exception: {}'.format(str(e)))
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
        except (SignatureExpired, Exception) as e:
            Config.LOGGER.error('change_email exception: {}'.format(str(e)))
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

    def get_auth_token(self, expiration=Config.EXPIRATION_TIME):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'auth': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.decode('utf-8'))
        except (SignatureExpired, Exception) as e:
            Config.LOGGER.error('verify_auth_toke exception: {}'.format(str(e)))
            return None
        return User.query.get(data.get('auth'))

    @property
    def url(self):
        return url_for('api.get_user', name=self.name)

    @property
    def blogs_url(self):
        return url_for('api.get_user_blogs', name=self.name)

    @property
    def followed_blogs_url(self):
        return url_for('api.get_user_followed_blogs', name=self.name)

    def to_json(self):
        json_str = {
            'url': self.url,
            'name': self.name,
            'email': self.email,
            'description': self.description,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'blogs_url': self.blogs_url,
            'followed_blogs_url': self.followed_blogs_url,
            'blogs_count': self.blogs.count(),
            'followed_count': self.followed.count(),
            'follower_count': self.follower.count(),
            'comments_count': self.comments.count(),
        }
        return json_str

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
    def self_blogs(self):
        return Blog.query.filter(Blog.user_id == self.id)

    @property
    def self_galleries(self):
        return Gallery.query.filter(Gallery.user_id == self.id)

    @property
    def self_diaries(self):
        return Diary.query.filter(Diary.user_id == self.id)

    @property
    def self_comments(self):
        return Comment.query.filter(Comment.user_id == self.id)

    @property
    def self_tags(self):
        return Tag.query.filter(Tag.user_id == self.id)

    @property
    def followed_blogs(self):
        return Blog.query.join(Follow, Follow.followed_id == Blog.user_id).filter(
            (not Blog.is_private) and Follow.follower_id == self.id)

    @property
    def followed_galleries(self):
        return Gallery.query.join(Follow, Follow.followed_id == Gallery.user_id).filter(
            (not Gallery.is_private) and Follow.follower_id == self.id)

    @property
    def followed_diaries(self):
        return Diary.query.join(Follow, Follow.followed_id == Diary.user_id).filter(
            (not Diary.is_private) and Follow.follower_id == self.id)

    @property
    def followed_comments(self):
        return Comment.query.join(Follow, Follow.followed_id == Comment.user_id).filter(
            Follow.follower_id == self.id)

    @property
    def followed_tags(self):
        return Tag.query.join(Follow, Follow.followed_id == Tag.user_id).filter(
            Follow.follower_id == self.id)


class AnonymousUser(AnonymousUserMixin):
    def can(self, perm):
        if perm:
            return False
        else:
            return self.is_anonymous()

    def is_admin(self):
        return self.is_authenticated()

    def is_anonymous(self):
        return self.is_anonymous()


loginMgr.anonymous_user = AnonymousUser


@loginMgr.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


"""
blog_tags = db.Table(
    'blog_tags',
    db.Column('blog_id', db.Integer, db.ForeignKey('blog.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id', ondelete='CASCADE'), primary_key=True))
"""


class BlogTags(db.Model):
    __table_name__ = 'blog_tags'
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), primary_key=True)


class TagQuery(BaseQuery):
    def search(self, key_word):
        key_word = '%{}%'.format(key_word.strip())
        return self.filter(Tag.name.ilike(key_word))


class Tag(db.Model):
    __table_name__ = 'tag'
    query_class = TagQuery
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    __mapper_args__ = {'order_by': [id.asc()]}
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=False, nullable=False, index=True)
    name = db.Column(db.String(Config.SHORT_STR_LEN), unique=False, nullable=False, index=True)
    blogs = db.relationship('BlogTags', foreign_keys=[BlogTags.tag_id],
                            backref=db.backref('tags', lazy='joined'), lazy='dynamic',
                            cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(Tag, self).__init__(**kwargs)

    def __repr__(self):
        return '{}: id={}, name={}'.format(self.__class__.__name__, self.id, self.name)

    def __str__(self):
        return self.__repr__()

    @property
    def url(self):
        return url_for('api.get_tag', id=self.id)

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=False, nullable=False, index=True)
    name = db.Column(db.String(Config.SHORT_STR_LEN), unique=False, nullable=False, index=True)
    parent_id = db.Column(db.Integer(), db.ForeignKey('category.id'), unique=False, nullable=True)
    parent = db.relationship('Category', primaryjoin='Category.parent_id == Category.id',
                             remote_side=id, backref=db.backref('children'))
    blogs = db.relationship('Blog', backref='category', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Category, self).__init__(**kwargs)

    def __repr__(self):
        return '{}: id={}, name={}'.format(self.__class__.__name__, self.id, self.name)

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def insert_categories(user_id):
        categories = ['ALGORITHM', 'CODE', 'TOOL', 'LIFE']
        for c in categories:
            if not Category.query.filter_by(name=c).first():
                category = Category(user_id=user_id, name=c)
                db.session.add(category)
                db.session.commit()

    @property
    def url(self):
        return url_for('api.get_category', id=self.id)

    @property
    def count(self):
        return Blog.query.public().filter_by(category_id=self.id).count()

    @property
    def count_all(self):
        categories = Category.query.all()
        ids = [c.id for c in categories]
        return Blog.query.public().filter(Blog.category_id.in_(ids)).count()

    @property
    def parents(self):
        cur, parent_list = self, []
        while cur:
            parent_list.append(cur)
            cur = cur.parent
        parent_list.reverse()
        return parent_list


@whoosh.register_model('title', 'content')
class Blog(db.Model):
    __table_name__ = 'blog'
    query_class = BlogQuery
    __rex_more_tag = re.compile(r'<!--more-->', re.I)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    __mapper_args__ = {'order_by': [id.asc()]}
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=False, nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), unique=False, nullable=False, index=True)
    is_private = db.Column(db.Boolean, unique=False, nullable=False, default=False)
    create_datetime = db.Column(db.DateTime, unique=False, nullable=False, index=True, default=datetime.datetime.utcnow)
    modify_datetime = db.Column(db.DateTime, unique=False, nullable=False, index=True, default=datetime.datetime.utcnow)
    title = db.Column(db.String(Config.SHORT_STR_LEN), unique=False, nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    content_html = db.Column(db.Text, unique=False, nullable=True)
    summary = db.Column(db.String(Config.LONG_STR_LEN), unique=False, nullable=True)
    # tags = db.relationship(Tag, secondary=blog_tags, backref=db.backref('blogs', lazy='dynamic'), lazy='dynamic')
    tags = db.relationship('BlogTags', foreign_keys=[BlogTags.blog_id],
                           backref=db.backref('blogs', lazy='joined'), lazy='dynamic',
                           cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref=db.backref('blog', lazy='joined'), lazy='dynamic')

    def __init__(self, **kwargs):
        super(Blog, self).__init__(**kwargs)

    def __repr__(self):
        return '{}: id={}, title={}'.format(self.__class__.__name__, self.id, self.title)

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def __truncate_data(s, length, end='...'):
        if len(s) <= length:
            return s
        result = s[:length - len(end)].rsplit(' ', 1)[0]
        return result + end

    def __generate_info(self, value):
        self.content_html = markdown2html(value)
        if self.summary is None or self.summary.strip() == '':
            rex_more_tag_match = Blog.__rex_more_tag.search(value)
            if rex_more_tag_match:
                html_data = markdown2html(value[:rex_more_tag_match.start()])
            else:
                html_data = self.content_html
            self.summary = Blog.__truncate_data(do_striptags(html_data), length=Config.LONG_STR_LEN)
            self.modify_datetime = datetime.datetime.utcnow()

    def to_json(self):
        json_str = {
            'url': self.url,
            'title': self.name,
            'summary': self.summary,
            'content': self.content,
            'create_datetime': self.create_datetime,
            'modify_datetime': self.modify_datetime,
            'user_url': self.user_url,
            'tags_url': self.tags_url,
            'tags_count': self.tags.count(),
            'comments_url': self.comments_url,
            'comments_count': self.comments.count(),
        }
        return json_str

    @staticmethod
    def from_json(json_str):
        try:
            user_id = json_str.get('user_id', None)
            if user_id is None:
                raise ValidationError('json blog does not have user_id')
            category_id = json_str.get('category_id', None)
            if category_id is None:
                raise ValidationError('json blog does not have category_id')
            is_private = json_str.get('is_private', None)
            if is_private is None:
                raise ValidationError('json blog does not have is_private')
            title = json_str.get('title', None)
            if title is None or title == '':
                raise ValidationError('json blog does not have title')
            content = json_str.get('content', None)
            if content is None or content == '':
                raise ValidationError('json blog does not have content')
        except ValidationError as e:
            Config.LOGGER.error('Blog.from_json error: {}'.format(str(e)))
            return None
        return Blog(category_id=category_id, is_private=is_private, title=title, content=content)

    @property
    def has_more(self):
        return Blog.__rex_more_tag.search(self.content) or self.summary.find('...') >= 0

    @property
    def url(self):
        return url_for('api.get_blog', id=self.id)

    @property
    def user_url(self):
        return url_for('api.get_blog_user_url', id=self.id)

    @property
    def tags_url(self):
        return url_for('api.get_blog_tags_url', id=self.id)

    @property
    def comments_url(self):
        return url_for('api.get_blog_comments_url', id=self.id)

    @property
    def next(self, from_category=False):
        _query = db.and_(Blog.category_id.in_([self.category_id]), Blog.id > self.id) \
            if from_category else db.and_(Blog.id > self.id,)
        return self.query.public().filter(_query).order_by(Blog.id.asc()).first

    @property
    def prev(self, from_category=False):
        _query = db.and_(Blog.category_id.in_([self.category_id]), Blog.id < self.id) \
            if from_category else db.and_(Blog.id < self.id,)
        return self.query.public().filter(_query).order_by(Blog.id.desc()).first

    @property
    def year(self):
        return int(self.create_datetime.year)

    @property
    def month(self):
        return int(self.create_datetime.month)

    @property
    def day(self):
        return int(self.create_datetime.day)

    @staticmethod
    def before_insert(mapper, connection, target):
        unused_param(mapper, connection)
        value = target.content
        target.__generate_info(value)

    @staticmethod
    def on_change_content(target, value, oldvalue, initiator):
        unused_param(oldvalue, initiator)
        target.__generate_info(value)


db.event.listen(Blog, 'before_insert', Blog.before_insert)
db.event.listen(Blog.content, 'set', Blog.on_change_content)


class Gallery(db.Model):
    __table_name__ = 'gallery'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    __mapper_args__ = {'order_by': [id.asc()]}
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=False, nullable=False, index=True)
    is_private = db.Column(db.Boolean, unique=False, nullable=False, default=True)
    datetime = db.Column(db.DateTime, unique=False, nullable=False, index=True, default=datetime.datetime.utcnow)
    content = db.Column(db.String(Config.LONG_STR_LEN), unique=False, nullable=False)

    def __init__(self, **kwargs):
        super(Gallery, self).__init__(**kwargs)

    def __repr__(self):
        return '{}: id={}, content={}'.format(self.__class__.__name__, self.id, self.content)

    def __str__(self):
        return self.__repr__()

    @property
    def url(self):
        return url_for('api.get_gallery', id=self.id)


@whoosh.register_model('content')
class Diary(db.Model):
    __table_name__ = 'diary'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    __mapper_args__ = {'order_by': [id.asc()]}
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=False, nullable=False, index=True)
    is_private = db.Column(db.Boolean, unique=False, nullable=False, default=True)
    datetime = db.Column(db.DateTime, unique=False, nullable=False, index=True, default=datetime.datetime.utcnow)
    content = db.Column(db.String(Config.LONG_STR_LEN), unique=False, nullable=False)

    def __init__(self, **kwargs):
        super(Diary, self).__init__(**kwargs)

    def __repr__(self):
        return '{}: id={}, content={}'.format(self.__class__.__name__, self.id, self.content)

    def __str__(self):
        return self.__repr__()

    @property
    def url(self):
        return url_for('api.get_diary', id=self.id)


@whoosh.register_model('content')
class Comment(db.Model):
    __table_name__ = 'comment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=False, nullable=False, index=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), unique=False, nullable=False, index=True)
    content = db.Column(db.String(Config.LONG_STR_LEN), unique=False, nullable=False)
    datetime = db.Column(db.DateTime, unique=False, nullable=False, index=True, default=datetime.datetime.utcnow)
    parent_id = db.Column(db.Integer(), db.ForeignKey('comment.id'), unique=False, nullable=True)
    parent = db.relationship('Comment', primaryjoin='Comment.parent_id == Comment.id',
                             remote_side=id, backref=db.backref('children'))

    def __init__(self, **kwargs):
        super(Comment, self).__init__(**kwargs)

    def __repr__(self):
        return '{}: id={}, content={}'.format(self.__class__.__name__, self.id, self.content)

    def __str__(self):
        return self.__repr__()

    def to_json(self):
        json_str = {
            'blog_url': url_for('api.get_blog', id=self.blog_id),
            'user_id': self.user_url,
            'blog_id': self.blog_id,
            'content': self.content,
            'datetime': self.datetime,
            'reply_to': self.reply_to,
        }
        return json_str

    @staticmethod
    def from_json(json_str):
        content = json_str.get('content', None)
        if content is None or content == '':
            raise ValidationError('json comment does not have content')
        reply_to = Comment.query.get(json_str.get('reply_to', None))
        if reply_to is None:
            raise ValidationError('json comment does not have reply_to')
        return Comment(content=content, reply_to=reply_to)
