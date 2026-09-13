from cartocrisp.geometry import GeometryLayers, Label, Polygon, RoadSegment
from cartocrisp.render.svg import render_svg, write_svg


def _sample_layers() -> GeometryLayers:
    return GeometryLayers(
        roads=[RoadSegment(points=[(0, 0), (100, 100)], road_type="primary", name="Main St")],
        polygons=[Polygon(points=[(10, 10), (20, 10), (20, 20)], kind="building")],
        labels=[Label(x=50, y=50, text="Main St", priority=1)],
    )


def test_render_svg_contains_expected_elements():
    svg = render_svg(_sample_layers(), width_px=200, height_px=200, attribution_text="© OpenStreetMap contributors")
    assert svg.startswith("<svg")
    assert svg.count("<path") == 2  # one polygon, one road
    assert "Main St" in svg
    assert "OpenStreetMap contributors" in svg


def test_write_svg_writes_file(tmp_path):
    output_path = tmp_path / "out.svg"
    write_svg(_sample_layers(), 200, 200, "© OpenStreetMap contributors", output_path)
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").startswith("<svg")
