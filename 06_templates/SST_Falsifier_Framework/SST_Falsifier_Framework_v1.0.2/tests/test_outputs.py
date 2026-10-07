from sst_falsifier.outputs import deterministic_zip
from sst_falsifier.util import sha256_file
from sst_falsifier.provenance import find_release_contamination

def test_deterministic_zip(tmp_path):
    r=tmp_path/"r";r.mkdir();(r/"a.txt").write_text("abc")
    z1=tmp_path/"1.zip";z2=tmp_path/"2.zip";deterministic_zip(r,z1);deterministic_zip(r,z2);assert sha256_file(z1)==sha256_file(z2)

def test_contamination_detected(tmp_path):
    (tmp_path/"x.pyd").write_bytes(b"x");(tmp_path/"__pycache__").mkdir(); assert len(find_release_contamination(tmp_path))>=2
