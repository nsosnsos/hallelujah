# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_pagedown import PageDown
from flask_sqlalchemy import SQLAlchemy
from flask_whooshee import Whooshee
from flask_cache import Cache

from config import config


bootstrap = Bootstrap()
loginMgr = LoginManager()
mail = Mail()
moment = Moment()
pagedown = PageDown()
db = SQLAlchemy()
whoosh = Whooshee()
cache = Cache()


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    loginMgr.login_view = 'auth.login'
    loginMgr.login_message = 'Unauthorized User'
    loginMgr.login_message_category = 'info'
    loginMgr.session_protection = 'strong'

    bootstrap.init_app(app)
    loginMgr.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    pagedown.init_app(app)
    db.init_app(app)
    whoosh.init_app(app)
    cache.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint, url_prefix='/')

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
