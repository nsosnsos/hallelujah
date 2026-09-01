#!/usr/bin/env python3
"""main views"""

import os
import shutil

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    jsonify,
    make_response,
    render_template,
    request,
    send_file,
)
from flask_login import current_user, login_required

from ..models import Article, Media, Resource, User
from ..utility import (
    IMAGE_SUFFIXES,
    MediaType,
    browse_directory,
    import_user_media,
    redirect_back,
    redirect_save,
)
from .forms import ArticleForm, DirectoryForm, ResourceForm

bp_main = Blueprint("main", __name__)


@bp_main.route("/")
def index():
    """index"""
    return render_template("main/articles.html", user=None, is_self=False)


@bp_main.route("/user/<user_name>")
def user(user_name):
    """user"""
    cur_user = User.query.filter(User.name == user_name).first_or_404()
    return render_template("main/user.html", user=cur_user)


@bp_main.route("/user_articles/<user_name>")
def user_articles(user_name):
    """user articles"""
    cur_user = User.query.filter(User.name == user_name).first_or_404()
    return render_template("main/articles.html", user=cur_user, is_self=False)


@bp_main.route("/article/<article_url>")
def article(article_url):
    """article"""
    cur_article = Article.query.filter(Article.url == article_url).first_or_404()
    if not cur_article.is_public and (not current_user.is_authenticated or cur_article.user_id != current_user.id):
        return redirect_back("main.index")
    return render_template(
        "main/view_article.html",
        article=cur_article,
        is_self=(current_user == cur_article.author),
    )


@bp_main.route("/articles")
@login_required
def articles():
    """articles"""
    return render_template("main/articles.html", user=current_user, is_self=True)


@bp_main.route("/new_article", methods=["GET", "POST"])
@login_required
def new_article():
    """new article"""
    form = ArticleForm()
    if form.validate_on_submit():
        cur_article = Article.add_article(
            user_id=current_user.id,
            title=form.title.data,
            content=form.content.data,
            is_public=form.is_public.data,
        )
        if cur_article:
            return redirect_back("main.article", article_url=cur_article.url)
        flash("Failed to post the article!")
        return redirect_back(redirect_before=True)
    redirect_save(request.referrer)
    return render_template("main/edit_article.html", form=form)


@bp_main.route("/article/<article_url>/edit", methods=["GET", "POST"])
@login_required
def edit_article(article_url):
    """edit article"""
    cur_article = Article.query.filter(Article.url == article_url).first()
    if not cur_article or cur_article.user_id != current_user.id:
        flash("Failed to find the article!")
        return redirect_back("main.index")
    form = ArticleForm()
    if form.validate_on_submit():
        cur_article = Article.edit_article(
            article_id=cur_article.id,
            title=form.title.data,
            content=form.content.data,
            is_public=form.is_public.data,
        )
        if cur_article:
            return redirect_back("main.article", article_url=cur_article.url)
        flash("Failed to post the article!")
        return redirect_back(redirect_before=True)
    form.title.data = cur_article.title
    form.content.data = cur_article.content
    form.is_public.data = cur_article.is_public
    redirect_save(request.referrer)
    return render_template("main/edit_article.html", form=form)


@bp_main.route("/article/<article_url>/delete")
@login_required
def delete_article(article_url):
    """delete article"""
    cur_article = Article.query.filter(Article.url == article_url).first()
    if (
        not cur_article
        or cur_article.user_id != current_user.id
        or not Article.delete_article(article_id=cur_article.id)
    ):
        flash("Failed to delete the article!")
    else:
        flash("Article " + cur_article.title + " is deleted!")
    return redirect_back("main.articles")


@bp_main.route("/medias")
@login_required
def medias():
    """medias"""
    return render_template("main/medias.html", current_path=current_user.name)


def _get_original_path():
    return current_app.config.get("SYS_MEDIA_ORIGINAL")


def _get_thumbnail_path():
    return current_app.config.get("SYS_MEDIA_THUMBNAIL")


def _get_full_path(current_path, cur_user):
    if not cur_user.is_authenticated:
        return None
    base_path = _get_original_path()
    user_path = os.path.realpath(os.path.join(base_path, cur_user.name))
    full_path = os.path.realpath(os.path.join(base_path, current_path))
    if full_path != user_path and not full_path.startswith(user_path + os.sep) and not os.path.isdir(full_path):
        return None
    return full_path


@bp_main.route("/medias/<path:current_path>")
@login_required
def show_medias(current_path):
    """show medias"""
    if not _get_full_path(current_path, current_user):
        return redirect_back()
    return render_template("main/medias.html", current_path=current_path)


