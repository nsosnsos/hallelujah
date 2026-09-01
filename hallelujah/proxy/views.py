#!/usr/bin/env python3
"""
proxy views
provides proxy functionality with multi-user isolation
"""

from flask import Blueprint, Response, current_app, render_template, request
from flask_login import current_user, login_required

from .browser_identity import get_browser_headers
from .collection_manager import CollectionManager
from .http_client import http_client
from .pywb_integration import PywbIntegration

bp_proxy = Blueprint("proxy", __name__)

pywb_integration = PywbIntegration()
collection_manager = None


def init_proxy(app):
    """initialize proxy with Flask app"""
    global collection_manager

    proxy_storage = app.config.get("PROXY_STORAGE", "proxy_data")
    collection_manager = CollectionManager(proxy_storage, app)
    pywb_integration.init_app(app)
    http_client.app = app

    app.logger.info(f"Proxy initialized with storage: {proxy_storage}")


@bp_proxy.route("/proxy", methods=["POST", "GET"])
@login_required
def proxy():
    """proxy view"""
    try:
        url = request.args.get("url", None)

        if request.method == "POST":
            url = request.form.get("url", None)
            if url:
                return _proxy_post(url)
            return render_template("proxy/proxy.html")

        if not url:
            return render_template("proxy/proxy.html")

        return _proxy_get(url)

    except Exception as e:
        current_app.logger.error(f"Proxy error: {e}")
        return render_template("proxy/proxy.html")


def _proxy_get(url):
    """handle GET proxy request"""
    try:
        headers = get_browser_headers("chrome")
        response = http_client.get(
            url,
            headers=headers,
            allow_redirects=True,
            timeout=current_app.config.get("SYS_REQ_TIMEOUT", 30),
        )

        content_type = response["content_type"]
        content = response["content"]
        headers = response["headers"]

        headers["Access-Control-Allow-Origin"] = "*"
        headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        headers["Access-Control-Allow-Headers"] = "Content-Type"
        headers.pop("X-Frame-Options", None)
        headers.pop("Content-Security-Policy", None)

        if "text/html" in content_type:
            decoded_content = content.decode(response["encoding"], errors="replace")
            rewritten = pywb_integration.rewrite_html(decoded_content, url)
            return Response(rewritten, headers=headers, content_type=content_type)

        if "text/css" in content_type:
            decoded_content = content.decode(response["encoding"], errors="replace")
            rewritten = pywb_integration.rewrite_css(decoded_content, url)
            return Response(rewritten, headers=headers, content_type=content_type)

        if "javascript" in content_type:
            decoded_content = content.decode(response["encoding"], errors="replace")
            rewritten = pywb_integration.rewrite_js(decoded_content, url)
            return Response(rewritten, headers=headers, content_type=content_type)

        return Response(content, headers=headers, content_type=content_type)

    except Exception as e:
        current_app.logger.error(f"Proxy GET error for {url}: {e}")
        return render_template("proxy/proxy.html")


def _proxy_post(url):
    """handle POST proxy request"""
    try:
        headers = get_browser_headers("chrome")
        form_data = request.form.to_dict()

        response = http_client.post(
            url,
            data=form_data,
            headers=headers,
            allow_redirects=True,
            timeout=current_app.config.get("SYS_REQ_TIMEOUT", 30),
        )

        content_type = response["content_type"]
        content = response["content"]
        headers = response["headers"]

        headers["Access-Control-Allow-Origin"] = "*"
        headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        headers["Access-Control-Allow-Headers"] = "Content-Type"
        headers.pop("X-Frame-Options", None)
        headers.pop("Content-Security-Policy", None)

        if "text/html" in content_type:
            decoded_content = content.decode(response["encoding"], errors="replace")
            rewritten = pywb_integration.rewrite_html(decoded_content, url)
            return Response(rewritten, headers=headers, content_type=content_type)

        return Response(content, headers=headers, content_type=content_type)

    except Exception as e:
        current_app.logger.error(f"Proxy POST error for {url}: {e}")
        return render_template("proxy/proxy.html")


@bp_proxy.route("/proxy/api/proxy", methods=["POST"])
@login_required
def proxy_api():
    """proxy API endpoint for AJAX requests"""
    try:
        data = request.get_json()
        if not data or "url" not in data:
            return {"error": "URL is required"}, 400

        url = data["url"]
        method = data.get("method", "GET").upper()
        headers = get_browser_headers("chrome")

        if method == "POST":
            response = http_client.post(
                url,
                data=data.get("data"),
                headers=headers,
                allow_redirects=True,
                timeout=current_app.config.get("SYS_REQ_TIMEOUT", 30),
            )
        else:
            response = http_client.get(
                url,
                headers=headers,
                allow_redirects=True,
                timeout=current_app.config.get("SYS_REQ_TIMEOUT", 30),
            )

        content_type = response["content_type"]
        content = response["content"]
        resp_headers = response["headers"]

        resp_headers["Access-Control-Allow-Origin"] = "*"
        resp_headers.pop("X-Frame-Options", None)
        resp_headers.pop("Content-Security-Policy", None)

        if "text/html" in content_type:
            decoded_content = content.decode(response["encoding"], errors="replace")
            rewritten = pywb_integration.rewrite_html(decoded_content, url)
            return {
                "status": response["status_code"],
                "content": rewritten,
                "content_type": content_type,
                "headers": resp_headers,
            }

        return {
            "status": response["status_code"],
            "content": content.decode(response["encoding"], errors="replace"),
            "content_type": content_type,
            "headers": resp_headers,
        }

    except Exception as e:
        current_app.logger.error(f"Proxy API error: {e}")
        return {"error": str(e)}, 500
