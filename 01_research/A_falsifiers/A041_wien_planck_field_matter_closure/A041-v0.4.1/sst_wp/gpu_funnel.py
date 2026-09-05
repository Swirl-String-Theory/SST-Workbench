from __future__ import annotations

import argparse, csv, json, math, os, secrets, shutil, subprocess, sys
from pathlib import Path
import numpy as np

from .common import dump_json, load_json
from .geometry import spacing_metrics
from .kernels import velocity
from .pklsa_adapter import atlas_rows, normalized_candidate, opaque_token, write_gpu_batch, write_xyz
from .blind_guard import assert_blind_code_clean, assert_blind_config_clean


def _pair_indices(next_idx, lags=(2,4,8,16)):
    nxt=np.asarray(next_idx,dtype=np.int64); pairs=[]
    for i in range(len(nxt)):
        if nxt[i] < 0: continue
        for lag in lags:
            j=i; ok=True
            for _ in range(lag):
                j=int(nxt[j])
                if j<0: ok=False; break
            if ok and j!=i: pairs.append((i,j))
    return pairs


def pair_strain_rms(X, V, next_idx):
    vals=[]
    for i,j in _pair_indices(next_idx):
        d=X[j]-X[i]; dv=V[j]-V[i]; den=float(np.dot(d,d))
        if den>1e-20: vals.append(float(np.dot(d,dv)/den))
    return float(np.sqrt(np.mean(np.square(vals)))) if vals else float('inf')


def shape_signature_drift(X0, X1, next_idx):
    vals=[]
    for i,j in _pair_indices(next_idx):
        d0=float(np.linalg.norm(X0[j]-X0[i])); d1=float(np.linalg.norm(X1[j]-X1[i]))
        if d0>1e-15 and d1>1e-15: vals.append(math.log(d1/d0))
    return float(np.sqrt(np.mean(np.square(vals)))) if vals else float('inf')


def _offsets_from_next(nxt):
    # Candidate writer lays each component contiguously; a wrap index marks each end.
    starts=[0];
    for i,j in enumerate(nxt):
        if int(j) >= 0 and int(j) <= i:
            if i+1 < len(nxt): starts.append(i+1)
    starts.append(len(nxt))
    return np.array(sorted(set(starts)),dtype=np.int64)


def cpu_screen_batch(records, core, cfl, steps=0, require_native=False):
    out=[]
    for rec in records:
        X=np.asarray(rec['points'],float).copy(); X0=X.copy(); offs=np.asarray(rec['offsets'],dtype=np.int64)
        nxt=np.asarray(rec['next'],dtype=np.int32)
        V0=velocity(X,offs,1.0,float(core),require_native=require_native)
        speed=np.linalg.norm(V0,axis=1); sm0=spacing_metrics(X,offs)
        strain=pair_strain_rms(X,V0,nxt)
        dt=4*math.pi*float(cfl)*float(sm0['ds_min'])**2
        for _ in range(int(steps)):
            k1=velocity(X,offs,1.0,float(core),require_native=require_native)
            mid=X+0.5*dt*k1
            k2=velocity(mid,offs,1.0,float(core),require_native=require_native)
            X=X+dt*k2
        sm1=spacing_metrics(X,offs)
        out.append({
            'opaque_id':rec['opaque_id'],
            'mean_speed':float(np.mean(speed)),
            'speed_cv':float(np.std(speed)/max(abs(np.mean(speed)),1e-30)),
            'pair_strain_rms':float(strain),
            'mesh_cv_initial':float(sm0['ds_cv']),
            'mesh_edge_ratio_initial':float(sm0['edge_ratio']),
            'shape_signature_drift':float(shape_signature_drift(X0,X,nxt)) if steps else 0.0,
            'mesh_cv_final':float(sm1['ds_cv']),
            'mesh_edge_ratio_final':float(sm1['edge_ratio']),
            'steps':int(steps),
            'dt_hat':float(dt),
        })
    return out, {'backend':'cpu_reference_fallback','device':'CPU/Python reference','precision':'float64'}


def _parse_csv(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))


def _parse_meta(path):
    d={}
    for line in Path(path).read_text(encoding='utf-8',errors='ignore').splitlines():
        if '=' in line:
            k,v=line.split('=',1);d[k.strip()]=v.strip()
    return d


