"""Blinded executable. Keys/labels not part of this source package."""
from __future__ import annotations
import argparse,hashlib,json,sys,subprocess,os,zipfile,io
from pathlib import Path
import numpy as np
from .metrics import analyze_arrays
ROOT=Path(__file__).resolve().parents[1]
NAME='SST_TopologyProjectionPhase_v0.1.0'
OUT=ROOT.parent/(NAME+'-outputs')


def canon(obj):return json.dumps(obj,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode()
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def sha_file(path):return sha_bytes(Path(path).read_bytes())
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
def clean_output():
    if OUT.exists():
        import shutil;shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

def input_integrity():
    manifest=json.loads((ROOT/'datasets'/'INPUT_MANIFEST.json').read_text())
    for item in manifest['inputs']:
        p=ROOT/'datasets'/item['path']
        if sha_file(p)!=item['sha256']:raise RuntimeError('input hash mismatch '+str(p))
        enc=ROOT/'datasets'/item['truth_cipher_path']
        if sha_file(enc)!=item['cipher_sha256']:raise RuntimeError('sealed truth ciphertext hash mismatch '+str(enc))
    return manifest

def protocol_hash():return sha_file(ROOT/'preregistration'/'PROTOCOL.json')

def run():
    clean_output(); manifest=input_integrity()
    out=[]
    for item in manifest['inputs']:
        with np.load(ROOT/'datasets'/item['path'],allow_pickle=False) as d:
            arr={name:d[name] for name in d.files}
        result=analyze_arrays(arr)
        result['blind_dataset']=item['id'];result['sha256_input']=item['sha256']
        out.append(result)
        save(OUT/(item['id']+'_ASSESSMENT.json'),result)
    status_counts={k:sum(r['gates'][k]=='PASS' for r in out) for k in out[0]['gates']}
    # The 2D observables are deliberately identical across cases, so no 2D-only
    # algorithm can legitimately identify the mechanism in this controlled task.
    phase_hashes=[]
    for item in manifest['inputs']:
        with np.load(ROOT/'datasets'/item['path'],allow_pickle=False) as d:
            phase_hashes.append(sha_bytes(d['re'].tobytes()+d['im'].tobytes()))
    phase_nonidentifiability=len(set(phase_hashes))==1
    s={'tool':'blinded_synthetic_calibration','framework_target':'v1.0.7 (external canonical framework not vendored)',
       'science_status':'SYNTHETIC_CALIBRATION_ONLY','blind':True,'protocol_sha256':protocol_hash(),
       'datasets':[r['blind_dataset'] for r in out],'passes_by_gate':status_counts,
       'dataset_predictions':{r['blind_dataset']:r['prediction'] for r in out},
       'two_dimensional_data_identical':phase_nonidentifiability,
       'G08_2D_ONLY_DISCRIMINATION':'EXPECTED_IMPOSSIBLE' if phase_nonidentifiability else 'UNRESOLVED',
       'warnings':['Synthetic 3D topology change is imposed surgery: not a solved Euler/Navier-Stokes reconnection.',
          '2D phase maps alone are nonidentifying; 3D geometry is mandatory.',
          'No native v1.0.7 backends or independent PKLSA trajectories have been certified.']}
    save(OUT/'RUN_SUMMARY.json',s)
    write_pdf(s,out)
    print(json.dumps(s,indent=2));return s

def write_pdf(s,rs):
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4
    p=OUT/'FALSIFIER_REPORT.pdf';c=Canvas(str(p),pagesize=A4)
    W,H=A4
    def line(y,text,size=10):
        c.setFont('Helvetica',size);c.drawString(40,y,text[:103])
    line(H-55,'SST: BLIND 3D TOPOLOGY / PROJECTION / PHASE',15)
    line(H-78,'v0.1.0 - synthetic qualification (not physical SST certification)',9)
    y=H-116
    for txt in ['Study: distinguish imposed 3D topology surgery, 2D section tangency and optical phase zeros.',
           'Paper basis: Bucher et al., Superluminal correlations in optical phase singularities.',
           'Protocol SHA256: '+s['protocol_sha256'],
           'All three observable datasets sealed before this run; labels withheld.',
           'Classification uses 3D component count, plane intersections and phase winding.',
           'Full Euler/Navier-Stokes nonideal reconnection remains UNRESOLVED.']:
        line(y,txt,9);y-=17
    y-=15
    for r in rs:
        if y<160:c.showPage();y=H-55
        line(y,'DATASET '+r['blind_dataset']+' | '+r['prediction'],10);y-=18
        line(y,'2D winding pre/post: '+str(r['phase_charges_pre'])+' / '+str(r['phase_charges_post']),9);y-=14
        line(y,'3D components pre/post: '+str(r['component_counts_pre_post'])+' | slice hits: '+str(r['slice_hits']),8);y-=15
        for key,val in r['gates'].items():
            line(y,f'{key}: {val}',8);y-=13
        y-=22
    if y<75:c.showPage();y=H-50
    line(y,'LIMITS: no qualified PKLSA time series; no nonideal PDE solution; no independent experiment.',9)
    line(y-24,'Automated by ReportLab; available independent of LaTeX installation.',9)
    c.showPage();c.save()

def manifest_tree():
    files={p.name:sha_file(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ('FREEZE_LEDGER.json','REVEAL_DECISION.json','REVEALED_RESULTS.json')}
    return files

def freeze():
    s=run()
    # Freeze the outputs exactly, seal salted run ID and protocol. Prevent later modifications.
    record={'protocol_sha256':protocol_hash(),'outputs':manifest_tree(),'input_manifest_sha256':sha_file(ROOT/'datasets'/'INPUT_MANIFEST.json')}
    record['self_sha256']=sha_bytes(canon(record))
    save(OUT/'FREEZE_LEDGER.json',record)
    z=ROOT.parent/(NAME+'-outputs_BLIND.zip')
    with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED) as f:
        for p in OUT.iterdir():
            if p.is_file():f.write(p,arcname=p.name)
    print('BLIND FROZEN:',z,'ledger:',record['self_sha256'])

def reveal(keys_path:Path,strict=True):
    ledpath=OUT/'FREEZE_LEDGER.json'
    if not ledpath.exists():raise RuntimeError('No frozen blind ledger. Run FREEZE before REVEAL.')
    led=json.loads(ledpath.read_text());s=led.pop('self_sha256')
    if sha_bytes(canon(led))!=s:raise RuntimeError('Tampered ledger')
    if led['protocol_sha256']!=protocol_hash():raise RuntimeError('Protocol changed after freeze')
    if led['input_manifest_sha256']!=sha_file(ROOT/'datasets'/'INPUT_MANIFEST.json'):raise RuntimeError('Input manifest changed')
    if manifest_tree()!=led['outputs']:raise RuntimeError('Blind outputs altered or added')
    if not keys_path.exists():
        if strict:raise RuntimeError('Reveal keys absent; keep blind. Supply --keys path')
        save(OUT/'REVEAL_DECISION.json',{'state':'WITHHELD','reason':'No external reveal keys supplied'})
        return
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    cfg=json.loads(keys_path.read_text());res=[]
    for row in cfg['keys']:
        item=row['dataset'];enc=ROOT/'datasets'/(item+'.truth.aesgcm')
        raw=enc.read_bytes();key=bytes.fromhex(row['key_hex'])
        truth=json.loads(AESGCM(key).decrypt(raw[:12],raw[12:],item.encode()))
        salt=bytes.fromhex(truth['salt_hex']);obj={'id':item,'truth':truth['truth'],'salt_hex':truth['salt_hex']}
        commit=sha_bytes(salt+canon({'id':item,'truth':truth['truth']}))
        mp=json.loads((ROOT/'datasets'/'INPUT_MANIFEST.json').read_text())
        expected=next(x['salted_truth_commitment_sha256'] for x in mp['inputs'] if x['id']==item)
        if commit!=expected:raise RuntimeError('Truth commitment mismatch '+item)
        blind=json.loads((OUT/(item+'_ASSESSMENT.json')).read_text())
        res.append({'id':item,'truth':truth['truth'],'prediction':blind['prediction'],
         'correct':truth['truth']==blind['prediction'],'commitment_verified':True})
    save(OUT/'REVEALED_RESULTS.json',{'reveal':res,'accuracy':sum(x['correct'] for x in res)/len(res),
      'notice':'Synthetic control accuracy only; no physical SST claim.'})
    save(OUT/'REVEAL_DECISION.json',{'state':'REVEALED','frozen_ledger_sha256':s,'all_commitments_verified':True})
    z=ROOT.parent/(NAME+'-outputs_REVEALED.zip')
    with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED) as f:
        for p in OUT.iterdir():
            if p.is_file():f.write(p,arcname=p.name)
    print('REVEALED:',z)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',nargs='?',default='FREEZE',choices=['SELFTEST','BASIC','FULL','CERTIFY','FREEZE','REVEAL','REVEAL_IF_ALLOWED','PKLSA_IMPORT'])
    parser.add_argument('--keys',type=Path);parser.add_argument('--pklsa',type=Path)
    args=parser.parse_args()
    if args.mode=='SELFTEST':
        return subprocess.call([sys.executable,'-m','pytest',str(ROOT/'tests'),'-q'],cwd=ROOT)
    if args.mode in ('BASIC','FULL'):run();return 0
    if args.mode=='CERTIFY':
        print('CERTIFY NOT_CLOSED: native v1.0.7, independent trajectories and nonideal PDE not available. Blind output (if frozen) remains unchanged.');return 2
    if args.mode=='FREEZE':freeze();return 0
    if args.mode in ('REVEAL','REVEAL_IF_ALLOWED'):
        reveal(args.keys or Path('__external_reveal_keys_missing__'),strict=args.mode=='REVEAL');return 0
    if args.mode=='PKLSA_IMPORT':
        from .pklsa import inspect
        if args.pklsa is None:raise RuntimeError('Supply --pklsa PATH.npz')
        print(json.dumps(inspect(args.pklsa),indent=2));return 0
if __name__=='__main__':sys.exit(main())
