# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import jsonify, request, g, current_app, url_for

from .. import db
from ..models import User, Blog
from ..utilities import Permission
from . import api
from .authentication import permission_required
from .errors import page_not_found, forbidden


@api.route('/users/<name>')
def get_user(name):
    user = User.query.filter_by(name=name).first()
    if not user:
        return page_not_found('{} does not exists.'.format(name))
    return jsonify(user.to_json())


@api.route('users/<name>/blogs/')
def get_user_blogs(name):
    user = User.query.filter_by(name=name).first()
    if not user:
        return page_not_found('{} does not exists.'.format(name))
    page = request.args.get('page', 1, type=int)
    pagination = user.blogs.filter_by(is_private=False).order_by(Blog.create_datetime.desc()).paginate(
        page, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    blogs = pagination.items
    prev_page = None
    if pagination.has_prev:
        prev_page = url_for('api.get_user_blogs', name=name, page=page-1)
    next_page = None
    if pagination.has_next:
        next_page = url_for('api.get_user_blogs', name=name, page=page+1)
    return jsonify({
        'blogs': [blog.to_json() for blog in blogs],
        'prev': prev_page,
        'next': next_page,
        'count': pagination.total,
    })


@api.route('users/<name>/followed_blogs/')
def get_user_followed_blogs(name):
    user = User.query.filter_by(name=name).first()
    if not user:
        return page_not_found('{} does not exists.'.format(name))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_blog.order_by(Blog.create_datetime.desc()).paginate(
        page, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    blogs = pagination.items
    prev_page = None
    if pagination.has_prev:
        prev_page = url_for('api.get_user_followed_blogs', name=name, page=page-1)
    next_page = None
    if pagination.has_next:
        next_page = url_for('api.get_user_followed_blogs', name=name, page=page+1)
    return jsonify({
        'blogs': [blog.to_json() for blog in blogs],
        'prev': prev_page,
        'next': next_page,
        'count': pagination.total,
    })


@api.route('/blogs/')
def get_blogs():
    page = request.args.get('page', 1, type=int)
    pagination = Blog.query.filter_by(is_private=False).order_by(Blog.create_datetime.desc()).paginate(
        page, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    blogs = pagination.items
    prev_page = None
    if pagination.has_prev:
        prev_page = url_for('api.get_blogs', page=page-1)
    next_page = None
    if pagination.has_next:
        next_page = url_for('api.get_blogs', page=page+1)
    return jsonify({
        'blogs': [blog.to_json() for blog in blogs],
        'prev': prev_page,
        'next': next_page,
        'count': pagination.total,
    })


@api.route('/blogs/<int:blog_id>')
def get_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if blog.is_private and blog.user_id != g.current_user.id:
        return forbidden('Insufficient permissions')
    return jsonify(blog.to_json())


@api.route('/blogs/', methods=['POST'])
@permission_required(Permission.BLOG)
def new_blog():
    blog = Blog.from_json(request.json)
    blog.user_id = g.current_user.id
    db.session.add(blog)
    db.session.commit()
    return jsonify(blog.to_json())


@api.route('/blogs/<int:id>', methods=['PUT'])
@permission_required(Permission.BLOG)
def edit_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if g.current_user != blog.user_id or not g.current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permissions')
    blog.category_id = request.json.get('category_id', blog.category_id)
    blog.is_private = request.json.get('is_private', blog.is_private)
    blog.title = request.json.get('title', blog.title)
    blog.content = request.json.get('content', blog.content)
    db.session.add(blog)
    db.session.commit()
    return jsonify(blog.to_json())
