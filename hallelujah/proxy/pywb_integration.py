#!/usr/bin/env python3
"""
pywb integration layer
provides pywb-based content rewriting and proxy functionality
"""

import os
import tempfile
import threading
from urllib.parse import quote_plus, urljoin, urlparse

from bs4 import BeautifulSoup


class PywbIntegration:
    """pywb integration for content rewriting and proxy"""

    def __init__(self, app=None):
        self.app = app
        self._rewriter = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """initialize with Flask app"""
        self.app = app
        self._setup_rewriter()

    def _setup_rewriter(self):
        """setup the content rewriter"""
        try:
            from pywb.rewrite.rewriter import Rewriter

            self._rewriter = Rewriter
        except ImportError:
            self.app.logger.warning("pywb not available, using basic rewriter")
            self._rewriter = None

    def rewrite_html(self, content, base_url, proxy_prefix="/proxy"):
        """rewrite HTML content to route through proxy"""
        soup = BeautifulSoup(content, "html.parser")

        for tag in soup.find_all(["a", "link", "form"], href=True):
            tag["href"] = f"{proxy_prefix}?url={self._encode_url(base_url, tag['href'])}"

        for form in soup.find_all(["form"], action=True):
            form["action"] = f"{proxy_prefix}?url={self._encode_url(base_url, form['action'])}"

        for tag in soup.find_all(["img", "script", "link"], src=True):
            tag["src"] = f"{proxy_prefix}?url={self._encode_url(base_url, tag['src'])}"

        for tag in soup.find_all(["video", "audio"], src=True):
            tag["src"] = f"{proxy_prefix}?url={self._encode_url(base_url, tag['src'])}"

        for tag in soup.find_all(["source"], src=True):
            tag["src"] = f"{proxy_prefix}?url={self._encode_url(base_url, tag['src'])}"

        return str(soup)

    def rewrite_css(self, content, base_url, proxy_prefix="/proxy"):
        """rewrite CSS content to route through proxy"""
        import re

        def replace_url(match):
            url = match.group(1)
            if url.startswith(("http://", "https://", "//")):
                encoded = self._encode_url(base_url, url)
                return f'url("{proxy_prefix}?url={encoded}")'
            return match.group(0)

        return re.sub(r'url\(["\']?([^"\')\s]+)["\']?\)', replace_url, content)

    def rewrite_js(self, content, base_url, proxy_prefix="/proxy"):
        """rewrite JavaScript content (basic URL replacement)"""
        import re

        def replace_url(match):
            url = match.group(1)
            if url.startswith(("http://", "https://", "//")):
                encoded = self._encode_url(base_url, url)
                return f'{proxy_prefix}?url={encoded}'
            return match.group(0)

        content = re.sub(r'["\']?(https?://[^"\'\s]+)["\']?', replace_url, content)
        return content

    def _encode_url(self, base_url, relative_url):
        """encode URL for proxy parameter"""
        try:
            full_url = urljoin(base_url, relative_url)
            return quote_plus(full_url)
        except Exception:
            return quote_plus(relative_url)

    def extract_redirect_url(self, content):
        """extract redirect URL from meta refresh or javascript redirect"""
        import re

        soup = BeautifulSoup(content, "html.parser")

        meta_refresh = soup.find("meta", attrs={"http-equiv": "refresh"})
        if meta_refresh:
            content_attr = meta_refresh.get("content", "")
            match = re.search(r"url=(.+)", content_attr, re.IGNORECASE)
            if match:
                return match.group(1).strip().strip("'\"")

        return None
