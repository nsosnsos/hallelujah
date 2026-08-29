#!/usr/bin/env python3
""" "utilities"""

import datetime
import os
import shutil
import smtplib
import struct
import subprocess
import time
from enum import Enum
from threading import Thread

import av
import bleach
from flask import current_app, redirect, request, session, url_for
from flask_mail import Message
from markdown import markdown
from PIL import ExifTags, Image, ImageOps, PngImagePlugin

from .extensions import mail


class MediaType(Enum):
    """media type"""

    OTHER = 0
    MUSIC = 1
    IMAGE = 2
    VIDEO = 3


MUSIC_SUFFIXES = [".mp3"]
IMAGE_SUFFIXES = [".jpg", ".jpeg", ".png"]
VIDEO_SUFFIXES = [".mp4"]

VIDEO_LONG_HEAD_LEN = 8
VIDEO_SHORT_HEAD_LEN = 4
EPOCH_1904 = datetime.datetime(1904, 1, 1, tzinfo=datetime.timezone.utc)
DEFAULT_MVHD_INFO = {"pos": -1, "version": -1, "timestamp": 0}


def markdown_to_html(text):
    """markdown to html"""
    extensions = ["fenced_code", "admonition", "tables", "extra"]
    return bleach.linkify(markdown(text, extensions=extensions, output_format="html5"))


def get_request_ip(requests):
    """get requests ip"""
    return requests.headers.get("Cf-Connecting-Ip") or requests.headers.get("X-Real-Ip") or requests.remote_addr


def redirect_back(endpoint=None, redirect_before=False, **kwargs):
    """redirect back"""
    if endpoint:
        target_url = url_for(endpoint, **kwargs, _external=True)
        return redirect(target_url)
    if redirect_before and "url" in session:
        return redirect(session["url"])
    if request.referrer and request.referrer != request.url:
        return redirect(request.referrer)
    return redirect(url_for("main.index", _external=True))


def redirect_save(url=None):
    """redirect save"""
    if not url:
        url = url_for("main.index", _external=True)
    session["url"] = url


def sqlite_in_use():
    """sqlite in use"""
    return current_app.config.get("SYS_SQLITE")


def db_backup():
    """db backup"""
    data_directory = os.path.join(os.path.join(current_app.config.get("SYS_MEDIA"), ".."))
    if sqlite_in_use():
        sqlite_path = current_app.config.get("SQLITE_PATH")
        sqlite_db = current_app.config.get("SQLITE_DB")
        src_file = os.path.join(sqlite_path, sqlite_db)
        dst_file = os.path.join(data_directory, sqlite_db)
        if os.path.exists(src_file):
            shutil.copyfile(src_file, dst_file)
            return True
        current_app.logger.error(f"db_backup failed: db({src_file}) not found.")
        return False
    env = os.environ.copy()
    env["MYSQL_PWD"] = current_app.config.get("DB_PASSWORD")
    db_usr = current_app.config.get("DB_USERNAME")
    db_name = current_app.config.get("DB_NAME")
    target_db = os.path.join(data_directory, db_name + ".sql")
    db_charset = current_app.config.get("DB_CHARSET")
    command = [
        "mysqldump",
        "--single-transaction",
        "--default-character-set=" + db_charset,
        "-u",
        db_usr,
        "--databases",
        db_name,
    ]
    try:
        with open(target_db, "wb") as out:
            ret = subprocess.run(
                command,
                stdout=out,
                stderr=subprocess.PIPE,
                env=env,
                shell=False,
                check=False,
            )
    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"db_backup failed: {e!s}")
        return False
    current_app.logger.info(f"db_backup result: {ret}")
    return ret.returncode == 0


