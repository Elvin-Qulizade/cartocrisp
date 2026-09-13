"""Render geometry layers to a vector PDF document using reportlab."""
from pathlib import Path

from reportlab.pdfgen import canvas as pdf_canvas

from cartocrisp.geometry import GeometryLayers
from cartocrisp.render.styles import DEFAULT_ROAD_STYLE, POLYGON_STYLES, ROAD_STYLES, place_non_overlapping_labels


def render_pdf(
    layers: GeometryLayers, width_px: int, height_px: int, attribution_text: str, output_path: Path
) -> None:
    c = pdf_canvas.Canvas(str(output_path), pagesize=(width_px, height_px))
    c.setFillColorRGB(0.949, 0.937, 0.914)
    c.rect(0, 0, width_px, height_px, fill=1, stroke=0)

    def flip_y(y: float) -> float:
        return height_px - y

    for polygon in layers.polygons:
        c.setFillColor(POLYGON_STYLES.get(polygon.kind, "#cccccc"))
        path = c.beginPath()
        x0, y0 = polygon.points[0]
        path.moveTo(x0, flip_y(y0))
        for x, y in polygon.points[1:]:
            path.lineTo(x, flip_y(y))
        path.close()
        c.drawPath(path, fill=1, stroke=0)

    for road in layers.roads:
        style = ROAD_STYLES.get(road.road_type, DEFAULT_ROAD_STYLE)
        c.setStrokeColor(style["color"])
        c.setLineWidth(style["width"])
        path = c.beginPath()
        x0, y0 = road.points[0]
        path.moveTo(x0, flip_y(y0))
        for x, y in road.points[1:]:
            path.lineTo(x, flip_y(y))
        c.drawPath(path, fill=0, stroke=1)

    c.setFont("Helvetica", 9)
    c.setFillColor("#333333")
    for label in place_non_overlapping_labels(layers.labels):
        c.drawString(label.x, flip_y(label.y), label.text)

    c.setFont("Helvetica", 8)
    c.setFillColor("#666666")
    c.drawString(8, 8, attribution_text)
    c.save()
