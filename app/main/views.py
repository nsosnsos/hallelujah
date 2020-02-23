# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import current_app, request, render_template, redirect, url_for

from ..utilities import split_key_words, string_to_url
from . import main
from app.models import Blog


@main.route('/')
@main.route('/index')
def index():
    page_num = request.args.get('page', 1, type=int)
    pagination = Blog.query.order_by(Blog.create_datetime.desc())\
        .paginate(page_num, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    blogs = pagination.items
    return render_template('index.html', blogs=blogs, pagination=pagination, endpoint='.index')


@main.route('/about')
def about():
    return render_template('about.html')


@main.route('/search', methods=['GET', 'POST'])
def search():
    data = request.form.get('search', None)
    keywords = string_to_url(' '.join(split_key_words(data))) if data else None
    return render_template('search.html', keywords=keywords)