def db_restore():
    """db restore"""
    data_directory = os.path.join(os.path.join(current_app.config.get("SYS_MEDIA"), ".."))
    if sqlite_in_use():
        sqlite_path = current_app.config.get("SQLITE_PATH")
        sqlite_db = current_app.config.get("SQLITE_DB")
        src_file = os.path.join(data_directory, sqlite_db)
        dst_file = os.path.join(sqlite_path, sqlite_db)
        if os.path.exists(src_file):
            shutil.copyfile(src_file, dst_file)
            return True
        current_app.logger.error("db_restore failed: db({src_file}) not found.")
        return False
    env = os.environ.copy()
    env["MYSQL_PWD"] = current_app.config.get("DB_PASSWORD")
    db_usr = current_app.config.get("DB_USERNAME")
    db_name = current_app.config.get("DB_NAME")
    target_db = os.path.join(data_directory, db_name + ".sql")
    db_charset = current_app.config.get("DB_CHARSET")
    command = [
        "mysql",
        "--default-character-set=" + db_charset,
        "-u",
        db_usr,
        db_name,
    ]
    if not os.path.isfile(target_db):
        current_app.logger.error("db_restore failed: db({target_db}) not found.")
        return False
    try:
        with open(target_db, "rb") as src:
            ret = subprocess.run(
                command,
                stdin=src,
                stderr=subprocess.PIPE,
                env=env,
                shell=False,
                check=False,
            )
    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"db_restore failed: {e!s}")
        return False
    current_app.logger.info(f"db_restore result: {ret}")
    return ret.returncode == 0


def db_is_exist(db_name=None):
    """db is exist"""
    env = os.environ.copy()
    env["MYSQL_PWD"] = current_app.config.get("DB_PASSWORD")
    db_usr = current_app.config.get("DB_USERNAME")
    if not db_name:
        db_name = current_app.config.get("DB_NAME")
    command = [
        "mysql",
        "-u",
        db_usr,
        "-e",
        f'SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME="{db_name}";',
    ]
    try:
        ret = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            env=env,
            shell=False,
            check=False,
        )
    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"db_is_exist failed: {e!s}")
    return ret.returncode == 0 and ret.stdout.decode() != ""


def db_drop(db_name=None):
    """db drop"""
    env = os.environ.copy()
    env["MYSQL_PWD"] = current_app.config.get("DB_PASSWORD")
    db_usr = current_app.config.get("DB_USERNAME")
    if not db_name:
        db_name = current_app.config.get("DB_NAME")
    command = [
        "mysql",
        "-u",
        db_usr,
        "-e",
        f"DROP DATABASE IF EXISTS {db_name};",
    ]
    try:
        ret = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            env=env,
            shell=False,
            check=False,
        )
    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"db_drop failed: {e!s}")
    return ret.returncode == 0 and ret.stdout.decode() != ""


def db_create(db_name=None):
    """db create"""
    env = os.environ.copy()
    env["MYSQL_PWD"] = current_app.config.get("DB_PASSWORD")
    db_usr = current_app.config.get("DB_USERNAME")
    if not db_name:
        db_name = current_app.config.get("DB_NAME")
    db_charset = current_app.config.get("DB_CHARSET")
    command = [
        "mysql",
        "-u",
        db_usr,
        "-e",
        f"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARSET {db_charset} COLLATE {db_charset}_unicode_ci;",
    ]
    try:
        ret = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            env=env,
            shell=False,
            check=False,
        )
    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"db_create failed: {e!s}")
    return ret.returncode == 0 and ret.stdout.decode() == ""


def send_async_email(app, message):
    """send async email"""
    with app.app_context():
        try:
            mail.send(message)
        except smtplib.SMTPException as e:
            app.logger.error(f"send_async_email: {e!s}")


def send_email(to, subject, msg):
    """send email"""
    message = Message(
        subject=current_app.config.get("SITE_NAME") + ": " + subject,
        sender=current_app.config.get("MAIL_USERNAME"),
        recipients=[to],
    )
    message.body = msg

    thread = Thread(
        target=send_async_email,
        args=[current_app._get_current_object(), message],  # pylint: disable=protected-access
    )
    thread.start()
    return thread


def browse_directory(current_path):
    """browse directory"""
    dirs = []
    if not os.path.isdir(current_path):
        return dirs
    for file in os.listdir(current_path):
        if os.path.isdir(os.path.join(current_path, file)):
            dirs.append(file)
    dirs.sort()
    return dirs


