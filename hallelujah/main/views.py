#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from flask_login import login_required, current_user
from flask import render_template, request, session, current_app, abort, make_response, redirect, url_for, flash

from ..utility import redirect_back, redirect_save
from ..models import User, Article, Media
from . import bp_main
from .forms import ArticleForm


@bp_main.route('/')
def index():
    return render_template('main/index.html')

@bp_main.route('/user/<user_name>')
def user(user_name):
    user = User.query.filter(User.name == user_name).first_or_404()
    return render_template('main/user.html', user=user)

@bp_main.route('/user_articles/<user_name>')
def user_articles(user_name):
    user = User.query.filter(User.name == user_name).first_or_404()
    return render_template('main/user_articles.html', user=user)

@bp_main.route('/article/<article_url>')
def article(article_url):
    article = Article.query.filter(Article.url == article_url).first_or_404()
    if not article.is_public and (not current_user.is_authenticated or article.user_id != current_user.id):
        return redirect(url_for('main.index', _external=True))
    return render_template('main/article.html', article=article)

@bp_main.route('/articles')
@login_required
def articles():
    return render_template('main/articles.html')

@bp_main.route('/new_article', methods=['GET', 'POST'])
@login_required
def new_article():
    if not current_user.is_authenticated:
        redirect(url_for('auth.login', _external=True))
    form = ArticleForm()
    if form.validate_on_submit():
        article = Article.add_article(user_id=current_user.id, title=form.title.data, content=form.content.data, is_public=form.is_public.data)
        if article:
            return redirect(url_for('main.article', article_url=article.url, _external=True))
        else:
            flash('Failed to post the article!')
            return redirect(url_for('main.index', _external=True))
    redirect_save(request.referrer)
    return render_template('main/new_article.html', form=form)

@bp_main.route('/medias')
def medias():
    return render_template('main/index.html')

@bp_main.route('/about')
def about():
    return render_template('main/index.html')

@bp_main.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        return redirect(url_for('main.index', _external=True))
    data = request.form.get('search', None)
    return render_template('main/search.html', data=data)

@bp_main.route('/theme', methods=['GET', 'POST'])
def theme_switch():
    if request.method == 'GET':
        return redirect(url_for('main.index', _external=True))
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

