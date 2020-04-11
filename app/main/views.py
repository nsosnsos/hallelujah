# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import current_app, request, render_template, flash, redirect, url_for
from flask_login import current_user
# noinspection PyProtectedMember
from flask_babel import _

from ..utilities import split_key_words, string_to_url
from ..models import Blog
from ..api.ns_datanalysis import get_cur_func
from . import main


@main.route('/')
@main.route('/index/')
def index():
    page_num = request.args.get('page', 1, type=int)
    if current_user.is_authenticated:
        blog_query = current_user.followed_blogs
    else:
        blog_query = Blog.query.filter(Blog.is_private == 0)
    paginations = blog_query.order_by(Blog.create_datetime.desc())\
        .paginate(page_num, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    return render_template('index.html', paginations=paginations)


@main.route('/blog/')
def blog():
    if not current_user.is_authenticated:
        flash(_('Please login first.'))
        return redirect(url_for('auth.login'))
    page_num = request.args.get('page', 1, type=int)
    blog_query = Blog.query.filter(Blog.user_id == current_user.id)
    paginations = blog_query.order_by(Blog.create_datetime.desc())\
        .paginate(page_num, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    return render_template('blog.html', paginations=paginations)


@main.route('/gallery/')
def gallery():
    if not current_user.is_authenticated:
        return render_template('gallery.html', page_title=None)
    page_title = ' '.join((current_app.config['SITE_NAME'], '-', get_cur_func()))
    return render_template('gallery.html', page_title=page_title)


@main.route('/diary/')
def diary():
    if not current_user.is_authenticated:
        return render_template('diary.html', page_title=None)
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
