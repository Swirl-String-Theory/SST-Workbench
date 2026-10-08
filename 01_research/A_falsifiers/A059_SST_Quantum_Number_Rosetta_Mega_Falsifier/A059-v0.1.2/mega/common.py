from __future__ import annotations
from pathlib import Path
import csv, hashlib, hmac, io, json, math, os, zipfile
from typing import Any
import numpy as np

EXPECTED_E011_SHA256 = "97cd1acbf23c102e4564f2d74fd329a2d03f32a29b8bd376ffa8b806c14246cc"
EXPECTED_FRAMEWORK_PACKAGE_MANIFEST_SHA256 = "233730abad5ef26f851db0ae75c691fd17daa75e99beb8419d6934ccf85c15be"
EXPECTED_FRAMEWORK_ARCHIVE_SHA256 = "24629848e3befcde67c02a935fc78347560ac42107043fbc14aaabdf146ee60d"
ATLAS_ZIP_NAME = "E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs.zip"
OUTPUT_NAME = "A059_SST_Quantum_Number_Rosetta_Mega_Falsifier_v0.1.2-outputs"


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20), b''): h.update(b)
    return h.hexdigest()


def root_from_here() -> Path:
    return Path(__file__).resolve().parents[1]


def output_root(root: Path|None=None) -> Path:
    r=root or root_from_here(); return r/OUTPUT_NAME


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')


def canonical_sha(obj: Any) -> str:
    data=json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def atlas_zip(root: Path|None=None) -> Path:
    return (root or root_from_here())/'inputs'/ATLAS_ZIP_NAME


def verify_source_archive(root: Path|None=None) -> dict[str,Any]:
    p=atlas_zip(root)
    actual=sha256_file(p) if p.is_file() else None
    return {'path':str(p),'exists':p.is_file(),'expected_sha256':EXPECTED_E011_SHA256,'actual_sha256':actual,'pass':actual==EXPECTED_E011_SHA256}


def _member_name(z: zipfile.ZipFile, basename: str) -> str:
    hits=[n for n in z.namelist() if n.endswith('/'+basename) or n==basename]
    if len(hits)!=1: raise RuntimeError(f'archive member {basename!r}: expected one match, got {len(hits)}')
    return hits[0]


def atlas_json(basename: str, root: Path|None=None) -> Any:
    with zipfile.ZipFile(atlas_zip(root)) as z:
        with z.open(_member_name(z,basename)) as f: return json.load(io.TextIOWrapper(f,encoding='utf-8-sig'))


def atlas_jsonl(basename: str, root: Path|None=None) -> list[dict[str,Any]]:
    rows=[]
    with zipfile.ZipFile(atlas_zip(root)) as z:
        with z.open(_member_name(z,basename)) as f:
            for line in io.TextIOWrapper(f,encoding='utf-8-sig'):
                if line.strip(): rows.append(json.loads(line))
    return rows


def atlas_csv(basename: str, root: Path|None=None) -> list[dict[str,str]]:
    with zipfile.ZipFile(atlas_zip(root)) as z:
        with z.open(_member_name(z,basename)) as f:
            return list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))


def private_key(root: Path|None=None) -> bytes:
    return ((root or root_from_here())/'private'/'OPAQUE_ID_KEY.bin').read_bytes()


def opaque_topology(topology_id: str, root: Path|None=None) -> str:
    dig=hmac.new(private_key(root),('topology:'+topology_id).encode(),hashlib.sha256).hexdigest()[:16].upper()
    return 'OBJ_'+dig


PHASE_SLUGS = {
    'P00':'SOURCE_INTAKE', 'P01':'STATIC_STRUCTURE', 'P02':'CONJUGATION',
    'P03':'SIGNED_RESPONSE', 'P04':'MONODROMY', 'P05':'INVOLUTIONS',
    'P06':'GRAVITY_CHIRAL_SELECTION', 'P07':'U1_CLOSURE', 'P08':'COMPOSITES'
}

def phase_dir(phase_id: str, root: Path|None=None) -> Path:
    pid=phase_id.upper(); slug=PHASE_SLUGS.get(pid,'UNKNOWN')
    return output_root(root)/'PHASES'/f'{pid}_{slug}' 


def load_phase_result(phase_id: str, root: Path|None=None) -> dict[str,Any]|None:
    p=phase_dir(phase_id,root)/'RESULT.json'
    return read_json(p) if p.is_file() else None


def advisory_state(inputs: list[str], root: Path|None=None) -> list[dict[str,Any]]:
    out=[]
    for pid in inputs:
        r=load_phase_result(pid,root)
        out.append({'phase':pid,'present':r is not None,'status':None if r is None else r.get('status'),'evidence_class':None if r is None else r.get('evidence_class')})
    return out


