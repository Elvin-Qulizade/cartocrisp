"""Fetch OSM elements for a bounding box from the Overpass API, with local caching."""
import json
import sqlite3
import time
from pathlib import Path

import httpx

from cartocrisp.bbox import BBox

DEFAULT_MIRRORS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)
DEFAULT_CACHE_PATH = Path.home() / ".cache" / "cartocrisp" / "overpass_cache.sqlite3"
# Real dense-city-center queries were measured at 27-37s against a healthy
# mirror, with occasional much slower responses under public-API load;
# 25/30s left too little margin and caused real, reported timeouts.
DEFAULT_QUERY_TIMEOUT = 80
DEFAULT_HTTP_TIMEOUT = 90.0


class OverpassUnavailableError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Overpass API unavailable: {reason}")


def build_query(bbox: BBox) -> str:
    box = f"{bbox.min_lat},{bbox.min_lon},{bbox.max_lat},{bbox.max_lon}"
    return f"""
[out:json][timeout:{DEFAULT_QUERY_TIMEOUT}];
(
  way["highway"]({box});
  way["building"]({box});
  way["natural"="water"]({box});
  way["waterway"]({box});
  way["leisure"~"park|garden"]({box});
  way["landuse"~"forest|grass|park"]({box});
  node["place"]({box});
);
out body;
>;
out skel qt;
""".strip()


class OverpassClient:
    def __init__(self, mirrors=DEFAULT_MIRRORS, cache_path=None, http_client=None):
        self.mirrors = mirrors
        self.cache_path = Path(cache_path) if cache_path is not None else DEFAULT_CACHE_PATH
        self._client = http_client or httpx.Client(timeout=DEFAULT_HTTP_TIMEOUT)
        self._init_cache()

    def fetch(self, bbox: BBox) -> dict:
        key = self._cache_key(bbox)
        cached = self._read_cache(key)
        if cached is not None:
            return cached

        query = build_query(bbox)
        last_error: Exception | None = None
        for mirror in self.mirrors:
            for attempt in range(3):
                try:
                    response = self._client.post(mirror, data={"data": query})
                    response.raise_for_status()
                    payload = response.json()
                    self._write_cache(key, payload)
                    return payload
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    if 400 <= exc.response.status_code < 500:
                        # A client error means this mirror will never succeed for
                        # this request - don't burn retries/backoff on it, move on.
                        break
                    time.sleep(2 ** attempt)
                except (httpx.HTTPError, ValueError) as exc:
                    last_error = exc
                    time.sleep(2 ** attempt)
        raise OverpassUnavailableError(str(last_error))

    def _init_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.cache_path)
        conn.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, payload TEXT, fetched_at REAL)")
        conn.commit()
        conn.close()

    def _cache_key(self, bbox: BBox) -> str:
        return f"{bbox.min_lat:.4f},{bbox.min_lon:.4f},{bbox.max_lat:.4f},{bbox.max_lon:.4f}"

    def _read_cache(self, key: str):
        conn = sqlite3.connect(self.cache_path)
        row = conn.execute("SELECT payload FROM cache WHERE key = ?", (key,)).fetchone()
        conn.close()
        return json.loads(row[0]) if row else None

    def _write_cache(self, key: str, payload: dict) -> None:
        conn = sqlite3.connect(self.cache_path)
        conn.execute(
            "INSERT OR REPLACE INTO cache (key, payload, fetched_at) VALUES (?, ?, ?)",
            (key, json.dumps(payload), time.time()),
        )
        conn.commit()
        conn.close()