def sycl_screen_batch(exe, input_path, output_csv, meta_path, steps):
    cmd=[str(Path(exe).resolve()),'--input',str(Path(input_path).resolve()),'--output',str(Path(output_csv).resolve()),'--meta',str(Path(meta_path).resolve()),'--steps',str(int(steps))]
    cp=subprocess.run(cmd,capture_output=True,text=True)
    if cp.returncode!=0:
        raise RuntimeError('SYCL funnel failed\nSTDOUT:\n'+cp.stdout[-4000:]+'\nSTDERR:\n'+cp.stderr[-4000:])
    rows=_parse_csv(output_csv); meta=_parse_meta(meta_path); meta['backend']='sycl_gpu'
    return rows,meta


def _f(v):
    try:return float(v)
    except:return float('inf')


def _stage1_key(m):
    return (_f(m.get('pair_strain_rms')), _f(m.get('speed_cv')), _f(m.get('mesh_cv_initial')), str(m.get('opaque_id')))


def _stage2_key(m):
    return (_f(m.get('shape_signature_drift')), _f(m.get('mesh_cv_final')), _f(m.get('mesh_edge_ratio_final')), _f(m.get('pair_strain_rms')), str(m.get('opaque_id')))


def _make_records(atlas_root, rows, N, secret_hex):
    rec=[]; private={}
    for row in rows:
        row,X,offs=normalized_candidate(atlas_root,row,N)
        oid=opaque_token(secret_hex,row['candidate_id'],'GF')
        nxt=np.full(len(X),-1,dtype=np.int32)
        for ci in range(len(offs)-1):
            a,b=int(offs[ci]),int(offs[ci+1]);nxt[a:b-1]=np.arange(a+1,b,dtype=np.int32);nxt[b-1]=a
        rec.append({'opaque_id':oid,'points':X,'offsets':offs,'next':nxt})
        private[oid]={'candidate_id':row['candidate_id'],'family':row['family'],'family_index':int(row['family_index']),'variant_index':int(row['variant_index'])}
    return rec,private


