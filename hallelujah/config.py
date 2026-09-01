#!/usr/bin/env python3
"""config"""

import datetime
import json
import logging
import os
import re
import secrets
import sys
from dataclasses import dataclass
from logging import handlers as log_handler

import cachelib
import redis
import requests

_REQ_TIMEOUT = 10


def _is_valid_email(email):
    """is valid email"""
    regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    return re.fullmatch(regex, email)


def _get_themes(static_dir, is_local):
    """get themes"""
    try:
        if is_local:
            bootswatch_cfg_file = os.path.join(static_dir, "plugins/bootswatch/5.json")
            with open(bootswatch_cfg_file, "r", encoding="utf-8") as f:
                bootswatch_cfg = json.load(f)
                cdn_prefix = r"https://cdn.jsdelivr.net/npm/bootswatch@5.3.2/"
                themes = {
                    theme["name"]: theme["cssCdn"].replace(cdn_prefix, "plugins/bootswatch/")
                    for theme in bootswatch_cfg["themes"]
                }
        else:
            bootswatch_cfg_obj = requests.get(url="https://bootswatch.com/api/5.json", timeout=_REQ_TIMEOUT)
            themes = {theme["name"]: theme["cssCdn"] for theme in json.loads(bootswatch_cfg_obj.text)["themes"]}
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        requests.RequestException,
    ) as e:
        raise RuntimeError(f"Failed to load Bootswatch themes: {e!s}") from e
    return themes


class Config:
    """config"""

    ENV = "production"
    DEBUG = False
    TESTING = False

    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get("SECRET_KEY", None)
    MIN_STR_LEN = 4
    SHORT_STR_LEN = 64
    LONG_STR_LEN = 256
    MAX_STR_LEN = 512
    ITEMS_PER_PAGE = 30
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=7)
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SITE
    SITE_NAME = "hallelujah"
    SITE_DESCRIPTION = "In God We Trust"
    SITE_AUTHOR = "Stan Lee"

    # SYSTEM
    SYS_HOST = "127.0.0.1"
    SYS_PORT = 4100
    SYS_STATIC = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static")
    SYS_TEMPLATE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates")
    SYS_MEDIA = os.path.join(os.path.abspath(os.path.expanduser("~")), "data", "media")
    SYS_MEDIA_ORIGINAL = os.path.join(SYS_MEDIA, "original")
    SYS_MEDIA_THUMBNAIL = os.path.join(SYS_MEDIA, "thumbnail")
    SYS_MEDIA_THUMBNAIL_HEIGHT = 200
    SYS_MEDIA_EXCLUDES = "public,private"
    SYS_REGISTER = False
    SYS_SQLITE = False
    SYS_LOCAL_DEPLOY = True
    SYS_THEMES = _get_themes(SYS_STATIC, SYS_LOCAL_DEPLOY)
    SYS_THEME_DAY = "United"
    SYS_THEME_NIGHT = "Darkly"
    SYS_REQ_TIMEOUT = _REQ_TIMEOUT

    # BLUEMAP
    AUTH_URL_PREFIX = "/auth"
    API_URL_PREFIX = "/api"

    # DROPZONE
    DROPZONE_PARALLEL_UPLOADS = 100
    DROPZONE_MAX_FILE_SIZE = 1024 * 1024 * 1024

    # PROXY
    PROXY_STORAGE = os.path.join(os.path.abspath(os.path.expanduser("~")), "data", "proxy")
    PROXY_BROWSER_TYPE = "chrome"
    PROXY_COLLECTION_CLEANUP_DAYS = 30
    PROXY_VERIFY_SSL = True

    # MAIL PORT CONFIG: 465 for SSL, 587 for TLS
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_ADDRESS = os.environ.get("MAIL_ADDRESS", None) or "MAIL_ADDRESS@SERVER.COM"
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", None) or "MAIL_PASSWORD"
    if not _is_valid_email(MAIL_ADDRESS):
        print("Invalid MAIL_ADDRESS.")
        sys.exit(-1)
    domain_start_index = MAIL_ADDRESS.find("@") + 1
    MAIL_SERVER = "smtp." + MAIL_ADDRESS[domain_start_index:]

    # DATABASE
    DB_HOST = SYS_HOST
    DB_PORT = 3306
    DB_NAME = SITE_NAME
    DB_USERNAME = os.environ.get("DB_USERNAME", None) or SITE_NAME
    DB_PASSWORD = os.environ.get("DB_PASSWORD", None) or SITE_NAME
    DB_CHARSET = "utf8mb4"

    # SQLITE
    SQLITE_PATH = os.path.dirname(os.path.realpath(__file__))
    SQLITE_DB = "sqlite.db"

    # REDIS
    REDIS_HOST = SYS_HOST
    REDIS_PORT = 6379

    # SESSION
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.from_url("redis://" + REDIS_HOST + ":" + str(REDIS_PORT))
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    # SSH TUNNEL
    SSH_TUNNEL_SWITCH = False
    SSH_TUNNEL_PORT = 22
    SSH_TUNNEL_USERNAME = os.environ.get("SSH_TUNNEL_USERNAME", None) or "SSH_TUNNEL_USERNAME"
    SSH_TUNNEL_PASSWORD = os.environ.get("SSH_TUNNEL_PASSWORD", None) or "SSH_TUNNEL_PASSWORD"

    # LOGGER
    LOG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), SITE_NAME + ".log")
    LOGGER = None

    # DATABASE
    MDB_CONN_STR = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset={DB_CHARSET}"
    SQLITE_CONN_STR = "sqlite:///" + os.path.join(SQLITE_PATH, SQLITE_DB)
    SQLALCHEMY_DATABASE_URI = SQLITE_CONN_STR if SYS_SQLITE else MDB_CONN_STR

    def __repr__(self):
        return f"<{self.__class__.__name__} : Config.__dict__>"

    def __str__(self):
        return self.__repr__()

    @classmethod
    def _get_logger(cls):
        log_format = logging.Formatter("[%(levelname)s][%(asctime)s]: %(message)s")
        logger = logging.getLogger(name=cls.SITE_NAME)
        logger.setLevel(logging.DEBUG)

        if cls.DEBUG:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(log_format)
            stream_handler.setLevel(logging.INFO)
            logger.addHandler(stream_handler)
        else:
            file_handler = log_handler.TimedRotatingFileHandler(
                filename=cls.LOG_FILE,
                encoding="utf8",
                when="W0",
                backupCount=7,
            )
            file_handler.setFormatter(log_format)
            file_handler.setLevel(logging.INFO)
            logger.addHandler(file_handler)

        return logger

    @classmethod
    def init_app(cls, app):
        """init app"""
        if not cls.LOGGER:
            cls.LOGGER = cls._get_logger()
        app.logger = cls.LOGGER


