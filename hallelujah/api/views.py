#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from sqlalchemy import and_
from flask_login import current_user
from flask import Blueprint, current_app, request, jsonify

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
    resources = Resource.query.filter(Resource.user_id== user_id).order_by(Resource.rank.desc(), Resource.id.asc())
    return jsonify([resource.to_json() for resource in resources])

@bp_api.route('/modify_resource', methods=['POST'])
def modify_resource():
    if not current_user.is_authenticated:
        return jsonify([])
    data = request.get_json()
    ret = Resource.modify_resource(data, current_user)
    return jsonify([ret]) if ret else jsonify([])

