#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import os
import requests
import urllib.parse
from bs4 import BeautifulSoup

from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, current_app, abort, make_response, url_for, flash, jsonify, Response, send_file

from ..utility import redirect_save, redirect_back, browse_directory, import_user_media, MediaType, VIDEO_SUFFIXES, IMAGE_SUFFIXES
from ..models import User, Article, Media, Resource
from .forms import ArticleForm, ResourceForm, DirectoryForm


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
        return redirect_back('main.index')
    return render_template('main/view_article.html', article=article, is_self=(current_user==article.author))

@bp_main.route('/articles')
@login_required
def articles():
    return render_template('main/articles.html', user=current_user, is_self=True)

@bp_main.route('/new_article', methods=['GET', 'POST'])
@login_required
def new_article():
    form = ArticleForm()
    if form.validate_on_submit():
        article = Article.add_article(user_id=current_user.id, title=form.title.data, content=form.content.data, is_public=form.is_public.data)
        if article:
            return redirect_back('main.article', article_url=article.url)
        else:
            flash('Failed to post the article!')
            return redirect_back(redirect_before=True)
    redirect_save(request.referrer)
    return render_template('main/edit_article.html', form=form)

@bp_main.route('/article/<article_url>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_url):
    article = Article.query.filter(Article.url == article_url).first()
    if not article or article.user_id != current_user.id:
        flash('Failed to find the article!')
        return redirect_back('main.index')
    form = ArticleForm()
    if form.validate_on_submit():
        article = Article.edit_article(article_id=article.id, title=form.title.data, content=form.content.data, is_public=form.is_public.data)
        if article:
            return redirect_back('main.article', article_url=article.url)
        else:
            flash('Failed to post the article!')
            return redirect_back(redirect_before=True)
    form.title.data = article.title
    form.content.data = article.content
    form.is_public.data = article.is_public
    redirect_save(request.referrer)
    return render_template('main/edit_article.html', form=form)

@bp_main.route('/article/<article_url>/delete')
@login_required
def delete_article(article_url):
    article = Article.query.filter(Article.url == article_url).first()
    if not article or article.user_id != current_user.id or not Article.delete_article(article_id=article.id):
        flash('Failed to find the article!')
    else:
        flash('Article ' + article.title +' is deleted!')
    return redirect_back('main.articles')

@bp_main.route('/medias')
@login_required
def medias():
    return render_template('main/medias.html', current_path=current_user.name)

def _get_original_path():
    return current_app.config.get('SYS_MEDIA_ORIGINAL')

def _get_thumbnail_path():
    return current_app.config.get('SYS_MEDIA_THUMBNAIL')

def _get_full_path(current_path, current_user):
    base_path = _get_original_path()
    root = current_path.split(os.sep)[0]
    if not current_user.is_authenticated or root != current_user.name:
        return None
    full_path = os.path.join(base_path, current_path)
    if os.path.isdir(full_path):
        return full_path
    return None

@bp_main.route('/medias/<path:current_path>')
@login_required
def show_medias(current_path):
    if not _get_full_path(current_path, current_user):
        return redirect_back()
    return render_template('main/medias.html', current_path=current_path)

@bp_main.route('/manage_medias/<path:current_path>', methods=['GET', 'POST'])
@login_required
def manage_medias(current_path):
    full_path = _get_full_path(current_path, current_user)
    if not full_path:
        return redirect_back()
    dirs = browse_directory(full_path)
    files = Media.query.filter(Media.path==current_path).order_by(Media.filename.asc()).all()
    form = DirectoryForm()
    if form.validate_on_submit():
        target_dir = form.directory_name.data
        target_path = os.path.join(full_path, target_dir)
        os.makedirs(target_path, mode=0o775, exist_ok=True)
        dirs.append(target_dir)
        dirs.sort()
        flash('Directory ' + os.path.join(current_path, target_dir) + ' is added successfully!')
    return render_template('main/medias.html', current_path=current_path, form=form, dirs=dirs, files=files)

@bp_main.route('/upload/<path:current_path>', methods=['POST'])
@login_required
def upload(current_path):
    result_dict = dict()
    full_path = _get_full_path(current_path, current_user)
    if not full_path:
        return make_response('forbidden', 403)
    is_public = True if request.form.get('is_public') else False
    upload_files = request.files
    for item in upload_files:
        file = upload_files.get(item)
        filename = file.filename
        if not filename:
            return make_response('bad request', 400)
        full_path_name = os.path.join(full_path, filename)
        file.save(full_path_name)
        if not os.path.isfile(full_path_name):
            return make_response('file not found', 404)
        media = import_user_media(full_path_name, is_public, current_user.query_user_media, current_user.add_user_media)
        if not media:
            return make_response('internal error', 500)
        result_dict[filename] = media.uuidname
    return make_response(jsonify(result_dict), 200)

@bp_main.route('/file/<filename>')
def get_file(filename):
    as_attachment = bool(request.args.get('download', 'no') == 'yes')
    media = Media.query.filter(Media.uuidname == filename).first()
    if not media or (not media.is_public and (not current_user.is_authenticated or current_user.name != media.author.name)):
        return Response('', status=204, mimetype='text/xml')
    full_path_name = os.path.join(_get_original_path(), media.path, media.filename)
    download_name = filename if not as_attachment else media.filename
    if not os.path.isfile(full_path_name):
        return Response('', status=204, mimetype='text/xml')
    return send_file(full_path_name, as_attachment=as_attachment, download_name=download_name)

@bp_main.route('/thumbnail/<filename>')
def get_thumbnail(filename):
    uuid = os.path.splitext(os.path.basename(filename))[0]
    media = Media.query.filter(Media.uuidname.like(f'{uuid}%')).first()
    if not media or media.media_type < MediaType.IMAGE or (not media.is_public and (not current_user.is_authenticated or current_user.name != media.author.name)):
        return Response('', status=204, mimetype='text/xml')
    if media.media_type == MediaType.VIDEO:
        media_filename = os.path.splitext(media.filename)[0] + IMAGE_SUFFIXES[0]
    else:
        media_filename = media.filename
    full_path_name = os.path.join(_get_thumbnail_path(), media.path, media_filename)
    if not os.path.isfile(full_path_name):
        return Response('', status=204, mimetype='text/xml')
    return send_file(full_path_name, as_attachment=False, download_name=filename)

def _delete_file(media):
    full_path_name = os.path.join(_get_original_path(), media.path, media.filename)
    if os.path.isfile(full_path_name):
        os.remove(full_path_name)
    if media.media_type == MediaType.VIDEO:
        thumbnail_filename = os.path.splitext(media.filename)[0] + IMAGE_SUFFIXES[0]
    else:
        thumbnail_filename = media.filename
    full_path_name = os.path.join(_get_thumbnail_path(), media.path, thumbnail_filename)
    if os.path.isfile(full_path_name):
        os.remove(full_path_name)

def _delete_directory(path):
    full_path_name = os.path.join(_get_original_path(), path)
    if os.path.isdir(full_path_name):
        os.removedirs(full_path_name)
    full_path_name = os.path.join(_get_thumbnail_path(), path)
    if os.path.isdir(full_path_name):
        os.removedirs(full_path_name)

@bp_main.route('/delete', methods=['POST'])
def delete_dropzone_file():
    filename = request.get_json().get('filename', '')
    if not current_user.is_authenticated:
        return 'bad request', 400
    media = Media.query.filter(Media.uuidname == filename).first()
    if not media:
        return jsonify('succesd')
    if media.author.name != current_user.name:
        return 'file not found', 404
    if not Media.delete_media(media.uuidname):
        return 'internal error', 500
    _delete_file(media)
    return jsonify('succeed')

@bp_main.route('/delete_directory/<path:current_path>', methods=['GET'])
@login_required
def delete_media_directory(current_path):
    full_path = _get_full_path(current_path, current_user)
    if not full_path:
        return redirect_back()
    medias = Media.query.filter(Media.path.like(f'{current_path}%')).all()
    for media in medias:
        if not media or media.author.name != current_user.name or not Media.delete_media(media.uuidname):
            flash('Failed to delete media directory {}!'.format(current_path))
            break
        else:
            _delete_file(media)
    else:
        _delete_directory(current_path)
        flash('Media directory ' + current_path + ' is deleted!')
    return redirect_back()

@bp_main.route('/delete/<filename>', methods=['GET'])
@login_required
def delete_media(filename):
    media = Media.query.filter(Media.uuidname == filename).first()
    if not media or media.author.name != current_user.name or not Media.delete_media(media.uuidname):
        flash('Failed to delete media {}!'.format(media.filename))
    else:
        _delete_file(media)
        flash('Media ' + media.filename +' is deleted!')
    return redirect_back()

@bp_main.route('/resourcesl')
@bp_main.route('/resources')
@login_required
def resources():
    user_resources = Resource.query.filter(Resource.user_id == current_user.id).order_by(Resource.rank.desc(), Resource.id.asc())
    json_resources = [resource.to_json() for resource in user_resources]
    categories = sorted(list(set([resource['category'] for resource in json_resources])))
    resources = {category: [] for category in categories}
    for resource in json_resources:
        resources[resource['category']].append(resource)
    local_icon = request.url.endswith('resourcesl')
    return render_template('main/resources.html', resources=resources, local_icon=local_icon)

@bp_main.route('/manage_resources', methods=['GET', 'POST'])
@login_required
def manage_resources():
    form = ResourceForm()
    if form.validate_on_submit():
        if Resource.add_resource(current_user.id, form.uri.data, form.rank.data, form.title.data, form.category.data):
            flash('Resource is added successfully!')
        else:
            flash('Failed to add resource!')
    columns = list(Resource(id=-1, uri=request.url_root).to_json().keys())
    return render_template('main/resources.html', columns=columns, form=form)

@bp_main.route('/delete_resource/<resource_id>')
@login_required
def delete_resource(resource_id):
    resource = Resource.query.filter(Resource.id == resource_id).first()
    if not resource or resource.user_id != current_user.id or not Resource.delete_resource(resource_id=resource_id):
        flash('Failed to delete the resource:[{}][{}]!'.format(resource.title, resource.uri))
    else:
        flash('Resource ' + resource.title + ' ' + resource.uri +' is deleted!')
    return redirect_back()

@bp_main.route('/proxy', methods=['POST', 'GET', 'OPTIONS'])
@login_required
def proxy():
    try:
        url = request.args.get('url', None)
        if request.method == 'POST':
            rsp = requests.post(url, data=request.form, allow_redirects=True)
        elif request.method == 'GET':
            if not url:
                return render_template('main/proxy.html')
            rsp = requests.get(url, allow_redirects=True)
        else:
            url = None
            rsp = Response()
        rsp.raise_for_status()
        rsp.headers['Access-Control-Allow-Origin'] = '*'
        rsp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        rsp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        if request.method != 'GET' and request.method != 'POST':
            return rsp
        content_type = rsp.headers.get('Content-Type', 'text/html')
        headers = dict(rsp.headers)
        headers.pop('X-Frame-Options', None)
        headers.pop('Content-Security-Policy', None)
        if 'text/html' in content_type or 'text/javascript' in content_type:
            soup = BeautifulSoup(rsp.content, 'html.parser')
            for tag in soup.find_all(['a', 'link', 'form'], href=True):
                tag['href'] = f'/proxy?url={urllib.parse.quote_plus(urllib.parse.urljoin(url, tag["href"]))}'
            for form in soup.find_all(['form'], action=True):
                form['action'] = f'/proxy?url={urllib.parse.quote_plus(urllib.parse.urljoin(url, form["action"]))}'
            for tag in soup.find_all(['img', 'script', 'link'], src=True):
                tag['src'] = f'/proxy?url={urllib.parse.quote_plus(urllib.parse.urljoin(url, tag["src"]))}'
            return Response(str(soup), headers=headers, content_type=content_type)
        else:
            return Response(rsp.content, headers=headers, content_type=content_type)
    except requests.RequestException as e:
        current_app.logger.info(f'failed to request {url}, {str(e)}.')
        return render_template('main/proxy.html')
    except Exception as e:
        current_app.logger.info(f'failed to proxy {url}, {str(e)}.')
        return render_template('main/proxy.html')


@bp_main.route('/about')
def about():
    return render_template('main/about.html')

@bp_main.route('/search', methods=['POST'])
def search():
    keywords = request.form.get('search', None)
    if not keywords:
        return redirect_back()
    keywords = '+'.join(keywords.split())
    return render_template('main/search.html', keywords=keywords)

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
    response.set_cookie('theme', theme_name)
    return response

