"""Parse a map link (Google Maps, OpenStreetMap, or plain text) into a location."""
import re
from dataclasses import dataclass

import httpx

_SHORTENER_DOMAINS = ("goo.gl", "maps.app.goo.gl")

_GOOGLE_AT_RE = re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+),(\d+(?:\.\d+)?)z")
_GOOGLE_3D4D_RE = re.compile(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)")
_GOOGLE_ZOOM_RE = re.compile(r"[,!](\d+(?:\.\d+)?)z")
_OSM_HASH_RE = re.compile(r"#map=(\d+(?:\.\d+)?)/(-?\d+\.\d+)/(-?\d+\.\d+)")
_PLAIN_RE = re.compile(r"^\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\s*,\s*(\d+(?:\.\d+)?)\s*$")


@dataclass(frozen=True)
class ParsedLocation:
    lat: float
    lon: float
    zoom: float


class UnrecognizedLinkError(Exception):
    def __init__(self, raw_input: str):
        self.raw_input = raw_input
        super().__init__(f"Could not parse a location from: {raw_input}")


class LinkResolutionError(Exception):
    def __init__(self, raw_input: str, reason: str):
        self.raw_input = raw_input
        self.reason = reason
        super().__init__(f"Could not resolve shortened link {raw_input}: {reason}")


def parse_link(raw_input: str) -> ParsedLocation:
    """Parse a Google Maps URL, an OSM URL, or a plain 'lat,lon,zoom' string."""
    match = _GOOGLE_AT_RE.search(raw_input)
    if match:
        lat, lon, zoom = match.groups()
        return ParsedLocation(float(lat), float(lon), float(zoom))

    match_3d4d = _GOOGLE_3D4D_RE.search(raw_input)
    if match_3d4d:
        lat, lon = match_3d4d.groups()
        zoom_match = _GOOGLE_ZOOM_RE.search(raw_input)
        zoom = float(zoom_match.group(1)) if zoom_match else 15.0
        return ParsedLocation(float(lat), float(lon), zoom)

    match_osm = _OSM_HASH_RE.search(raw_input)
    if match_osm:
        zoom, lat, lon = match_osm.groups()
        return ParsedLocation(float(lat), float(lon), float(zoom))

    match_plain = _PLAIN_RE.match(raw_input)
    if match_plain:
        lat, lon, zoom = match_plain.groups()
        return ParsedLocation(float(lat), float(lon), float(zoom))

    raise UnrecognizedLinkError(raw_input)


def resolve_short_link(raw_input: str, http_client: httpx.Client | None = None) -> str:
    """If raw_input is a shortened Google Maps link, resolve it to its final URL."""
    if not any(domain in raw_input for domain in _SHORTENER_DOMAINS):
        return raw_input

    client = http_client or httpx.Client(follow_redirects=True, timeout=10.0)
    try:
        response = client.get(raw_input)
    except httpx.HTTPError as exc:
        raise LinkResolutionError(raw_input, str(exc)) from exc
    return str(response.url)
