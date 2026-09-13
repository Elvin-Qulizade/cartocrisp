from fastapi.testclient import TestClient

from cartocrisp.overpass import OverpassClient
from cartocrisp.web.app import app


def test_generate_endpoint_returns_svg(monkeypatch, tmp_path, overpass_fixture):
    monkeypatch.setattr(OverpassClient, "fetch", lambda self, bbox: overpass_fixture)
    monkeypatch.setattr("cartocrisp.overpass.DEFAULT_CACHE_PATH", tmp_path / "cache.sqlite3")

    client = TestClient(app)
    response = client.post("/generate", json={"link": "40.409,49.867,16", "lang": "en"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert b"Nizami Street" in response.content


def test_generate_endpoint_rejects_bad_link(monkeypatch, tmp_path):
    monkeypatch.setattr("cartocrisp.overpass.DEFAULT_CACHE_PATH", tmp_path / "cache.sqlite3")

    client = TestClient(app)
    response = client.post("/generate", json={"link": "garbage-input"})

    assert response.status_code == 400
