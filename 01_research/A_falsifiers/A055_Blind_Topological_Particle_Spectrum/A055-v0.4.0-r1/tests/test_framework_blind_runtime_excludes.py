from pathlib import Path
from a055_science.framework_compat import install_runtime_safe_blind_scan

def test_runtime_owned_venv_is_excluded_but_source_is_not(tmp_path):
    import sst_falsifier.blind as blind
    install_runtime_safe_blind_scan()
    (tmp_path/'.venv'/'Lib'/'site-packages').mkdir(parents=True)
    (tmp_path/'.venv'/'Lib'/'site-packages'/'foreign.py').write_text('SECRET_TARGET',encoding='utf-8')
    assert blind.scan_tree(tmp_path,['secret_target'])==[]
    (tmp_path/'owned.py').write_text('SECRET_TARGET',encoding='utf-8')
    hits=blind.scan_tree(tmp_path,['secret_target'])
    assert [h['path'] for h in hits]==['owned.py']
