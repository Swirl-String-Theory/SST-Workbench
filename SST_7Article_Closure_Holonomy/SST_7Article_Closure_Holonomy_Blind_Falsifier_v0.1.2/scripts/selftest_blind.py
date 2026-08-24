from pathlib import Path
import tempfile,json,hashlib,subprocess,sys,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sst7.blind import prepare,sha256_file

ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td0:
    td=Path(td0); data=td/'data'; data.mkdir(); state=td/'state'
    t=np.linspace(0,2*np.pi,96,endpoint=False)
    c=np.c_[np.cos(t),np.sin(t),0*t]
    d=np.c_[4+np.cos(t),np.sin(t),0*t]
    (data/'single.txt').write_text('\n'.join(' '.join(map(str,x)) for x in c)+'\n',encoding='utf-8')
    (data/'link.txt').write_text('\n'.join(' '.join(map(str,x)) for x in c)+'\n\n'+
                                  '\n'.join(' '.join(map(str,x)) for x in d)+'\n',encoding='utf-8')
    r1=td/'basic'; r2=td/'extended'
    p1=prepare(data,r1,0.3,state_dir=state); p2=prepare(data,r2,0.3,state_dir=state)
    a=[(x['case_id'],x['split'],x['n_components']) for x in p1['cases']]
    b=[(x['case_id'],x['split'],x['n_components']) for x in p2['cases']]
    assert a==b,(a,b)
    assert p1['dataset_snapshot_sha256']==p2['dataset_snapshot_sha256']
    # Run + byte-stable freeze + reveal verification.
    cmd=[sys.executable,str(ROOT/'scripts/run_campaign.py'),'--run-dir',str(r1),'--config','config/basic.json','--mode','basic']
    subprocess.check_call(cmd,cwd=ROOT)
    recorded=(r1/'freeze.sha256').read_text(encoding='ascii').split()[0]
    actual=sha256_file(r1/'opaque_results.json'); assert recorded==actual,(recorded,actual)
    subprocess.check_call([sys.executable,str(ROOT/'scripts/reveal.py'),'--run-dir',str(r1)],cwd=ROOT)
    rev=json.loads((r1/'revealed_results.json').read_text()); assert rev['freeze_verified'] is True
print('[SST7] blind infrastructure selftest PASS')
