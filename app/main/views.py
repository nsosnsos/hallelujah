# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import current_app, request, render_template

from . import main
from .. import db
from app.models import Article


@main.route('/')
@main.route('/index/')
def index():
    page_num = request.args.get('page', 1, type=int)
    pagination = Article.query.order_by(Article.create_datetime.desc())\
        .paginate(page_num, per_page=current_app.config['SYS_ARTICLE_PER_PAGE'], error_out=False)
    articles = pagination.items
    return render_template('index.html', articles=articles, pagination=pagination, endpoint='.index')


@main.route('/about/')
def about():
    return render_template('about.html')
