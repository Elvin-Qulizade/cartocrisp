from cartocrisp.bbox import compute_bbox
from cartocrisp.geometry import build_layers


def test_build_layers_extracts_roads_polygons_labels(overpass_fixture):
    bbox = compute_bbox(lat=40.409, lon=49.867, zoom=16, width_px=1600, height_px=1200)
    layers = build_layers(overpass_fixture, bbox, zoom=16)

    assert len(layers.roads) == 1
    assert layers.roads[0].name == "Nizami Street"

    kinds = {polygon.kind for polygon in layers.polygons}
    assert kinds == {"building", "water"}

    assert len(layers.labels) == 2  # the road name label + the place label
