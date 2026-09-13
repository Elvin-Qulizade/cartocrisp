from cartocrisp.cli import main
from cartocrisp.overpass import OverpassClient


def test_cli_generates_svg(tmp_path, monkeypatch, overpass_fixture):
    monkeypatch.setattr(OverpassClient, "fetch", lambda self, bbox: overpass_fixture)
    monkeypatch.setattr("cartocrisp.overpass.DEFAULT_CACHE_PATH", tmp_path / "cache.sqlite3")

    output_path = tmp_path / "map.svg"
    exit_code = main(["40.409,49.867,16", "-o", str(output_path), "--lang", "en"])

    assert exit_code == 0
    assert output_path.exists()
    assert "Nizami Street" in output_path.read_text(encoding="utf-8")


def test_cli_reports_error_for_bad_link(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("cartocrisp.overpass.DEFAULT_CACHE_PATH", tmp_path / "cache.sqlite3")
    output_path = tmp_path / "map.svg"

    exit_code = main(["garbage-input", "-o", str(output_path), "--lang", "en"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "garbage-input" in captured.err
