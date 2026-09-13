import math

from cartocrisp.projection import latlon_to_pixel, pixel_to_latlon


def test_latlon_to_pixel_known_value_at_origin():
    x, y = latlon_to_pixel(lat=0.0, lon=0.0, zoom=0)
    assert math.isclose(x, 128.0, abs_tol=1e-6)
    assert math.isclose(y, 128.0, abs_tol=1e-6)


def test_pixel_to_latlon_is_inverse_of_latlon_to_pixel():
    original_lat, original_lon, zoom = 40.4093, 49.8671, 14
    x, y = latlon_to_pixel(original_lat, original_lon, zoom)
    lat, lon = pixel_to_latlon(x, y, zoom)
    assert math.isclose(lat, original_lat, abs_tol=1e-6)
    assert math.isclose(lon, original_lon, abs_tol=1e-6)
