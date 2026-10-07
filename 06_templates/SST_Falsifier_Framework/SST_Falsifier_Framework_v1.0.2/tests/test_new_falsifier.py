from pathlib import Path
import os, subprocess, sys


def test_new_instance_unvalidated_and_private(tmp_path):
    root=Path(__file__).resolve().parents[1];dst=tmp_path/"A999-v0.1.0"
    cp=subprocess.run([sys.executable,str(root/"tools"/"new_falsifier.py"),"A999","demo",str(dst),"--profile","cpu"],text=True,capture_output=True)
    assert cp.returncode==0,cp.stderr
    assert "UNVALIDATED" in (dst/"VALIDATION.md").read_text()
    assert (dst/"private"/"OPAQUE_ID_KEY.bin").stat().st_size==32
    assert "profile = \"cpu\"" in (dst/"falsifier.toml").read_text()


def test_tex_profile_is_escaped(tmp_path):
    root=Path(__file__).resolve().parents[1];dst=tmp_path/"t"
    cp=subprocess.run([sys.executable,str(root/"tools"/"new_falsifier.py"),"A1","demo_name",str(dst),"--profile","multilibrary_gpu"],text=True,capture_output=True)
    assert cp.returncode==0
    tex=(dst/"report"/"FALSIFIER_REPORT.tex").read_text()
    assert "multilibrary\\_gpu" in tex and "demo\\_name" in tex


def test_generator_writes_relative_framework_locator(tmp_path):
    root=Path(__file__).resolve().parents[1]
    dst=tmp_path/"nested"/"A999-v0.1.0"
    cp=subprocess.run([sys.executable,str(root/"tools"/"new_falsifier.py"),"A999","demo",str(dst),"--profile","minimal"],text=True,capture_output=True)
    assert cp.returncode==0,cp.stderr
    locator=(dst/".sst_framework_root").read_text(encoding="utf-8").strip()
    assert locator
    assert not Path(locator).is_absolute()
    assert (dst/locator).resolve()==root.resolve()


def test_run_all_has_no_hardcoded_legacy_framework_path():
    root=Path(__file__).resolve().parents[1]
    cmd=(root/"instance_template"/"run_all.cmd").read_text(encoding="utf-8")
    assert "04_tools\\D_proof" not in cmd
    assert "SST_FALSIFIER_FRAMEWORK_ROOT=%~dp0" not in cmd


def test_run_instance_supports_nested_canonical_template_layout():
    root=Path(__file__).resolve().parents[1]
    src=(root/"instance_template"/"run_instance.py").read_text(encoding="utf-8")
    assert 'family = templates / "SST_Falsifier_Framework"' in src
    assert 'family.glob("SST_Falsifier_Framework_v*")' in src
    assert '04_tools' not in src and 'D_proof' not in src
