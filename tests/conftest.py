import json
from pathlib import Path

import pytest


@pytest.fixture
def overpass_fixture():
    path = Path(__file__).parent / "fixtures" / "overpass_sample.json"
    return json.loads(path.read_text(encoding="utf-8"))
