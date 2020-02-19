# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import current_app, request, render_template

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
