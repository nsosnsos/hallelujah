#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import os
import cv2
import bleach
import datetime
import subprocess
from PIL import Image, ExifTags
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from threading import Thread
from markdown import markdown
from flask import current_app, request, redirect, url_for, session
from flask_mail import Message

from .extensions import mail


class MediaType:
    OTHER = 0
    MUSIC = 1
    IMAGE = 2
    VIDEO = 3


MUSIC_SUFFIXES = ['.mp3', '.wav']
IMAGE_SUFFIXES = ['.jpg', '.jpeg', '.png', '.gif']
VIDEO_SUFFIXES = ['.mp4', '.mov', '.m4v']
EXIF_TAG_MAP = {ExifTags.TAGS[tag]: tag for tag in ExifTags.TAGS}


def markdown_to_html(text):
    extensions = ['fenced_code', 'admonition', 'tables', 'extra']
    return bleach.linkify(markdown(text, extensions=extensions, output_format='html5'))


def get_request_ip(request):
    return request.headers.get('Cf-Connecting-Ip') or request.headers.get('X-Real-Ip') or request.remote_addr


def redirect_back(endpoint=None, redirect_before=False, **kwargs):
    if endpoint:
        target_url = url_for(endpoint, **kwargs, _external=True)
        return redirect(target_url)
    if redirect_before and 'url' in session:
        return redirect(session['url'])
    if request.referrer and request.referrer != request.url:
        return redirect(request.referrer)
    return redirect(url_for('main.index', _external=True))


def redirect_save(url=None):
    if not url:
        url = url_for('main.index', _external=True)
    session['url'] = url


def mariadb_is_in_use():
    return current_app.config.get('SYS_MARIADB')


def mariadb_backup():
    db_usr = current_app.config.get('MARIADB_USERNAME')
    db_pwd = current_app.config.get('MARIADB_PASSWORD')
    db_name = current_app.config.get('MARIADB_DB')
    data_directory = os.path.join(os.path.join(current_app.config.get('SYS_MEDIA'), '..'))
    target_db = os.path.join(data_directory, db_name + '.sql')
    command = f'mariadb-dump -u{db_usr} -p\'{db_pwd}\' --databases \'{db_name}\' > {target_db}'
    try:
        ret = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        current_app.logger.error('mariadb_backup failed: {}'.format(str(e)))
    return ret.returncode == 0 and ret.stdout.decode() != ''


def mariadb_restore():
    db_usr = current_app.config.get('MARIADB_USERNAME')
    db_pwd = current_app.config.get('MARIADB_PASSWORD')
    db_name = current_app.config.get('MARIADB_DB')
    data_directory = os.path.join(os.path.join(current_app.config.get('SYS_MEDIA'), '..'))
    target_db = os.path.join(data_directory, db_name + '.sql')
    command = f'mariadb -u{db_usr} -p\'{db_pwd}\' \'{db_name}\' < {target_db}'
    try:
        ret = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        current_app.logger.error('mariadb_backup failed: {}'.format(str(e)))
    return ret.returncode == 0 and ret.stdout.decode() != ''


def mariadb_is_exist_db(db_name=None):
    db_usr = current_app.config.get('MARIADB_USERNAME')
    db_pwd = current_app.config.get('MARIADB_PASSWORD')
    if not db_name:
        db_name = current_app.config.get('MARIADB_DB')
    command = f'mariadb -u {db_usr} -p\'{db_pwd}\' -e \"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME=\'{db_name}\';\"'
    try:
        ret = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        current_app.logger.error('mariadb_is_exist_database: {}'.format(str(e)))
    return ret.returncode == 0 and ret.stdout.decode() != ''


def mariadb_drop_db(db_name=None):
    db_usr = current_app.config.get('MARIADB_USERNAME')
    db_pwd = current_app.config.get('MARIADB_PASSWORD')
    if not db_name:
        db_name = current_app.config.get('MARIADB_DB')
    command = f'mariadb -u {db_usr} -p\'{db_pwd}\' -e \"DROP DATABASE IF EXISTS {db_name};\"'
    try:
        ret = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        current_app.logger.error('mariadb_drop_database: {}'.format(str(e)))
    return ret.returncode == 0 and ret.stdout.decode() != ''


def mariadb_create_db(db_name=None):
    db_usr = current_app.config.get('MARIADB_USERNAME')
    db_pwd = current_app.config.get('MARIADB_PASSWORD')
    if not db_name:
        db_name = current_app.config.get('MARIADB_DB')
    db_charset = current_app.config.get('MARIADB_CHARSET')
    command = f'mariadb -u {db_usr} -p\'{db_pwd}\' -e \"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARSET {db_charset} COLLATE {db_charset}_unicode_ci;\"'
    try:
        ret = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        current_app.logger.error('mariadb_create_database: {}'.format(str(e)))
    return ret.returncode == 0 and ret.stdout.decode() == ''


def send_async_email(app, message):
    with app.app_context():
        try:
            mail.send(message)
        except Exception as e:
            app.logger.error('send_async_email: {}'.format(str(e)))


