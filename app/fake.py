# !/usr/bin/env python
# -*- coding:utf-8 -*-

from random import randint
from faker import Faker
from sqlalchemy.exc import IntegrityError

from config import Config
from . import db
from .models import User, Category, Blog


def fake_users(count=10):
    fake = Faker()
    for i in range(count):
        u = User(name=fake.user_name(), email=fake.email(), description=fake.text(), confirmed=True,
                 password='password')
        db.session.add(u)
        try:
            db.session.commit()
        except IntegrityError as e:
            Config.LOGGER.error('fake_user: {}'.format(str(e)))
            db.session.rollback()


def fake_blogs(count=200):
    fake = Faker()
    user_count = User.query.count()
    category_count = Category.query.count()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        c = Category.query.offset(randint(0, category_count - 1)).first()
        b = Blog(user_id=u.id, category_id=c.id, is_private=randint(0, 1),
                 title=fake.text()[:Config.SHORT_STR_LEN], content=fake.text())
        db.session.add(b)
        try:
            db.session.commit()
        except IntegrityError as e:
            Config.LOGGER.error('fake_blog: {}'.format(str(e)))
            db.session.rollback()
