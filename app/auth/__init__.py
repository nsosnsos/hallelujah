# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import Blueprint

auth = Blueprint(name='auth', import_name=__name__)

try:
    from . import views
except Exception:
    raise
