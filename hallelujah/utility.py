# !/usr/bin/env python
# -*- coding:utf-8 -*-


import bleach
import subprocess
from threading import Thread
from markdown import markdown
from flask import current_app, request, redirect, url_for, session
from flask_mail import Message

from .extensions import mail


def markdown_to_html(text):
    extensions = ['fenced_code', 'admonition', 'tables', 'extra']
    return bleach.linkify(markdown(text, extensions=extensions, output_format='html5'))


def redirect_back(endpoint=None, is_auth=False, **kwargs):
    if endpoint:
        target_url = url_for(endpoint, **kwargs, _external=True)
        return redirect(target_url)
    if is_auth and 'url' in session:
        return redirect(session['url'])
    if not is_auth and request.referrer and request.referrer != request.url:
        return redirect(request.referrer)
    return redirect(url_for('main.index', _external=True))


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

