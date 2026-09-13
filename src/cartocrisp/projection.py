"""Web Mercator projection helpers shared by the bbox and geometry stages."""
import math

TILE_SIZE = 256


def latlon_to_pixel(lat: float, lon: float, zoom: float) -> tuple[float, float]:
    """Project (lat, lon) to absolute pixel coordinates at the given zoom level."""
    scale = TILE_SIZE * (2 ** zoom)
    x = (lon + 180.0) / 360.0 * scale
    sin_lat = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi)) * scale
    return x, y


def pixel_to_latlon(x: float, y: float, zoom: float) -> tuple[float, float]:
    """Inverse of latlon_to_pixel: absolute pixel coordinates -> (lat, lon)."""
    scale = TILE_SIZE * (2 ** zoom)
    lon = x / scale * 360.0 - 180.0
    n = math.pi - 2 * math.pi * y / scale
    lat = math.degrees(math.atan(math.sinh(n)))
    return lat, lon
