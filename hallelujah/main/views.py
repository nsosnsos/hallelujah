#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from flask_login import login_required
from flask import render_template, request, session, current_app, abort, make_response

from ..utility import redirect_back
from ..models import User, Article, Media
from . import bp_main

@bp_main.route('/')
def index():
    return render_template('index.html')

@bp_main.route('/user/<user_name>')
def user(user_name):
    user = User.query.filter(User.name == user_name).first_or_404()
    return render_template('user.html', user=user)

@bp_main.route('/user_articles/<user_name>')
def user_articles(user_name):
    user = User.query.filter(User.name == user_name).first_or_404()
    return render_template('user_articles.html', user=user)

@bp_main.route('/article/<article_url>')
def article(article_url):
    article = Article.query.filter(Article.url == article_url).first_or_404()
    return render_template('article.html', article=article)

@bp_main.route('/articles')
@login_required
def articles():
    return render_template('articles.html')

@bp_main.route('/medias')
def medias():
    return render_template('index.html')

@bp_main.route('/about')
def about():
    return render_template('index.html')

@bp_main.route('/search', methods=['POST'])
def search():
    data = request.form.get('search', None)
    return render_template('search.html', data=data)

@bp_main.route('/theme', methods=['POST'])
def theme_switch():
    status = request.form.get('toggle', False)
    theme_day = current_app.config.get('SYS_THEME_DAY')
    theme_night = current_app.config.get('SYS_THEME_NIGHT')
    new_theme = theme_night if status else theme_day
    response = make_response(redirect_back())
    response.set_cookie('theme', new_theme)
    return response

@bp_main.route('/theme/<theme_name>', methods=['GET'])
def theme_choose(theme_name):
    themes = current_app.config.get('SYS_THEMES', dict())
    if theme_name not in themes.keys():
        abort(404)
    response = make_response(redirect_back())
    response.set_cookie('theme', themes[theme_name])
    return response

