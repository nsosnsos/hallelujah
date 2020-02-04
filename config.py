# !/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import configparser
import logging
from logging import handlers


_CONFIG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'site.conf')


if not os.path.isfile(_CONFIG_FILE):
    print('Error: missing site config file.')
    sys.exit(-1)
_CONFIG_PARSER = configparser.ConfigParser()
_CONFIG_PARSER.read(_CONFIG_FILE)


def get_logger(log_switch, log_file, log_name):
    log_format = logging.Formatter('[%(asctime)s]{0}: %(message)s'.format(log_name))
    logger = logging.getLogger(name=log_name)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_format)
    stream_handler.setLevel(logging.WARNING)
    logger.addHandler(stream_handler)
    if log_switch:
        file_handler = logging.handlers.TimedRotatingFileHandler(filename=log_file,
                                                                 encoding='utf8', when='W0', backupCount=7)
        file_handler.setFormatter(log_format)
        file_handler.setLevel(logging.ERROR)
        logger.addHandler(file_handler)
    return logger


class Config:
    CSRF_ENABLED = True
    SECRET_KEY = os.urandom(32)
    LOCALHOST = '127.0.0.1'
    SHORT_STR_LEN = 64
    LONG_STR_LEN = 1024
    EXPIRATION_TIME = 3600
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SYS_HOST = _CONFIG_PARSER.get('SYSTEM', 'SYS_HOST')
    SYS_PORT = _CONFIG_PARSER.getint('SYSTEM', 'SYS_PORT')
    SYS_DEBUG = _CONFIG_PARSER.getboolean('SYSTEM', 'SYS_DEBUG')
    SYS_ADMIN = _CONFIG_PARSER.get('SYSTEM', 'SYS_ADMIN')
    SYS_ARTICLE_PER_PAGE = _CONFIG_PARSER.getint('SYSTEM', 'SYS_ITEMS_PER_PAGE')
    SYS_FOLLOWERS_PER_PAGE = _CONFIG_PARSER.getint('SYSTEM', 'SYS_FOLLOWERS_PER_PAGE')
    SYS_COMMENTS_PER_PAGE = _CONFIG_PARSER.getint('SYSTEM', 'SYS_COMMENTS_PER_PAGE')
    SYS_SLOW_QUERY_TIME = _CONFIG_PARSER.getfloat('SYSTEM', 'SYS_SLOW_QUERY_TIME')

    SSL_CRT = _CONFIG_PARSER.get('SSL', 'SSL_CERT')
    SSL_KEY = _CONFIG_PARSER.get('SSL', 'SSL_KEY')

    MAIL_SERVER = _CONFIG_PARSER.get('MAIL', 'MAIL_SERVER')
    MAIL_PORT = _CONFIG_PARSER.getint('MAIL', 'MAIL_PORT')
    MAIL_USE_TLS = _CONFIG_PARSER.getboolean('MAIL', 'MAIL_TLS')
    MAIL_USERNAME = os.environ.get('MAIL_USR', None) or _CONFIG_PARSER.get('MAIL', 'MAIL_USR')
    MAIL_PASSWORD = os.environ.get('MAIL_PWD', None) or _CONFIG_PARSER.get('MAIL', 'MAIL_PWD')
    MAIL_ADMIN = MAIL_USERNAME + MAIL_SERVER[MAIL_SERVER.find('.'):]

    SITE_NAME = _CONFIG_PARSER.get('SITE', 'SITE_NAME')
    SITE_TITLE = _CONFIG_PARSER.get('SITE', 'SITE_TITLE')
    SITE_AUTHOR = _CONFIG_PARSER.get('SITE', 'SITE_AUTHOR')
    SITE_KEYWORDS = _CONFIG_PARSER.get('SITE', 'SITE_KEYWORDS')
    SITE_DESCRIPTION = _CONFIG_PARSER.get('SITE', 'SITE_DESCRIPTION')

    MYSQL_HOST = _CONFIG_PARSER.get('MYSQL', 'MYSQL_HOST')
    MYSQL_PORT = _CONFIG_PARSER.getint('MYSQL', 'MYSQL_PORT')
    MYSQL_DB = _CONFIG_PARSER.get('MYSQL', 'MYSQL_DB')
    MYSQL_USR = os.environ.get('MYSQL_USR', None) or _CONFIG_PARSER.get('MYSQL', 'MYSQL_USR')
    MYSQL_PWD = os.environ.get('MYSQL_PWD', None) or _CONFIG_PARSER.get('MYSQL', 'MYSQL_PWD')
    MYSQL_CHARSET = _CONFIG_PARSER.get('MYSQL', 'MYSQL_CHARSET')

    SSH_TUNNEL_SWITCH = _CONFIG_PARSER.getboolean('SSH_TUNNEL', 'SSH_TUNNEL_SWITCH')
    SSH_TUNNEL_PORT = _CONFIG_PARSER.getint('SSH_TUNNEL', 'SSH_TUNNEL_PORT')
    SSH_TUNNEL_USR = os.environ.get('SSH_TUNNEL_USR', None) or _CONFIG_PARSER.get('SSH_TUNNEL', 'SSH_TUNNEL_USR')
    SSH_TUNNEL_PWD = os.environ.get('SSH_TUNNEL_PWD', None) or _CONFIG_PARSER.get('SSH_TUNNEL', 'SSH_TUNNEL_PWD')

    CACHE_TYPE = 'redis' if _CONFIG_PARSER.getboolean('REDIS', 'REDIS_SWITCH') else 'simple'
    CACHE_REDIS_HOST = _CONFIG_PARSER.get('REDIS', 'REDIS_HOST')
    CACHE_REDIS_PORT = _CONFIG_PARSER.get('REDIS', 'REDIS_PORT')
    CACHE_REDIS_DB = _CONFIG_PARSER.get('REDIS', 'REDIS_DB')

    LOG_SWITCH = _CONFIG_PARSER.getboolean('LOG', 'LOG_SWITCH')
    LOG_FILE = _CONFIG_PARSER.get('LOG', 'LOG_FILE')

    LOGGER = get_logger(LOG_SWITCH, LOG_FILE, SITE_NAME)
    MYSQL_CONN_STR = 'mysql+pymysql://{0}:{1}@{2}:{3}/{4}?charset={5}'
    SQLALCHEMY_DATABASE_URI = MYSQL_CONN_STR.format(MYSQL_USR, MYSQL_PWD, MYSQL_HOST, MYSQL_PORT,
                                                    MYSQL_DB, MYSQL_CHARSET)

    def __repr__(self):
        return '<%s : %s>' % (self.__class__.__name__, Config.__dict__)

    def __str__(self):
        return self.__repr__()

    @classmethod
    def init_app(cls, app):
        app.logger.addHandler(cls.LOGGER)


class TestingConfig(Config):
    SQLITE_PATH = _CONFIG_PARSER.get('SQLITE', 'SQLITE_PATH')
    SQLITE_DB = _CONFIG_PARSER.get('SQLITE', 'SQLITE_DB')

    DEBUG = False
    TESTING = True
    SQLITE_CONN_STR = 'sqlite:///{0}'
    SQLALCHEMY_DATABASE_URI = SQLITE_CONN_STR.format(os.path.join(SQLITE_PATH, SQLITE_DB))


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

    @classmethod
    def __get_mail_handler(cls):
        credentials, secure = None, None
        if getattr(cls, 'MAIL_USERNAME', None):
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = handlers.SMTPHandler(mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT), fromaddr=cls.MAIL_ADMIN,
                                            toaddrs=[cls.MAIL_ADMIN], subject=cls.SITE_NAME + ' ERROR MESSGAE',
                                            credentials=credentials, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        return mail_handler

    @classmethod
    def init_app(cls, app):
        super().init_app(app)
        Config.init_app(app)
        app.logger.addHandler(cls.__get_mail_handler())


config = {
    'testing': TestingConfig,
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
