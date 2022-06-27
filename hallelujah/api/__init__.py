#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from flask import Blueprint


bp_api = Blueprint('api', __name__)

try:
    from . import views
except Exception:
    raise

