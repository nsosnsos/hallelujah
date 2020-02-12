# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import abort, current_app, render_template
from flask_login import current_user
from flask_mail import Message
from functools import wraps

from .models import Permission
from . import mail


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


def send_async_mail(app, msg):
    with app.app_context():
        mail.send(msg)


def send_mail(to, subject, template, **kwargs):
    msg = Message(subject=current_app.config['SITE_NAME'] + ': ' + subject, sender=current_app.config['MAIL_ADMIN'],
                  recipients=[to])
    msg.body = render_template(template+'.txt', **kwargs)
    msg.html = render_template(template+'.html', **kwargs)
    with current_app.app_context():
        mail.send(msg)
    # from threading import Thread
    # thread = Thread(target=send_async_mail, args=[current_app._get_current_object(), msg])
    # thread.start()
    # return thread