def get_thumbnail_size(image_size, thumbnail_height):
    """get thumbnail size"""
    width = round((float(thumbnail_height) / image_size[1]) * image_size[0])
    return width, thumbnail_height


def get_file_ctime(file):
    """get file create time"""
    try:
        stat = os.stat(file)
        if hasattr(stat, "st_birthtime"):
            return stat.st_birthtime
        return stat.st_mtime
    except (FileNotFoundError, PermissionError, IsADirectoryError, OSError, ValueError, AttributeError):
        current_app.logger.error(f"failed to get created time in {file}")
        return time.time()


def set_image_timestamp(image_file, timestamp):
    """set image timestamp"""
    root, ext = os.path.splitext(image_file)
    tmp_output = f"{root}_tmp{ext}"
    datetime_info = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    datetime_target = datetime.datetime.strptime(os.path.basename(root)[4:], "%Y%m%d_%H%M%S").replace(
        tzinfo=datetime.timezone.utc
    )
    if datetime_info != datetime_target:
        datetime_info = datetime_target
    datetime_str = datetime_info.strftime("%Y:%m:%d %H:%M:%S")
    timezone_str = datetime_info.strftime("%z")
    if ":" not in timezone_str:
        timezone_str = f"{timezone_str[:-2]}:{timezone_str[-2:]}"
    try:
        with Image.open(image_file) as image:
            exif_info = image.getexif()
            exif_sub_info = exif_info.get_ifd(ExifTags.IFD.Exif)
            exif_info[ExifTags.Base.DateTime] = datetime_str
            exif_info[ExifTags.Base.OffsetTime] = timezone_str
            exif_sub_info[ExifTags.Base.DateTimeOriginal] = datetime_str
            exif_sub_info[ExifTags.Base.OffsetTimeOriginal] = timezone_str
            exif_sub_info[ExifTags.Base.DateTimeDigitized] = datetime_str
            exif_sub_info[ExifTags.Base.OffsetTimeDigitized] = timezone_str
            exif_info[ExifTags.IFD.Exif] = exif_sub_info
            saved_args = {"exif": exif_info}
            saved_args.update(image.info)
            if ext.lower() == IMAGE_SUFFIXES[-1]:
                target_format = IMAGE_SUFFIXES[-1][1:].upper()
                png_info = PngImagePlugin.PngInfo()
                png_info.add_text("Creation Time", datetime_str)
                image.save(tmp_output, format=target_format, pnginfo=png_info, **saved_args)
            else:
                target_format = IMAGE_SUFFIXES[1][1:].upper()
                if getattr(image, "format", None) == IMAGE_SUFFIXES[1][1:].upper():
                    saved_args["quality"] = "keep"
                else:
                    saved_args["quality"] = 95
                image.save(tmp_output, format=target_format, **saved_args)
        os.replace(tmp_output, image_file)
        os.utime(image_file, (timestamp, timestamp))
    except (FileNotFoundError, PermissionError, IsADirectoryError, OSError, AttributeError, ValueError, TypeError):
        current_app.logger.error(f"failed to write timestamp to {image_file}")
        if os.path.exists(tmp_output):
            os.remove(tmp_output)


def _parse_exif_timestamp(timestamp_string):
    """parse exif timestamp"""
    if not timestamp_string:
        return None
    timestamp_string = timestamp_string.strip()
    if "+" in timestamp_string or "-" in timestamp_string:
        sign_idx = max(timestamp_string.rfind("+"), timestamp_string.rfind("-"))
        if sign_idx != -1 and ":" in timestamp_string[sign_idx:]:
            tz_part = timestamp_string[sign_idx:].replace(":", "")
            timestamp_string = timestamp_string[:sign_idx] + tz_part
    try:
        return datetime.datetime.strptime(timestamp_string, "%Y:%m:%d %H:%M:%S%z").timestamp()
    except ValueError:
        try:
            return datetime.datetime.strptime(timestamp_string, "%Y:%m:%d %H:%M:%S").astimezone().timestamp()
        except ValueError:
            current_app.logger.error(f"failed to parse timestamp string [{timestamp_string}]")
            return None


