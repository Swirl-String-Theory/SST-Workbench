from pathlib import Path

from sstcbhf.io import load_gilbert_database
from sstcbhf.util import sha256_file


def test_bundled_database_and_trefoil_metadata():
    path = Path(__file__).resolve().parents[1] / "data" / "ideal_favorites.txt"
    assert path.exists()
    assert path.stat().st_size == 786423
    assert sha256_file(path) == "942cb24b2a461b66cc3d35352f0723de97718a0e579ec524b8bb1c7ac4b9ad27"
    records = load_gilbert_database(path)
    trefoil = next(record for record in records if record.record_id == "3:1:1")
    assert trefoil.reported_length == 16.371637
    assert trefoil.diameter == 1.0
    assert len(trefoil.components[0]) == 183
