#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from sqlalchemy import and_
from flask_login import current_user
from flask import Blueprint, current_app, request, jsonify

from ..extensions import db
from ..models import Article, User, Media, Resource


bp_api = Blueprint('api', __name__)

@bp_api.route('/get_articles')
def get_articles():
    offset = int(request.args.get('offset', 0)) if request.args else 0
    limit = current_app.config.get('ITEMS_PER_PAGE')
    articles = Article.query.filter(Article.is_public == True).order_by(Article.timestamp.desc()).offset(offset).limit(limit)
    return jsonify([article.to_json() for article in articles])

@bp_api.route('/get_user_articles')
def get_user_articles():
    user_name = request.args.get('name', '') if request.args else ''
    user = User.query.filter(User.name == user_name).first()
    user_id = user.id if user else -1
    offset = int(request.args.get('offset', 0)) if request.args else 0
    limit = current_app.config.get('ITEMS_PER_PAGE')
    articles = Article.query.filter(and_(Article.is_public == True, Article.user_id == user_id)).order_by(Article.timestamp.desc()).offset(offset).limit(limit)
    return jsonify([article.to_json() for article in articles])

@bp_api.route('/get_self_articles')
def get_self_articles():
    user_id = current_user.id if current_user.is_authenticated else -1
    offset = int(request.args.get('offset', 0)) if request.args else 0
    limit = current_app.config.get('ITEMS_PER_PAGE')
    articles = Article.query.filter(Article.user_id== user_id).order_by(Article.timestamp.desc()).offset(offset).limit(limit)
    return jsonify([article.to_json() for article in articles])

@bp_api.route('/get_self_medias')
def get_self_medias():
    user_id = current_user.id if current_user.is_authenticated else -1
    offset = int(request.args.get('offset', 0)) if request.args else 0
    limit = current_app.config.get('ITEMS_PER_PAGE')
    medias = Media.query.filter(Media.user_id== user_id).order_by(Media.timestamp.desc()).offset(offset).limit(limit)
    return jsonify([media.to_json() for media in medias])

@bp_api.route('/get_self_resources')
def get_self_resources():
    user_id = current_user.id if current_user.is_authenticated else -1
    query = Resource.query.filter(Resource.user_id== user_id)
    search = request.args.get('search')
    if search:
        query = query.filter(db.or_(
            Resource.uri.like(f'%{search}%'),
            Resource.category.like(f'%{search}%'),
            Resource.title.like(f'%{search}%')
        ));
    sort = request.args.get('sort')
    if sort:
        column_names = Resource.__table__.columns.keys()
        order_options = []
        for s in sort.split(','):
            direction = s[0]
            item = s[1:]
            if item in column_names:
                col = getattr(Resoure, item)
                if direction == '-':
                    col = col.desc()
                order_options.append(col)
        if order_options:
            query = query.order_by(*order_options)
    return jsonify([resource.to_json() for resource in query])

@bp_api.route('/modify_resource', methods=['POST'])
def modify_resource():
    if not current_user.is_authenticated:
        return jsonify([])
    data = request.get_json()
    ret = Resource.modify_resource(data, current_user)
    return jsonify([ret]) if ret else jsonify([])

