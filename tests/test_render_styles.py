from cartocrisp.geometry import Label
from cartocrisp.render.styles import place_non_overlapping_labels


def test_overlapping_labels_are_dropped():
    labels = [
        Label(x=0, y=0, text="A", priority=0),
        Label(x=5, y=5, text="B", priority=1),  # too close to A, dropped
        Label(x=100, y=100, text="C", priority=1),  # far enough, kept
    ]
    placed = place_non_overlapping_labels(labels, min_distance=40.0)
    assert {label.text for label in placed} == {"A", "C"}
