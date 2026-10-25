"""A006 blind, dimensionless, unforced twist-knot versus triple-link falsifier."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, os, sys, zipfile
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from geometry import parse_xyz, arclength_resample, normalized, pair_linking, point_clearance, self_clearance_proxy, q_curvature, perturb_shape
from dynamics import evolve, velocity, run_controls, clock_diagnostic, result_metrics, perturbation_growth
ROOT=Path(__file__).resolve().parents[1]
SOURCE_DEFAULT=ROOT/'sources'/'A006-v0.5.0.zip'
CONTRACT=ROOT/'config'/'SCIENCE_CONTRACT.json'

def digest(data):return hashlib.sha256(data).hexdigest()
def filehash(path):return digest(Path(path).read_bytes())
def dump(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.partial')
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False),encoding='utf-8')
    os.replace(tmp,path)
def readjson(path):return json.loads(Path(path).read_text(encoding='utf8'))
def timestamp():return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')

def prepare(src,output):
    src=Path(src);output=Path(output)
    contract=readjson(CONTRACT); actual=filehash(src)
    if actual!=contract['source_archive_sha256']:raise RuntimeError('A006 archive SHA256 mismatch; unchanged source required')
    if (output/'SOURCE_FREEZE.json').exists():
        old=readjson(output/'SOURCE_FREEZE.json')
        if old['source_zip_sha256']!=actual:raise RuntimeError('Output dir has different frozen source')
        print('Already prepared: immutable source freeze verified')
        return
    with zipfile.ZipFile(src) as z:
        members=set(z.namelist())
        prefix='A006-v0.5.0/Output/v050/geometry/'
        records=[]
        for name in sorted(n for n in members if n.startswith(prefix) and n.endswith('.json') and '/LINK_' in n and 'CPFIXED61' in n):
            meta=json.loads(z.read(name)); xyz=name[:-5]+'.xyz'
            if xyz not in members:raise RuntimeError('missing '+xyz)
            raw=z.read(xyz); X=parse_xyz(raw)
            if len(X)!=3:raise RuntimeError('unexpected component count '+name)
            if meta['sha256']!=digest(raw):raise RuntimeError('source XYZ hash mismatch '+name)
            family=meta['composition']+'|'+meta['profile']
            records.append({'name':name,'xyz':xyz,'meta':meta,'raw_hash':digest(raw),'raw':raw,'family':family})
        if len(records)!=64:raise RuntimeError(f'Expected exactly 64 active records; got {len(records)}')
        groups=sorted(set(r['family'] for r in records))
        if len(groups)!=8:raise RuntimeError('Expected eight composition/profile family groups')
        held={}
        for comp in ['5_5_6','6_6_5']:
            gg=sorted(g for g in groups if g.startswith(comp+'|'))
            held[comp]=min(gg,key=lambda g:digest((actual+'|HOLDOUT|'+g).encode()))
        hold=set(held.values())
        primary=set()
        for comp in ('5_5_6','6_6_5'):
            eligible=[r for r in records if r['meta']['composition']==comp
                and r['family'] not in hold and r['meta']['minN']==512
                and r['meta']['name'].endswith('_ORIG_CPFIXED61')]
            if not eligible:raise RuntimeError('Missing DEV scout representative for '+comp)
            primary.add(min(eligible,key=lambda r:r['raw_hash'])['xyz'])
        sealed={};index=[]
        for item in records:
            meta=item['meta'];group=item['family'];fold='HOLDOUT' if group in hold else 'DEV'
            opaque='BX_'+digest((actual+'|'+item['raw_hash']).encode())[:14].upper()
            if opaque in sealed:raise RuntimeError('Opaque id collision')
            geom,info=normalized(item['raw'] and parse_xyz(item['raw']))
            dest=output/'BLIND_INPUTS'/(opaque+'.npz')
            dest.parent.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(dest,X0=geom[0],X1=geom[1],X2=geom[2])
            blindsha=filehash(dest)
            index.append({'id':opaque,'split':fold,'blind_npz_sha256':blindsha,'components':3,
                          'scout_primary':item['xyz'] in primary,
                          'scout': meta['minN']==512 and meta['orientation'] and meta['orientation'].get('policy')=='FIXED61' and 'MIRROR' not in meta['name']})
            sealed[opaque]={'zip_member_xyz':item['xyz'],'source_sha256':item['raw_hash'],
                             'metadata_member':item['name'],'composition':meta['composition'],
                             'profile':meta['profile'],'orientation':meta.get('orientation'),
                             'declared_minN':meta['minN'],'family':group,'split':fold,
                             'source_status':meta['status'],'raw_point_counts':[len(x) for x in geom],
                             'source_L0':info['L0_source_units'],
                             'component_knot_labels':meta['component_knots']}
        dump(output/'SOURCE_FREEZE.json',{'source_zip_sha256':actual,'contract_sha256':filehash(CONTRACT),'generator_source':'A006-v0.5.0','created_utc':timestamp(),
            'seed_count':len(index),'held_out_groups_count':len(hold),'source_unchanged':True})
        dump(output/'BLIND_INDEX.json',{'schema':'A006-BLIND-INDEX-1','seeds':index})
        dump(output/'SEALED_SOURCE_MAP.json',sealed)
        dump(output/'SPLIT_COMMIT.json',{'holdout_group_hashes':[digest((actual+g).encode()) for g in sorted(hold)],
            'holdout_policy':contract['holdout_policy'],'seed_count':len(index)})
        dump(output/'PREPARE_AUDIT.json',{'status':'SOURCE_FROZEN_BLIND_DATA_PREPARED','candidate_link_topology':'UNRESOLVED',
             'individual_component_knot_labels':'SOURCE_CLAIM_NOT_REVERIFIED','geometry_interpretation':'source-native 3-component candidate links, NOT proven L6a4 Borromean',
             'link_benefit':'UNTESTED','swirl_clock':'UNTESTED','source_version':'A006-v0.5.0'})
    print('PREPARE PASS: 64 blind samples, 8 families, 2 sealed holdout families; no dynamics run.')

def verify(out):
    out=Path(out)
    freeze=readjson(out/'SOURCE_FREEZE.json')
    if freeze['contract_sha256']!=filehash(CONTRACT):raise RuntimeError('Contract mutated since source preparation')
    idx=readjson(out/'BLIND_INDEX.json')['seeds']
    for row in idx:
        if filehash(out/'BLIND_INPUTS'/(row['id']+'.npz'))!=row['blind_npz_sha256']:
            raise RuntimeError('Blind coordinate tampering '+row['id'])
    return idx

def load_seed(out,seed_id,n):
    p=Path(out)/'BLIND_INPUTS'/(seed_id+'.npz')
    with np.load(p,allow_pickle=False) as z:
        X=[arclength_resample(z['X'+str(i)],n) for i in range(3)]
    return X

def diagnostic_seed(X,core):
    g=[pair_linking(X[i],X[j]) for i,j in ((0,1),(0,2),(1,2))]
    median=[float(np.median(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1))) for x in X]
    return {'pair_gauss_proxy':g,'max_spacing_to_core':max(median)/core,
        'intercomponent_vertex_clearance':min(point_clearance(X[i],X[j]) for i,j in ((0,1),(0,2),(1,2))),
        'self_vertex_clearance_proxies':[self_clearance_proxy(x) for x in X],
        'Q0':[q_curvature(x) for x in X],
        'B1_status':'UNRESOLVED_MILNOR_AND_COMPONENT_ISOTOPY'}

def calc_feedback(X,gamma,core,tmax,steps,eps):
    # Fixed perturbation in one component only, plus/minus: no external force.
    responses=[]
    for j in range(3):
        vals=[]
        for sign in [1,-1]:
            test=[x.copy() for x in X]
            test[j]=perturb_shape(test[j],sign*eps)
            r=evolve(test,gamma,core,tmax,steps,record=False)
            vals.append(np.asarray(r['q'][-1]))
        responses.append(((vals[0]-vals[1])/(2*eps)).tolist())
    R=np.asarray(responses).T
    return {'response_at_tmax':R.tolist(), 'perturbation_epsilon':eps,
            'three_cycle_product':float(R[0,1]*R[1,2]*R[2,0]),
            'feedback_gate':'DIAGNOSTIC_ONLY_CAUSAL_OPERATOR_NOT_INDEPENDENT_THREE_BODY_FORCE'}

def run(args):
    out=Path(args.out);index=verify(out)
    contract=readjson(CONTRACT)
    split='HOLDOUT' if args.mode=='HOLDOUT' else 'DEV'
    if args.mode=='HOLDOUT':
        lock=readjson(out/'DEV_LOCK.json')
        if lock['contract_sha256']!=filehash(CONTRACT) or lock['implementation_sha256']!=implementation_hash():
            raise RuntimeError('DEV lock invalidated by code/contract mutation')
    matching=[x for x in index if x['split']==split]
    if args.ids:
        wanted=set(args.ids.split(',')); matching=[x for x in matching if x['id'] in wanted]
        if len(matching)!=len(wanted):raise RuntimeError('Unknown or wrong-partition ID')
    elif args.mode=='BASIC':
        # Source identity remains sealed. First two by opaque ID for deterministic smoketest.
        matching=sorted([r for r in matching if r.get('scout_primary')],key=lambda x:x['id'])[:2]
    elif args.mode=='FEEDBACK':
        matching=sorted([r for r in matching if r.get('scout_primary')],key=lambda x:x['id'])[:2]
    elif args.mode=='STABILITY':
        matching=sorted([r for r in matching if r.get('scout')],key=lambda x:x['id'])[:6]
    elif args.mode=='FULL':
        # Prespecified first one per family is impossible without revealing map;
        # choose deterministic 6 opaque seeds for bounded development diagnostic.
        matching=sorted([r for r in matching if r.get('scout')],key=lambda x:x['id'])[:6]
    elif args.mode=='HOLDOUT':
        matching=sorted([r for r in matching if r.get('scout')],key=lambda x:x['id'])[:8]
    if args.limit:matching=matching[:args.limit]
    if not matching:raise RuntimeError('No cases selected')
    summary=[];reports=out/'RESULTS';reports.mkdir(exist_ok=True)
    batch=timestamp();tag=args.mode
    for idx,row in enumerate(matching,1):
        seed_id=row['id'];X=load_seed(out,seed_id,args.points)
        gamma=[float(v) for v in contract['gamma_sectors'][args.sector]]
        core=float(args.core or contract['core_ratio'])
        audit=diagnostic_seed(X,core)
        arms=('triple','single') if args.mode=='BASIC' else ('triple','single','pair','unlinked')
        result=run_controls(X,gamma,core,args.horizon,args.steps,arms=arms)
        result['topology_diagnostic']=audit
        result['clock']=clock_diagnostic(result['triple'],minimum_cycles=contract['minimum_clock_cycles'])
        result['parameters']={'N_per_component':args.points,'dimensionless_core':core,
           'dimensionless_t_horizon':args.horizon,'steps':args.steps,'gamma':gamma,'circulation_sector_index':args.sector,'mode':tag}
        if args.stability or args.mode in ('FULL','STABILITY'):
            result['stability_perturbation']=perturbation_growth(X,gamma,core,args.horizon,args.steps,contract['perturbation_epsilon'])
            ratios=[a['linked_to_isolated_amplification_ratio'] for a in result['stability_perturbation']['per_component']]
            policy=contract['stabilization_preregistered_diagnostic']
            if all(r<=policy['effect_threshold_linked_to_isolated_ratio'] for r in ratios):
                signal='COLLECTIVE_SUPPRESSION_SHORT_HORIZON_DIAGNOSTIC'
            elif all(r>=policy['countereffect_threshold'] for r in ratios):
                signal='COLLECTIVE_AMPLIFICATION_SHORT_HORIZON_DIAGNOSTIC'
            else:signal='MIXED_OR_EQUIVOCAL_DIAGNOSTIC'
            result['stability_perturbation']['preregistered_signal']=signal
            result['stability_perturbation']['scientific_stability']='UNRESOLVED'
        if args.feedback or args.mode=='FEEDBACK':
            result['feedback']=calc_feedback(X,gamma,core,args.horizon,args.steps,contract['perturbation_epsilon'])
        if args.temporal_check:
            a=evolve(X,gamma,core,args.horizon,args.steps,record=False)['final']
            b=evolve(X,gamma,core,args.horizon,args.steps*2,record=False)['final']
            d=np.linalg.norm(np.concatenate([x-y for x,y in zip(a,b)]))/max(np.linalg.norm(np.concatenate(b)),1e-20)
            result['temporal_refinement_relative_L2']=float(d)
        else:result['temporal_refinement_relative_L2']=None
        result['gate_ledger']={
            'B0':{'status':'PASS','reason':'source SHA verified, blind samples unchanged'},
            'B1':{'status':'UNRESOLVED','reason':'Milnor triple and rigorous component isotopy not certified'},
            'B2':{'status':'FAIL' if audit['max_spacing_to_core']>0.25 or 2*core>=min(audit['self_vertex_clearance_proxies']+[audit['intercomponent_vertex_clearance']]) else 'UNRESOLVED',
                'reason':'Needs >=4 sample intervals per core, core diameter below nonlocal vertex proximity; independent spatial/time convergence and segment clearance still required'},
            'B3':{'status':'UNRESOLVED','reason':'finite core surrogate; invariants and collision verification not fully certified'},
            'B4':{'status':'UNRESOLVED','reason':'finite-horizon deformation not Lyapunov/Floquet stability'},
            'B5':{'status':'UNRESOLVED','reason':'comparisons and feedback diagnostic are not certified causal stability proof'},
            'B6':{'status':'UNRESOLVED','reason':'independent clock observables and refinemement not certified'},
            'B7':{'status':'UNRESOLVED','reason':'holdout evidence not certified'},
            'B8':{'status':'NOT_RUN','reason':'no independent 3D Euler/GPE solver'},
            'B9':{'status':'UNRESOLVED','reason':'no SST constants or proper-time claims'}}
        result['scientific_conclusion']='MODEL_DIAGNOSTICS_ONLY_NOT_CERTIFIED'
        result['source_identity_revealed']=False
        result['id']=seed_id
        fname=f'{batch}_{tag}_{idx:03d}_{seed_id}.json'
        dump(reports/fname,result)
        summary.append({'id':seed_id,'result_file':fname,'split':split,'B0':'PASS',
            'B1':'UNRESOLVED','B2':result['gate_ledger']['B2']['status'],'B9':'UNRESOLVED',
            'three_ring_final_shape_error':result['triple']['final_shape_error'],
            'single_ring_final_shape_errors':[result[f'single_{i}']['final_shape_error'][0] for i in range(3)]})
        print(f'{idx}/{len(matching)} {seed_id} {tag}: B0 PASS, B1/B9 UNRESOLVED; numerical data saved',flush=True)
    outpath=reports/f'{batch}_{tag}_SUMMARY.json'
    dump(outpath,{'mode':tag,'batch_id':batch,'source_archive_sha256':readjson(out/'SOURCE_FREEZE.json')['source_zip_sha256'],
        'contract_sha256':filehash(CONTRACT),'implementation_sha256':implementation_hash(),
        'qualification':'DEVELOPMENT_DIAGNOSTIC_NOT_CERTIFIED','cases':summary})
    print('SUMMARY '+str(outpath));return outpath

def implementation_hash():
    h=hashlib.sha256()
    for n in sorted((ROOT/'src').glob('*.py')):h.update(n.name.encode()+b'\0'+n.read_bytes())
    return h.hexdigest()

def lock(out):
    out=Path(out);verify(out)
    summaries=sorted((out/'RESULTS').glob('*_FULL_SUMMARY.json'))
    if not summaries:raise RuntimeError('FULL DEV run required before LOCK')
    current=readjson(summaries[-1]);
    if current['contract_sha256']!=filehash(CONTRACT) or current['implementation_sha256']!=implementation_hash():raise RuntimeError('FULL used different contract or solver')
    dump(out/'DEV_LOCK.json',{'contract_sha256':filehash(CONTRACT),'implementation_sha256':implementation_hash(),
        'locked_from':summaries[-1].name,'source_freeze_sha256':filehash(out/'SOURCE_FREEZE.json'),
        'locked_utc':timestamp(),'holdout':'NOT_YET_RUN'})
    print('DEV LOCK written; holdout can now be run without changes to implementation or science contract.')

def reveal(out):
    out=Path(out)
    if not (out/'DEV_LOCK.json').exists():raise RuntimeError('LOCK required')
    runs=list((out/'RESULTS').glob('*_HOLDOUT_SUMMARY.json'))
    if not runs:raise RuntimeError('HOLDOUT results required before reveal')
    outpath=out/'REVEAL_ONLY.json'
    if outpath.exists():raise RuntimeError('Already revealed, refusing overwrite')
    dump(outpath,{'classification':'REVEAL_ONLY_NO_SCIENCE_PROMOTION','source_map':readjson(out/'SEALED_SOURCE_MAP.json'),
             'holdout_batches':[x.name for x in runs]})
    print('Revealed in '+str(outpath))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['PREPARE','BASIC','FULL','STABILITY','FEEDBACK','MATRIX','HOLDOUT','LOCK','REVEAL','REPORT','SELFTEST'])
    p.add_argument('--zip',default=str(SOURCE_DEFAULT));p.add_argument('--out',default=str(ROOT/'outputs'))
    p.add_argument('--points',type=int,default=None);p.add_argument('--steps',type=int,default=None)
    p.add_argument('--horizon',type=float,default=None);p.add_argument('--core',type=float,default=None)
    p.add_argument('--sector',type=int,choices=[0,1,2,3],default=0,help='Locked gamma sign sector; default 0 is +++')
    p.add_argument('--ids',help='Comma-separated blind IDs');p.add_argument('--limit',type=int,default=None)
    p.add_argument('--feedback',action='store_true');p.add_argument('--stability',action='store_true');p.add_argument('--temporal-check',action='store_true')
    a=p.parse_args()
    if a.mode=='SELFTEST':
        import unittest
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py')
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1
    if a.mode=='PREPARE':prepare(a.zip,a.out)
    elif a.mode=='LOCK':lock(a.out)
    elif a.mode=='REVEAL':reveal(a.out)
    elif a.mode=='REPORT':
        from report import produce
        pdf,md=produce(a.out,ROOT);print('REPORT '+str(pdf)+' '+str(md))
    else:
        if not Path(a.out,'SOURCE_FREEZE.json').exists():prepare(a.zip,a.out)
        defaults={'BASIC':(48,4,.004),'FULL':(96,16,.08),'FEEDBACK':(72,8,.04),'STABILITY':(192,64,.5),'MATRIX':(96,16,.08),'HOLDOUT':(96,16,.08)}
        n,s,t=defaults[a.mode];a.points=a.points or n;a.steps=a.steps or s;a.horizon=a.horizon or t
        if a.points<24 or a.steps<1 or a.horizon<=0:raise ValueError('invalid numerical arguments')
        run(a)
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:
        print(f'REJECTED {type(e).__name__}: {e}',file=sys.stderr)
        sys.exit(3)
