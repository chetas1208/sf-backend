import pytest

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
