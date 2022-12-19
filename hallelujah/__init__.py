#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import os
import click
import unittest
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, request, jsonify

from .config import configs
from .extensions import db, migrate, bootstrap, login_manager, mail, moment
from .models import User, AnonymousUser, Article, Media, Resource
from .utility import redirect_back, mariadb_is_in_use, mariadb_is_exist_db, mariadb_create_db, send_email
from .main.views import bp_main
from .auth.views import bp_auth
from .api.views import bp_api


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

    app.add_template_global(os.path.join, 'os_path_join')

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
        return redirect_back('main.index')

    @app.errorhandler(403)
    def forbidden_error(e):
        if request.path.startswith(app.config.get('API_URL_PREFIX')):
            return jsonify({'error': 'forbidden error', 'message': str(e)})
        return redirect_back('main.index')

    @app.errorhandler(404)
    def page_not_found(e):
        if request.path.startswith(app.config.get('API_URL_PREFIX')):
            return jsonify({'error': 'page not found', 'message': str(e)})
        return redirect_back('main.index')

    @app.errorhandler(413)
    def payload_too_large(e):
        if request.endpoint == 'main.upload':
            return 'File is too large', 413
        return redirect_back('main.index')

    @app.errorhandler(500)
    def internal_server_error(e):
        if request.path.startswith(app.config.get('API_URL_PREFIX')):
            return jsonify({'error': 'internal server error', 'message': str(e)})
        return redirect_back('main.index')

def register_shell_context_processor(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, User=User, Article=Article,
                    Media=Media, Resource=Resource)

def register_commands(app):
    @app.cli.command()
    def test():
        test_set = unittest.TestLoader().discover('test')
        unittest.TextTestRunner(verbosity=2).run(test_set)

    @app.cli.command()
    @click.option('--username', prompt=True, required=True,
                  help='new user name')
    @click.option('--password', prompt=True, required=True, hide_input=True,
                  help='new user password')
    @click.option('--mail_address', prompt=True, required=True,
                  help='new user mail address')
    def addusr(username, password, mail_address):
        print(f'Adding user: {username} ...')
        User.add_user(name=username, email=mail_address, password=password)
        print(f'Sending email to {mail_address} ...')
        thread = send_email(to=mail_address, subject=app.config.get('SITE_NAME'),
                           msg=f'Hello, {username}. Thanks for registering!')
        thread.join()

    @app.cli.command()
    @click.option('--username', prompt=True, required=True,
                  help='user name to be deleted')
    def delusr(username):
        u = User.query.filter(User.name==username).first()
        if not u:
            print(f'User[{username}] is not exists')
            return
        print(f'Deleting user: {username} ...')
        User.delete_user(name=username)
        print(f'Sending email to {u.email} ...')
        thread = send_email(to=u.email, subject=app.config.get('SITE_NAME'),
                           msg=f'Bye, {username}. I wish you good luck!')
        thread.join()

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
        print(f'Adding administrator: {user_name} ...')
        User.add_user(name=user_name, email=mail_address, password=mail_password)
        '''
        print('Adding fake users ...')
        User.add_fake_users(5)
        print('Adding fake articles ...')
        Article.add_fake_articles(20)
        print('Adding fake resources ...')
        Resource.add_fake_resources(20)
        '''

