#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import os
import datetime

from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, session, current_app, abort, make_response, redirect, url_for, flash, jsonify, Response

from ..utility import redirect_back, redirect_save
from ..models import User, Article, Media, Resource
from .forms import ArticleForm, ResourceForm


bp_main = Blueprint('main', __name__)

@bp_main.route('/')
def index():
    return render_template('main/articles.html', user=None, is_self=False)

@bp_main.route('/user/<user_name>')
def user(user_name):
    user = User.query.filter(User.name == user_name).first_or_404()
    return render_template('main/user.html', user=user)

@bp_main.route('/user_articles/<user_name>')
def user_articles(user_name):
    user = User.query.filter(User.name == user_name).first_or_404()
    return render_template('main/articles.html', user=user, is_self=False)

@bp_main.route('/article/<article_url>')
def article(article_url):
    article = Article.query.filter(Article.url == article_url).first_or_404()
    if not article.is_public and (not current_user.is_authenticated or article.user_id != current_user.id):
        return redirect(url_for('main.index', _external=True))
    return render_template('main/view_article.html', article=article, is_self=(current_user==article.author))

@bp_main.route('/articles')
@login_required
def articles():
    return render_template('main/articles.html', user=current_user, is_self=True)

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
    return render_template('main/edit_article.html', form=form)

@bp_main.route('/article/<article_url>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_url):
    if not current_user.is_authenticated:
        redirect(url_for('auth.login', _external=True))
    article = Article.query.filter(Article.url == article_url).first()
    if not article or article.user_id != current_user.id:
        flash('Failed to find the article!')
        return redirect_back()
    form = ArticleForm()
    if form.validate_on_submit():
        article = Article.edit_article(article_id=article.id, title=form.title.data, content=form.content.data, is_public=form.is_public.data)
        if article:
            return redirect(url_for('main.article', article_url=article.url, _external=True))
        else:
            flash('Failed to post the article!')
            return redirect(url_for('main.index', _external=True))
    redirect_save(request.referrer)
    form.title.data = article.title
    form.content.data = article.content
    form.is_public.data = article.is_public
    return render_template('main/edit_article.html', form=form)

@bp_main.route('/article/<article_url>/delete')
@login_required
def delete_article(article_url):
    if not current_user.is_authenticated:
        redirect(url_for('auth.login', _external=True))
    article = Article.query.filter(Article.url == article_url).first()
    if not article or article.user_id != current_user.id or not Article.delete_article(article_id=article.id):
        flash('Failed to find the article!')
    else:
        flash('Article ' + article.title +' is deleted!')
    return redirect_back()

def get_valid_path(path):
    root = path.split('/')[0]
    if root != 'public' and root != current_user.name:
        return None
    base = current_app.config.get('SYS_STORAGE')
    full_path = os.path.join(base, path)
    if not os.path.isdir(full_path):
        return None 
    return full_path

@bp_main.route('/medias', methods=['GET', 'POST'])
@login_required
def medias():
    return render_template('main/medias.html', path=None, manage_medias=False)

@bp_main.route('/medias/<path:path>', methods=['GET', 'POST'])
@login_required
def show_medias(path):
    full_path = get_valid_path(path)
    if not full_path:
        return redirect_back()
    return render_template('main/medias.html', path=path, manage_medias=False)

@bp_main.route('/manage_medias/<path:path>', methods=['GET', 'POST'])
@login_required
def manage_medias(path):
    full_path = get_valid_path(path)
    if not full_path:
        return redirect_back()
    return render_template('main/medias.html', path=path, manage_medias=True)

@bp_main.route('/resources')
@login_required
def resources():
    user_resources = Resource.query.filter(Resource.user_id == current_user.id).order_by(Resource.rank.desc(), Resource.id.asc())
    json_resources = [resource.to_json() for resource in user_resources]
    categories = sorted(list(set([resource['category'] for resource in json_resources])))
    resources = {category: [] for category in categories}
    for resource in json_resources:
        resources[resource['category']].append(resource)
    return render_template('main/resources.html', resources=resources)

@bp_main.route('/manage_resources', methods=['GET', 'POST'])
@login_required
def manage_resources():
    form = ResourceForm()
    if form.validate_on_submit():
        if Resource.add_resource(current_user.id, form.uri.data, form.rank.data, form.title.data, form.category.data):
            flash('Resource is added successfully!')
        else:
            flash('Resource is failed to be added!')
        return redirect(url_for('main.resources', _external=True))
    redirect_save(request.referrer)
    columns = list(Resource(id=-1, uri=request.url_root).to_json().keys())
    return render_template('main/resources.html', columns=columns, form=form)

@bp_main.route('/delete_resource/<resource_id>')
@login_required
def delete_resource(resource_id):
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login', _external=True))
    resource = Resource.query.filter(Resource.id == resource_id).first()
    if not resource or resource.user_id != current_user.id or not Resource.delete_resource(resource_id=resource_id):
        flash('Failed to find the resource!')
    else:
        flash('Resource ' + resource.title + ' ' + resource.uri +' is deleted!')
    return redirect_back()

@bp_main.route('/about')
def about():
    return render_template('main/about.html')

@bp_main.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        return redirect(url_for('main.index', _external=True))
    redirect_save(request.referrer)
    data = request.form.get('search', None)
    return render_template('main/search.html', data=data)

@bp_main.route('/upload', methods=['GET', 'POST'])
def upload():
    file = request.files.get('upload_file')
    if not file:
        res = {'success': False, 'message': 'file format error'}
    else:
        ext = os.path.splitext(file.filename)[1]
        filename = datetime.now().strftime('%Y%m%d%H%M%S') + ext
        file.save(os.path.join(current_app.config.get('SYS_UPLOAD'), filename))
        res = {'success': True, 'message': 'file upload success', 'url': url_for('main.file', filename=filename, _external=True)}
    return jsonify(res)

@bp_main.route('/file/<filename>')
def file(filename):
    with open(os.path.join(current_app.config.get('SYS_UPLOAD'), filename), 'rb') as f:
        return Response(f.read(), mimetype="image/jpeg")

@bp_main.route('/theme', methods=['GET', 'POST'])
def theme_switch():
    if request.method == 'GET':
        return redirect(url_for('main.index', _external=True))
    redirect_save(request.referrer)
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

