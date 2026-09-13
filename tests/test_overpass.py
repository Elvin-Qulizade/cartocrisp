import httpx
import pytest

from cartocrisp.bbox import BBox
from cartocrisp.overpass import DEFAULT_QUERY_TIMEOUT, OverpassClient, OverpassUnavailableError, build_query

SAMPLE = {"elements": []}


def _client_with_transport(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_returns_json_and_caches(tmp_path):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=SAMPLE)

    client = OverpassClient(
        mirrors=("https://fake-overpass.example/api",),
        cache_path=tmp_path / "cache.sqlite3",
        http_client=_client_with_transport(handler),
    )
    bbox = BBox(min_lat=40.0, min_lon=49.0, max_lat=40.1, max_lon=49.1)

    result_1 = client.fetch(bbox)
    result_2 = client.fetch(bbox)

    assert result_1 == SAMPLE
    assert result_2 == SAMPLE
    assert len(calls) == 1  # second call served from cache


def test_fetch_raises_after_all_mirrors_fail(tmp_path, monkeypatch):
    monkeypatch.setattr("cartocrisp.overpass.time.sleep", lambda seconds: None)

    def handler(request):
        return httpx.Response(500)

    client = OverpassClient(
        mirrors=("https://fake-overpass.example/api",),
        cache_path=tmp_path / "cache.sqlite3",
        http_client=_client_with_transport(handler),
    )
    bbox = BBox(min_lat=40.0, min_lon=49.0, max_lat=40.1, max_lon=49.1)

    with pytest.raises(OverpassUnavailableError):
        client.fetch(bbox)


def test_fetch_skips_retries_on_client_error_and_tries_next_mirror(tmp_path, monkeypatch):
    """A 4xx response means this mirror will never succeed for this request -
    retrying it with backoff wastes the whole retry budget. Confirmed against
    real overpass-api.de, which returns 406 for every request from some
    networks while overpass.kumi.systems works fine - the client must not
    burn 3 retries against a mirror that is rejecting the request outright."""
    monkeypatch.setattr("cartocrisp.overpass.time.sleep", lambda seconds: None)
    broken_calls = []
    working_calls = []

    def handler(request):
        if "broken" in str(request.url):
            broken_calls.append(request)
            return httpx.Response(406)
        working_calls.append(request)
        return httpx.Response(200, json=SAMPLE)

    client = OverpassClient(
        mirrors=("https://broken-overpass.example/api", "https://working-overpass.example/api"),
        cache_path=tmp_path / "cache.sqlite3",
        http_client=_client_with_transport(handler),
    )
    bbox = BBox(min_lat=40.0, min_lon=49.0, max_lat=40.1, max_lon=49.1)

    result = client.fetch(bbox)

    assert result == SAMPLE
    assert len(broken_calls) == 1  # no retries burned on a definitive client error
    assert len(working_calls) == 1


def test_default_http_client_has_generous_timeout():
    client = OverpassClient(mirrors=("https://fake-overpass.example/api",))
    # The real dense-area query against a working mirror was measured at ~27s;
    # 30s left no margin and caused real, reported timeouts.
    assert client._client.timeout.read >= 60.0


def test_build_query_timeout_matches_client_headroom():
    bbox = BBox(min_lat=40.0, min_lon=49.0, max_lat=40.1, max_lon=49.1)
    query = build_query(bbox)
    assert f"[timeout:{DEFAULT_QUERY_TIMEOUT}]" in query
    assert DEFAULT_QUERY_TIMEOUT >= 50
