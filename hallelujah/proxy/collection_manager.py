#!/usr/bin/env python3
"""
collection manager
manages per-user pywb collections for data isolation
"""

import os
import shutil
from datetime import datetime, timedelta


class CollectionManager:
    """manages per-user pywb collections"""

    def __init__(self, base_dir, app=None):
        self.base_dir = base_dir
        self.app = app
        self._ensure_base_dir()

    def _ensure_base_dir(self):
        """ensure base directory exists"""
        os.makedirs(self.base_dir, exist_ok=True)

    def get_user_collection_dir(self, user_id):
        """get collection directory for a user"""
        collection_name = f"user_{user_id}"
        collection_dir = os.path.join(self.base_dir, collection_name)
        os.makedirs(collection_dir, exist_ok=True)
        return collection_dir

    def get_user_collection_name(self, user_id):
        """get pywb collection name for a user"""
        return f"user_{user_id}"

    def ensure_user_collection(self, user_id):
        """ensure user collection exists and is properly configured"""
        collection_dir = self.get_user_collection_dir(user_id)
        archive_dir = os.path.join(collection_dir, "archive")
        os.makedirs(archive_dir, exist_ok=True)

        config_file = os.path.join(collection_dir, "config.yaml")
        if not os.path.exists(config_file):
            self._create_collection_config(collection_dir, user_id)

        return collection_dir

    def _create_collection_config(self, collection_dir, user_id):
        """create pywb collection config"""
        config_content = f"""# pywb collection config for user {user_id}
name: user_{user_id}
description: Proxy collection for user {user_id}
"""
        config_file = os.path.join(collection_dir, "config.yaml")
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_content)

    def cleanup_inactive_collections(self, days=30):
        """cleanup collections inactive for specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        cleaned = 0

        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            if os.path.isdir(item_path) and item.startswith("user_"):
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                    if mtime < cutoff_time:
                        shutil.rmtree(item_path)
                        cleaned += 1
                except (OSError, ValueError):
                    continue

        return cleaned

    def get_collection_stats(self, user_id):
        """get collection statistics for a user"""
        collection_dir = self.get_user_collection_dir(user_id)
        if not os.path.exists(collection_dir):
            return None

        total_size = 0
        file_count = 0
        for root, dirs, files in os.walk(collection_dir):
            for f in files:
                fp = os.path.join(root, f)
                total_size += os.path.getsize(fp)
                file_count += 1

        return {
            "collection_dir": collection_dir,
            "total_size": total_size,
            "file_count": file_count,
            "last_modified": datetime.fromtimestamp(os.path.getmtime(collection_dir)),
        }

    def delete_user_collection(self, user_id):
        """delete a user's collection"""
        collection_dir = self.get_user_collection_dir(user_id)
        if os.path.exists(collection_dir):
            shutil.rmtree(collection_dir)
            return True
        return False
