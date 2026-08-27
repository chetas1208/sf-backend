"""Container healthcheck for the configured Contacts API listener."""

from __future__ import annotations

import ipaddress
import urllib.request

from app.config import get_settings


def probe_host(configured_host: str) -> str:
    """Return a routable probe host for an application bind address."""

    host = configured_host.strip()
    if host in {"", "0.0.0.0"}:
        return "127.0.0.1"
    if host == "::":
        return "[::1]"

    try:
        address = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        return host

    return f"[{host.strip('[]')}]" if address.version == 6 else host


def health_url(host: str | None = None, port: str | None = None) -> str:
    """Build the health endpoint URL from the container's runtime settings."""

    settings = get_settings()
    configured_host = host if host is not None else settings.host
    configured_port = port if port is not None else str(settings.port)
    return f"http://{probe_host(configured_host)}:{configured_port}/health"


def main() -> None:
    with urllib.request.urlopen(health_url(), timeout=2) as response:
        if response.status >= 400:
            raise RuntimeError(f"healthcheck returned HTTP {response.status}")


if __name__ == "__main__":
    main()
