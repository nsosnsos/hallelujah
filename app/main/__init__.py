# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import Blueprint

main = Blueprint(name='main', import_name=__name__)

try:
    from ..models import Permission
    from . import views, errors
except Exception:
    raise


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