def _public_rows(metrics, selected_ids):
    sel=set(selected_ids); out=[]
    for m in metrics:
        q={k:(_f(v) if k not in {'opaque_id','steps'} else v) for k,v in m.items()}
        q['selected_for_next_stage']=m['opaque_id'] in sel
        out.append(q)
    secrets.SystemRandom().shuffle(out)
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('atlas_root')
    ap.add_argument('--config',required=True)
    ap.add_argument('--out-root',required=True)
    ap.add_argument('--private-dir',required=True)
    ap.add_argument('--backend',choices=['sycl','cpu'],default='sycl')
    ap.add_argument('--gpu-exe',default='gpu/sycl_funnel_fp32.exe')
    a=ap.parse_args()
    root=Path(__file__).resolve().parents[1]; assert_blind_code_clean(root)
    cfg=load_json(a.config); assert_blind_config_clean(cfg)
    atlas=Path(a.atlas_root); rows=atlas_rows(atlas)
    expected=int(cfg.get('funnel_expected_candidates',2352)); expected_fam=int(cfg.get('funnel_expected_families',49))
    fams=sorted({r['family'] for r in rows})
    if len(rows)!=expected or len(fams)!=expected_fam:
        raise SystemExit(f'PKLSA scope mismatch: candidates={len(rows)} families={len(fams)}')
    outroot=Path(a.out_root); pubdir=outroot/'funnel'; pubdir.mkdir(parents=True,exist_ok=True)
    priv=Path(a.private_dir);work=priv/'gpu_work';stagec=priv/'funnel_cpu_candidates'
    if work.exists(): shutil.rmtree(work)
    if stagec.exists(): shutil.rmtree(stagec)
    work.mkdir(parents=True);stagec.mkdir(parents=True)
    secret=secrets.token_hex(32)
    core=float(cfg['core_fraction']);cfl=float(cfg.get('funnel_gpu_cfl',0.12))

    # Stage 1: all 2352, instantaneous dimensionless velocity/strain screen.
    N1=int(cfg.get('funnel_stage1_resolution',64)); rec1,map1=_make_records(atlas,rows,N1,secret)
    if a.backend=='sycl':
        b1=write_gpu_batch(work/'stage1.bin',rec1,N1,core,cfl)
        met1,meta1=sycl_screen_batch(a.gpu_exe,b1,work/'stage1.csv',work/'stage1_meta.txt',0)
    else:
        met1,meta1=cpu_screen_batch(rec1,core,cfl,0,require_native=bool(cfg.get('require_native',False)))
    m1={m['opaque_id']:m for m in met1}
    per1=int(cfg.get('funnel_stage1_per_family',8)); survivors1=[]
    for fam in fams:
        ids=[oid for oid,q in map1.items() if q['family']==fam]
        ids.sort(key=lambda oid:_stage1_key(m1[oid]))
        survivors1.extend(ids[:per1])
    if len(survivors1)!=len(fams)*per1: raise RuntimeError('stage1 family quota incomplete')

    # Stage 2: short GPU RK2 shape/mesh screen, still target-free.
    row_by_id={r['candidate_id']:r for r in rows}
    rows2=[row_by_id[map1[oid]['candidate_id']] for oid in survivors1]
    N2=int(cfg.get('funnel_stage2_resolution',96)); rec2,map2=_make_records(atlas,rows2,N2,secret)
    steps=int(cfg.get('funnel_stage2_steps',8))
    if a.backend=='sycl':
        b2=write_gpu_batch(work/'stage2.bin',rec2,N2,core,cfl)
        met2,meta2=sycl_screen_batch(a.gpu_exe,b2,work/'stage2.csv',work/'stage2_meta.txt',steps)
    else:
        met2,meta2=cpu_screen_batch(rec2,core,cfl,steps,require_native=bool(cfg.get('require_native',False)))
    m2={m['opaque_id']:m for m in met2}; per2=int(cfg.get('funnel_stage2_per_family',2)); survivors2=[]
    for fam in fams:
        ids=[oid for oid,q in map2.items() if q['family']==fam]
        ids.sort(key=lambda oid:_stage2_key(m2[oid]))
        survivors2.extend(ids[:per2])
    if len(survivors2)!=len(fams)*per2: raise RuntimeError('stage2 family quota incomplete')

    # Materialize only Stage-C CPU certification candidates, with new opaque filenames.
    cpu_map={};
    for oid in survivors2:
        q=map2[oid]; row=row_by_id[q['candidate_id']]
        row,X,offs=normalized_candidate(atlas,row,int(cfg.get('qualification_input_resolution',256)))
        fname=opaque_token(secret,q['candidate_id'],'FC')+'.xyz'; p=stagec/fname
        write_xyz(p,X,offs,header='PKLSA candidate identity quarantined until reveal')
        cpu_map[str(p.resolve())]={**q,'gpu_stage2_opaque_id':oid,'gpu_stage2_metrics':m2[oid]}

    private={
        'format':'SST-WP-PKLSA-GPU-FUNNEL-PRIVATE-4.0','atlas_root':str(atlas.resolve()),'secret_hex':secret,
        'stage1_map':map1,'stage2_map':map2,'cpu_candidate_map':cpu_map,
        'stage1_survivors':survivors1,'stage2_survivors':survivors2,
    }
    dump_json(priv/'GPU_FUNNEL_PRIVATE.json',private)
    public={
        'format':'SST-WP-PKLSA-GPU-FUNNEL-PUBLIC-4.0',
        'atlas_candidate_count':len(rows),'atlas_family_count':len(fams),'SST_canonical_constants_used':False,'SI_units_used':False,
        'selection_target_used':False,'backend_requested':a.backend,
        'stage1':{'resolution_N':N1,'input_count':len(rec1),'per_family_survivors':per1,'survivor_count':len(survivors1),'backend_meta':meta1,'records':_public_rows(met1,survivors1)},
        'stage2':{'resolution_N':N2,'steps':steps,'input_count':len(rec2),'per_family_survivors':per2,'survivor_count':len(survivors2),'backend_meta':meta2,'records':_public_rows(met2,survivors2)},
        'stage3_cpu_candidate_count':len(cpu_map),
        'selection_policy':'Stage1: lexicographic pair-strain/speed-CV, fixed quota per family; Stage2: lexicographic invariant-shape-drift/mesh quality, fixed quota per family; Stage3: CPU reference qualification; no action result enters selection.',
        'identity_policy':'candidate and family identities are quarantined in private_reveal_keys; public rows use salted opaque IDs and randomized row order.',
        'epistemic_status':'GPU SCREENING ONLY; no GPU score is a final scientific PASS. Full-action finalists require CPU-native certification.'
    }
    dump_json(pubdir/'GPU_FUNNEL_PUBLIC.json',public)
    dump_json(pubdir/'FUNNEL_COUNTS.json',{'stage0':len(rows),'stage1':len(survivors1),'stage2':len(survivors2),'stage3_cpu_candidates':len(cpu_map),'families':len(fams),'backend':a.backend})
    print(json.dumps({'atlas':len(rows),'families':len(fams),'stage1_survivors':len(survivors1),'stage2_survivors':len(survivors2),'cpu_candidates':len(cpu_map),'backend':a.backend,'public':str(pubdir/'GPU_FUNNEL_PUBLIC.json')},indent=2))

if __name__=='__main__': main()
