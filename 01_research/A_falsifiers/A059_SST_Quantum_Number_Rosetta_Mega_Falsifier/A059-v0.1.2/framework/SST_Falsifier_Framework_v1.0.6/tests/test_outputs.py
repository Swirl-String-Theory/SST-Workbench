from sst_falsifier.outputs import deterministic_zip,make_output_manifest,verify_output_manifest
from sst_falsifier.util import sha256_file
from sst_falsifier.provenance import find_release_contamination


def test_deterministic_zip(tmp_path):
    r=tmp_path/"r";r.mkdir();(r/"a.txt").write_text("abc")
    z1=tmp_path/"1.zip";z2=tmp_path/"2.zip";deterministic_zip(r,z1);deterministic_zip(r,z2);assert sha256_file(z1)==sha256_file(z2)


def test_contamination_detected(tmp_path):
    (tmp_path/"x.pyd").write_bytes(b"x");(tmp_path/"__pycache__").mkdir(); assert len(find_release_contamination(tmp_path))>=2


def test_output_manifest_verifies_exact_tree(tmp_path):
    out=tmp_path/'out'; out.mkdir(); (out/'x.txt').write_text('abc',encoding='utf-8')
    make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    ok,detail=verify_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    assert ok,detail
    (out/'x.txt').write_text('changed',encoding='utf-8')
    ok,detail=verify_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    assert not ok and 'x.txt' in detail['changed']
