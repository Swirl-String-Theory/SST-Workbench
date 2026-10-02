import json
from pathlib import Path

import numpy as np

from sstcbhf.util import json_dump


def test_json_dump_converts_nonfinite_to_null(tmp_path: Path):
    path = tmp_path / "test.json"
    json_dump(path, {"a": np.nan, "b": np.inf, "c": np.float64(1.25)})
    payload = json.loads(path.read_text())
    assert payload == {"a": None, "b": None, "c": 1.25}
