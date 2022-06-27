# !/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import bleach
import datetime
from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from flask import current_app
from flask_mail import Message
from threading import Thread

from . import mail


def string_to_url(s):
    r = re.sub(r'[/\\\'\"\s\t~!@#$%^&*()`|<>?]', '+', s)
    while '++' in r:
        r = r.replace('++', '+')
    return r

def markdown_to_html(text):
    allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                    'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    'dl', 'dd', 'dt', 'tt', 'cite',
                    'br', 'img', 'span', 'div', 'pre', 'p',
                    'table', 'col', 'tr', 'td', 'th', 'tbody', 'thead',
                    'sup', 'sub', 'colgroup']
    extensions = ['fenced_code', CodeHiliteExtension(css_class='highlight', linenums=True),
                  'admonition', 'tables', 'extra']
    return bleach.linkify(bleach.clean(
        markdown(text, extensions=extensions, output_format='html5'), tags=allowed_tags, strip=True))

def get_timestamp(t=None):
    if not t:
        t = datetime.datetime.now()
    return t.strftime('%Y-%m-%d %H:%M:%S')

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.config['LOGGER'].error('send_async_email exception: {}'.format(str(e)))

def send_email(to, subject, msg):
    msg = Message(subject=current_app.config['SITE_NAME'] + ': ' + subject,
                  sender=current_app.config['MAIL_USERNAME'], recipients=[to])
    msg.body = msg

    thread = Thread(target=send_async_email, args=[current_app._get_current_object(), msg])
    thread.start()
    return thread