def get_image_timestamp(image_file):
    """get image timestamp"""
    image_timestamp = None
    try:
        with Image.open(image_file) as image:
            exif_info = image.getexif()
            if exif_info:
                exif_sub_info = exif_info.get_ifd(ExifTags.IFD.Exif)
                if ExifTags.Base.DateTimeOriginal in exif_sub_info:
                    tz_str = exif_sub_info.get(ExifTags.Base.OffsetTimeOriginal, "")
                    image_timestamp = _parse_exif_timestamp(exif_sub_info[ExifTags.Base.DateTimeOriginal] + tz_str)
                if not image_timestamp and ExifTags.Base.DateTimeDigitized in exif_sub_info:
                    tz_str = exif_sub_info.get(ExifTags.Base.OffsetTimeDigitized, "")
                    image_timestamp = _parse_exif_timestamp(exif_sub_info[ExifTags.Base.DateTimeDigitized] + tz_str)
                if not image_timestamp and ExifTags.Base.DateTime in exif_info:
                    tz_str = exif_info.get(ExifTags.Base.OffsetTime, "")
                    image_timestamp = _parse_exif_timestamp(exif_info[ExifTags.Base.DateTime] + tz_str)
    except (FileNotFoundError, PermissionError, UnicodeDecodeError, IsADirectoryError, ValueError, KeyError):
        current_app.logger.error(f"{image_file} meta data read error")
    if not image_timestamp:
        image_timestamp = get_file_ctime(image_file)
    return image_timestamp


def _is_file_exist(cur_filename, query_func):
    """is file exist"""
    pathname = os.path.dirname(_get_relative_name(cur_filename))
    filename = os.path.basename(cur_filename)
    username = pathname.split(os.sep)[0]
    return query_func(username, pathname, filename)


def _get_solid_filename(cur_filename, query_func):
    """get solid filename"""
    file_path = os.path.dirname(cur_filename)
    file_name, file_ext = os.path.splitext(os.path.basename(cur_filename))
    prefix_str, dt_str = file_name.split("_", 1)
    cur_dt = datetime.datetime.strptime(dt_str, "%Y%m%d_%H%M%S").replace(tzinfo=datetime.timezone.utc)
    while _is_file_exist(cur_filename, query_func):
        cur_dt += datetime.timedelta(seconds=1)
        file_basename = prefix_str + "_" + cur_dt.strftime("%Y%m%d_%H%M%S") + file_ext
        cur_filename = os.path.join(file_path, file_basename)
    return cur_filename


def _create_image_thumbnail(image_file, thumbnail_dirname, height, query_func):
    """create image thumbnail"""
    try:
        image_timestamp = get_image_timestamp(image_file)
        new_filename = (
            "IMG_"
            + datetime.datetime.fromtimestamp(timestamp=image_timestamp, tz=datetime.timezone.utc).strftime(
                "%Y%m%d_%H%M%S"
            )
            + os.path.splitext(image_file)[1]
        )
        new_file = os.path.join(os.path.dirname(image_file), new_filename)
        new_file = _get_solid_filename(new_file, query_func)
        if image_file != new_file:
            os.rename(image_file, new_file)
            new_filename = os.path.basename(new_file)
        set_image_timestamp(new_file, image_timestamp)
        image_size = (0, 0)

        with Image.open(new_file) as image:
            image = ImageOps.exif_transpose(image)
            image_size = image.size

            thumbnail_file = os.path.join(thumbnail_dirname, new_filename)
            if not os.path.isfile(thumbnail_file):
                thumbnail_size = get_thumbnail_size(image_size, height)
                if thumbnail_size != image_size:
                    image = image.resize(thumbnail_size, Image.Resampling.LANCZOS)
                if image.mode != "RGB":
                    image = image.convert("RGB")
                image.save(thumbnail_file)
                set_image_timestamp(thumbnail_file, image_timestamp)
    except (FileNotFoundError, PermissionError, UnicodeDecodeError, IsADirectoryError, ValueError, TypeError):
        current_app.logger.error(f"failed to create image thumbnail {image_file}")

    return (image_size, MediaType.IMAGE.value, image_timestamp, new_filename)


