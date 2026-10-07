from pathlib import Path
import json, hashlib, math
import numpy as np
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from a056_falsifier.numeric import mittag_leffler_relax

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data'/'blind'; PRIV=ROOT/'PRIVATE'; OUT.mkdir(parents=True,exist_ok=True); PRIV.mkdir(exist_ok=True)
rng=np.random.default_rng(560100)

def sg_field(t,s,omega=0.72):
    # Exact stationary Sine-Gordon breather for phi_tt - phi_ss + sin(phi)=0.
    eta=math.sqrt(1-omega*omega)
    num=(eta/omega)*np.sin(omega*t[:,None])
    den=np.cosh(eta*s[None,:])
    return 4*np.arctan(num/den)

def kg_field(t,s,A=0.7,k=1.0,c=1.0,m=1.1):
    om=math.sqrt(c*c*k*k+m*m); return A*np.cos(k*s[None,:])*np.cos(om*t[:,None])

def save(oid,phase_kind,ring_kind,group,boundary):
    if phase_kind=='SG':
        t=np.linspace(0,12.0,181); s=np.linspace(-10,10,161); phi=sg_field(t,s); boundary='open'
    else:
        t=np.linspace(0,4.0,121); s=np.linspace(0,2*np.pi,160,endpoint=False); phi=kg_field(t,s); boundary='periodic'
    phi=phi + rng.normal(0,2e-5,phi.shape)
    rt=np.linspace(0,12,180)
    if ring_kind=='ML': rd=mittag_leffler_relax(rt,3.0,0.72)
    else: rd=0.62*np.exp(-rt/1.8)+0.38*np.exp(-rt/5.0)
    rd=np.clip(rd+rng.normal(0,5e-4,rd.shape),0,None)
    np.savez_compressed(OUT/f'{oid}.npz',t=t,s=s,phi=phi,ringdown_t=rt,ringdown=rd)
    meta={"opaque_id":oid,"source_group":group,"boundary":boundary,"t_unit":"arb_time","s_unit":"arb_length","synthetic":True}
    (OUT/f'{oid}.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return {"opaque_id":oid,"phase_truth":phase_kind,"ringdown_truth":ring_kind,"source_group":group}

reveal=[
 save('C0001','SG','ML','SYNTH_A','open'),
 save('C0002','SG','BIEXP','SYNTH_B','open'),
 save('C0003','KG','ML','SYNTH_C','periodic'),
 save('C0004','KG','BIEXP','SYNTH_D','periodic'),
 save('C0005','SG','ML','SYNTH_E','open'),
]
rp=PRIV/'smoke_reveal.json'; rp.write_text(json.dumps({"schema":"A056-SMOKE-REVEAL-1","cases":reveal},indent=2),encoding='utf-8')
h=hashlib.sha256(rp.read_bytes()).hexdigest(); (ROOT/'reveal_commitment.sha256').write_text(h+'  PRIVATE/smoke_reveal.json\n',encoding='utf-8')
print('generated',len(reveal),'blind smoke cases; reveal commitment',h)
