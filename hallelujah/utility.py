# !/usr/bin/env python
# -*- coding:utf-8 -*-


import re
import bleach
import datetime
import subprocess
from threading import Thread
from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from flask import current_app, request, redirect, url_for, session
from flask_mail import Message

from .extensions import mail


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

def redirect_back(default='main.index', **kwargs):
    if request.referrer:
        return redirect(request.referrer)
    return redirect(url_for(default, _external=True, **kwargs))

def redirect_before(default='main.index', **kwargs):
    if request and request.args.get('next'):
        target = request.args.get('next')
        if target and not target.startswith('/'):
            return redirect(url_for(target, _external=True))
    elif 'url' in session:
        return redirect(session['url'])
    return redirect(url_for(default, _external=True, **kwargs))

def redirect_save(url=None):
    if not url:
        url = url_for('main.index', _external=True)
    session['url'] = url

def mariadb_is_in_use():
    return current_app.config.get('SYS_MARIADB')

def mariadb_is_exist_db():
    db_usr = current_app.config.get('MARIADB_USERNAME')
    db_pwd = current_app.config.get('MARIADB_PASSWORD')
    db_name = current_app.config.get('MARIADB_DB')
    command = f'mariadb -u {db_usr} -p\'{db_pwd}\' -e \"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME=\'{db_name}\';\"'
    try:
        ret = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        current_app.config.get('LOGGER').error('is_exist_database: {}'.format(str(e)))
    return ret.returncode == 0 and ret.stdout.decode() != ''

def mariadb_create_db():
    db_usr = current_app.config.get('MARIADB_USERNAME')
    db_pwd = current_app.config.get('MARIADB_PASSWORD')
    db_name = current_app.config.get('MARIADB_DB')
    db_charset = current_app.config.get('MARIADB_CHARSET')
    command = f'mariadb -u {db_usr} -p\'{db_pwd}\' -e \"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARSET {db_charset} COLLATE {db_charset}_unicode_ci;\"'
    try:
        ret = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        current_app.config.get('LOGGER').error('create_database: {}'.format(str(e)))
    return ret.returncode == 0 and ret.stdout.decode() == ''

def send_async_email(app, message):
    with app.app_context():
        try:
            mail.send(message)
        except Exception as e:
            app.config.get('LOGGER').error('send_async_email: {}'.format(str(e)))

def send_email(to, subject, msg):
    message = Message(subject=current_app.config.get('SITE_NAME') + ': ' + subject,
                      sender=current_app.config.get('MAIL_USERNAME'), recipients=[to])
    message.body = msg

    thread = Thread(target=send_async_email, args=[current_app._get_current_object(), message])
    thread.start()
    return thread

