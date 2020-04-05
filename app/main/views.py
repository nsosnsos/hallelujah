# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import current_app, request, render_template

from ..utilities import split_key_words, string_to_url
from ..models import Blog
from ..api.ns_datanalysis import get_cur_func
from . import main


@main.route('/')
@main.route('/index/')
def index():
    page_num = request.args.get('page', 1, type=int)
    pagination = Blog.query.order_by(Blog.create_datetime.desc())\
        .paginate(page_num, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    blogs = pagination.items
    return render_template('index.html', blogs=blogs, pagination=pagination, endpoint='.index')


@main.route('/blog/')
def blog():
    page_title = ' '.join((current_app.config['SITE_NAME'], '-', get_cur_func()))
    return render_template('blog.html', page_title=page_title)


@main.route('/gallery/')
def gallery():
    page_title = ' '.join((current_app.config['SITE_NAME'], '-', get_cur_func()))
    return render_template('gallery.html', page_title=page_title)


@main.route('/diary/')
def diary():
    page_title = ' '.join((current_app.config['SITE_NAME'], '-', get_cur_func()))
    return render_template('diary.html', page_title=page_title)


@main.route('/about/')
def about():
    page_title = ' '.join((current_app.config['SITE_NAME'], '-', get_cur_func()))
    return render_template('about.html', page_title=page_title)


@main.route('/search/', methods=['GET', 'POST'])
def search():
    page_title = ' '.join((current_app.config['SITE_NAME'], '-', get_cur_func()))
    data = request.form.get('search', None)
    keywords = string_to_url(' '.join(split_key_words(data))) if data else None
    return render_template('search.html', page_title=page_title, keywords=keywords)
