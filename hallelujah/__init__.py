#!/usr/bin/env python3
"""
app service entry
create app
register extensions
register blue prints
register error handlers
register request handlers
register shell context processor
register commands
"""

import os
import sys
import unittest

import click
from flask import Flask, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix

from .api.views import bp_api
from .auth.views import bp_auth
from .config import configs
from .extensions import (
    bootstrap,
    db,
    login_manager,
    mail,
    migrate,
    moment,
    session,
)
from .main.views import bp_main
from .models import AnonymousUser, Article, Media, Resource, User
from .utility import (
    db_backup,
    db_create,
    db_drop,
    db_is_exist,
    db_restore,
    get_request_ip,
    redirect_back,
    send_email,
    sqlite_in_use,
)

login_manager.anonymous_user = AnonymousUser


def create_app(config_name="default"):
    """create app"""
    app = Flask(
        configs[config_name].SITE_NAME,
        static_folder=configs[config_name].SYS_STATIC,
        template_folder=configs[config_name].SYS_TEMPLATE,
    )
    app.config.from_object(configs[config_name])
    if not app.config.get("SECRET_KEY", None):
        app.logger.error("secret key is not found!")
        sys.exit(1)
    configs[config_name].init_app(app)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)

    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_requesthandlers(app)
    register_shell_context_processor(app)
    register_commands(app)

    app.add_template_global(os.path.join, "os_path_join")

    return app


def register_extensions(app):
    """register extensions"""
    db.init_app(app)
    migrate.init_app(app, db)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    session.init_app(app)


def register_blueprints(app):
    """register blueprints"""
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_auth, url_prefix=app.config.get("AUTH_URL_PREFIX"))
    app.register_blueprint(bp_api, url_prefix=app.config.get("API_URL_PREFIX"))


def register_errorhandlers(app):
    """register error handlers"""

    def payload_too_large(e):
        if request.endpoint == "main.upload":
            return f"File is too large: {e!s}", 413
        return redirect_back("main.index")

    def make_api_or_redirect_handler(error_name):
        def handler(e):
            if request.path.startswith(app.config.get("API_URL_PREFIX")):
                return jsonify({"error": error_name, "message": str(e)})
            return redirect_back("main.index")

        return handler

    errors = {
        400: "bad request",
        403: "forbidden error",
        404: "page not found",
        500: "internal server error",
    }
    for code, name in errors.items():
        app.register_error_handler(code, make_api_or_redirect_handler(name))
    app.register_error_handler(413, payload_too_large)


def register_requesthandlers(app):
    """register request handlers"""

    @app.before_request
    def request_handler():
        parts = request.url.split("/")
        if len(parts) < 4 or parts[3] != "static":
            app.logger.info(f"[{get_request_ip(request)}] {request.url}")


def register_shell_context_processor(app):
    """register shell context processor"""

    @app.shell_context_processor
    def make_shell_context():
        return {
            "db": db,
            "User": User,
            "Article": Article,
            "Media": Media,
            "Resource": Resource,
        }


def cli_test():
    """cli test"""
    test_set = unittest.TestLoader().discover("test")
    unittest.TextTestRunner(verbosity=2).run(test_set)


def cli_backup():
    """cli backup"""
    db_backup()


def cli_restore():
    """cli restore"""
    db_restore()


def cli_check():
    """cli check"""
    Media.check_media()


@click.option("--username", prompt=True, required=True, help="new user name")
@click.option(
    "--password",
    prompt=True,
    required=True,
    hide_input=True,
    help="new user password",
)
@click.option("--mail_address", prompt=True, required=True, help="new user mail address")
@click.pass_context
def cli_addusr(ctx, username, password, mail_address):
    """cli addusr"""
    app = ctx.obj["app"]
    app.logger.info(f"Adding user: {username} ...")
    User.add_user(name=username, email=mail_address, password=password)

    app.logger.info(f"Sending email to {mail_address} ...")
    thread = send_email(
        to=mail_address,
        subject=app.config.get("SITE_NAME"),
        msg=f"Hello, {username}. Thanks for registering!",
    )
    thread.join()


@click.option("--username", prompt=True, required=True, help="user name to be deleted")
@click.pass_context
def cli_delusr(ctx, username):
    """cli delusr"""
    app = ctx.obj["app"]
    u = User.query.filter(User.name == username).first()
    if not u:
        app.logger.error(f"User[{username}] does not exist")
        return

    app.logger.info(f"Deleting user: {username} ...")
    User.delete_user(name=username)

    app.logger.info(f"Sending email to {u.email} ...")
    thread = send_email(
        to=u.email,
        subject=app.config.get("SITE_NAME"),
        msg=f"Bye, {username}. I wish you good luck!",
    )
    thread.join()


def cli_init(app, database, mail_address, mail_password):
    """cli init"""
    if sqlite_in_use():
        app.logger.info("Drop all tables...")
        database.drop_all()
    else:
        if db_is_exist():
            app.logger.info("Dropping database...")
            db_drop()
        app.logger.info("Creating database...")
        db_create()
        if not db_is_exist():
            app.logger.error("Failed to create database!")
            return

    app.logger.info("Creating all tables...")
    database.create_all()
    user_name = mail_address.split("@")[0]
    app.logger.info(f"Adding administrator: {user_name} ...")
    User.add_user(name=user_name, email=mail_address, password=mail_password)

    app.logger.info(f"Sending email to {mail_address} ...")
    thread = send_email(
        to=mail_address,
        subject=app.config.get("SITE_NAME"),
        msg=f"Hello, {user_name}. Thanks for registering!",
    )
    thread.join()


def register_commands(app):
    """register commands"""

    app.cli.command("test")(cli_test)
    app.cli.command("backup")(cli_backup)
    app.cli.command("restore")(cli_restore)
    app.cli.command("check")(cli_check)

    @app.cli.command("addusr")
    @click.pass_context
    def cli_addusr_wrap(ctx, **kwargs):
        ctx.obj = {"app": app}
        ctx.invoke(cli_addusr, **kwargs)

    @app.cli.command("delusr")
    @click.pass_context
    def cli_delusr_wrap(ctx, **kwargs):
        ctx.obj = {"app": app}
        ctx.invoke(cli_delusr, **kwargs)

    @app.cli.command("init")
    @click.option(
        "--mail_address",
        prompt=True,
        default=lambda: app.config.get("MAIL_USERNAME"),
        help="Administrator mail address",
    )
    @click.option(
        "--mail_password",
        prompt=True,
        hide_input=True,
        default=lambda: app.config.get("MAIL_PASSWORD"),
        help="Administrator mail password",
    )
    def cli_init_wrap(mail_address, mail_password):
        cli_init(app, db, mail_address, mail_password)
