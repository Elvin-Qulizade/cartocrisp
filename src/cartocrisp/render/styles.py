"""Visual styles and label-placement logic shared by the SVG and PDF renderers."""
from cartocrisp.geometry import Label

ROAD_STYLES = {
    "motorway": {"width": 5, "color": "#e66"},
    "trunk": {"width": 4.5, "color": "#f90"},
    "primary": {"width": 4, "color": "#fc0"},
    "secondary": {"width": 3, "color": "#ffffff"},
    "residential": {"width": 2, "color": "#ffffff"},
}
DEFAULT_ROAD_STYLE = {"width": 1.5, "color": "#dddddd"}

POLYGON_STYLES = {
    "building": "#d9d0c9",
    "water": "#a9cce3",
    "greenery": "#b7d7a8",
}


def place_non_overlapping_labels(labels: list[Label], min_distance: float = 40.0) -> list[Label]:
    """Greedily keep the highest-priority (lowest number) labels, dropping any
    that would land within min_distance of an already-placed label."""
    placed: list[Label] = []
    for label in sorted(labels, key=lambda l: l.priority):
        if all(_distance(label, other) >= min_distance for other in placed):
            placed.append(label)
    return placed


def _distance(a: Label, b: Label) -> float:
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
