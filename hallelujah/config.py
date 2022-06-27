#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import re
import sys
import configparser
import logging
from logging import handlers


def is_valid_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.fullmatch(regex, email)


def get_logger(log_switch, log_file, log_name):
    log_format = logging.Formatter('[%(asctime)s][{0}]: %(message)s'.format(log_name))
    logger = logging.getLogger(name=log_name)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_format)
    stream_handler.setLevel(logging.WARNING)
    logger.addHandler(stream_handler)
    if log_switch:
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_file, encoding='utf8', when='W0', backupCount=7)
        file_handler.setFormatter(log_format)
        file_handler.setLevel(logging.ERROR)
        logger.addHandler(file_handler)
    return logger


class Config():
    CSRF_ENABLED = True
    SECRET_KEY = os.urandom(32)
    LOCALHOST = '127.0.0.1'
    MIN_STR_LEN = 5
    SHORT_STR_LEN = 64
    LONG_STR_LEN = 1024
    EXPIRATION_TIME = 3600
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SITE_NAME = 'hallelujah'
    SITE_DESCRIPTION = 'In God We Trust'
    SITE_AUTHOR = 'Stan Lee'

    SYS_HOST = '0.0.0.0'
    SYS_PORT = 4100
    SYS_DEBUG = True

    # MAIL PORT CONFIG: 465 for SSL, 587 for TLS
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', None) or 'test@test.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', None) or 'MAIL_PASSWORD'
    if not is_valid_email(MAIL_USERNAME):
        print('Invalid MAIL_USERNAME in {}'.format(__file__))
        sys.exit(-1)
    MAIL_SERVER = 'smtp.' + MAIL_USERNAME[MAIL_USERNAME.find('@')+1:]

    MYSQL_HOST = LOCALHOST
    MYSQL_PORT = 3306
    MYSQL_DB = SITE_NAME
    MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME', None) or 'MYSQL_USERNAME'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', None) or 'MYSQL_PASSWORD'
    MYSQL_CHARSET = 'uft8_bin'

    SQLITE_PATH = os.path.dirname(os.path.realpath(__file__))
    SQLITE_DB = 'sqlite.db'

    SSH_TUNNEL_SWITCH = False
    SSH_TUNNEL_PORT = 22
    SSH_TUNNEL_USERNAME = os.environ.get('SSH_TUNNEL_USERNAME', None) or 'SSH_TUNNEL_USERNAME'
    SSH_TUNNEL_PASSWORD = os.environ.get('SSH_TUNNEL_PASSWORD', None) or 'SSH_TUNNEL_PASSWORD'

    REDIS_SWITCH = False
    REDIS_HOST = LOCALHOST
    REDIS_PORT = 3389
    REDIS_DB = SITE_NAME

    LOG_SWITCH = True
    LOG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), SITE_NAME + '.log')

    LOGGER = get_logger(LOG_SWITCH, LOG_FILE, SITE_NAME)
    MYSQL_CONN_STR = 'mysql+pymysql://{0}:{1}@{2}:{3}/{4}?charset={5}'.format(
        MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DB, MYSQL_CHARSET)
    SQLITE_CONN_STR = 'sqlite:///' + os.path.join(SQLITE_PATH, SQLITE_DB)
    SQLALCHEMY_DATABASE_URI = MYSQL_CONN_STR if not SYS_DEBUG else SQLITE_CONN_STR

    def __repr__(self):
        return '<%s : %s>' % (self.__class__.__name__, Config.__dict__)

    def __str__(self):
        return self.__repr__()

    @classmethod
    def init_app(cls, app):
        app.logger.addHandler(cls.LOGGER)


class TestConfig(Config):
    DEBUG = False
    TESTING = True


class DevelopConfig(Config):
    DEBUG = True
    TESTING = False


class ProductConfig(Config):
    DEBUG = False
    TESTING = False

    @classmethod
    def __get_mail_handler(cls):
        credentials, secure = None, None
        if getattr(cls, 'MAIL_USERNAME', None):
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = logging.handlers.SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT), fromaddr=cls.MAIL_USERNAME,
            toaddrs=[cls.MAIL_USERNAME], subject=cls.SITE_NAME + ' message',
            credentials=credentials, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        return mail_handler

    @classmethod
    def init_app(cls, app):
        super().init_app(app)
        app.logger.addHandler(cls.__get_mail_handler())


configs = {
    'test': TestConfig,
    'develop': DevelopConfig,
    'product': ProductConfig,
    'default': ProductConfig
}

