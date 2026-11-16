"""pywb live-collection integration and URL safety checks."""

import ipaddress
import re
import socket
from urllib.parse import unquote, urlsplit

_URL_RE = re.compile(r"https?://", re.IGNORECASE)
_REPLAY_MODIFIERS = {
    "id_", "im_", "if_", "mp_", "oe_", "js_", "cs_", "es_", "sw_",
    "wkrf_", "wkr_", "bn_", "fr_", "fw_",
}
_BLOCKED_SUFFIXES = (".localhost", ".local", ".internal", ".test", ".invalid")


def validate_target_url(url, *, resolve_dns=True):
    """Validate a public HTTP(S) URL before handing it to pywb."""
    if not isinstance(url, str) or not url or len(url) > 8192:
        raise ValueError("Invalid URL")
    parsed = urlsplit(url.strip())
    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are allowed")
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise ValueError("Invalid URL authority")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid URL port") from exc
    expected_port = 443 if parsed.scheme.lower() == "https" else 80
    if port is not None and port != expected_port:
        raise ValueError("Only the standard port for the URL scheme is allowed")
    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(_BLOCKED_SUFFIXES):
        raise ValueError("Local hostnames are not allowed")
    try:
        literal_ip = ipaddress.ip_address(host)
    except ValueError:
        literal_ip = None
    if literal_ip is not None:
        if not literal_ip.is_global:
            raise ValueError("Non-public IP addresses are not allowed")
        return parsed
    if "." not in host:
        raise ValueError("Single-label hostnames are not allowed")
    if resolve_dns:
        try:
            answers = socket.getaddrinfo(host, port or expected_port, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise ValueError("Hostname could not be resolved") from exc
        addresses = {answer[4][0] for answer in answers}
        if not addresses:
            raise ValueError("Hostname has no addresses")
        for address in addresses:
            try:
                ip = ipaddress.ip_address(address.split("%", 1)[0])
            except ValueError as exc:
                raise ValueError("Invalid DNS address") from exc
            if not ip.is_global:
                raise ValueError("Host resolves to a non-public IP address")
    return parsed


def _target_from_pywb_path(path_info):
    """Extract the original URL from a pywb live-collection request path."""
    path = unquote(path_info or "")
    if not path.startswith("/live/"):
        return None
    remainder = path[len("/live/"):]
    parts = remainder.split("/", 1)
    while parts and parts[0] in _REPLAY_MODIFIERS:
        remainder = parts[1] if len(parts) > 1 else ""
        parts = remainder.split("/", 1)
    match = _URL_RE.search(remainder)
    return remainder[match.start():] if match else None


class PywbURLGuard:
    """WSGI middleware rejecting non-public targets on every pywb request."""
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path_info = environ.get("PATH_INFO", "")
        target = _target_from_pywb_path(path_info)
        if path_info.startswith("/live/") and target is None and path_info.rstrip("/") != "/live":
            body = b"Invalid proxy target"
            start_response("400 Bad Request", [
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Content-Length", str(len(body))),
                ("Cache-Control", "no-store"),
            ])
            return [body]
        if target:
            try:
                validate_target_url(target)
            except ValueError:
                body = b"Proxy target is not allowed"
                start_response("403 Forbidden", [
                    ("Content-Type", "text/plain; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                    ("Cache-Control", "no-store"),
                ])
                return [body]
        return self.app(environ, start_response)


def create_pywb_app():
    """Build pywb with a live collection, guarded by URL validation."""
    from pywb.apps.frontendapp import FrontEndApp
    app = FrontEndApp(custom_config={"collections": {"live": {"index": "$live"}}})
    return PywbURLGuard(app)
