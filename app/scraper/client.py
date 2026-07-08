import hashlib
import time
from pathlib import Path
from typing import Optional

import httpx

BASE_URL = "https://www.filmweb.pl"
CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 "
    "(personal-use scraper; contact: pablo23k8@gmail.com)"
)

MAX_RETRIES = 3


class FilmwebClient:
    """Rate-limited HTTP client with an on-disk HTML cache.

    The cache lets repeated pipeline runs (e.g. after fixing a parser bug)
    skip re-downloading pages that were already fetched, which keeps load on
    filmweb.pl low and speeds up local iteration.
    """

    def __init__(self, delay_seconds: float = 1.5, use_cache: bool = True):
        self.delay_seconds = delay_seconds
        self.use_cache = use_cache
        self._last_request_at = 0.0
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT, "Accept-Language": "pl-PL,pl;q=0.9"},
            timeout=15.0,
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "FilmwebClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()  # noqa: ANN002 - exc_type/exc_val/exc_tb, unused

    def get_html(self, path: str, force_refresh: bool = False) -> str:
        """Fetch a page (path relative to BASE_URL) and return its raw HTML."""
        cache_file = self._cache_path(path)
        if self.use_cache and not force_refresh and cache_file.exists():
            return cache_file.read_text(encoding="utf-8")

        html = self._fetch_with_retries(path)

        if self.use_cache:
            cache_file.write_text(html, encoding="utf-8")
        return html

    def _fetch_with_retries(self, path: str) -> str:
        url = f"{BASE_URL}{path}"
        last_error: Optional[Exception] = None
        for attempt in range(1, MAX_RETRIES + 1):
            self._throttle()
            try:
                response = self._client.get(url)
            except httpx.HTTPError as exc:
                last_error = exc
            else:
                if response.status_code == 200:
                    return response.text
                if response.status_code in (429, 500, 502, 503, 504):
                    last_error = RuntimeError(f"HTTP {response.status_code} for {url}")
                else:
                    response.raise_for_status()
            backoff = 2**attempt
            time.sleep(backoff)
        raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} attempts") from last_error

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        remaining = self.delay_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_request_at = time.monotonic()

    @staticmethod
    def _cache_path(path: str) -> Path:
        digest = hashlib.sha256(path.encode("utf-8")).hexdigest()[:24]
        safe_suffix = "".join(c if c.isalnum() else "_" for c in path)[-60:]
        return CACHE_DIR / f"{digest}{safe_suffix}.html"
