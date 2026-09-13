import pytest

from cartocrisp.bbox import AreaTooLargeError, compute_bbox


def test_compute_bbox_is_centered_and_ordered():
    bbox = compute_bbox(lat=40.4093, lon=49.8671, zoom=16, width_px=800, height_px=600)
    assert bbox.min_lat < 40.4093 < bbox.max_lat
    assert bbox.min_lon < 49.8671 < bbox.max_lon


def test_compute_bbox_raises_when_area_too_large():
    with pytest.raises(AreaTooLargeError):
        compute_bbox(lat=40.4093, lon=49.8671, zoom=1, width_px=1600, height_px=1200)