def _parse_mvhd_payload(file_handler, version):
    """parse mvhd payload"""
    timestamp_pos = file_handler.tell()
    if version == 1:
        timestamp_bytes = file_handler.read(VIDEO_LONG_HEAD_LEN + VIDEO_LONG_HEAD_LEN)
        if len(timestamp_bytes) != VIDEO_LONG_HEAD_LEN + VIDEO_LONG_HEAD_LEN:
            return DEFAULT_MVHD_INFO
        creation_ts, modification_ts = struct.unpack(">QQ", timestamp_bytes)
    else:
        timestamp_bytes = file_handler.read(VIDEO_SHORT_HEAD_LEN + VIDEO_SHORT_HEAD_LEN)
        if len(timestamp_bytes) != VIDEO_SHORT_HEAD_LEN + VIDEO_SHORT_HEAD_LEN:
            return DEFAULT_MVHD_INFO
        creation_ts, modification_ts = struct.unpack(">II", timestamp_bytes)
    return {"pos": timestamp_pos, "version": version, "timestamp": creation_ts or modification_ts}


def _get_video_mvhd_info(file_handler):
    """get video mvhd info"""
    file_handler.seek(0, os.SEEK_END)
    file_size = file_handler.tell()
    file_handler.seek(0)
    while file_handler.tell() + VIDEO_LONG_HEAD_LEN <= file_size:
        cur_pos = file_handler.tell()
        header = file_handler.read(VIDEO_LONG_HEAD_LEN)
        if len(header) < VIDEO_LONG_HEAD_LEN:
            break

        size, box_type = struct.unpack(">I4s", header)
        if size == 1:
            header_ext = file_handler.read(VIDEO_LONG_HEAD_LEN)
            if len(header_ext) < VIDEO_LONG_HEAD_LEN:
                break
            size = struct.unpack(">Q", header_ext)[0]
        if size <= 0:
            break

        if box_type == b"mvhd":
            version_flags = file_handler.read(VIDEO_SHORT_HEAD_LEN)
            if len(version_flags) < VIDEO_SHORT_HEAD_LEN:
                break
            return _parse_mvhd_payload(file_handler, version_flags[0])
        if box_type != b"moov":
            file_handler.seek(cur_pos + size)
    return DEFAULT_MVHD_INFO


def get_video_timestamp(video_file):
    """get video timestamp"""
    try:
        with open(video_file, "rb") as file_handler:
            mvhd_info = _get_video_mvhd_info(file_handler)
            if mvhd_info.get("pos", -1) != -1:
                dt = EPOCH_1904 + datetime.timedelta(seconds=mvhd_info.get("timestamp", 0))
                return dt.timestamp()
    except (FileNotFoundError, PermissionError, IsADirectoryError, AttributeError, ValueError, TypeError):
        current_app.logger.error(f"failed to get timestamp from {video_file}")
    return get_file_ctime(video_file)


def set_video_timestamp(video_file, timestamp):
    """set video timestmap"""
    try:
        target_dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
        target_timestamp = int((target_dt - EPOCH_1904).total_seconds())

        with open(video_file, "r+b") as file_handler:
            mvhd_info = _get_video_mvhd_info(file_handler)
            if mvhd_info.get("pos", -1) == -1:
                current_app.logger.error(f"failed to get mvhd info in {video_file}")
                return

            file_handler.seek(mvhd_info["pos"])
            if mvhd_info["version"] == 1:
                new_bytes = struct.pack(">QQ", target_timestamp, target_timestamp)
            else:
                new_bytes = struct.pack(">II", target_timestamp, target_timestamp)
            file_handler.write(new_bytes)
    except (FileNotFoundError, PermissionError, IsADirectoryError, AttributeError, ValueError, TypeError):
        current_app.logger.error(f"failed write timestamp to {video_file}")
    os.utime(video_file, (timestamp, timestamp))


