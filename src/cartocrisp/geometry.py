"""Convert raw Overpass JSON into typed, SVG-space geometry layers."""
from dataclasses import dataclass, field

from cartocrisp.bbox import BBox
from cartocrisp.projection import latlon_to_pixel


@dataclass(frozen=True)
class RoadSegment:
    points: list[tuple[float, float]]
    road_type: str
    name: str | None


@dataclass(frozen=True)
class Polygon:
    points: list[tuple[float, float]]
    kind: str  # "building" | "water" | "greenery"


@dataclass(frozen=True)
class Label:
    x: float
    y: float
    text: str
    priority: int  # lower is placed first / more important


@dataclass
class GeometryLayers:
    roads: list[RoadSegment] = field(default_factory=list)
    polygons: list[Polygon] = field(default_factory=list)
    labels: list[Label] = field(default_factory=list)


def build_layers(overpass_json: dict, bbox: BBox, zoom: float) -> GeometryLayers:
    elements = overpass_json["elements"]
    nodes = {el["id"]: (el["lat"], el["lon"]) for el in elements if el["type"] == "node"}
    origin_x, origin_y = latlon_to_pixel(bbox.max_lat, bbox.min_lon, zoom)

    def project(lat: float, lon: float) -> tuple[float, float]:
        x, y = latlon_to_pixel(lat, lon, zoom)
        return (x - origin_x, y - origin_y)

    layers = GeometryLayers()

    for el in elements:
        tags = el.get("tags", {})

        if el["type"] == "node" and "place" in tags and tags.get("name"):
            x, y = project(el["lat"], el["lon"])
            layers.labels.append(Label(x, y, tags["name"], priority=0))
            continue

        if el["type"] != "way":
            continue

        points = [project(*nodes[node_id]) for node_id in el.get("nodes", []) if node_id in nodes]

        if "highway" in tags and len(points) >= 2:
            layers.roads.append(RoadSegment(points, tags["highway"], tags.get("name")))
            if tags.get("name"):
                mid_x, mid_y = points[len(points) // 2]
                layers.labels.append(Label(mid_x, mid_y, tags["name"], priority=1))
        elif "building" in tags and len(points) >= 3:
            layers.polygons.append(Polygon(points, "building"))
        elif (tags.get("natural") == "water" or "waterway" in tags) and len(points) >= 2:
            layers.polygons.append(Polygon(points, "water"))
        elif (
            tags.get("leisure") in ("park", "garden") or tags.get("landuse") in ("forest", "grass", "park")
        ) and len(points) >= 3:
            layers.polygons.append(Polygon(points, "greenery"))

    return layers
