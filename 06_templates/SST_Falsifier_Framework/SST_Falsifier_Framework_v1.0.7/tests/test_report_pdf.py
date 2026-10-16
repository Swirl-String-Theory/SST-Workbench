from pathlib import Path
import shutil
import pytest
from sst_falsifier.report import compile_report_pdf,publish_instance_report


def test_report_pdf_publish_location(tmp_path):
    if not (shutil.which('pdflatex') or shutil.which('latexmk')):
        pytest.skip('LaTeX engine not installed')
    root=tmp_path/'A056-v0.2.0'; src=root/'A056-v0.2.0-outputs'/'BLIND'; src.mkdir(parents=True)
    tex=src/'A056_FALSIFIER_REPORT.tex'
    tex.write_text(r'''\documentclass{article}\begin{document}SST report smoke.\end{document}''',encoding='utf-8')
    r=publish_instance_report(root,tex,strict=True)
    expect=tmp_path/'A056-v0.2.0_FALSIFIER_REPORT.pdf'
    assert r['success'] and expect.is_file() and expect.stat().st_size>500


def test_compile_report_missing_tex_is_skip(tmp_path):
    r=compile_report_pdf(tmp_path/'missing.tex',tmp_path/'x.pdf',strict=False)
    assert not r['success'] and r['status']=='SKIP'
