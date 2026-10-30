from __future__ import annotations
from pathlib import Path
import json
import zipfile
import pytest
from sst_falsifier.output_policy import (new_run_id, reserve_blind_output, read_run_id,
    package_path,report_path, instance_lock)
from sst_falsifier.outputs import deterministic_zip, make_output_manifest,verify_output_manifest
from sst_falsifier.report import compile_report_pdf
from sst_falsifier.blind import scan_tree

CFG={'project':{'name':'A888','version':'v0.1.0'}}


def test_new_run_archives_existing_without_overwrite(tmp_path):
    instance=tmp_path/'A888-v0.1.0'; instance.mkdir()
    out=instance/'A888_v0.1.0-outputs'; out.mkdir()
    (out/'RUN_SUMMARY.json').write_text('old')
    legacy_zip=tmp_path/'A888_v0.1.0-outputs_BLIND.zip'; legacy_zip.write_bytes(b'oldzip')
    legacy_pdf=tmp_path/'A888-v0.1.0_FALSIFIER_REPORT.pdf'; legacy_pdf.write_bytes(b'oldpdf')
    with instance_lock(instance):
        first, archived=reserve_blind_output(instance,out,CFG,'BASIC')
    assert archived is not None and (archived/'RUN_SUMMARY.json').read_text()=='old'
    assert read_run_id(out)==first
    (out/'RUN_SUMMARY.json').write_text('new')
    with instance_lock(instance):
        second, archived2=reserve_blind_output(instance,out,CFG,'FULL')
    assert second!=first and archived2 is not None
    assert (archived2/'RUN_SUMMARY.json').read_text()=='new'
    assert legacy_zip.read_bytes()==b'oldzip' and legacy_pdf.read_bytes()==b'oldpdf'
    assert package_path(instance,CFG,first,'BLIND')!=package_path(instance,CFG,second,'BLIND')
    assert report_path(instance,first,'BLIND')!=report_path(instance,first,'REVEALED')


def test_zip_fails_closed_on_existing_destination(tmp_path):
    root=tmp_path/'r';root.mkdir();(root/'a.txt').write_text('new')
    z=tmp_path/'arch.zip'; z.write_bytes(b'preexisting')
    with pytest.raises(FileExistsError): deterministic_zip(root,z)
    assert z.read_bytes()==b'preexisting'


def test_pdf_fails_closed_without_replacing_existing_file(tmp_path):
    src=tmp_path/'report.tex';src.write_text('\\documentclass{article}\\begin{document}Hello\\end{document}')
    dest=tmp_path/'existing.pdf';dest.write_bytes(b'PRESERVE')
    import shutil
    if not(shutil.which('pdflatex') or shutil.which('latexmk')):pytest.skip('TeX unavailable')
    with pytest.raises(FileExistsError):compile_report_pdf(src,dest,strict=True)
    assert dest.read_bytes()==b'PRESERVE'


def test_lock_prevents_parallel_publish(tmp_path):
    root=tmp_path/'instance';root.mkdir()
    with instance_lock(root):
        with pytest.raises(RuntimeError,match='another run'):
            with instance_lock(root): pass
    with instance_lock(root): pass


def test_archives_excluded_from_blind_scanner_but_current_owned_source_scanned(tmp_path):
    root=tmp_path/'instance';root.mkdir()
    archived=root/f'X_v1.0.0-outputs__{new_run_id()}';archived.mkdir()
    (archived/'old.txt').write_text('private_reveal_token',encoding='utf-8')
    current=root/'X_v1.0.0-outputs'; current.mkdir()
    assert scan_tree(root,('private_reveal_token',))==[]
    (current/'owned.txt').write_text('private_reveal_token',encoding='utf-8')
    assert any(x['path'].endswith('owned.txt') for x in scan_tree(root,('private_reveal_token',)))


def test_new_run_manifest_tracks_identity(tmp_path):
    root=tmp_path/'instance';root.mkdir();out=root/'X_v0.1.0-outputs'
    cfg={'project':{'name':'X','version':'v0.1.0'}}
    with instance_lock(root):run_id,_=reserve_blind_output(root,out,cfg,'FULL')
    make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    ok,detail=verify_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    assert ok,detail
    assert json.loads((out/'RUN_ID.json').read_text())['run_id']==run_id


def test_archive_existing_invalid_identity_fails_closed(tmp_path):
    root=tmp_path/'instance';root.mkdir();out=root/'X_v0.1.0-outputs';out.mkdir()
    (out/'RUN_ID.json').write_text('{"run_id":"../../escape"}',encoding='utf-8')
    (out/'old.txt').write_text('must survive',encoding='utf-8')
    with instance_lock(root):
        with pytest.raises(RuntimeError,match='invalid existing RUN_ID'):
            reserve_blind_output(root,out,{'project':{'name':'X','version':'v0.1.0'}},'FULL')
    assert (out/'old.txt').read_text()=='must survive'
