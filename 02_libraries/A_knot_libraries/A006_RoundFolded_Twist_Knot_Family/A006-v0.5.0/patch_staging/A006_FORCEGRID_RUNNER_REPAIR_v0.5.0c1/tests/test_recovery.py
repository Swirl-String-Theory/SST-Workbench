"""Run using: py -3 tests/test_recovery.py ; only isolated fixture roots."""
from __future__ import annotations
import importlib.util
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
REPAIR=HERE/'repair.py'
ZIP=Path(__file__).resolve().parents[3]/'A006_RoundFolded_NearUnknot_v0.5.0a_FIXED61_DEFAULT.zip'
if not ZIP.exists():ZIP=Path('/mnt/data/A006_RoundFolded_NearUnknot_v0.5.0a_FIXED61_DEFAULT.zip')
BASE='A006-v0.5.0a_ROUNDFOLDED_REBUILD/'
ASSETS=('run_all.cmd','knotplotrc.kps','tools/selection_v050.py','Output/v050/geometry/LINK_5_5_6_BALANCED_N1024_ORIG_CPFIXED61.xyz')

def fixture(root):
    with zipfile.ZipFile(ZIP) as z:
        for p in ASSETS:
            (root/p).parent.mkdir(parents=True,exist_ok=True)
            (root/p).write_bytes(z.read(BASE+p))
    return root

def command(root,*args):
    return subprocess.run([sys.executable,str(REPAIR),'--base',str(root),*args],capture_output=True,text=True)

def checks(root):
    text=(root/'run_all.cmd').read_text()
    assert 'if /I "%~1"=="FORCEGRID" goto forcegrid' in text
    assert ':forcegrid\npy -3 tools\\force_grid_v050c.py %2' in text
    assert len(list((root/'Output/qualification_v050c/scripts').glob('FQ_*.kps')))==14
    assert len(list((root/'Output/qualification_v050c/runs').iterdir()))==14
    assert 'alias fgB0 ' in (root/'knotplotrc.kps').read_text()
    assert json.loads((root/'Output/qualification_v050c/PLAN.json').read_text())['status']=='PREPARED_NOT_EXECUTED'

with tempfile.TemporaryDirectory(prefix='A006v050c1_') as d:
    for scenario in ('no_grid','partial_grid','existing_grid','forcequal_module'):
        root=fixture(Path(d)/scenario)
        if scenario in ('partial_grid','existing_grid','forcequal_module'):
            mod=root/'tools/force_grid_v050c.py'
            mod.write_bytes((HERE/'payload/force_grid_v050c.py').read_bytes())
            spec=importlib.util.spec_from_file_location('force_grid_v050c',mod)
            m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.prepare(root)
            # Simulate prior v0.5.0c install already having aliases in RC but old run_all restored
            rc=root/'knotplotrc.kps';old=rc.read_text()
            b='% >>> A006_FORCEGRID_v050c_ALIASES_BEGIN\n'
            b+='\n'.join(f'alias {short} "read Output/qualification_v050c/scripts/FQ_{arm}.kps"' for arm,short in m.ALIASES.items())
            b+='\n% <<< A006_FORCEGRID_v050c_ALIASES_END\n'
            rc.write_text(old+'\n'+b)
            if scenario=='existing_grid':
                cmd=root/'run_all.cmd';old=cmd.read_text()
                old=old.replace('cd /d "%~dp0"','cd /d "%~dp0"\nif /I "%~1"=="FORCEGRID" goto forcegrid',1)
                old=old.replace(':usage\n',':forcegrid\npy -3 tools\\force_grid_v050c.py %2 %3 %4 %5 %6 %7 %8 %9\nexit /b %errorlevel%\n:usage\n',1)
                cmd.write_text(old)
            if scenario=='forcequal_module':
                (root/'tools/force_qualification_v050b.py').write_text('print("forcequal")\n')
        before_seed=(root/ASSETS[-1]).read_bytes()
        before_cfg=(root/'run_all.cmd').read_bytes()
        result=command(root,'--check');assert result.returncode==0,(scenario,result.stdout,result.stderr)
        result=command(root,'--apply');assert result.returncode==0,(scenario,result.stdout,result.stderr)
        checks(root)
        if scenario=='forcequal_module':assert 'if /I "%~1"=="FORCEQUAL" goto forcequal' in (root/'run_all.cmd').read_text()
        assert (root/ASSETS[-1]).read_bytes()==before_seed
        result=command(root,'--apply'); assert result.returncode==0,(scenario,result.stderr)
        if scenario!='existing_grid':
            result=command(root,'--rollback');assert result.returncode==0,(scenario,result.stdout,result.stderr)
            assert (root/'run_all.cmd').read_bytes()==before_cfg
        print(f'PASS {scenario}: initial recovery, alias protection, plan integrity, rerun, rollback')
print('ALL TESTS PASS')

with tempfile.TemporaryDirectory(prefix='A006_v050c1_negative_') as d:
    root=fixture(Path(d)/'user_alias')
    rc=root/'knotplotrc.kps';rc.write_text(rc.read_text()+'\nalias fgB0 "custom command"\n')
    a=command(root,'--check')
    assert a.returncode!=0 and 'Alias fgB0 already exists' in a.stderr
    assert not (root/'patch_backups/v050c1_RUNNER_RECOVERY').exists()
    print('PASS alias collision -> refusal, no writes')
    root=fixture(Path(d)/'modified_module')
    (root/'tools/force_grid_v050c.py').write_text('print("modified")\n')
    a=command(root,'--apply')
    assert a.returncode!=0 and 'differs' in a.stderr
    assert not (root/'patch_backups/v050c1_RUNNER_RECOVERY').exists()
    print('PASS changed module -> refusal, no writes')
    root=fixture(Path(d)/'partial_output')
    (root/'Output/qualification_v050c/runs/BEND_OFF').mkdir(parents=True)
    (root/'Output/qualification_v050c/runs/BEND_OFF/i0000001.xyz').write_text('existing\n')
    a=command(root,'--apply')
    assert a.returncode!=0 and 'without PLAN.json' in a.stderr
    assert not (root/'patch_backups/v050c1_RUNNER_RECOVERY').exists()
    print('PASS orphan runtime output -> refusal, no writes')
