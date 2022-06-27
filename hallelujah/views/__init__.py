#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from flask import Blueprint


main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
api = Blueprint('api', __name__)

