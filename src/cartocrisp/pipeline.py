"""Ties link parsing, bbox math, Overpass fetch, geometry building, and
rendering into a single generate() call shared by the CLI and web UI."""
from dataclasses import dataclass
from pathlib import Path

from cartocrisp.bbox import AreaTooLargeError, compute_bbox
from cartocrisp.geometry import build_layers
from cartocrisp.i18n import translate
from cartocrisp.link_parser import UnrecognizedLinkError, parse_link, resolve_short_link
from cartocrisp.overpass import OverpassClient, OverpassUnavailableError
from cartocrisp.render.pdf import render_pdf
from cartocrisp.render.svg import write_svg


@dataclass(frozen=True)
class GenerateOptions:
    output_path: Path
    width_px: int = 1600
    height_px: int = 1200
    fmt: str = "svg"  # "svg" | "pdf"
    locale: str = "en"


class GenerationError(Exception):
    """A user-facing pipeline error; str(exc) is already localized."""


def generate(raw_link: str, options: GenerateOptions, overpass_client: OverpassClient | None = None) -> Path:
    client = overpass_client or OverpassClient()
    resolved_link = resolve_short_link(raw_link)

    try:
        location = parse_link(resolved_link)
    except UnrecognizedLinkError as exc:
        raise GenerationError(
            translate(options.locale, "error.unrecognized_link", input=exc.raw_input)
        ) from exc

    try:
        bbox = compute_bbox(location.lat, location.lon, location.zoom, options.width_px, options.height_px)
    except AreaTooLargeError as exc:
        raise GenerationError(
            translate(options.locale, "error.area_too_large", area=exc.area_km2, max_area=exc.max_km2)
        ) from exc

    try:
        overpass_json = client.fetch(bbox)
    except OverpassUnavailableError as exc:
        raise GenerationError(
            translate(options.locale, "error.overpass_unavailable", reason=exc.reason)
        ) from exc

    layers = build_layers(overpass_json, bbox, location.zoom)
    attribution = translate(options.locale, "attribution.osm")

    if options.fmt == "pdf":
        render_pdf(layers, options.width_px, options.height_px, attribution, options.output_path)
    else:
        write_svg(layers, options.width_px, options.height_px, attribution, options.output_path)

    return options.output_path