def _get_video_thumbnail_filename(original_filename):
    """get video thumbnail filename"""
    prefix, _ = os.path.splitext(original_filename)
    return prefix + IMAGE_SUFFIXES[0]


def _get_first_frame_from_video(video_file):
    image = None
    try:
        with av.open(video_file) as container:
            video_stream = container.streams.video[0]
            for frame in container.decode(video_stream):
                rotation = int(getattr(frame, "rotation", 0)) % 360
                image = frame.to_image()
                if rotation == 90:
                    image = image.transpose(Image.Transpose.ROTATE_90)
                elif rotation == 180:
                    image = image.transpose(Image.Transpose.ROTATE_180)
                elif rotation == 270:
                    image = image.transpose(Image.Transpose.ROTATE_270)
                break
    except (FileNotFoundError, PermissionError, UnicodeDecodeError, IsADirectoryError, ValueError, TypeError):
        current_app.logger.error(f"{video_file} decode error")
    return image


def _create_video_thumbnail(video_file, thumbnail_dirname, height, query_func):
    """create video thumbnail"""
    image = _get_first_frame_from_video(video_file)
    if image is None:
        return ((0, 0), MediaType.VIDEO.value, 0, "")

    video_timestamp = get_video_timestamp(video_file)
    dt = datetime.datetime.fromtimestamp(timestamp=video_timestamp, tz=datetime.timezone.utc)
    new_filename = f"VID_{dt.strftime('%Y%m%d_%H%M%S')}{os.path.splitext(video_file)[1]}"
    new_file = os.path.join(os.path.dirname(video_file), new_filename)
    new_file = _get_solid_filename(new_file, query_func)
    if video_file != new_file:
        os.rename(video_file, new_file)
        new_filename = os.path.basename(new_file)
    set_video_timestamp(new_file, video_timestamp)

    thumbnail_filename = _get_video_thumbnail_filename(new_filename)
    thumbnail_file = os.path.join(thumbnail_dirname, thumbnail_filename)
    if not os.path.isfile(thumbnail_file):
        thumbnail_size = get_thumbnail_size(image.size, height)
        image = image.resize(thumbnail_size, Image.Resampling.LANCZOS)
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(thumbnail_file)
        set_image_timestamp(thumbnail_file, video_timestamp)
    return (image.size, MediaType.VIDEO.value, video_timestamp, new_filename)


def _create_thumbnail(media_fullname, thumbnail_dirname, height, query_func):
    """create thumbnail"""
    file_ext = os.path.splitext(media_fullname)[1]
    if file_ext in IMAGE_SUFFIXES:
        meta_data = _create_image_thumbnail(media_fullname, thumbnail_dirname, height, query_func)
    elif file_ext in VIDEO_SUFFIXES:
        meta_data = _create_video_thumbnail(media_fullname, thumbnail_dirname, height, query_func)
    elif file_ext in MUSIC_SUFFIXES:
        meta_data = (
            (None, None),
            MediaType.MUSIC.value,
            get_file_ctime(media_fullname),
            os.path.basename(media_fullname),
        )
    else:
        meta_data = (
            (None, None),
            MediaType.OTHER.value,
            get_file_ctime(media_fullname),
            os.path.basename(media_fullname),
        )
    return meta_data


def _get_relative_name(media_fullname):
    """get relative name"""
    original_path = current_app.config.get("SYS_MEDIA_ORIGINAL")
    relative_name_pos = len(original_path) + 1
    media_relative_name = media_fullname[relative_name_pos:]
    return media_relative_name


def _get_thumbnail_name(media_fullname):
    """get thumbnail name"""
    thumbnail_path = current_app.config.get("SYS_MEDIA_THUMBNAIL")
    media_relative_name = _get_relative_name(media_fullname)
    thumbnail_full_name = os.path.join(thumbnail_path, media_relative_name)
    return thumbnail_full_name