@bp_main.route("/manage_medias/<path:current_path>", methods=["GET", "POST"])
@login_required
def manage_medias(current_path):
    """manage medias"""
    full_path = _get_full_path(current_path, current_user)
    if not full_path:
        return redirect_back()
    dirs = browse_directory(full_path)
    files = Media.query.filter(Media.path == current_path).order_by(Media.filename.asc()).all()
    form = DirectoryForm()
    if form.validate_on_submit():
        target_dir = form.directory_name.data
        target_path = os.path.join(full_path, target_dir)
        os.makedirs(target_path, mode=0o775, exist_ok=True)
        dirs.append(target_dir)
        dirs.sort()
        flash("Directory " + os.path.join(current_path, target_dir) + " is added successfully!")
    return render_template(
        "main/medias.html",
        current_path=current_path,
        form=form,
        dirs=dirs,
        files=files,
    )


@bp_main.route("/upload/<path:current_path>", methods=["POST"])
@login_required
def upload(current_path):
    """upload"""
    result_dict = {}
    full_path = _get_full_path(current_path, current_user)
    if not full_path:
        return make_response("forbidden", 403)
    is_public = bool(request.form.get("is_public"))
    upload_files = request.files
    for item in upload_files:
        file = upload_files.get(item)
        filename = file.filename
        if not filename:
            return make_response("bad request", 400)
        filename = os.path.basename(filename.replace("\\", "/"))
        if not filename or filename in (".", ".."):
            return make_response("bad request", 400)
        full_path_name = os.path.join(full_path, filename)
        if os.path.isfile(full_path_name):
            return make_response("file allready exists", 400)
        file.save(full_path_name)
        media = import_user_media(
            full_path_name,
            is_public,
            current_user.query_user_media,
            current_user.add_user_media,
        )
        if not media:
            return make_response("internal error", 500)
        result_dict[filename] = media.uuidname
    return make_response(jsonify(result_dict), 200)


@bp_main.route("/file/<filename>")
def get_file(filename):
    """get file"""
    as_attachment = bool(request.args.get("download", "no") == "yes")
    media = Media.query.filter(Media.uuidname == filename).first()
    if not media or (
        not media.is_public and (not current_user.is_authenticated or current_user.name != media.author.name)
    ):
        return Response("", status=204, mimetype="text/xml")
    full_path_name = os.path.join(_get_original_path(), media.path, media.filename)
    download_name = filename if not as_attachment else media.filename
    if not os.path.isfile(full_path_name):
        return Response("", status=204, mimetype="text/xml")
    return send_file(
        full_path_name,
        as_attachment=as_attachment,
        download_name=download_name,
    )


@bp_main.route("/thumbnail/<filename>")
def get_thumbnail(filename):
    """get thumbnail"""
    uuid = os.path.splitext(os.path.basename(filename))[0]
    media = Media.query.filter(Media.uuidname.like(f"{uuid}%")).first()
    if (
        not media
        or media.media_type < MediaType.IMAGE.value
        or (not media.is_public and (not current_user.is_authenticated or current_user.name != media.author.name))
    ):
        return Response("", status=204, mimetype="text/xml")
    if media.media_type == MediaType.VIDEO.value:
        media_filename = os.path.splitext(media.filename)[0] + IMAGE_SUFFIXES[0]
    else:
        media_filename = media.filename
    full_path_name = os.path.join(_get_thumbnail_path(), media.path, media_filename)
    if not os.path.isfile(full_path_name):
        return Response("", status=204, mimetype="text/xml")
    return send_file(full_path_name, as_attachment=False, download_name=filename)


def _delete_file(media):
    full_path_name = os.path.join(_get_original_path(), media.path, media.filename)
    if os.path.isfile(full_path_name):
        os.remove(full_path_name)
        current_app.logger.info(f"deleted file {full_path_name}")
    if media.media_type == MediaType.VIDEO.value:
        thumbnail_filename = os.path.splitext(media.filename)[0] + IMAGE_SUFFIXES[0]
    else:
        thumbnail_filename = media.filename
    full_path_name = os.path.join(_get_thumbnail_path(), media.path, thumbnail_filename)
    if os.path.isfile(full_path_name):
        os.remove(full_path_name)
        current_app.logger.info(f"deleted file {full_path_name}")


def _delete_directory(path):
    for base_path in (_get_original_path(), _get_thumbnail_path()):
        full_path_name = os.path.realpath(os.path.join(base_path, path))
        if os.path.isdir(full_path_name):
            shutil.rmtree(full_path_name, ignore_errors=True)
            current_app.logger.info(f"deleted directory {full_path_name}")


