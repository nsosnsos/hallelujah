#!/usr/bin/env python3
"""
http client module
provides browser-like HTTP requests using curl_cffi
"""

import json
from urllib.parse import urlparse

from flask import current_app

from .browser_identity import (
    CHROME_WINDOWS_HEADERS,
    get_curl_cffi_impersonate,
    get_browser_headers,
)


class HttpClient:
    """HTTP client with browser impersonation"""

    def __init__(self, app=None):
        self.app = app
        self._curl_cffi_available = False
        self._check_curl_cffi()

    def _check_curl_cffi(self):
        """check if curl_cffi is available"""
        try:
            import curl_cffi  # noqa: F401
            self._curl_cffi_available = True
        except ImportError:
            self._curl_cffi_available = False

    def get(self, url, headers=None, cookies=None, allow_redirects=True, timeout=30):
        """perform GET request"""
        return self._request(
            "GET",
            url,
            headers=headers,
            cookies=cookies,
            allow_redirects=allow_redirects,
            timeout=timeout,
        )

    def post(self, url, data=None, headers=None, cookies=None, allow_redirects=True, timeout=30):
        """perform POST request"""
        return self._request(
            "POST",
            url,
            data=data,
            headers=headers,
            cookies=cookies,
            allow_redirects=allow_redirects,
            timeout=timeout,
        )

    def _request(
        self,
        method,
        url,
        data=None,
        headers=None,
        cookies=None,
        allow_redirects=True,
        timeout=30,
    ):
        """perform HTTP request with browser impersonation"""
        request_headers = CHROME_WINDOWS_HEADERS.copy()
        if headers:
            request_headers.update(headers)

        if self._curl_cffi_available:
            return self._request_with_curl_cffi(
                method, url, data=data, headers=request_headers,
                cookies=cookies, allow_redirects=allow_redirects, timeout=timeout
            )
        else:
            return self._request_with_requests(
                method, url, data=data, headers=request_headers,
                cookies=cookies, allow_redirects=allow_redirects, timeout=timeout
            )

    def _request_with_curl_cffi(
        self, method, url, data=None, headers=None, cookies=None,
        allow_redirects=True, timeout=30, verify=None
    ):
        """perform request using curl_cffi"""
        from curl_cffi import requests as curl_requests

        impersonate = get_curl_cffi_impersonate("chrome")

        session = curl_requests.Session(impersonate=impersonate)

        try:
            response = session.request(
                method=method,
                url=url,
                data=data,
                headers=headers,
                cookies=cookies,
                allow_redirects=allow_redirects,
                timeout=timeout,
                verify=verify if verify is not None else self._get_verify(),
            )

            return self._normalize_response(response)
        finally:
            session.close()

    def _get_verify(self):
        """get SSL verification setting from app config"""
        if self.app is not None:
            return self.app.config.get("PROXY_VERIFY_SSL", True)
        return True

    def _request_with_requests(
        self, method, url, data=None, headers=None, cookies=None,
        allow_redirects=True, timeout=30
    ):
        """perform request using standard requests library"""
        import requests

        session = requests.Session()

        try:
            response = session.request(
                method=method,
                url=url,
                data=data,
                headers=headers,
                cookies=cookies,
                allow_redirects=allow_redirects,
                timeout=timeout,
            )

            return self._normalize_response(response)
        finally:
            session.close()

    def _normalize_response(self, response):
        """normalize response to common format"""
        content_type = response.headers.get("Content-Type", "")
        encoding = response.encoding or "utf-8"

        try:
            if "json" in content_type:
                text = json.dumps(response.json(), ensure_ascii=False)
                content = text.encode(encoding)
            else:
                content = response.content
        except Exception:
            content = response.content

        headers = dict(response.headers)
        headers.pop("Transfer-Encoding", None)
        headers.pop("Content-Encoding", None)

        return {
            "status_code": response.status_code,
            "headers": headers,
            "content": content,
            "content_type": content_type,
            "encoding": encoding,
            "url": response.url,
        }


http_client = HttpClient()
