# !/usr/bin/env python
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

JPEG_SUFFIXES = ['.jpg', '.jpeg']
IMAGE_SUFFIXES = JPEG_SUFFIXES + ['.png', '.gif']
VIDEO_SUFFIXES = ['.mp4', '.mov', '.m4v']
EXIF_TAG_MAP = {ExifTags.TAGS[tag]: tag for tag in ExifTags.TAGS}


def markdown_to_html(text):
    extensions = ['fenced_code', 'admonition', 'tables', 'extra']
    return bleach.linkify(markdown(text, extensions=extensions, output_format='html5'))


def redirect_back(endpoint=None, is_auth=False, **kwargs):
    if endpoint:
        target_url = url_for(endpoint, **kwargs, _external=True)
        return redirect(target_url)
    if is_auth and 'url' in session:
        return redirect(session['url'])
    if not is_auth and request.referrer and request.referrer != request.url:
        return redirect(request.referrer)
    return redirect(url_for('main.index', _external=True))


def redirect_save(url=None):
    if not url:
        url = url_for('main.index', _external=True)
    session['url'] = url


def mariadb_is_in_use():
    return current_app.config.get('SYS_MARIADB')


def mariadb_is_exist_db(db_name=None):
    db_usr = current_app.config.get('MARIADB_USERNAME')
    db_pwd = current_app.config.get('MARIADB_PASSWORD')
    if not db_name:
        db_name = current_app.config.get('MARIADB_DB')
    command = f'mariadb -u {db_usr} -p\'{db_pwd}\' -e \"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME=\'{db_name}\';\"'
    try:
        ret = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        current_app.config.get('LOGGER').error('mariadb_is_exist_database: {}'.format(str(e)))
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
        current_app.config.get('LOGGER').error('mariadb_drop_database: {}'.format(str(e)))
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
        current_app.config.get('LOGGER').error('mariadb_create_database: {}'.format(str(e)))
    return ret.returncode == 0 and ret.stdout.decode() == ''


def send_async_email(app, message):
    with app.app_context():
        try:
            mail.send(message)
        except Exception as e:
            app.config.get('LOGGER').error('send_async_email: {}'.format(str(e)))


def send_email(to, subject, msg):
    message = Message(subject=current_app.config.get('SITE_NAME') + ': ' + subject,
                      sender=current_app.config.get('MAIL_USERNAME'), recipients=[to])
    message.body = msg

    thread = Thread(target=send_async_email, args=[current_app._get_current_object(), message])
    thread.start()
    return thread

def _rotate_image_by_orientation(image):
    try:
        exif_info = image.getexif()
        if exif_info and EXIF_TAG_MAP['Orientation'] in exif_info:
            orientation = exif_info[EXIF_TAG_MAP['Orientation']]
            if orientation == 3:
                rotation_angle = 180
            elif orientation == 6:
                rotation_angle = 270
            elif orientation == 8:
                rotation_angle = 90
            else:
                rotation_angle = 0
            if rotation_angle != 0:
                return image.rotate(rotation_angle, expand=True)
    except:
        pass
    return image

def _get_thumbnail_size(image_size, thumbnail_height):
    if thumbnail_height >= image_size[1]:
        return None
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

def _create_image_thumbnail(image_file, thumbnail_file, height):
    image = Image.open(image_file)
    image = _rotate_image_by_orientation(image)
    image_size = image.size

    if not os.path.isfile(thumbnail_file):
        thumbnail_size = _get_thumbnail_size(image.size, height)
        if thumbnail_size:
            image = image.resize(thumbnail_size, Image.ANTIALIAS)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(thumbnail_file)

    image.close()
    image_timestamp = _get_image_timestamp(image_file)
    return (image_size, image_timestamp)

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

def _create_video_thumbnail(video_file, thumbnail_file, height):
    video_capture = cv2.VideoCapture(video_file)
    _, image = video_capture.read()
    video_size = (image.shape[1], image.shape[0])
    video_timestamp = _get_video_timestamp(video_file)

    if not os.path.isfile(thumbnail_file):
        thumbnail_image = cv2.resize(image, (round(image.shape[1] * float(height) / image.shape[0]), height))
        cv2.imwrite(thumbnail_file, thumbnail_image)
    return (video_size, video_timestamp)

def _create_thumbnail(media_full_name, thumbnail_full_name, height):
    file_ext = os.path.splitext(media_full_name)[1].lower()
    if file_ext in IMAGE_SUFFIXES:
        meta_data = _create_image_thumbnail(media_full_name, thumbnail_full_name, height)
    elif file_ext in VIDEO_SUFFIXES:
        meta_data = _create_video_thumbnail(media_full_name, thumbnail_full_name, height)
    else:
        meta_data = ((None, None), get_file_ctime(media_full_name))
    return meta_data

def _get_relative_path(media_full_name):
    storage_path = current_app.config.get('SYS_STORAGE')
    media_relative_name = media_full_name[len(storage_path)+1:]
    return os.path.dirname(media_relative_name)

def _get_thumbnail_name(media_full_name):
    storage_path = current_app.config.get('SYS_STORAGE')
    thumbnail_path = current_app.config.get('SYS_THUMBNAIL')
    media_relative_name = media_full_name[len(storage_path)+1:]
    thumbnail_full_name = os.path.join(thumbnail_path, media_relative_name)
    thumbnail_prefix, thumbnail_ext = os.path.splitext(thumbnail_full_name)
    if thumbnail_ext.lower() in VIDEO_SUFFIXES:
        thumbnail_full_name = thumbnail_prefix + IMAGE_SUFFIXES[0]
    return thumbnail_full_name

def import_user_media(media_full_name, user_name, user_add_media_func):
    thumbnail_full_name = _get_thumbnail_name(media_full_name)
    relative_path = _get_relative_path(media_full_name)
    filename = os.path.basename(media_full_name)
    os.makedirs(os.path.dirname(thumbnail_full_name), mode=0o750, exist_ok=True)
    metadata = _create_thumbnail(media_full_name, thumbnail_full_name, current_app.config.get('SYS_THUMBNAIL_HEIGHT'))
    width, height = metadata[0]
    timestamp = datetime.datetime.fromtimestamp(metadata[1])
    user_add_media_func(username=user_name, path=relative_path, filename=filename,
                      width=width, height=height, timestamp=timestamp, is_public=False)

def import_user_medias(user_name, user_add_media_func):
    storage_path = current_app.config.get('SYS_STORAGE')

    cur_path = os.path.join(storage_path, user_name)
    if not os.path.exists(cur_path):
        os.makedirs(cur_path, mode=0o750, exist_ok=True)
        return

    for root, dirs, files in os.walk(cur_path, topdown=False):
        for filename in files:
            import_user_media(os.path.join(root, filename), user_name, user_add_media_func)

