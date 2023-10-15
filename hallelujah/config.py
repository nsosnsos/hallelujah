#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import os
import re
import sys
import json
import redis
import logging
import requests
import datetime
from logging import handlers


def _is_valid_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.fullmatch(regex, email)


def _get_themes():
    try:
        bootswatch5 = requests.get('https://bootswatch.com/api/5.json')
        themes = {theme['name']: theme['cssCdn'] for theme in json.loads(bootswatch5.text)['themes']}
    except Exception as e:
        print('_get_themes: {}'.format(str(e)))
        sys.exit(-1)
    return themes


class Config:
    ENV = 'production'
    DEBUG = False
    TESTING = False

    CSRF_ENABLED = True
    SECRET_KEY = os.urandom(32)
    MIN_STR_LEN = 4
    SHORT_STR_LEN = 64
    LONG_STR_LEN = 128
    MAX_STR_LEN = 512
    ITEMS_PER_PAGE = 30
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=7)
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SITE
    SITE_NAME = 'hallelujah'
    SITE_DESCRIPTION = 'In God We Trust'
    SITE_AUTHOR = 'Stan Lee'

    # SYSTEM
    SYS_HOST = '127.0.0.1'
    SYS_PORT = 4100
    SYS_STATIC = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')
    SYS_TEMPLATE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates')
    SYS_MEDIA = os.path.join(os.path.abspath(os.path.expanduser('~')), 'data', 'media')
    SYS_MEDIA_ORIGINAL = os.path.join(SYS_MEDIA, 'original')
    SYS_MEDIA_THUMBNAIL = os.path.join(SYS_MEDIA, 'thumbnail')
    SYS_MEDIA_THUMBNAIL_HEIGHT = 200
    SYS_MEDIA_EXCLUDES = 'public,private'
    SYS_THEMES = _get_themes()
    SYS_THEME_DAY = SYS_THEMES.get('United')
    SYS_THEME_NIGHT = SYS_THEMES.get('Darkly')
    SYS_LOCAL_PLUGINS = True
    SYS_MARIADB = True
    SYS_REGISTER = False

    # BLUEMAP
    AUTH_URL_PREFIX = '/auth'
    API_URL_PREFIX = '/api'

    # DROPZONE
    DROPZONE_PARALLEL_UPLOADS = 999
    DROPZONE_MAX_FILE_SIZE = 1024 * 1024 * 1024

    # MAIL PORT CONFIG: 465 for SSL, 587 for TLS
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', None) or 'MAIL_USERNAME@SERVER.COM'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', None) or 'MAIL_PASSWORD'
    if not _is_valid_email(MAIL_USERNAME):
        print('Invalid MAIL_USERNAME.')
        sys.exit(-1)
    MAIL_SERVER = 'smtp.' + MAIL_USERNAME[MAIL_USERNAME.find('@')+1:]

    # MARIADB
    MARIADB_HOST = SYS_HOST
    MARIADB_PORT = 3306
    MARIADB_DB = SITE_NAME
    MARIADB_USERNAME = os.environ.get('MARIADB_USERNAME', None) or SITE_NAME
    MARIADB_PASSWORD = os.environ.get('MARIADB_PASSWORD', None) or SITE_NAME
    MARIADB_CHARSET = 'utf8mb4'

    # SQLITE
    SQLITE_PATH = os.path.dirname(os.path.realpath(__file__))
    SQLITE_DB = 'sqlite.db'

    # REDIS
    REDIS_HOST = SYS_HOST
    REDIS_PORT = 6379

    # SESSION
    SESSION_TYPE = 'redis'
    SESSION_REDIS = redis.from_url('redis://' + REDIS_HOST + ':' + str(REDIS_PORT))
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    # SSH TUNNEL
    SSH_TUNNEL_SWITCH = False
    SSH_TUNNEL_PORT = 22
    SSH_TUNNEL_USERNAME = os.environ.get('SSH_TUNNEL_USERNAME', None) or 'SSH_TUNNEL_USERNAME'
    SSH_TUNNEL_PASSWORD = os.environ.get('SSH_TUNNEL_PASSWORD', None) or 'SSH_TUNNEL_PASSWORD'

    # LOGGER
    LOG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), SITE_NAME + '.log')
    LOGGER = None

    # DATABASE
    MARIADB_CONN_STR = 'mysql+pymysql://{0}:{1}@{2}:{3}/{4}?charset={5}'.format(
        MARIADB_USERNAME, MARIADB_PASSWORD, MARIADB_HOST, MARIADB_PORT, MARIADB_DB, MARIADB_CHARSET)
    SQLITE_CONN_STR = 'sqlite:///' + os.path.join(SQLITE_PATH, SQLITE_DB)
    SQLALCHEMY_DATABASE_URI = MARIADB_CONN_STR if SYS_MARIADB else SQLITE_CONN_STR

    def __repr__(self):
        return '<%s : %s>' % (self.__class__.__name__, Config.__dict__)

    def __str__(self):
        return self.__repr__()

    @classmethod
    def _get_logger(cls):
        log_format = logging.Formatter('[%(asctime)s] %(message)s')
        logger = logging.getLogger(name=cls.SITE_NAME)
        logger.setLevel(logging.DEBUG)

        if cls.DEBUG:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(log_format)
            stream_handler.setLevel(logging.INFO)
            logger.addHandler(stream_handler)
        else:
            file_handler = logging.handlers.TimedRotatingFileHandler(
                filename=cls.LOG_FILE, encoding='utf8', when='W0', backupCount=7)
            file_handler.setFormatter(log_format)
            file_handler.setLevel(logging.INFO)
            logger.addHandler(file_handler)

        return logger

    @classmethod
    def init_app(cls, app):
        if not cls.LOGGER:
            cls.LOGGER = cls._get_logger()
        app.logger = cls.LOGGER


class TestingConfig(Config):
    ENV = 'testing'
    TESTING = True
    SYS_MARIADB = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SESSION_TYPE = 'null'


class DevelopmentConfig(Config):
    ENV = 'development'
    DEBUG = True
    SESSION_TYPE = 'filesystem'


class ProductionConfig(Config):
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
    'testing': TestingConfig,
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}

