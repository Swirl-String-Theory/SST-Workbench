"""Deterministic mock-runtime install integration tests.

These tests certify orchestration only, not compatibility with real KnotPlot.
"""
from pathlib import Path
import importlib.util
import json
import math
import shutil
import subprocess


def _load_install_module(root: Path):
    path = root / 'tools/install_test_export.py'
    spec = importlib.util.spec_from_file_location('_a058_v026_install', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _simulator(script: Path, log: Path, safe_transform: bool):
    private_meta = json.loads((script.parent.parent/'axis_map.json').read_text(encoding='utf-8'))
    reset = {
        'close': .2, 'max-dr': .02, 'stusplit': 0.0,
        'dstep': 1.0, 'timeincr': 15.0, 'iteration': 0.0,
    }
    defaults = (15.0, 5.0, 1.0, 1.4, 2.0, .1, 1.0, 1.0)
    for i, default in enumerate(defaults):
        if i == 3:  # non-reporting numeric GUI control
            continue
        reset[private_meta['axes'][f'S{i}']['parameter']] = default
    for section in private_meta['sectors'].values():
        reset[section['switch_parameter']] = 'off'
    reset[private_meta['sectors']['R1']['switch_parameter']] = 'on'
    params = reset.copy()
    safe = False
    messages = []
    for line in script.read_text(encoding='utf-8').splitlines():
        cmd = line.strip()
        if not cmd:
            continue
        if cmd == 'reset all':
            params = reset.copy(); safe = False
        elif cmd in ('collision fast', 'version', 'refine nbeads 300'):
            pass
        elif cmd.startswith('load '):
            safe = Path(cmd[5:]).is_file() if cmd[5:] != '3.1' else False
        elif cmd.startswith('fitto mindist '):
            safe = bool(safe_transform)
        elif cmd.startswith('echo '):
            messages.append(cmd[5:])
        elif cmd == 'parameters':
            for k, v in params.items():
                if k == private_meta['axes']['S3']['parameter']:
                    continue
                messages.append(f'{k} = {v}')
        elif cmd == 'safe':
            messages.append('Current position is safe' if safe else 'Current position is not safe')
        elif cmd.startswith('go '):
            params['iteration'] = float(params['iteration']) + float(cmd[3:]) if safe else float(params['iteration'])
        elif cmd.startswith('save '):
            dest = Path(cmd.split('save ', 1)[1].rsplit(' ascii', 1)[0]); dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(''.join(f'{(2+math.cos(3*t))*math.cos(2*t):.16g} {(2+math.cos(3*t))*math.sin(2*t):.16g} {math.sin(3*t):.16g}\n' for t in (2*math.pi*i/300 for i in range(300))),encoding='utf-8')
        elif ' = ' in cmd:
            k, value = cmd.split(' = ',1)
            if value in ('on','off'):
                params[k] = value
            else:
                params[k] = float(value)
        else:
            raise AssertionError(f'Unexpected mock command: {cmd}')
    log.write_text('\n'.join(messages)+'\n',encoding='utf-8')
    return subprocess.CompletedProcess([],0)


def _prepare(tmp_path, monkeypatch, safe_transform):
    from tools import install_test_export as install
    origin = Path(__file__).resolve().parents[1]
    (tmp_path/'tools').mkdir()
    (tmp_path/'private').mkdir()
    (tmp_path/'configs').mkdir()
    shutil.copy2(origin/'private/axis_map.json',tmp_path/'private/axis_map.json')
    shutil.copy2(origin/'configs/default.json',tmp_path/'configs/default.json')
    (tmp_path/'fake_knotplot.exe').write_bytes(b'mock-only')
    monkeypatch.setattr(install,'ROOT',tmp_path)
    monkeypatch.setattr(install,'resolve_exe',lambda _: (tmp_path/'fake_knotplot.exe','test'))
    monkeypatch.setattr(install,'resolve_workdir',lambda _: (tmp_path,'test'))
    monkeypatch.setattr(install,'_run',lambda exe,wd,script,log: _simulator(script,log,safe_transform))
    return install


def test_mock_install_creates_one_reload_safe_seed(tmp_path, monkeypatch):
    install = _prepare(tmp_path,monkeypatch,True)
    install.main()
    obj=json.loads((tmp_path/'private/install_test_runtime/defaults.json').read_text())
    assert obj['pass'] and obj['export_count']==1 and obj['safe_start']
    assert obj['shared_seed']['close_default']==0.2
    assert math.isclose(obj['shared_seed']['fitto_mindist_target'],0.21)
    assert not obj['shared_seed']['raw_catalogue_safe']
    assert obj['shared_seed']['prepared_safe'] and obj['shared_seed']['reload_safe']
    assert obj['shared_seed']['post_go_safe']
    assert len(list((tmp_path/'private/install_test_runtime').glob('*.txt')))==1
    assert obj['shared_seed_sha256']==obj['shared_seed']['sha256']


def test_mock_install_fails_when_geometry_cannot_be_made_safe(tmp_path, monkeypatch):
    import pytest
    install = _prepare(tmp_path,monkeypatch,False)
    with pytest.raises(SystemExit,match='seed normalization did not produce'):
        install.main()
    assert not (tmp_path/'private/install_test_runtime/defaults.json').exists()
