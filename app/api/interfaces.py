# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import jsonify, request, current_app, url_for

from ..models import User, Blog
from . import api
from .errors import page_not_found


@api.route('/users/<int:user_name>')
def get_user(user_name):
    user = User.query.get_or_404(user_name)
    return jsonify(user.to_json())


@api.route('users/<int:user_name>/blogs/')
def get_user_blogs(user_name):
    user = User.query.filter_by(name=user_name).first()
    if not user:
        return page_not_found('{} does not exists.'.format(user_name))
    page = request.args.get('page', 1, type=int)
    pagination = user.blogs.order_by(Blog.create_datetime.desc()).paginate(
        page, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    blogs = pagination.items
    prev_page = None
    if pagination.has_prev:
        prev_page = url_for('api.get_user_blogs', user_name=user_name, page=page - 1)
    next_page = None
    if pagination.has_next:
        next_page = url_for('api.get_user_blogs', user_name=user_name, page=page + 1)
    return jsonify({
        'blogs': [blog.to_json() for blog in blogs],
        'prev': prev_page,
        'next': next_page,
        'count': pagination.total,
    })


@api.route('users/<int:user_name>/followed_blogs/')
def get_user_followed_blogs(user_name):
    user = User.query.filter_by(name=user_name).first()
    if not user:
        return page_not_found('{} does not exists.'.format(user_name))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_blog.order_by(Blog.create_datetime.desc()).paginate(
        page, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    blogs = pagination.items
    prev_page = None
    if pagination.has_prev:
        prev_page = url_for('api.get_user_followed_blogs', user_name=user_name, page=page - 1)
    next_page = None
    if pagination.has_next:
        next_page = url_for('api.get_user_followed_blogs', user_name=user_name, page=page + 1)
    return jsonify({
        'blogs': [blog.to_json() for blog in blogs],
        'prev': prev_page,
        'next': next_page,
        'count': pagination.total,
    })
