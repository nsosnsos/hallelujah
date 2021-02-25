# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import jsonify, request, g, current_app, url_for

from .. import db
from ..models import User, Blog, Comment
from ..utilities import Permission
from . import api
from .authentication import permission_required
from .errors import page_not_found, forbidden, bad_request


@api.route('/get_user/<user_name>')
def get_user(user_name):
    user = User.query.filter_by(name=user_name).first()
    if not user:
        return page_not_found('{} does not exists.'.format(user_name))
    return jsonify(user.to_json())


def _get_user_blogs(user_name, api_name, page, only_followed=False, only_public=True):
    user = User.query.filter_by(name=user_name).first()
    if not user or (not only_followed and not only_public and user.id != g.current_user.id):
        return page_not_found('{} does not exists.'.format(user_name))
    if only_followed:
        pagination = user.followed_blogs.order_by(Blog.create_datetime.desc()).paginate(
            page, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    elif only_public:
        pagination = user.blogs.filter_by(is_private=False).order_by(Blog.create_datetime.desc()).paginate(
            page, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    else:
        pagination = user.blogs.order_by(Blog.create_datetime.desc()).paginate(
            page, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    blogs = pagination.items
    prev_page, next_page = None, None
    if pagination.has_prev:
        prev_page = url_for('.'.join(('api', api_name)), name=user_name, page=page-1)
    if pagination.has_next:
        next_page = url_for('.'.join(('api', api_name)), name=user_name, page=page+1)
    return jsonify({
        'blogs': [blog.digest_json() for blog in blogs],
        'prev': prev_page,
        'next': next_page,
        'count': pagination.total,
    })


@api.route('get_user_public_blogs/<name>')
def get_user_public_blogs(name):
    page = request.args.get('page', 1, type=int)
    return _get_user_blogs(name, get_user_public_blogs.__name__, page)


@api.route('get_user_all_blogs/<name>')
def get_user_all_blogs(name):
    page = request.args.get('page', 1, type=int)
    return _get_user_blogs(name, get_user_all_blogs.__name__, page, only_public=False)


@api.route('get_user_followed_blogs/<name>')
def get_user_followed_blogs(name):
    page = request.args.get('page', 1, type=int)
    return _get_user_blogs(name, get_user_all_blogs.__name__, page, only_followed=True)


@api.route('/get_blogs/')
def get_blogs():
    page = request.args.get('page', 1, type=int)
    pagination = Blog.query.filter_by(is_private=False).order_by(Blog.create_datetime.desc()).paginate(
        page, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    blogs = pagination.items
    prev_page, next_page = None, None
    if pagination.has_prev:
        prev_page = url_for('.'.join(('api', get_blogs.__name__)), page=page-1)
    if pagination.has_next:
        next_page = url_for('.'.join(('api', get_blogs.__name__)), page=page+1)
    return jsonify({
        'blogs': [blog.to_json() for blog in blogs],
        'prev': prev_page,
        'next': next_page,
        'count': pagination.total,
    })


@api.route('/get_blog/<title_url>')
def get_blog(title_url):
    blog = Blog.query.filter_by(title_url=title_url).first()
    if not blog or (blog.is_private and blog.user_id != g.current_user.id):
        return page_not_found('{} is not found'.format(title_url))
    return blog.to_json()


@api.route('/new_blog/', methods=['POST'])
@permission_required(Permission.BLOG)
def new_blog():
    blog = Blog.from_json(request.json)
    blog.user_id = g.current_user.id
    db.session.add(blog)
    db.session.commit()
    return jsonify(blog.to_json()), 201, \
        {'Location': url_for('.'.join(('api', get_blog.__name__)), title_url=blog.title_url)}


@api.route('/edit_blog/<title_url>', methods=['POST'])
@permission_required(Permission.BLOG)
def edit_blog(title_url):
    blog = Blog.query.filter_by(title_url=title_url).first()
    if not blog:
        return page_not_found('{} is not found'.format(title_url))
    if not (g.current_user.id == blog.user_id or g.current_user.can(Permission.ADMIN)):
        return forbidden('Insufficient permissions')
    blog.category_id = request.json.get('category_id', blog.category_id)
    blog.is_private = request.json.get('is_private', blog.is_private)
    blog.title = request.json.get('title', blog.title)
    blog.content = request.json.get('content', blog.content)
    db.session.add(blog)
    db.session.commit()
    return jsonify(blog.to_json()), 201,\
        {'Location': url_for('.'.join(('api', get_blog.__name__)), title_url=blog.title_url)}


@api.route('/delete_blog/<title_url>', methods=['POST'])
@permission_required(Permission.BLOG)
def delete_blog(title_url):
    confirm_url = request.json.get('title_url', None)
    if title_url != confirm_url:
        return bad_request('Inconsistent blog title_url')
    blog = Blog.query.filter_by(title_url=title_url).first()
    if not blog:
        return page_not_found('{} is not found'.format(title_url))
    if not (g.current_user.id == blog.user_id or g.current_user.can(Permission.ADMIN)):
        return forbidden('Insufficient permissions')
    db.session.delete(blog)
    db.session.commit()
    return jsonify({'delete_blog': title_url})


@api.route('/get_blog_comments/<title_url>')
def get_blog_comments(title_url):
    blog = Blog.query.filter_by(title_url=title_url).first()
    if not blog or blog.is_private:
        return page_not_found('{} is not found'.format(title_url))
    if not (g.current_user.id == blog.user_id or g.current_user.can(Permission.ADMIN)):
        return forbidden('Insufficient permissions')
    page = request.args.get('page', 1, type=int)
    pagination = blog.comments.filter(Comment.parent_id.isnot(None)).order_by(Comment.datetime.desc()).paginate(
        page, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    comments = pagination.items
    prev_page = None
    if pagination.has_prev:
        prev_page = url_for('.'.join(('api', get_blog_comments.__name__)), title_url=title_url, page=page-1)
    next_page = None
    if pagination.has_next:
        next_page = url_for('.'.join(('api', get_blog_comments.__name__)), title_url=title_url, page=page+1)
    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev_page,
        'next': next_page,
        'count': pagination.total,
    })


@api.route('/get_user_comments/<user_name>')
def get_user_comments(user_name):
    user = User.query.filter_by(name=user_name).first()
    if not user:
        return page_not_found('{} does not exists.'.format(user_name))
    if not (g.current_user.id == user.id or g.current_user.can(Permission.ADMIN)):
        return forbidden('Insufficient permissions')
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.filter_by(user_id=user.id).order_by(Comment.datetime.desc()).paginate(
        page, per_page=current_app.config['SYS_ITEMS_PER_PAGE'], error_out=False)
    comments = pagination.items
    prev_page, next_page = None, None
    if pagination.has_prev:
        prev_page = url_for('.'.join(('api', get_user_comments.__name__)), user_name=user_name, page=page-1)
    if pagination.has_next:
        next_page = url_for('.'.join(('api', get_user_comments.__name__)), user_name=user_name, page=page+1)
    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev_page,
        'next': next_page,
        'count': pagination.total,
    })


@api.route('/new_blog_comment/<title_url>', methods=['POST'])
@permission_required(Permission.COMMENT)
def new_blog_comment(title_url):
    blog = Blog.query.filter_by(title_url=title_url).first()
    if not blog or blog.is_private:
        return page_not_found('{} is not found'.format(title_url))
    if not (g.current_user.id == blog.user_id or g.current_user.can(Permission.ADMIN)):
        return forbidden('Insufficient permissions')
    comment = Comment.from_json(request.json)
    comment.user_id = g.current_user.id
    comment.blog_id = blog.id
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_json()), 201,\
        {'Location': url_for('.'.join(('api', get_blog.__name__)), title_url=title_url)}


@api.route('/delete_blog_comment/<int:comment_id>', methods=['POST'])
@permission_required(Permission.COMMENT)
def delete_blog_comment(comment_id):
    confirm_id = request.json.get('comment_id', None, type=int)
    if comment_id != confirm_id:
        return bad_request('Inconsistent comment id')
    comment = Comment.query.get(comment_id)
    if not comment:
        return page_not_found('Comment {} is not found'.format(comment_id))
    blog = Blog.query.get(comment.blog_id)
    if not blog:
        return page_not_found('Blog {} is not found'.format(blog.title_url))
    if not (g.current_user.id == comment.user_id or g.current_user.id == blog.user_id
            or g.current_user.can(Permission.ADMIN)):
        return forbidden('Insufficient permissions')
    db.session.delete(blog)
    db.session.commit()
    return jsonify({'delete_comment': comment_id})


@api.route('/get_blog_comment/<int:comment_id>', methods=['POST'])
def get_blog_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return jsonify(comment.to_json())