@dataclass
class TestingConfig(Config):
    """testing config"""

    ENV = "testing"
    TESTING = True
    SYS_SQLITE = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SESSION_TYPE = "cachelib"
    SESSION_CACHELIB = cachelib.simple.SimpleCache()
    SYS_LOCAL_DEPLOY = False
    SECRET_KEY = secrets.token_hex(16)


@dataclass
class DevelopmentConfig(Config):
    """development config"""

    ENV = "development"
    DEBUG = True
    SESSION_TYPE = "cachelib"
    SESSION_CACHELIB = cachelib.simple.SimpleCache()


@dataclass
class ProductionConfig(Config):
    """production config"""

    @classmethod
    def __get_mail_handler(cls):
        credentials, secure = None, None
        if getattr(cls, "MAIL_ADDRESS", None):
            credentials = (cls.MAIL_ADDRESS, cls.MAIL_PASSWORD)
            if getattr(cls, "MAIL_USE_TLS", None):
                secure = ()
        mail_handler = log_handler.SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.MAIL_ADDRESS,
            toaddrs=[cls.MAIL_ADDRESS],
            subject=cls.SITE_NAME + " message",
            credentials=credentials,
            secure=secure,
        )
        mail_handler.setLevel(logging.ERROR)
        return mail_handler

    @classmethod
    def init_app(cls, app):
        super().init_app(app)
        app.logger.addHandler(cls.__get_mail_handler())


configs = {
    "testing": TestingConfig,
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": ProductionConfig,
}
