from cartocrisp.geometry import GeometryLayers, Label, Polygon, RoadSegment
from cartocrisp.render.pdf import render_pdf


def test_render_pdf_writes_nonempty_file(tmp_path):
    layers = GeometryLayers(
        roads=[RoadSegment(points=[(0, 0), (100, 100)], road_type="primary", name="Main St")],
        polygons=[Polygon(points=[(10, 10), (20, 10), (20, 20)], kind="building")],
        labels=[Label(x=50, y=50, text="Main St", priority=1)],
    )
    output_path = tmp_path / "out.pdf"

    render_pdf(layers, 200, 200, "© OpenStreetMap contributors", output_path)

    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"%PDF")
