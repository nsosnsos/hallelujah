# !/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import configparser
import logging
from logging import handlers


CONFIG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'site.conf')

SHORT_STR_LEN = 64
LONG_STR_LEN = 1024
EXPIRATION_TIME = 3600


if not os.path.isfile(CONFIG_FILE):
    print('Error: missing site config file.')
    sys.exit(-1)
config = configparser.ConfigParser()
config.read(CONFIG_FILE)


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
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SYS_HOST = config.get('SYSTEM', 'SYS_HOST')
    SYS_PORT = config.getint('SYSTEM', 'SYS_PORT')
    SYS_DEBUG = config.getboolean('SYSTEM', 'SYS_DEBUG')
    SYS_ARTICLE_PER_PAGE = config.getint('SYSTEM', 'SYS_ITEMS_PER_PAGE')
    SYS_FOLLOWERS_PER_PAGE = config.getint('SYSTEM', 'SYS_FOLLOWERS_PER_PAGE')
    SYS_ADMIN = config.get('SYSTEM', 'SYS_ADMIN')

    MAIL_SERVER = config.get('MAIL', 'MAIL_SERVER')
    MAIL_PORT = config.getint('MAIL', 'MAIL_PORT')
    MAIL_USE_TLS = config.getboolean('MAIL', 'MAIL_TLS')
    MAIL_USERNAME = os.environ.get('MAIL_USR', None) or config.get('MAIL', 'MAIL_USR')
    MAIL_PASSWORD = os.environ.get('MAIL_PWD', None) or config.get('MAIL', 'MAIL_PWD')
    MAIL_ADMIN = MAIL_USERNAME + MAIL_SERVER[MAIL_SERVER.find('.'):]

    SITE_NAME = config.get('SITE', 'SITE_NAME')
    SITE_TITLE = config.get('SITE', 'SITE_TITLE')
    SITE_AUTHOR = config.get('SITE', 'SITE_AUTHOR')
    SITE_KEYWORDS = config.get('SITE', 'SITE_KEYWORDS')
    SITE_DESCRIPTION = config.get('SITE', 'SITE_DESCRIPTION')

    MYSQL_HOST = config.get('MYSQL', 'MYSQL_HOST')
    MYSQL_PORT = config.getint('MYSQL', 'MYSQL_PORT')
    MYSQL_DB = config.get('MYSQL', 'MYSQL_DB')
    MYSQL_USR = os.environ.get('MYSQL_USR', None) or config.get('MYSQL', 'MYSQL_USR')
    MYSQL_PWD = os.environ.get('MYSQL_PWD', None) or config.get('MYSQL', 'MYSQL_PWD')
    MYSQL_CHARSET = config.get('MYSQL', 'MYSQL_CHARSET')

    SSH_TUNNEL_SWITCH = config.getboolean('SSH_TUNNEL', 'SSH_TUNNEL_SWITCH')
    SSH_TUNNEL_PORT = config.getint('SSH_TUNNEL', 'SSH_TUNNEL_PORT')
    SSH_TUNNEL_USR = os.environ.get('SSH_TUNNEL_USR', None) or config.get('SSH_TUNNEL', 'SSH_TUNNEL_USR')
    SSH_TUNNEL_PWD = os.environ.get('SSH_TUNNEL_PWD', None) or config.get('SSH_TUNNEL', 'SSH_TUNNEL_PWD')

    CACHE_TYPE = 'redis' if config.getboolean('REDIS', 'REDIS_SWITCH') else 'simple'
    CACHE_REDIS_HOST = config.get('REDIS', 'REDIS_HOST')
    CACHE_REDIS_PORT = config.get('REDIS', 'REDIS_PORT')
    CACHE_REDIS_DB = config.get('REDIS', 'REDIS_DB')

    LOG_SWITCH = config.getboolean('LOG', 'LOG_SWITCH')
    LOG_FILE = config.get('LOG', 'LOG_FILE')

    LOGGER = get_logger(LOG_SWITCH, LOG_FILE, SITE_NAME)
    MYSQL_CONN_STR = 'mysql+pymysql://{0}:{1}@{2}:{3}/{4}?charset={5}'
    SQLALCHEMY_DATABASE_URI = MYSQL_CONN_STR.format(MYSQL_USR, MYSQL_PWD, MYSQL_HOST, MYSQL_PORT,
                                                    MYSQL_DB, MYSQL_CHARSET)

    def __repr__(self):
        return '<%s : %s>' % (self.__class__.__name__, Config.__dict__)

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def init_app(app):
        pass


class TestingConfig(Config):
    SQLITE_PATH = config.get('SQLITE', 'SQLITE_PATH')
    SQLITE_DB = config.get('SQLITE', 'SQLITE_DB')

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


config = {
    'testing': TestingConfig,
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
