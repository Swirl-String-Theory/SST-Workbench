import json, zipfile
from pathlib import Path
import importlib.util


def _load_tool():
    p=Path(__file__).resolve().parents[1]/'tools'/'pack_outputs.py'
    spec=importlib.util.spec_from_file_location('pack_outputs',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def test_blind_archive_excludes_private(tmp_path):
    for name in ['BLIND_MANIFEST.json','BLIND_CONFIG.json','BACKEND_QUALIFICATION.json','BLIND_RESULTS.json','ANALYSIS_BLIND.json','BLIND_SEAL.json']:
        (tmp_path/name).write_text('{}')
    (tmp_path/'REPORT_BLIND.md').write_text('blind')
    (tmp_path/'_private').mkdir(); (tmp_path/'_private'/'PRIVATE_MAPPING.json').write_text('SECRET')
    tool=_load_tool(); zpath=tool.pack(tmp_path,'blind')
    with zipfile.ZipFile(zpath) as z:
        names=z.namelist(); payload='\n'.join(names)
        assert '_private' not in payload
        assert 'PRIVATE_MAPPING' not in payload
