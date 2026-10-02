from pathlib import Path

import numpy as np

from sstcbhf.io import load_gilbert_curve, load_gilbert_database


def test_parse_mini_database():
    path = Path(__file__).parents[1] / "examples" / "ideal_mini.txt"
    records = load_gilbert_database(path)
    assert [record.record_id for record in records] == ["0:1:1", "3:1:demo"]
    points, record = load_gilbert_curve(path, "0:1:1", samples=128)
    assert record.reported_length is not None
    radius = np.linalg.norm(points[:, :2], axis=1)
    assert np.max(np.abs(radius - 1.0)) < 1e-12
