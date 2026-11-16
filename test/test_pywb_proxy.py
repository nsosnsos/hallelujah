"""Unit tests for pywb proxy URL validation."""

import socket
import unittest
from unittest.mock import patch

from hallelujah.pywb_proxy import PywbURLGuard, _target_from_pywb_path, validate_target_url


class ValidateTargetURLTests(unittest.TestCase):
    def test_rejects_non_http_schemes(self):
        for url in ("file:///etc/passwd", "ftp://example.com/file", "javascript:alert(1)"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_target_url(url, resolve_dns=False)

    def test_rejects_local_and_private_addresses(self):
        for url in ("http://localhost/", "http://127.0.0.1/", "http://10.0.0.2/",
                    "http://192.168.1.1/", "http://169.254.169.254/", "http://service.local/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_target_url(url, resolve_dns=False)

    def test_rejects_userinfo_and_nonstandard_ports(self):
        for url in ("https://user:pass@example.com/", "http://example.com:8080/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_target_url(url, resolve_dns=False)

    def test_accepts_public_ip_and_domain(self):
        self.assertEqual(validate_target_url("https://8.8.8.8/", resolve_dns=False).hostname, "8.8.8.8")
        with patch("hallelujah.pywb_proxy.socket.getaddrinfo", return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
        ]):
            self.assertEqual(validate_target_url("https://example.com/").hostname, "example.com")

    def test_rejects_domain_resolving_to_private_ip(self):
        with patch("hallelujah.pywb_proxy.socket.getaddrinfo", return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
        ]), self.assertRaises(ValueError):
            validate_target_url("https://example.com/")


class PywbPathTests(unittest.TestCase):
    def test_extracts_original_and_modified_urls(self):
        self.assertEqual(_target_from_pywb_path("/live/https://example.com/a"), "https://example.com/a")
        self.assertEqual(_target_from_pywb_path("/live/mp_/https://example.com/a"), "https://example.com/a")
        self.assertIsNone(_target_from_pywb_path("/live/"))
        self.assertIsNone(_target_from_pywb_path("/static/wombat.js"))

    def test_guard_blocks_private_targets(self):
        captured = {}
        def start_response(status, headers):
            captured["status"] = status
        app = PywbURLGuard(lambda environ, start_response: [b"ok"])
        response = app({"PATH_INFO": "/live/http://127.0.0.1/", "QUERY_STRING": "", "REQUEST_METHOD": "GET"}, start_response)
        self.assertEqual(captured["status"], "403 Forbidden")
        self.assertEqual(b"".join(response), b"Proxy target is not allowed")


if __name__ == "__main__":
    unittest.main()
