import httpx
import pytest

from cartocrisp.link_parser import (
    LinkResolutionError,
    ParsedLocation,
    UnrecognizedLinkError,
    parse_link,
    resolve_short_link,
)

GOOGLE_AT = "https://www.google.com/maps/@40.4093,49.8671,16z"
GOOGLE_PLACE = (
    "https://www.google.com/maps/place/Some+Place/@40.4093,49.8671,15z/"
    "data=!4m5!3m4!1s0x0:0x0!8m2!3d40.4093!4d49.8671"
)
GOOGLE_PLACE_NO_AT_WITH_ZOOM = (
    "https://www.google.com/maps/place/Some+Place/"
    "data=!4m5!3m4!1s0x0:0x0!8m2!3d40.4093!4d49.8671!16z"
)
GOOGLE_PLACE_NO_AT_NO_ZOOM = (
    "https://www.google.com/maps/place/Some+Place/"
    "data=!4m5!3m4!1s0x0:0x0!8m2!3d40.4093!4d49.8671"
)
OSM_HASH = "https://www.openstreetmap.org/#map=14/40.4093/49.8671"
PLAIN = "40.4093,49.8671,16"


@pytest.mark.parametrize(
    "raw_input,expected",
    [
        (GOOGLE_AT, ParsedLocation(40.4093, 49.8671, 16.0)),
        (OSM_HASH, ParsedLocation(40.4093, 49.8671, 14.0)),
        (PLAIN, ParsedLocation(40.4093, 49.8671, 16.0)),
    ],
)
def test_parse_link_recognized_formats(raw_input, expected):
    assert parse_link(raw_input) == expected


def test_parse_link_google_place_url():
    result = parse_link(GOOGLE_PLACE)
    assert result.lat == 40.4093
    assert result.lon == 49.8671
    assert result.zoom == 15.0


def test_parse_link_3d4d_with_separate_zoom_marker():
    result = parse_link(GOOGLE_PLACE_NO_AT_WITH_ZOOM)
    assert result.lat == 40.4093
    assert result.lon == 49.8671
    assert result.zoom == 16.0


def test_parse_link_3d4d_defaults_to_zoom_15_when_no_zoom_marker():
    result = parse_link(GOOGLE_PLACE_NO_AT_NO_ZOOM)
    assert result.lat == 40.4093
    assert result.lon == 49.8671
    assert result.zoom == 15.0


def test_parse_link_raises_for_garbage_input():
    with pytest.raises(UnrecognizedLinkError):
        parse_link("this is not a map link")


def test_resolve_short_link_follows_redirect():
    target = "https://www.google.com/maps/@40.4093,49.8671,16z"

    def handler(request):
        if str(request.url) == target:
            return httpx.Response(200)
        return httpx.Response(302, headers={"Location": target})

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
    resolved = resolve_short_link("https://maps.app.goo.gl/abc123", http_client=client)
    assert resolved == target


def test_resolve_short_link_passes_through_normal_links():
    resolved = resolve_short_link(GOOGLE_AT)
    assert resolved == GOOGLE_AT


def test_resolve_short_link_raises_link_resolution_error_on_connection_failure():
    def handler(request):
        raise httpx.ConnectError("connection refused")

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)

    with pytest.raises(LinkResolutionError) as exc_info:
        resolve_short_link("https://maps.app.goo.gl/abc123", http_client=client)

    assert exc_info.value.raw_input == "https://maps.app.goo.gl/abc123"
    assert exc_info.value.reason
