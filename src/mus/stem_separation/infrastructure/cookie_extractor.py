"""YouTube cookie extraction, validation, and cache management."""

from __future__ import annotations

import http.cookiejar
import logging
import re
import time
from pathlib import Path
from typing import cast

logger = logging.getLogger(__name__)

AUTH_COOKIE_NAMES: frozenset[str] = frozenset(
    {
        "SID",
        "SSID",
        "HSID",
        "SAPISID",
        "APISID",
        "LOGIN_INFO",
        "__Secure-1PSID",
        "__Secure-3PSID",
        "__Secure-1PAPISID",
        "__Secure-3PAPISID",
    }
)

DEFAULT_DOMAINS: tuple[str, ...] = ("youtube.com", "google.com", "ytimg.com")
IGNORED_SUBDOMAINS: tuple[str, ...] = (
    "docs",
    "drive",
    "mail",
    "cloud",
    "meet",
    "chat",
    "play",
    "photos",
)

SUPPORTED_BROWSERS: tuple[str, ...] = (
    "firefox",
    "chrome",
    "chromium",
    "brave",
    "edge",
    "opera",
    "vivaldi",
)

MAX_COOKIE_EXPIRY: int = 2147483647
MIN_COOKIE_FILE_BYTES: int = 50

_COOKIE_NAME_RE = re.compile(r"^[!-~]+$")
_COOKIE_VALUE_RE = re.compile(r"^[ -~]+$")


def has_valid_auth_cookies(cookie_file: Path) -> bool:
    """Checks if a cookie file exists and contains valid authenticated YouTube session tokens."""
    if not cookie_file.exists() or cookie_file.stat().st_size < MIN_COOKIE_FILE_BYTES:
        return False
    try:
        content = cookie_file.read_text(encoding="utf-8", errors="ignore")
        return any(
            f"\t{token}\t" in content or content.endswith(f"\t{token}")
            for token in AUTH_COOKIE_NAMES
        )
    except OSError:
        return False


def _extract_raw_cookies(browser: str) -> http.cookiejar.CookieJar | None:
    """Invokes yt-dlp internal browser cookie extraction with exception handling."""
    try:
        import yt_dlp.cookies  # noqa: PLC0415

        raw_jar = yt_dlp.cookies.extract_cookies_from_browser(browser)
        return cast(http.cookiejar.CookieJar, raw_jar)
    except Exception as exc:
        logger.debug("Failed extracting cookies from '%s': %s", browser, exc)
        return None


def _is_valid_cookie(cookie: http.cookiejar.Cookie, domains: tuple[str, ...]) -> bool:
    """Validates domain matching and basic sanity rules."""
    domain = (cookie.domain or "").lower()
    if not any(domain.endswith(d) for d in domains):
        return False

    if any(sub in domain for sub in IGNORED_SUBDOMAINS):
        return False

    if not cookie.name or not cookie.value or not cookie.value.strip():
        return False

    return bool(_COOKIE_NAME_RE.match(cookie.name) and _COOKIE_VALUE_RE.match(cookie.value))


def export_cookies_from_browser(
    browser: str,
    output_file: Path | str,
    domains: tuple[str, ...] = DEFAULT_DOMAINS,
    require_auth: bool = False,
) -> bool:
    """Extracts cookies from the given browser and writes a Netscape cookie file atomically."""
    out_path = Path(output_file).resolve()
    temp_path = out_path.with_suffix(".tmp")

    jar = _extract_raw_cookies(browser)
    if not jar:
        return False

    mcj = http.cookiejar.MozillaCookieJar(str(temp_path))
    valid_count = 0
    has_auth = False

    for c in jar:
        if not _is_valid_cookie(c, domains):
            continue

        if c.expires and c.expires > MAX_COOKIE_EXPIRY:
            c.expires = MAX_COOKIE_EXPIRY

        if c.name in AUTH_COOKIE_NAMES:
            has_auth = True

        mcj.set_cookie(c)
        valid_count += 1

    if valid_count == 0 or (require_auth and not has_auth):
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    mcj.save(ignore_discard=True, ignore_expires=True)
    temp_path.replace(out_path)
    logger.info("Saved %d cookies from '%s' to %s", valid_count, browser, out_path.name)
    return True


def export_cookies_auto(
    output_file: Path | str,
    preferred_browser: str | None = "firefox",
) -> bool:
    """Scans installed browsers in priority order, preferring authenticated sessions."""
    priority: list[str] = []
    if preferred_browser and preferred_browser in SUPPORTED_BROWSERS:
        priority.append(preferred_browser)
    for b in SUPPORTED_BROWSERS:
        if b not in priority:
            priority.append(b)

    # First pass: try with require_auth=True
    for b in priority:
        if export_cookies_from_browser(browser=b, output_file=output_file, require_auth=True):
            return True

    # Second pass: fallback without require_auth
    for b in priority:
        if export_cookies_from_browser(browser=b, output_file=output_file, require_auth=False):
            return True

    return False


def ensure_cookies_file(
    output_file: Path | str,
    browser: str | None = "firefox",
    max_age_hours: int = 12,
) -> Path | None:
    """Ensures an active, valid Netscape cookie file exists, refreshing cache if expired."""
    out_path = Path(output_file).resolve()
    should_refresh = False

    if (
        not out_path.exists()
        or out_path.stat().st_size < MIN_COOKIE_FILE_BYTES
        or not has_valid_auth_cookies(out_path)
    ):
        should_refresh = True
    elif max_age_hours > 0:
        age_seconds = time.time() - out_path.stat().st_mtime
        if age_seconds > max_age_hours * 3600:
            should_refresh = True

    if should_refresh:
        success = False
        if browser:
            success = export_cookies_from_browser(
                browser=browser, output_file=out_path, require_auth=True
            )
        if not success:
            success = export_cookies_auto(output_file=out_path, preferred_browser=browser)

    return out_path if out_path.exists() and out_path.stat().st_size > 0 else None
