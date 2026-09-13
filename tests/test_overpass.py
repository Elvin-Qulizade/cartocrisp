import httpx
import pytest

from cartocrisp.bbox import BBox
from cartocrisp.overpass import OverpassClient, OverpassUnavailableError

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
