#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from flask import Blueprint


bp_main = Blueprint('main', __name__)

try:
    from . import views
except Exception:
    raise

