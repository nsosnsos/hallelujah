# !/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import bleach
from markdown import markdown
from flask import abort, current_app, render_template, g, request
from flask_login import current_user
from flask_mail import Message
from functools import wraps
from threading import Thread

from . import mail, babel


class Permission:
    GUEST = 0x00
    COMMENT = 0x01
    DIARY = 0x02
    GALLERY = 0x04
    BLOG = 0x08
    ADMIN = 0x10


def split_key_words(keywords):
    return re.sub(r'[,，;；+　]', ' ', keywords).split(' ')


def string_to_url(s):
    return re.sub(r'[，　,.:;\s]', '+', s)


def markdown2html(text):
    allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                    'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                    'h1', 'h2', 'h3', 'p', 'img']
    # extensions = ['fenced_code', 'codehilite(css_class=highlight, linenums=true)', 'admonition', 'tables', 'extra']
    extensions = ['fenced_code', 'codehilite', 'admonition', 'tables', 'extra']
    return bleach.linkify(bleach.clean(
        markdown(text, extensions=extensions, output_format='html5'), tags=allowed_tags, strip=True))


# noinspection PyUnusedLocal
def unused_param(*args, **kwargs):
    pass


def permission_required(perm):
    def decorator(f):
        @wraps(f)
        def decoratored_function(*args, **kwargs):
            if not current_user.can(perm):
                abort(403)
            return f(*args, **kwargs)
        return decoratored_function
    return decorator


def admin_required(f):
    return permission_required(Permission.ADMIN)(f)


def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.config['LOGGER'].error('send_async_email exception: {}'.format(str(e)))


def send_email(to, subject, template, **kwargs):
    msg = Message(subject=current_app.config['SITE_NAME'] + ': ' + subject, sender=current_app.config['MAIL_USERNAME'],
                  recipients=[to])
    msg.body = render_template(template+'.txt', **kwargs)
    msg.html = render_template(template+'.html', **kwargs)

    # with current_app.app_context():
    #    mail.send(msg)

    # noinspection PyProtectedMember
    thread = Thread(target=send_async_email, args=[current_app._get_current_object(), msg])
    thread.start()
    return thread


@babel.localeselector
def get_locale():
    user = getattr(g, 'user', None)
    if user is not None:
        return user.locale
    config_locales = current_app.config['LOCALES']
    return request.accept_languages.best_match(config_locales)


@babel.timezoneselector
def get_timezone():
    user = getattr(g, 'user', None)
    if user is not None:
        return user.timezone
