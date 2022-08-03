#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import click
import unittest
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, request, redirect, url_for, jsonify

from .config import configs
from .extensions import db, migrate, bootstrap, login_manager, mail, moment
from .models import User, AnonymousUser, Article, Media
from .utility import mariadb_is_in_use, mariadb_is_exist_db, mariadb_create_db, send_email
from .main import bp_main
from .auth import bp_auth
from .api import bp_api


login_manager.anonymous_user = AnonymousUser


def create_app(config_name='default'):
    app = Flask(configs[config_name].SITE_NAME,
                static_folder=configs[config_name].SYS_STATIC,
                template_folder=configs[config_name].SYS_TEMPLATE)
    app.config.from_object(configs[config_name])
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)
    configs[config_name].init_app(app)

    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
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
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_auth, url_prefix=app.config.get('AUTH_URL_PREFIX'))
    app.register_blueprint(bp_api, url_prefix=app.config.get('API_URL_PREFIX'))

def register_errorhandlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        if request.path.startswith(app.config.get('API_URL_PREFIX')):
            return jsonify({'error': 'bad request', 'message': str(e)})
        return redirect(url_for('main.index', _external=True))

    @app.errorhandler(403)
    def forbidden_error(e):
        if request.path.startswith(app.config.get('API_URL_PREFIX')):
            return jsonify({'error': 'forbidden error', 'message': str(e)})
        return redirect(url_for('main.index', _external=True))

    @app.errorhandler(404)
    def page_not_found(e):
        if request.path.startswith(app.config.get('API_URL_PREFIX')):
            return jsonify({'error': 'page not found', 'message': str(e)})
        return redirect(url_for('main.index', _external=True))

    @app.errorhandler(500)
    def internal_server_error(e):
        if request.path.startswith(app.config.get('API_URL_PREFIX')):
            return jsonify({'error': 'internal server error', 'message': str(e)})
        return redirect(url_for('main.index', _external=True))

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
    @click.option('--mail_address', prompt=True,
                  default=app.config.get('MAIL_USERNAME'),
                  help='Administrator mail address')
    @click.option('--mail_password', prompt=True, hide_input=True,
                  default=app.config.get('MAIL_PASSWORD'),
                  help='Administrator mail password')
    def init(mail_address, mail_password):
        if not mariadb_is_in_use():
            print('Drop all tables in SQLite...')
            db.drop_all()
        elif mariadb_is_exist_db():
            print('Database exists already. There is no need to initialize database.')
            return
        else:
            print('Creating database for MariaDB...')
            mariadb_create_db()
            if not mariadb_is_exist_db():
                print('Failed to create database!')
                return
        print('Creating all tables...')
        db.create_all()
        user_name = mail_address.split('@')[0]
        print(f'Adding user: {user_name} ...')
        User.add_user(name=user_name, email=mail_address, password=mail_password)
        print('Adding fake users ...')
        User.add_fake_users(10)
        print('Adding fake articles ...')
        Article.add_fake_articles(50)
        print(f'Sending email to {mail_address} ...')
        thread = send_email(to=mail_address, subject=app.config.get('SITE_NAME'),
                           msg='Hello, {}. Thanks for register.'.format(user_name))
        thread.join()

