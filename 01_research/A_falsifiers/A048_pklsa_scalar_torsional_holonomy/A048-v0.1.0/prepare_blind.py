from pathlib import Path
import csv, hashlib, json, secrets, shutil
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.1.0-outputs'
CFG=json.loads((ROOT/'configs'/'default.json').read_text(encoding='utf-8'))
PRIVATE=ROOT/'.a048_private_reveal.json'
FORBIDDEN=['1.09384563e6','1.40897017e-15','3.8934358266918687e18','7.0e-7']

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def sha256_file(p): return sha256_bytes(Path(p).read_bytes())

def source_manifest():
    exts={'.py','.cpp','.md','.json','.cmd','.toml','.txt'}
    rows=[]
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and p.suffix.lower() in exts and p.name!='MANIFEST_SHA256.txt' and p.name!='.a048_private_reveal.json':
            rows.append({'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha256_file(p)})
    return rows

def main():
    if OUT.exists(): shutil.rmtree(OUT)
    if PRIVATE.exists(): PRIVATE.unlink()
    (OUT/'BLIND'/'input').mkdir(parents=True)
    (OUT/'BLIND'/'python_backend').mkdir(parents=True)
    (OUT/'BLIND'/'native_backend').mkdir(parents=True)
    (OUT/'BLIND'/'logs').mkdir(parents=True)
    (OUT/'REVEALED').mkdir(parents=True)
    # random seed and permutation deliberately withheld from BLIND
    seed=secrets.randbits(63); rng=np.random.default_rng(seed)
    n=int(CFG['synthetic_case_count']); modes=np.array(CFG['modes'],float); sigma=float(CFG['relative_noise_sigma'])
    labels=(['KELVIN_QUADRATIC']*(n//2)+['TORSIONAL_LINEAR_GAPPED']*(n-n//2)); rng.shuffle(labels)
    salt=secrets.token_hex(16); key={'seed':seed,'salt':salt,'cases':{}}
    for i,label in enumerate(labels):
        cid=hashlib.sha256(f'{salt}:{i}'.encode()).hexdigest()[:16]
        k=modes.copy()
        if label=='KELVIN_QUADRATIC':
            beta=float(rng.uniform(0.08,0.30)); true=beta*k*k; pars={'beta':beta}; target_p=2.0
        else:
            c=float(rng.uniform(0.7,1.4)); gap=float(rng.uniform(0.02,0.25)); true=np.sqrt((c*k)**2+gap**2); pars={'c_phase':c,'gap':gap}; target_p=1.0
        omega=true*(1.0+rng.normal(0.0,sigma,size=len(k)))
        f=OUT/'BLIND'/'input'/f'case_{cid}.csv'
        with f.open('w',newline='',encoding='utf-8') as h:
            cw=csv.writer(h); cw.writerow(['k','omega']); cw.writerows(zip(k,omega))
        key['cases'][cid]={'label':label,'parameters':pars,'target_exponent':target_p}
    PRIVATE.write_text(json.dumps(key,indent=2),encoding='utf-8')
    manifest=source_manifest()
    cfg_text=(ROOT/'configs'/'default.json').read_text(encoding='utf-8')
    blind_text='\n'.join(p.read_text(encoding='utf-8',errors='ignore') for p in (OUT/'BLIND').rglob('*') if p.is_file())+cfg_text
    forbidden={x:(x in blind_text) for x in FORBIDDEN}
    prep={
      'stage':'prepared','blind':True,'version':'0.1.0','config_sha256':sha256_bytes(cfg_text.encode()),
      'source_manifest':manifest,'seed_commitment':hashlib.sha256(str(seed).encode()).hexdigest(),
      'canonical_constants_present_in_blind_payload':any(forbidden.values()),'forbidden_scan':forbidden,
    }
    (OUT/'BLIND'/'prepare_manifest.json').write_text(json.dumps(prep,indent=2),encoding='utf-8')
    print(json.dumps({k:prep[k] for k in ['stage','blind','version','config_sha256','seed_commitment','canonical_constants_present_in_blind_payload']},indent=2))
if __name__=='__main__': main()
