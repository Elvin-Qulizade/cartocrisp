from cartocrisp.bbox import BBox
from cartocrisp.pipeline import GenerateOptions, GenerationError, generate


class FakeOverpassClient:
    def __init__(self, payload):
        self.payload = payload

    def fetch(self, bbox: BBox) -> dict:
        return self.payload


def test_generate_writes_svg_file(tmp_path, overpass_fixture):
    output_path = tmp_path / "map.svg"
    options = GenerateOptions(output_path=output_path, width_px=800, height_px=600, fmt="svg", locale="en")

    result_path = generate("40.409,49.867,16", options, overpass_client=FakeOverpassClient(overpass_fixture))

    assert result_path == output_path
    content = output_path.read_text(encoding="utf-8")
    assert content.startswith("<svg")
    assert "Nizami Street" in content
    assert "OpenStreetMap contributors" in content


def test_generate_rejects_unrecognized_link(tmp_path, overpass_fixture):
    options = GenerateOptions(output_path=tmp_path / "map.svg", locale="en")

    try:
        generate("not a link at all", options, overpass_client=FakeOverpassClient(overpass_fixture))
        assert False, "expected GenerationError"
    except GenerationError as exc:
        assert "not a link at all" in str(exc)
