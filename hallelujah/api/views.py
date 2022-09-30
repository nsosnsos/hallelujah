#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from sqlalchemy import and_
from flask_login import current_user
from flask import Blueprint, current_app, request, jsonify

from ..models import Article, User


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

