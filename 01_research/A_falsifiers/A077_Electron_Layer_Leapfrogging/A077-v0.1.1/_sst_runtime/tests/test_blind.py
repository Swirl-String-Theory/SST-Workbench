from pathlib import Path
from sst_falsifier.blind import scan_tree,opaque_id,reveal_commitment,verify_reveal,blind_terms_commitment,verify_blind_terms

def test_scan_includes_tex(tmp_path):
    (tmp_path/"x.tex").write_text("SECRET_TARGET",encoding="utf-8")
    assert scan_tree(tmp_path,["secret_target"])[0]["path"]=="x.tex"

def test_private_tree_excluded(tmp_path):
    (tmp_path/"private").mkdir();(tmp_path/"private"/"x.txt").write_text("SECRET_TARGET")
    assert scan_tree(tmp_path,["secret_target"])==[]

def test_hmac_opaque_id_depends_on_secret():
    assert opaque_id("3_1",b"a"*32)!=opaque_id("3_1",b"b"*32)

def test_nonced_reveal_commitment(tmp_path):
    r=tmp_path/"r.json";n=tmp_path/"n.bin";c=tmp_path/"c.json";r.write_text('{"x":1}');n.write_bytes(b"n"*32);reveal_commitment(r,n,c);assert verify_reveal(r,n,c)[0];r.write_text('{"x":2}');assert not verify_reveal(r,n,c)[0]


def test_blind_terms_commitment(tmp_path):
    t=tmp_path/"terms.txt";n=tmp_path/"n.bin";c=tmp_path/"c.json";t.write_text("secret\n");n.write_bytes(b"z"*32);blind_terms_commitment(t,n,c);assert verify_blind_terms(t,n,c)[0];t.write_text("other\n");assert not verify_blind_terms(t,n,c)[0]


def test_runtime_vendor_trees_are_excluded_from_blind_scan(tmp_path):
    forbidden="SECRET_TARGET"
    for rel in [
        ".venv/Lib/site-packages/pkg/x.py",
        "venv/lib/python/site-packages/pkg/x.py",
        "build/generated/x.cpp",
        "dist/vendor/x.txt",
        "node_modules/pkg/x.py",
        "__pycache__/x.txt",
    ]:
        p=tmp_path/rel
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(forbidden,encoding="utf-8")
    assert scan_tree(tmp_path,[forbidden])==[]


def test_instance_owned_source_remains_fail_closed(tmp_path):
    (tmp_path/"owned.py").write_text("SECRET_TARGET",encoding="utf-8")
    hits=scan_tree(tmp_path,["secret_target"])
    assert hits==[{"path":"owned.py","term":"secret_target"}]