def get_media_files(pathname, filename, media_type):
    """get media files"""
    original_base_path = current_app.config.get("SYS_MEDIA_ORIGINAL")
    thumbnail_base_path = current_app.config.get("SYS_MEDIA_THUMBNAIL")
    original_media = os.path.join(original_base_path, pathname, filename)
    if media_type == MediaType.IMAGE.value:
        thumbnail_media = os.path.join(thumbnail_base_path, pathname, filename)
    elif media_type == MediaType.VIDEO.value:
        thumbnail_filename = _get_video_thumbnail_filename(filename)
        thumbnail_media = os.path.join(thumbnail_base_path, pathname, thumbnail_filename)
    else:
        thumbnail_media = None
    return original_media, thumbnail_media


def _verify_media_integrity(added_media, pathname, filename, media_type):
    """verify media integrity"""
    original_media, thumbnail_media = get_media_files(pathname, filename, media_type)
    if (
        (not added_media)
        or (not os.path.isfile(original_media))
        or (thumbnail_media and not os.path.isfile(thumbnail_media))
    ):
        if os.path.isfile(original_media):
            os.remove(original_media)
            current_app.logger.error(f"verify media integrity: remove original media {original_media}")
        if thumbnail_media and os.path.isfile(thumbnail_media):
            os.remove(thumbnail_media)
            current_app.logger.error(f"verify media integrity: remove thumbnail media {thumbnail_media}")
        if added_media:
            added_media.delete_media(added_media.uuidname)
            current_app.logger.error(f"verify media integrity: remove media {added_media.uuidname}")
    return added_media


def _normalize_media_extension(media_fullname):
    """normalize media extension"""
    prefix, ext = os.path.splitext(media_fullname)
    target_ext = ext.lower()
    if ext != target_ext:
        media_old_name, media_fullname = media_fullname, prefix + target_ext
        os.rename(media_old_name, media_fullname)
    return media_fullname


def _prepare_media_metadata(media_fullname, user_query_media_func):
    """prepare media metadata"""
    thumbnail_dirname = os.path.dirname(_get_thumbnail_name(media_fullname))
    os.makedirs(thumbnail_dirname, mode=0o750, exist_ok=True)

    return _create_thumbnail(
        media_fullname,
        thumbnail_dirname,
        current_app.config.get("SYS_MEDIA_THUMBNAIL_HEIGHT"),
        user_query_media_func,
    )


def import_user_media(media_fullname, is_public, user_query_media_func, user_add_media_func):
    """import user media"""
    media_fullname = _normalize_media_extension(media_fullname)
    relative_path = os.path.dirname(_get_relative_name(media_fullname))
    username = relative_path.split(os.sep)[0]
    metadata = _prepare_media_metadata(media_fullname, user_query_media_func)
    (width, height), media_type, media_datetime, media_filename = metadata
    props = (width, height, media_type, is_public)
    added_media = user_add_media_func(
        username,
        relative_path,
        media_filename,
        datetime.datetime.fromtimestamp(timestamp=media_datetime, tz=datetime.timezone.utc),
        props,
    )
    return _verify_media_integrity(added_media, relative_path, media_filename, media_type)


def import_user_medias(username, user_query_media_func, user_add_media_func):
    """import user medias"""
    original_path = current_app.config.get("SYS_MEDIA_ORIGINAL")
    thumbnail_path = os.path.join(current_app.config.get("SYS_MEDIA_THUMBNAIL"), username)

    cur_path = os.path.join(original_path, username)
    if not os.path.exists(cur_path):
        os.makedirs(cur_path, mode=0o750, exist_ok=True)
        return

    shutil.rmtree(thumbnail_path, ignore_errors=True)
    count = 0
    for root, _, files in os.walk(cur_path, topdown=False):
        for filename in files:
            import_user_media(os.path.join(root, filename), False, user_query_media_func, user_add_media_func)
            count += 1
            current_app.logger.info(f"imported {count} items, cuurent: {os.path.join(root, filename)}.")
