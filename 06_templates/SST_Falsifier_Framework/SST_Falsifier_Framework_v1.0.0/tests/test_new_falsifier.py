from pathlib import Path
import subprocess,sys

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
