"""Compute the geographic bounding box a canvas covers at a given center/zoom."""
import math
from dataclasses import dataclass

from cartocrisp.projection import latlon_to_pixel, pixel_to_latlon

MAX_AREA_KM2 = 400.0  # keeps Overpass queries bounded


@dataclass(frozen=True)
class BBox:
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


class AreaTooLargeError(Exception):
    def __init__(self, area_km2: float, max_km2: float):
        self.area_km2 = area_km2
        self.max_km2 = max_km2
        super().__init__(f"Requested area {area_km2:.1f} km^2 exceeds max {max_km2:.1f} km^2")


def compute_bbox(lat: float, lon: float, zoom: float, width_px: int, height_px: int) -> BBox:
    """Compute the bounding box a width_px x height_px canvas centered at
    (lat, lon) covers at the given zoom level."""
    center_x, center_y = latlon_to_pixel(lat, lon, zoom)
    half_w, half_h = width_px / 2.0, height_px / 2.0

    top_left_lat, top_left_lon = pixel_to_latlon(center_x - half_w, center_y - half_h, zoom)
    bottom_right_lat, bottom_right_lon = pixel_to_latlon(center_x + half_w, center_y + half_h, zoom)

    bbox = BBox(
        min_lat=bottom_right_lat,
        min_lon=top_left_lon,
        max_lat=top_left_lat,
        max_lon=bottom_right_lon,
    )
    _check_area(bbox)
    return bbox


def _check_area(bbox: BBox) -> None:
    lat_km = (bbox.max_lat - bbox.min_lat) * 111.0
    avg_lat_rad = math.radians((bbox.max_lat + bbox.min_lat) / 2.0)
    lon_km = (bbox.max_lon - bbox.min_lon) * 111.0 * math.cos(avg_lat_rad)
    area = abs(lat_km * lon_km)
    if area > MAX_AREA_KM2:
        raise AreaTooLargeError(area, MAX_AREA_KM2)