def send_email(to, subject, msg):
    message = Message(subject=current_app.config.get('SITE_NAME') + ': ' + subject,
                      sender=current_app.config.get('MAIL_USERNAME'), recipients=[to])
    message.body = msg

    thread = Thread(target=send_async_email, args=[current_app._get_current_object(), message])
    thread.start()
    return thread

def browse_directory(current_path):
    dirs = []
    if not os.path.isdir(current_path):
        return dirs
    for file in os.listdir(current_path):
        if os.path.isdir(os.path.join(current_path, file)):
            dirs.append(file)
    dirs.sort()
    return dirs

def _rotate_image_by_orientation(image):
    try:
        exif_info = image._getexif()
        if exif_info and EXIF_TAG_MAP['Orientation'] in exif_info:
            orientation = exif_info[EXIF_TAG_MAP['Orientation']]
            if orientation == 3:
                image = image.rotate(Image.ROTATE_180, expand=True)
            elif orientation == 6:
                image = image.rotate(Image.ROTATE_270, expand=True)
            elif orientation == 8:
                image = image.rotate(Image.ROTATE_90, expand=True)
            """
            if orientation == 1:
                pass
            elif orientation == 2:
                image = image.transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                image = image.rotate(Image.ROTATE_180)
            elif orientation == 4:
                image = image.transpose(Image.FLIP_TOP_BOTTOM)
            elif orientation == 5:
                image = image.rotate(Image.ROTATE_270).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 6:
                image = image.rotate(Image.ROTATE_270)
            elif orientation == 7:
                image = image.rotate(Image.ROTATE_90).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 8:
                image = image.rotate(Image.ROTATE_90)
            else:
                pass
            """
    except Exception as e:
        current_app.logger.error('_rotate_image_by_orientation: {}'.format(str(e)))
    return image

def get_thumbnail_size(image_size, thumbnail_height):
    width = round((float(thumbnail_height) / image_size[1]) * image_size[0])
    return width, thumbnail_height

def get_file_ctime(file):
    stat = os.stat(file)
    if 'st_birthtime' in dir(stat):
        timestamp = stat.st_birthtime
    else:
        timestamp = os.path.getctime(file)
    return timestamp

def _parse_exif_timestamp(timestamp_string):
    timestamp_string = timestamp_string.split('+')[0]
    try:
        timestamp = datetime.datetime.strptime(timestamp_string, '%Y:%m:%d %H:%M:%S').timestamp()
    except ValueError:
        timestamp = None
    return timestamp

def _get_image_timestamp(image_file):
    image = Image.open(image_file)
    exif_info = image._getexif()
    image.close()
    image_timestamp = None
    if exif_info:
        if EXIF_TAG_MAP['DateTimeOriginal'] in exif_info:
            image_timestamp = _parse_exif_timestamp(exif_info[EXIF_TAG_MAP['DateTimeOriginal']])
        elif EXIF_TAG_MAP['DateTimeDigitized'] in exif_info:
            image_timestamp = _parse_exif_timestamp(exif_info[EXIF_TAG_MAP['DateTimeDigitized']])
        elif EXIF_TAG_MAP['DateTime'] in exif_info:
            image_timestamp = _parse_exif_timestamp(exif_info[EXIF_TAG_MAP['DateTime']])
    if not image_timestamp:
        image_timestamp = get_file_ctime(image_file)
    return image_timestamp

def _is_file_exist(cur_filename, query_func):
    path = os.path.dirname(_get_relative_name(cur_filename))
    filename = os.path.basename(cur_filename)
    username = path.split(os.sep)[0]
    return query_func(username, path, filename)

def _get_solid_filename(cur_filename, query_func):
    while _is_file_exist(cur_filename, query_func):
        file_path = os.path.dirname(cur_filename)
        file_name, file_ext = os.path.splitext(os.path.basename(cur_filename))
        prefix_str, dt_str = file_name.split('_', 1)
        cur_dt = datetime.datetime.strptime(dt_str, '%Y%m%d_%H%M%S')
        next_dt = cur_dt + datetime.timedelta(seconds=1)
        file_basename = prefix_str + '_' +  next_dt.strftime('%Y%m%d_%H%M%S') + file_ext
        cur_filename = os.path.join(file_path, file_basename)
    return cur_filename

def _create_image_thumbnail(image_file, thumbnail_dirname, height, query_func):
    image_timestamp = _get_image_timestamp(image_file)
    new_filename = 'IMG_' + datetime.datetime.fromtimestamp(image_timestamp).strftime('%Y%m%d_%H%M%S') + os.path.splitext(image_file)[1]
    new_file = os.path.join(os.path.dirname(image_file), new_filename)
    new_file = _get_solid_filename(new_file, query_func)
    if image_file != new_file:
        os.rename(image_file, new_file)
        new_filename = os.path.basename(new_file)

    image = Image.open(new_file)
    ### PIL.Image.rotate is not good enough to be applyed!
    # image = _rotate_image_by_orientation(image)
    image_size = image.size

    thumbnail_file = os.path.join(thumbnail_dirname, new_filename)
    if not os.path.isfile(thumbnail_file):
        thumbnail_size = get_thumbnail_size(image_size, height)
        if thumbnail_size != image_size:
            image = image.resize(thumbnail_size, Image.ANTIALIAS)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(thumbnail_file)

    image.close()
    return (image_size, MediaType.IMAGE, image_timestamp, new_filename)

