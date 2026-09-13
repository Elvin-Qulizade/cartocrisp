"""Render geometry layers to a true vector SVG document."""
from pathlib import Path

from cartocrisp.geometry import GeometryLayers
from cartocrisp.render.styles import DEFAULT_ROAD_STYLE, POLYGON_STYLES, ROAD_STYLES, place_non_overlapping_labels


def render_svg(layers: GeometryLayers, width_px: int, height_px: int, attribution_text: str) -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_px}" height="{height_px}" '
        f'viewBox="0 0 {width_px} {height_px}">',
        f'<rect x="0" y="0" width="{width_px}" height="{height_px}" fill="#f2efe9"/>',
    ]

    for polygon in layers.polygons:
        color = POLYGON_STYLES.get(polygon.kind, "#cccccc")
        path = _points_to_path(polygon.points, close=True)
        parts.append(f'<path d="{path}" fill="{color}" stroke="none"/>')

    for road in layers.roads:
        style = ROAD_STYLES.get(road.road_type, DEFAULT_ROAD_STYLE)
        path = _points_to_path(road.points, close=False)
        parts.append(
            f'<path d="{path}" fill="none" stroke="{style["color"]}" '
            f'stroke-width="{style["width"]}" stroke-linecap="round" stroke-linejoin="round"/>'
        )

    for label in place_non_overlapping_labels(layers.labels):
        parts.append(
            f'<text x="{label.x:.1f}" y="{label.y:.1f}" font-size="11" '
            f'font-family="sans-serif" fill="#333333">{_escape(label.text)}</text>'
        )

    parts.append(
        f'<text x="8" y="{height_px - 8}" font-size="10" font-family="sans-serif" '
        f'fill="#666666">{_escape(attribution_text)}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def write_svg(
    layers: GeometryLayers, width_px: int, height_px: int, attribution_text: str, output_path: Path
) -> None:
    svg = render_svg(layers, width_px, height_px, attribution_text)
    Path(output_path).write_text(svg, encoding="utf-8")


def _points_to_path(points: list[tuple[float, float]], close: bool) -> str:
    if not points:
        return ""
    commands = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
    commands += [f"L {x:.1f} {y:.1f}" for x, y in points[1:]]
    if close:
        commands.append("Z")
    return " ".join(commands)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
