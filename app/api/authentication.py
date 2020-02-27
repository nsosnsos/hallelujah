# !/usr/bin/env python
# -*- coding:utf-8 -*-

from functools import wraps
from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth

from config import Config
from .. import db
from ..models import User
from . import api
from .errors import unauthorized, forbidden


http_auth = HTTPBasicAuth()


def permission_required(perm):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user.can(perm):
                return forbidden('Insufficient permissions')
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@http_auth.verify_password
def verify_password(id_or_token, password):
    if not id_or_token or id_or_token == '':
        return False
    if not password or password == '':
        g.current_user = User.verify_auth_token(id_or_token)
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter(db.or_(User.email == id_or_token.lower(), User.name == id_or_token)).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@http_auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@http_auth.login_required
def before_request():
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('Unconfirmed account')


@api.route('/tokens/', methods=['POST'])
def get_token():
    if g.current_user.is_anonymous and g.token_used:
        return auth_error()
    return jsonify({'token': g.current_user.get_auth_token(), 'expiration': Config.EXPIRATION_TIME})