def robust_z(X: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    med=np.nanmedian(X,axis=0)
    mad=np.nanmedian(np.abs(X-med),axis=0)
    scale=1.4826*mad
    std=np.nanstd(X,axis=0)
    scale=np.where(scale>1e-12,scale,np.where(std>1e-12,std,1.0))
    Y=(X-med)/scale
    Y=np.where(np.isfinite(Y),Y,0.0)
    return Y,med,scale


def kmeans(X: np.ndarray,k:int,seed:int=5600106,max_iter:int=100) -> tuple[np.ndarray,np.ndarray,float]:
    if len(X)<k: raise ValueError('k > n')
    rng=np.random.default_rng(seed+k)
    # deterministic farthest-ish init: first random, then max distance
    idx=[int(rng.integers(len(X)))]
    while len(idx)<k:
        C=X[idx]
        d=((X[:,None,:]-C[None,:,:])**2).sum(2).min(1)
        for j in idx:d[j]=-1
        idx.append(int(np.argmax(d)))
    C=X[idx].copy(); labels=np.zeros(len(X),dtype=int)
    for _ in range(max_iter):
        d=((X[:,None,:]-C[None,:,:])**2).sum(2)
        new=d.argmin(1)
        if np.array_equal(new,labels) and _>0: break
        labels=new
        for j in range(k):
            m=X[labels==j]
            if len(m): C[j]=m.mean(0)
    inertia=float(((X-C[labels])**2).sum())
    return labels,C,inertia


def silhouette(X: np.ndarray, labels: np.ndarray) -> float:
    n=len(X)
    if n<3 or len(set(labels.tolist()))<2:return float('nan')
    D=np.sqrt(((X[:,None,:]-X[None,:,:])**2).sum(2))
    vals=[]
    for i in range(n):
        same=(labels==labels[i]); same[i]=False
        a=float(D[i,same].mean()) if same.any() else 0.0
        bs=[]
        for lab in sorted(set(labels.tolist())):
            if lab==labels[i]:continue
            m=labels==lab
            if m.any():bs.append(float(D[i,m].mean()))
        b=min(bs) if bs else 0.0
        vals.append((b-a)/max(a,b,1e-15))
    return float(np.mean(vals))


def finite(v: Any) -> float|None:
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except Exception:return None


def provider_aggregates(root: Path|None=None) -> dict[str,dict[str,Any]]:
    anchors=atlas_jsonl('STATIC_READY_PROVIDER_ANCHORS.jsonl',root)
    idx={r['topology_id']:r for r in atlas_csv('STATIC_READY_INDEX.csv',root)}
    by={}
    for a in anchors: by.setdefault(a['topology_id'],[]).append(a)
    out={}
    metrics=['Wr','ACN','L','ropelength','kappa_rms','tau_rms','dcsd']
    for tid,arr in by.items():
        vals={m:[finite(x.get('finest_metrics',{}).get(m)) for x in arr] for m in metrics}
        vals={m:[x for x in xs if x is not None] for m,xs in vals.items()}
        med={m:(float(np.median(xs)) if xs else None) for m,xs in vals.items()}
        spread={m:((max(xs)-min(xs))/max(abs(float(np.median(xs))),1e-12) if len(xs)>1 else 0.0) for m,xs in vals.items()}
        out[tid]={'topology_id':tid,'candidate_id':opaque_topology(tid,root),'metrics':med,'provider_values':vals,'relative_spread':spread,'providers':sorted({x.get('provider_group') for x in arr}), 'static_status':idx.get(tid,{}).get('static_status'), 'static_ready':idx.get(tid,{}).get('static_ready')=='True'}
    return out


def implementation_verify(root: Path|None=None) -> dict[str,Any]:
    r=root or root_from_here(); p=r/'IMPLEMENTATION_MANIFEST.json'
    if not p.is_file():return {'pass':False,'reason':'missing IMPLEMENTATION_MANIFEST.json'}
    man=read_json(p); bad=[]
    for row in man.get('files',[]):
        q=r/row['path']; actual=sha256_file(q) if q.is_file() else None
        if actual!=row['sha256']:bad.append({'path':row['path'],'expected':row['sha256'],'actual':actual})
    return {'pass':not bad,'manifest_sha256':man.get('manifest_sha256'),'file_count':len(man.get('files',[])),'mismatches':bad}


def make_local_manifest(folder: Path) -> dict[str,Any]:
    rows=[]
    for p in sorted(folder.rglob('*')):
        if p.is_file() and p.name!='OUTPUT_MANIFEST.json':
            rows.append({'relpath':p.relative_to(folder).as_posix(),'size':p.stat().st_size,'sha256':sha256_file(p)})
    payload={'schema':'A059-PHASE-OUTPUT-MANIFEST-1','files':rows}
    payload['manifest_sha256']=canonical_sha({'files':rows})
    write_json(folder/'OUTPUT_MANIFEST.json',payload); return payload


def verify_local_manifest(folder: Path) -> dict[str,Any]:
    p=folder/'OUTPUT_MANIFEST.json'
    if not p.is_file():return {'pass':False,'reason':'missing phase output manifest'}
    old=read_json(p); rows=[]
    for q in sorted(folder.rglob('*')):
        if q.is_file() and q.name!='OUTPUT_MANIFEST.json':rows.append({'relpath':q.relative_to(folder).as_posix(),'size':q.stat().st_size,'sha256':sha256_file(q)})
    ok=old.get('files')==rows and old.get('manifest_sha256')==canonical_sha({'files':rows})
    return {'pass':ok,'manifest_sha256':old.get('manifest_sha256'),'file_count':len(rows)}