@bp_main.route("/delete", methods=["POST"])
def delete_dropzone_file():
    """delete dropzone file"""
    filename = request.get_json().get("filename", "")
    if not current_user.is_authenticated:
        return "bad request", 400
    media = Media.query.filter(Media.uuidname == filename).first()
    if not media:
        return jsonify("succesd")
    if media.author.name != current_user.name:
        return "file not found", 404
    if not Media.delete_media(media.uuidname):
        return "internal error", 500
    _delete_file(media)
    return jsonify("succeed")


@bp_main.route("/delete_directory/<path:current_path>", methods=["GET"])
@login_required
def delete_media_directory(current_path):
    """delete media directory"""
    full_path = _get_full_path(current_path, current_user)
    if not full_path:
        return redirect_back()
    matched_medias = Media.query.filter(Media.path.like(f"{current_path}%")).all()
    for media in matched_medias:
        if not media or media.author.name != current_user.name or not Media.delete_media(media.uuidname):
            flash(f"Failed to delete media directory {current_path}!")
            break
        _delete_file(media)
    else:
        _delete_directory(current_path)
        flash("Media directory " + current_path + " is deleted!")
    return redirect_back()


@bp_main.route("/delete/<filename>", methods=["GET"])
@login_required
def delete_media(filename):
    """delete media"""
    media = Media.query.filter(Media.uuidname == filename).first()
    if not media or media.author.name != current_user.name or not Media.delete_media(media.uuidname):
        flash(f"Failed to delete media {media.filename}!")
    else:
        _delete_file(media)
        flash("Media " + media.filename + " is deleted!")
    return redirect_back()


@bp_main.route("/resourcesl")
@bp_main.route("/resources")
@login_required
def resources():
    """resources"""
    user_resources = Resource.query.filter(Resource.user_id == current_user.id).order_by(
        Resource.rank.desc(), Resource.id.asc()
    )
    json_resources = [resource.to_json() for resource in user_resources]
    categories = sorted({resource["category"] for resource in json_resources})
    all_resources = {category: [] for category in categories}
    for resource in json_resources:
        all_resources[resource["category"]].append(resource)
    local_icon = request.url.endswith("resourcesl")
    return render_template("main/resources.html", resources=all_resources, local_icon=local_icon)


@bp_main.route("/manage_resources", methods=["GET", "POST"])
@login_required
def manage_resources():
    """manage resources"""
    form = ResourceForm()
    if form.validate_on_submit():
        if Resource.add_resource(
            current_user.id,
            form.uri.data,
            form.rank.data,
            form.title.data,
            form.category.data,
        ):
            flash("Resource is added successfully!")
        else:
            flash("Failed to add resource!")
    columns = list(Resource(id=-1, uri=request.url_root).to_json().keys())
    return render_template("main/resources.html", columns=columns, form=form)


@bp_main.route("/delete_resource/<resource_id>")
@login_required
def delete_resource(resource_id):
    """delete resources"""
    resource = Resource.query.filter(Resource.id == resource_id).first()
    if not resource or resource.user_id != current_user.id or not Resource.delete_resource(resource_id=resource_id):
        flash(f"Failed to delete the resource:[{resource.title}][{resource.uri}]!")
    else:
        flash("Resource " + resource.title + " " + resource.uri + " is deleted!")
    return redirect_back()


@bp_main.route("/about")
def about():
    """about"""
    return render_template("main/about.html")


@bp_main.route("/search", methods=["POST"])
def search():
    """search"""
    keywords = request.form.get("search", None)
    if not keywords:
        return redirect_back()
    keywords = "+".join(keywords.split())
    return render_template("main/search.html", keywords=keywords)


@bp_main.route("/theme", methods=["POST"])
def theme_switch():
    """theme switch"""
    status = request.form.get("toggle", False)
    theme_day = current_app.config.get("SYS_THEME_DAY")
    theme_night = current_app.config.get("SYS_THEME_NIGHT")
    new_theme = theme_night if status else theme_day
    response = make_response(redirect_back())
    response.set_cookie("theme", new_theme)
    return response


@bp_main.route("/theme/<theme_name>", methods=["GET"])
def theme_choose(theme_name):
    """theme choose"""
    themes = current_app.config.get("SYS_THEMES", {})
    if theme_name not in themes:
        abort(404)
    response = make_response(redirect_back())
    response.set_cookie("theme", theme_name)
    return response
