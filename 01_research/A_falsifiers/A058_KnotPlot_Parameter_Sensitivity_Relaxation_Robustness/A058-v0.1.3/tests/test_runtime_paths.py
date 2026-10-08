from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]

def _module():
    spec=importlib.util.spec_from_file_location("a058_run_kp", ROOT/"tools"/"run_knotplot_campaign.py")
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_outputs_workdir_selector():
    m=_module(); p,src=m._resolve_workdir("outputs")
    assert src=="instance_outputs"
    assert p.name.endswith("-outputs")

def test_explicit_exe_resolution(tmp_path):
    m=_module(); x=tmp_path/"KnotPlot.exe"; x.write_bytes(b"x")
    p,src=m._resolve_exe(str(x))
    assert p==x.resolve() and src=="argument"
