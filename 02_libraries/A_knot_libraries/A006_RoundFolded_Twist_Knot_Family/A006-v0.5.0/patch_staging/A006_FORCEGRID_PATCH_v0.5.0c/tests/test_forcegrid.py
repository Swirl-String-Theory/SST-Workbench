"""Run against supplied A006 v0.5.0a zip in env A006_V050A_ZIP."""
import os, sys, tempfile, subprocess, zipfile, shutil, json, hashlib, re
from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec
PKG=Path(__file__).resolve().parents[1]
ORIG=Path(os.environ.get('A006_V050A_ZIP','/mnt/data/A006_RoundFolded_NearUnknot_v0.5.0a_FIXED61_DEFAULT.zip'))
BPKG=Path(os.environ.get('A006_V050B_ZIP','/mnt/data/A006_Force_Isolation_Qualification_Patch_v0.5.0b.zip'))
BASE='A006-v0.5.0a_ROUNDFOLDED_REBUILD/'
SEED='Output/v050/geometry/LINK_5_5_6_BALANCED_N1024_ORIG_CPFIXED61.xyz'

def proc(script,base,*args):
    return subprocess.run([sys.executable,str(script),'--base',str(base),*args],capture_output=True,text=True)

def fixture(parent):
    parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(ORIG) as z:
      for relative in ('run_all.cmd','knotplotrc.kps','tools/selection_v050.py',SEED):
       dest=parent/relative;dest.parent.mkdir(parents=True,exist_ok=True)
       dest.write_bytes(z.read(BASE+relative))
    return parent

for hasb in (False,True):
 with tempfile.TemporaryDirectory(prefix=f'a006_fg_{hasb}_') as d:
    root=fixture(Path(d)/'project')
    before={f:(root/f).read_bytes() for f in ('run_all.cmd','knotplotrc.kps')}
    if hasb:
      with zipfile.ZipFile(BPKG) as z:
        bd=Path(d)/'b';z.extractall(bd)
        bp=bd/'A006_FORCEQUAL_PATCH_v0.5.0b/install_patch.py'
        r=proc(bp,root,'--apply');assert r.returncode==0,(r.stdout,r.stderr)
        before={f:(root/f).read_bytes() for f in before}
    pi=PKG/'install_patch.py'
    for action in ('--check','--apply'):
      r=proc(pi,root,action)
      assert r.returncode==0,(action,r.stdout,r.stderr)
    assert proc(pi,root,'--apply').returncode!=0
    sys.path.insert(0,str(root/'tools'))
    import force_grid_v050c as fg
    fg.selftest(root)
    plan=json.loads((root/fg.REL/'PLAN.json').read_text())
    assert len(plan['arms'])==14
    assert plan['component_n']==[1138,1055,1024]
    assert abs(plan['median_initial_edge']-1.968625)<0.001
    for name,meta in plan['arms'].items():
      s=(root/meta['script']).read_text()
      assert s.count('coords ')==5,(name,s)
      assert 'go beadlimit 4000' in s
      assert 'data format "/I,/N,/l,/g"' in s and 'data format "/I,/N,/l,/g,/s"' not in s
      assert 'data close' in s and '\nstop\n' not in s
      assert s.index('load ')<s.index('go beadlimit')<s.index('ago 1')
      assert re.search('^close = [0-9]',s,re.M)
      assert re.search('^max-dr = [0-9]',s,re.M)
      assert 'collision fast\ncollision' in s
      assert 'mechforce = off\n' in s if name.startswith('AMECH') or name=='ELEC_ONLY' else 'mechforce = on\n' in s
    assert plan['arms']['AMECH_MATCH_ELEC']['spring']>1.96
    assert plan['arms']['AMECH_140_ELEC']['spring']==1.4
    assert plan['arms']['AMECH_MATCH_ELEC']['afmpower']==1
    assert plan['arms']['CLOSE_030']['close']==.3
    assert plan['arms']['MAXDR_0005']['max_dr']==.005
    r=fg.analyze(root)
    assert r['report_status']=='NO_KNOTPLOT_RUNTIME_DATA'
    assert len(r['arms'])==14 and all(a['status']=='NOT_EXECUTED' for a in r['arms'])
    assert fg.prepare(root)['checkpoints']==[0,1,8,32,128]
    assert len(fg.NAMES)==len(fg.ALIASES)==14
    assert all(f'alias {alias} ' in (root/'knotplotrc.kps').read_text() for alias in fg.ALIASES.values())
    # rollback; tolerate installed B, if any
    r=proc(pi,root,'--rollback');assert r.returncode==0,(r.stdout,r.stderr)
    assert all((root/f).read_bytes()==before[f] for f in before)
    print(f'PASS baseline={"v0.5.0b" if hasb else "v0.5.0a"}: install, duplicate refusal, 14 scripts, all metadata, missing-runtime, rollback')
print('ALL TESTS PASS')
