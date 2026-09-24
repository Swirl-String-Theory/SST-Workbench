from pathlib import Path
from sst_thpcf.campaign import run

def test_python_smoke(tmp_path):
    root=Path(__file__).parents[1]
    out=run(root/"configs/smoke.json",backend="python",root=root,reveal=False)
    assert (out/"summary.json").exists()