def _get_video_timestamp(video_file):
    file_ctime = get_file_ctime(video_file)
    parser = createParser(video_file)
    if not parser:
        return file_ctime

    try:
        metadata = extractMetadata(parser)
    except Exception as error:
        metadata = None
    if not metadata:
        return file_ctime

    for line in metadata.exportPlaintext():
        datetime_caption, datetime_str = line.split(':', 1)
        if datetime_caption == '- Creation date':
            datetime_str = datetime_str.strip()
            timestamp = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S').timestamp()
            return timestamp
    return file_ctime

def _create_video_thumbnail(video_file, thumbnail_dirname, height, query_func):
    video_capture = cv2.VideoCapture(video_file)
    _, image = video_capture.read()
    video_size = (image.shape[1], image.shape[0])
    video_timestamp = _get_video_timestamp(video_file)
    new_filename = 'VID_' + datetime.datetime.fromtimestamp(video_timestamp).strftime('%Y%m%d_%H%M%S') + os.path.splitext(video_file)[1]
    new_file = os.path.join(os.path.dirname(video_file), new_filename)
    new_file = _get_solid_filename(new_file, query_func)
    if video_file != new_file:
        os.rename(video_file, new_file)
        new_filename = os.path.basename(new_file)

    prefix, ext = os.path.splitext(new_filename)
    thumbnail_filename = prefix + IMAGE_SUFFIXES[0]
    thumbnail_file = os.path.join(thumbnail_dirname, thumbnail_filename)
    if not os.path.isfile(thumbnail_file):
        width = round(image.shape[1] * float(height) / image.shape[0])
        thumbnail_image = cv2.resize(image, (width, height))
        cv2.imwrite(thumbnail_file, thumbnail_image)
    return (video_size, MediaType.VIDEO, video_timestamp, new_filename)

def _create_thumbnail(media_full_name, thumbnail_dirname, height, query_func):
    file_ext = os.path.splitext(media_full_name)[1]
    if file_ext in IMAGE_SUFFIXES:
        meta_data = _create_image_thumbnail(media_full_name, thumbnail_dirname, height, query_func)
    elif file_ext in VIDEO_SUFFIXES:
        meta_data = _create_video_thumbnail(media_full_name, thumbnail_dirname, height, query_func)
    elif file_ext in MUSIC_SUFFIXES:
        meta_data = ((None, None), MediaType.MUSIC, get_file_ctime(media_full_name), os.path.basename(media_full_name))
    else:
        meta_data = ((None, None), MediaType.OTHER, get_file_ctime(media_full_name), os.path.basename(media_full_name))
    return meta_data

def _get_relative_name(media_full_name):
    original_path = current_app.config.get('SYS_MEDIA_ORIGINAL')
    media_relative_name = media_full_name[len(original_path)+1:]
    return media_relative_name

def _get_thumbnail_name(media_full_name):
    thumbnail_path = current_app.config.get('SYS_MEDIA_THUMBNAIL')
    media_relative_name = _get_relative_name(media_full_name)
    thumbnail_full_name = os.path.join(thumbnail_path, media_relative_name)
    return thumbnail_full_name

def import_user_media(media_full_name, is_public, user_query_media_func, user_add_media_func):
    prefix, ext = os.path.splitext(media_full_name)
    target_ext = ext.lower()
    if ext != target_ext:
        media_old_name, media_full_name = media_full_name, prefix + target_ext
        os.rename(media_old_name, media_full_name)
    thumbnail_dirname = os.path.dirname(_get_thumbnail_name(media_full_name))
    relative_path = os.path.dirname(_get_relative_name(media_full_name))
    user_name = relative_path.split(os.sep)[0]
    os.makedirs(thumbnail_dirname, mode=0o750, exist_ok=True)
    metadata = _create_thumbnail(media_full_name, thumbnail_dirname, current_app.config.get('SYS_MEDIA_THUMBNAIL_HEIGHT'), user_query_media_func)
    (width, height), media_type, media_datetime, media_filename = metadata
    timestamp = datetime.datetime.fromtimestamp(media_datetime)
    return user_add_media_func(username=user_name, path=relative_path, filename=media_filename,
                               width=width, height=height, timestamp=timestamp,
                               media_type=media_type, is_public=is_public)

def import_user_medias(user_name, user_query_media_func, user_add_media_func):
    original_path = current_app.config.get('SYS_MEDIA_ORIGINAL')

    cur_path = os.path.join(original_path, user_name)
    if not os.path.exists(cur_path):
        os.makedirs(cur_path, mode=0o750, exist_ok=True)
        return

    for root, dirs, files in os.walk(cur_path, topdown=False):
        for filename in files:
            import_user_media(os.path.join(root, filename), False, user_query_media_func, user_add_media_func)

