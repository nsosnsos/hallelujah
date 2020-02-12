# !/usr/bin/env python
# -*- coding:utf-8 -*-

import bleach
from markdown import markdown


def split_key_words(keywords):
    return keywords.replace(u',', ' ') \
        .replace(u';', ' ') \
        .replace(u'+', ' ') \
        .replace(u'；', ' ') \
        .replace(u'，', ' ') \
        .replace(u'　', ' ') \
        .split(' ')


def string_to_url(string):
    return string.replace(u' ', '+') \
        .replace(u',', '+') \
        .replace(u'　', '+') \
        .replace(u'，', '+')


def markdown2html(text):
    allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                    'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                    'h1', 'h2', 'h3', 'p', 'img']
    extensions = ['fenced_code', 'codehilite(css_class=highlight, linenums=true)', 'admonition', 'tables', 'extra']
    return bleach.linkify(bleach.clean(
        markdown(text, extensions=extensions, output_format='html5'), tags=allowed_tags, strip=True))


# noinspection PyUnusedLocal
def unused_param(*args, **kwargs):
    pass


class ValidationError(ValueError):
    pass
