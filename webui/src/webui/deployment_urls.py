"""Build browser-reachable URLs for the app, custom API routes, and Dagster UI."""

from __future__ import annotations

import os


def _strip_base(url: str) -> str:
    return url.strip().rstrip("/")


def resolve_public_backend_base_url(backend_port: int) -> str:
    """Return the base URL for the Reflex backend as seen from the user's browser.

    Precedence:
    1. ``PUBLIC_BACKEND_URL`` — explicit backend/custom API override
    2. ``DEPLOY_URL`` / ``PUBLIC_APP_URL`` — production fullstack app origin
    3. ``API_URL`` — legacy split-backend override, also read by Reflex
    4. ``http://localhost:{backend_port}`` — local dev backend
    """
    pub = os.environ.get("PUBLIC_BACKEND_URL", "").strip()
    if pub:
        return _strip_base(pub)
    app_url = resolve_configured_public_app_url()
    if app_url:
        return app_url
    api = os.environ.get("API_URL", "").strip()
    if api:
        return _strip_base(api)
    return f"http://localhost:{backend_port}"


def resolve_configured_public_app_url() -> str:
    """Return the configured public app origin, or empty when unset."""

    deploy = os.environ.get("DEPLOY_URL", "").strip()
    if deploy:
        return _strip_base(deploy)
    public_app = os.environ.get("PUBLIC_APP_URL", "").strip()
    if public_app:
        return _strip_base(public_app)
    return ""


def resolve_public_app_url() -> str:
    """Return the canonical browser-facing app origin for public metadata.

    ``DEPLOY_URL`` is preferred because production reverse proxies often expose a
    different public origin than the internal Reflex backend URL.
    """

    return resolve_configured_public_app_url() or "http://localhost:3000"


def resolve_dagster_web_public_url() -> str:
    """Return the Dagster web UI base URL as seen from the user's browser."""
    pub = os.environ.get("PUBLIC_DAGSTER_WEB_URL", "").strip()
    if pub:
        return _strip_base(pub)
    base = os.environ.get("DAGSTER_WEB_URL", "").strip()
    if base:
        return _strip_base(base)
    port = os.environ.get("DAGSTER_PORT", "3005").strip() or "3005"
    return f"http://localhost:{port}"
