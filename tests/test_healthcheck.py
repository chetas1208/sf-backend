from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from app import healthcheck
from app.healthcheck import health_url, probe_host


@pytest.mark.parametrize(
    ("configured_host", "expected"),
    [
        ("", "127.0.0.1"),
        ("0.0.0.0", "127.0.0.1"),
        ("::", "[::1]"),
        ("::1", "[::1]"),
        ("api", "api"),
    ],
)
def test_probe_host_handles_wildcards_ipv6_and_hostnames(configured_host, expected):
    assert probe_host(configured_host) == expected


def test_health_url_uses_runtime_host_and_port():
    assert health_url("0.0.0.0", "9000") == "http://127.0.0.1:9000/health"
    assert health_url("api", "9000") == "http://api:9000/health"


def test_main_bypasses_proxy_environment(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()

        def log_message(self, _format, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        proxy = "http://127.0.0.1:1"
        monkeypatch.setenv("HTTP_PROXY", proxy)
        monkeypatch.setenv("http_proxy", proxy)
        monkeypatch.setenv("NO_PROXY", "")
        monkeypatch.setenv("no_proxy", "")
        monkeypatch.setattr(
            healthcheck,
            "health_url",
            lambda: f"http://127.0.0.1:{server.server_port}/health",
        )

        healthcheck.main()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
