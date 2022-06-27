#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from flask import Blueprint


bp_auth = Blueprint('auth', __name__)

try:
    from . import views
except Exception:
    raise

