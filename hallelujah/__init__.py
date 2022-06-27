#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import click
import unittest
from flask import Flask
from flask_migrate import upgrade

from .config import configs
from .extensions import db, migrate, bootstrap, login_manager, mail, moment
from .models import User, AnonymousUser, Article, Media
from .views import main, auth, api


login_manager.login_view = 'auth.login'
login_manager.anonymous_user = AnonymousUser


def create_app(config_name='develop'):
    app = Flask(configs[config_name].SITE_NAME)
    app.config.from_object(configs[config_name])
    configs[config_name].init_app(app)

    register_extensions(app)
    register_blueprints(app)
    register_shell_context_processor(app)
    register_commands(app)

    return app

def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    moment.init_app(app)

def register_blueprints(app):
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(api, url_prefix='api')

def register_shell_context_processor(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, User=User, Article=Article,
                    Media=Media)

def register_commands(app):
    @app.cli.command()
    def test():
        test_set = unittest.TestLoader().discover('test')
        unittest.TextTestRunner(verbosity=2).run(test_set)

    @app.cli.command()
    @click.option('--mail_username', prompt=True,
                  default=app.config.get('MAIL_USERNAME', ''),
                  help='The mail address')
    @click.option('--mail_password', prompt=True, hide_input=True,
                  default=app.config.get('MAIL_PASSWORD', ''),
                  help='The mail password')
    @click.option('--mysql_username', prompt=True,
                  default=app.config.get('MYSQL_USERNAME', ''),
                  help='The username of Mysql')
    @click.option('--mysql_password', prompt=True, hide_input=True,
                  default=app.config.get('MYSQL_PASSWORD', ''),
                  help='The password of Mysql')
    @click.option('--ssh_tunnel_username', prompt=False,
                  default=app.config.get('SSH_TUNNEL_USERNAME', ''),
                  help='The username of ssh tunnel for mysql')
    @click.option('--ssh_tunnel_password', prompt=False, hide_input=True,
                  default=app.config.get('SSH_TUNNEL_PASSWORD', ''),
                  help='The password of ssh tunnel for mysql')
    def init(mail_username, mail_password, mysql_username, mysql_password,
             ssh_tunnel_username, ssh_tunnel_password):
        db.create_all()
        User.add(user)

