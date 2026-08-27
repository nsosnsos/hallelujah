#!/usr/bin/env python3
"""debug"""

import datetime
import os
import sys

import hallelujah

app = hallelujah.create_app("development")
with app.app_context():
    cur_path = sys.argv[1]
    if not os.path.exists(cur_path):
        print(f"{cur_path} is not found")
        sys.exit(1)

    count = 0
    for root, _, files in os.walk(cur_path, topdown=False):
        for filename in files:
            cur_file = os.path.join(root, filename)
            file_ext = os.path.splitext(cur_file)[1]
            if file_ext in hallelujah.utility.IMAGE_SUFFIXES:
                ts = hallelujah.utility.get_image_timestamp(cur_file)
                ts_str = datetime.datetime.fromtimestamp(timestamp=ts, tz=datetime.timezone.utc)
                print(f"[{count}]{cur_file} created at {ts_str}")
                hallelujah.utility.set_image_timestamp(cur_file, ts)
                ts = hallelujah.utility.get_image_timestamp(cur_file)
                ts_str = datetime.datetime.fromtimestamp(timestamp=ts, tz=datetime.timezone.utc)
                print(f"[{count}]{cur_file} updated at {ts_str}")
            elif file_ext in hallelujah.utility.VIDEO_SUFFIXES:
                ts = hallelujah.utility.get_video_timestamp(cur_file)
                ts_str = datetime.datetime.fromtimestamp(timestamp=ts, tz=datetime.timezone.utc)
                print(f"[{count}]{cur_file} created at {ts_str}")
                hallelujah.utility.set_video_timestamp(cur_file, ts)
                ts = hallelujah.utility.get_video_timestamp(cur_file)
                ts_str = datetime.datetime.fromtimestamp(timestamp=ts, tz=datetime.timezone.utc)
                print(f"[{count}]{cur_file} updated at {ts_str}")
            else:
                pass
            count += 1
