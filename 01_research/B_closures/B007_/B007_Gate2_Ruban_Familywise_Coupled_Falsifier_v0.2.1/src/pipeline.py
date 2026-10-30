"""Gate2 Ruban Familywise Coupled Falsifier v0.2.1.

G1 analytic knot/link geometry; G2 finite-time *reduced* filament screen;
G3 independent sampling + self-contained promotion; G4 development-only
fully coupled periodic finite-core Euler pilot. NO PHYSICAL EQUILIBRIUM PROVEN.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,os,sys,datetime,subprocess,zipfile,platform
from pathlib import Path
import numpy as np
from .geometry import (ROOT,CONFIG,GENER,fingerprint,get_config,families,generate,metrics,export)
from .filaments import run_pair,exploratory_score
from .report import create as make_pdf
from .external_links import get_registry,generate_imported,gauss_midpoint,verify_source,REGISTRY

VERSION='v0.2.1';PREFIX='Gate2_Ruban_Familywise_Coupled_Falsifier'
OUTBASE=ROOT/(PREFIX+'_'+VERSION+'-outputs')

def save_json(f,obj):
    f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False,default=str)+'\n',encoding='utf-8')

def save_csv(f,rows):
    rows=list(rows);f.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        f.write_text('NO_ROWS\n');return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with f.open('w',encoding='utf-8',newline='') as h:
        w=csv.DictWriter(h,fieldnames=keys);w.writeheader();w.writerows(rows)

def parse_floats(s):
    a=[float(x.strip()) for x in s.split(',') if x.strip()]
    if not a or len(set(a))!=len(a) or any(not math.isfinite(x) for x in a):raise ValueError('Expected finite distinct comma-separated values')
    return a

def parse_integers(s):
    z=[int(k) for k in s.split(',')]
    if not z or len(set(z))!=len(z) or any(k<64 for k in z):raise ValueError('Invalid point list')
    return z

def values(args,cfg):
    if args.b0:
        bb=parse_floats(args.b0)
    elif args.b_min is not None:
        if args.b_max is None or args.b_step is None:raise ValueError('--b-min also needs --b-max and --b-step')
        if args.b_step<=0:raise ValueError('B step must be positive')
        steps=(args.b_max-args.b_min)/args.b_step
        if steps<0 or abs(steps-round(steps))>1e-8:raise ValueError('B range requires exact integer number of steps')
        bb=[round(args.b_min+i*args.b_step,10) for i in range(int(round(steps))+1)]
    elif args.profile=='fine':
        f=cfg['fine_B0_range'];s=int(round((f['max']-f['min'])/f['step']))
        bb=[round(f['min']+i*f['step'],10) for i in range(s+1)]
    else:bb=list(cfg['pilot_B0'])
    bb=sorted(bb)
    if not all(0<x<1 for x in bb):raise ValueError('B0 must be in (0,1)')
    ll=parse_floats(args.lambda_values) if args.lambda_values else [float(x) for x in cfg['Lambda']]
    if any(x<=0 for x in ll):raise ValueError('Lambda must be positive')
    return bb,ll

def selected_families(args,cfg):
    fs=families(cfg)
    for name,ent in get_registry().items():
        fs[name]={'kind':'external_link','topology_id':'BORROMEAN_UNCERTIFIED',
                  'source_kind':'IMPORTED_CUSTOM_3_COMPONENT', 'component_knot_labels':ent['component_knots']}
    if args.topology is not None:
        if args.family!='T_2_3':raise ValueError('Use --topology without --family; selectors are exclusive')
        found={name:meta for name,meta in fs.items() if meta.get('topology_id')==args.topology}
        if not found:raise ValueError('Topology not found: '+args.topology)
        return found
    if args.kind is not None:
        if args.family!='T_2_3':raise ValueError('Use --kind without --family; selectors are exclusive')
        return {name:meta for name,meta in fs.items() if
            (args.kind=='knots' and not is_external(meta) and math.gcd(meta['p'],meta['q'])==1) or
            (args.kind=='links' and (is_external(meta) or math.gcd(meta['p'],meta['q'])>1)) or
            (args.kind=='torus-links' and not is_external(meta) and math.gcd(meta['p'],meta['q'])>1) or
            (args.kind=='borromean' and is_external(meta))}

    if args.family.lower()=='all':return fs
    a=[x.strip() for x in args.family.split(',') if x.strip()]
    for f in a:
        if f not in fs:raise ValueError(f'Unknown {f}. Select from --list-families.')
    return {f:fs[f] for f in a}

def is_external(f):return f.get('kind')=='external_link'

def seed_for(name,f,b,n,pert,cfg,source_variant='original'):
    if is_external(f):return generate_imported(name,n,perturbed=pert,reference=(source_variant=='reference'))[0]
    return generate(f['p'],f['q'],b,n,pert,cfg)

def parameter_b_for(name,f,bb):return [None] if is_external(f) else bb

def manifest(out):
    d={p.relative_to(out).as_posix():fingerprint(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='MANIFEST_SHA256.json'}
    save_json(out/'MANIFEST_SHA256.json',d)
    return d

def pack_run(out):
    """Immutable per-run archive with hash. Source release stays separately."""
    tar=out.parent/(out.name+'_outputs.zip')
    if tar.exists():raise FileExistsError('Immutable run archive already exists: '+str(tar))
    with zipfile.ZipFile(tar,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,out.name+'/'+p.relative_to(out).as_posix())
    with zipfile.ZipFile(tar) as z:
        first=z.testzip()
        if first:raise RuntimeError('corrupt zipped entry '+first)
    (Path(str(tar)+'.sha256')).write_text(fingerprint(tar)+'  '+tar.name+'\n')
    return tar

def imported_sidecar(name):
    from .external_links import DATADIR
    e=verify_source(name)
    x=e['original'].replace('.xyz','.json').replace('.txt','.json')
    candidate=DATADIR/x
    if candidate.is_file():
        info=json.loads(candidate.read_text(encoding='utf-8'))
        return info.get('status','NOT_SPECIFIED')
    return 'NO_SIDECAR_MILNOR_UNRESOLVED'

def stage1(selected,bb,out,args,cfg):
    rows=[]
    for name,f in selected.items():
        for b in parameter_b_for(name,f,bb):
            part=seed_for(name,f,b,args.seed_points,False,cfg,getattr(args,"external_source","original"))
            g=metrics(part)
            rows.append({'family':name,'topology':f.get('topology_id'),'B0':b,'p':f.get('p'),'q':f.get('q'),
             'kind':'knot' if len(part)==1 else 'link','components':len(part),
             'source':'IMPORTED_CUSTOM_SHA256' if is_external(f) else 'ANALYTIC_E010_V036','seed_geometry_sha256':hashlib.sha256(b''.join(p.tobytes() for p in part)).hexdigest(),
             **g,'pairwise_gauss_approx':gauss_midpoint(part) if is_external(f) else None,
             'milnor_mu123':'UNRESOLVED' if is_external(f) else 'NOT_MEASURED',
             'selected_import_sha256':verify_source(name)[args.external_source+'_sha256'] if is_external(f) else None,
             'selected_import_source':args.external_source if is_external(f) else None,
             'original_source_status':imported_sidecar(name) if is_external(f) else 'ANALYTIC',
             'gate':'IMPORTED_LINK_ISOTOPY_UNRESOLVED' if is_external(f) else 'SCREENED_NOT_FINITE_CORE_CERTIFIED'})
    save_csv(out/'G1_GEOMETRY.csv',rows)
    stat={'status':'PASS_GEOMETRY_SCREEN_IMPORTED_TOPOLOGY_UNRESOLVED' if any(is_external(f) for f in selected.values()) else 'PASS_ANALYTIC_GEOMETRY_SCREEN_ONLY','count':len(rows),'families':len(selected),
          'imported_custom_families':sum(is_external(f) for f in selected.values()),
          'unproven':['Exact reach','Continuous polygon segment nonintersection','Finite-core vortex equilibrium',
          'Imported link Milnor mu123 and full isotopy']}
    save_json(out/'G1_GATE.json',stat)
    return rows,stat

def mode_gamma(n,mode):return [1.0/n]*n if mode=='total' else [1.0]*n

def imported_link_audit(selected,out):
    """Preserve exact source provenance; only *approximate* pairwise diagnostics.

    Full Milnor mu123 and link isotopy remain deliberately UNRESOLVED.
    """
    from .external_links import normalized_parts
    from scipy.spatial import cKDTree
    audited=[]
    for name,f in selected.items():
        if not is_external(f):continue
        entry=verify_source(name)
        originals,o_meta=normalized_parts(name,'original')
        row={'family':name,'profile':entry['profile'],'component_knot_labels':entry['component_knots'],
             'source_status':imported_sidecar(name),'original_sha256':entry['original_sha256'],
             'reference_sha256':entry.get('reference_sha256'),
             'original_component_counts':o_meta['original_counts'],
             'original_source_normalization':o_meta,
             'pairwise_gauss_midpoint_128':gauss_midpoint(originals,128),
             'pairwise_linking_certified':False,'milnor_mu123':'UNRESOLVED',
             'full_link_isotopy':'UNRESOLVED',
             'has_exact_borromean_topology_proof':False}
        if entry.get('reference'):
            refs,r_meta=normalized_parts(name,'reference')
            row['reference_component_counts']=r_meta['original_counts']
            row['reference_source_normalization']=r_meta
            row['sampled_bidirectional_hausdorff_normalized']=[float(max(
                    np.max(cKDTree(y).query(x)[0]),np.max(cKDTree(x).query(y)[0])))
                    for x,y in zip(originals,refs)]
        audited.append(row)
    if audited:save_json(out/'G1_IMPORTED_LINK_PROVENANCE.json',{
        'status':'PROVENANCE_VERIFIED_LINK_ISOTOPY_UNRESOLVED',
        'reference_geometry_warning':'Source resolution checks are sampled geometric proximity, not topology certification',
        'sources':audited})
    return audited

def stage2(selected,bb,ll,out,args,cfg):
    rows=[];allcount=sum(len(parameter_b_for(n,f,bb)) for n,f in selected.items())*len(ll)
    count=0
    for name,f in selected.items():
        for b in parameter_b_for(name,f,bb):
            o=seed_for(name,f,b,args.seed_points,False,cfg,getattr(args,"external_source","original"))
            p=seed_for(name,f,b,args.seed_points,True,cfg,getattr(args,"external_source","original"))
            for lam in ll:
                r=run_pair(o,p,lam,args.screen_points,args.screen_steps,args.final_time,component_gamma=mode_gamma(len(o),getattr(args,'circulation_mode','total')))
                seg_over_xi=max(float(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1).sum()/args.screen_points) for c in o)/math.exp(-lam)
                dt_over_xi2=(args.final_time/args.screen_steps)*math.exp(2*lam)
                spatial_eligible=seg_over_xi<=args.max_segment_over_core
                rows.append({'family':name,'topology':f.get('topology_id'),'B0':b,'Lambda':lam,
                   'component_count':len(o),'source_kind':f.get('source_kind','ANALYTIC_E010_V036'),
                   'circulation_mode':getattr(args,'circulation_mode','total'),'xi_over_R0':math.exp(-lam),
                   'segment_over_xi':seg_over_xi,
                   'dt_over_xi2':dt_over_xi2,
                   'spatial_preflight_pass':spatial_eligible,
                   'thin_tube_screen_warning': 'IMPORTED_NO_B0_THIN_CORE_UNRESOLVED' if b is None else ('B0_OVER_XI_LT_4' if b*math.exp(lam)<4 else 'UNQUALIFIED_AS_THIN_CORE'),
                   'score':exploratory_score(r),**r,
                   'status':'REDUCED_FILAMENT_EXPLORATORY_NOT_3D_EULER'})
                count+=1
            if count%max(1,len(parameter_b_for(name,f,bb))*len(ll))==0:
                print(f'  G2: {count}/{allcount} nominal+perturbed matched scenarios, family={name}',flush=True)
    save_csv(out/'G2_FILAMENT_SCAN.csv',rows)
    eligible_count=sum(1 for r in rows if r['spatial_preflight_pass'])
    stat={'status':'PASS_REDUCED_SCREEN_EXECUTED_RESOLUTION_LIMITED','count':len(rows)*2,
          'spatial_preflight_eligible_pairs':eligible_count,'spatial_preflight_ineligible_pairs':len(rows)-eligible_count,
          'max_segment_over_core_heuristic':args.max_segment_over_core,
          'paired_cases':len(rows),'final_time_star':args.final_time,'filament_points':args.screen_points,'circulation_mode':getattr(args,'circulation_mode','total'),
          'ranking_function':'max(initial rigid residuals) + max(shape drifts) + 0.02*max(0,perturbation amplification - 1)',
          'warning':'Not a physical stability measurement, full Euler solve, or validated thin-core limit'}
    save_json(out/'G2_GATE.json',stat)
    return rows,stat

def stage3(selected,bb,ll,scores,out,args,cfg):
    winners=[];hold=[];exports=[]
    ns=parse_integers(args.refine_points);promote=parse_integers(args.promote_points)
    for name,f in selected.items():
        local=[r for r in scores if r['family']==name]
        qualified=[r for r in local if r['spatial_preflight_pass']]
        best=min(qualified if qualified else local,key=lambda r:(r['score'],r['B0'] if r['B0'] is not None else 0,r['Lambda']))
        b=best['B0'];lam=best['Lambda'];res={}
        for n in ns:
            o=seed_for(name,f,b,n,False,cfg,getattr(args,"external_source","original"))
            p=seed_for(name,f,b,n,True,cfg,getattr(args,"external_source","original"))
            test=run_pair(o,p,lam,n,args.screen_steps,args.final_time,component_gamma=mode_gamma(len(o),getattr(args,'circulation_mode','total')))
            res[str(n)]={'score':exploratory_score(test),'measurements':test}
        last=res[str(ns[-1])]['score'];previous=res[str(ns[-2])]['score'] if len(ns)>1 else last
        shift=abs(last-previous)
        row={'family':name,'topology':f.get('topology_id'),'p':f.get('p'),'q':f.get('q'),
         'B0':b,'Lambda':lam,'score':float(best['score']),
         'selected_from_spatial_eligible_candidates':bool(qualified),
         'segment_over_xi_at_screening':best['segment_over_xi'],
         'dt_over_xi2_at_screening':best['dt_over_xi2'],
         'B_at_scanned_edge':False if b is None else b in (bb[0],bb[-1]),'Lambda_at_scanned_edge':lam in (min(ll),max(ll)),
         'score_last_refinement':last,'holdout_difference':shift,
         'holdout_relative_change':shift/max(abs(last),1e-30),
         'holdout_points':ns,'promoted_points':promote,
         'status':'PROVISIONAL_IMPORTED_LINK_TOPOLOGY_UNRESOLVED' if is_external(f) else ('PROVISIONAL_SPATIALLY_UNRESOLVED' if not qualified else 'PROVISIONAL_AWAITING_INDEPENDENT_CONVERGENCE')}
        winners.append(row)
        hold.append({'family':name,'B0':b,'Lambda':lam,'resolution_evidence':res,'status':row['status']})
        for n in promote:
            o=seed_for(name,f,b,n,False,cfg,getattr(args,"external_source","original"))
            p=seed_for(name,f,b,n,True,cfg,getattr(args,"external_source","original"))
            name_id=f'{name}_N{n}' if b is None else f'{name}_B{round(b*10000):04d}_N{n}'
            exports += [*export(o,out,name_id,'nominal'),*export(p,out,name_id,'perturbed')]
            if is_external(f):
                ref=verify_source(name)
                for record in exports[-(len(o)+len(p)) :]:record.update({'source_family':name,'source_sha256':ref[args.external_source+'_sha256'],
                         'selected_import_source':args.external_source, 'regeneration':'POLYGON_ARCLENGTH_INTERPOLATION_NOT_ANALYTIC','milnor_mu123':'UNRESOLVED'})
    winners.sort(key=lambda r:(r['score'],r['holdout_difference']))
    for i,r in enumerate(winners,1):r['provisional_rank']=i
    save_csv(out/'G3_FAMILY_WINNERS.csv',winners)
    save_json(out/'G3_HOLDOUT.json',hold)
    save_json(out/'G3_PROMOTED_FILES.json',exports)
    stat={'status':'RANKING_PROVISIONAL_NUMERICAL_CONVERGENCE_UNRESOLVED','count':len(winners),
          'spatially_ineligible_family_count':sum(not w['selected_from_spatial_eligible_candidates'] for w in winners),
          'promoted_xyz_files':len(exports),'resolution_checks':ns,'promoted_points':promote,
          'note':'Analytic torus seeds regenerated from E010 formula; imported custom links promoted by polygon arclength interpolation only, never adding source information. Promoted N does not imply N-point dynamics.',
          'selection':'B0 and Lambda jointly varied; family winners are separate topological embeddings, not independent physical source groups'}
    save_json(out/'G3_GATE.json',stat)
    return winners,stat

def stage4(selected,winners,out,args,cfg):
    from .coupled import evaluate
    chosen=winners[:min(len(winners),args.max_g4)] if args.euler=='preview' else []
    if args.euler=='off':
        stat={'status':'NOT_RUN_USER_DISABLED','count':0}
        save_json(out/'G4_GATE.json',stat);save_csv(out/'G4_COUPLED.csv',[]);return [],stat
    records=[]
    bgstyles=[x.strip() for x in args.background.split(',')]
    if any(s not in ('none','single','triple','3x3','5x5') for s in bgstyles):raise ValueError('Invalid background style')
    for winner in chosen:
        fam=selected[winner['family']];b=winner['B0']
        parts=seed_for(winner['family'],fam,b,args.euler_curve_points,False,cfg,getattr(args,"external_source","original"))
        for style in bgstyles:
            r=evaluate(parts,style,args.euler_grid,args.euler_holdout,args.euler_sigma,args.euler_box,args.gamma_background,args.euler_dt,args.circulation_mode)
            r.update({'family':winner['family'],'B0':b,'Lambda_selected_for_filament_only':winner['Lambda'],
                  'scientific_admission':'BLOCKED_IMPORTED_LINK_ISOTOPY_AND_MILNOR_UNRESOLVED' if is_external(fam) else 'UNRESOLVED_EULER_ROOT',
                  'source_geometry_points_euler':args.euler_curve_points,
                  'independent_numerical_backend':False,'full_field_root_finder':False,
                  'imported_link_isotopy':'UNRESOLVED' if is_external(fam) else 'NOT_APPLICABLE'})
            print(f"  G4: {winner['family']} B={b if b is not None else 'n/a'} {style} -> {r['status']}; holdout R*={r['holdout']['max_Rstar']:.4g}",flush=True)
            records.append(r)
    save_json(out/'G4_COUPLED.json',records)
    save_csv(out/'G4_COUPLED.csv',[{'family':r['family'],'B0':r['B0'],'background':r['background'],
       'train_Rstar':r['train']['max_Rstar'],'holdout_Rstar':r['holdout']['max_Rstar'],
       'filter_train':r['projection_change_train_max'],
       'filter_holdout':r['projection_change_holdout_max'],
       'separation_lower':r['geometry']['clearance_lower_bound'],'status':r['status']} for r in records])
    stat={'status':'G2_UNRESOLVED_NO_CERTIFIED_EQUILIBRIUM','count':len(records),
     'blocked_count':sum(r['status'].startswith('BLOCKED') for r in records),
     'imported_link_topology_admission':'BLOCKED_MILNOR_MU123_AND_ISOTOPY_UNRESOLVED' if any(is_external(f) for f in selected.values()) else 'NOT_APPLICABLE',
     'limits':['Single shared periodic Euler field; not a full-field equilibrium optimizer',
      'No independent backend parity','No domain size/extrapolation certification',
      'No material topology guarantee during spectral time stepping','No rotational relative equilibria in periodic cube']}
    save_json(out/'G4_GATE.json',stat)
    return records,stat

def create_parser():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--list-families',action='store_true')
    p.add_argument('--family',default='T_2_3',help='T_2_3 or T_3_2 or T_2_9, comma-separated choices, or all')
    p.add_argument('--topology',default=None,help='Compare ALL embeddings of a topology_id, e.g. 3_1')
    p.add_argument('--kind',choices=['knots','links','torus-links','borromean'],default=None,help='Select only the 24 knots or only 6 links')
    p.add_argument('--external-source',choices=['original','reference'],default='original',help='Choose imported N2048 original or N1024 source reference (two mixed families only)')
    p.add_argument('--circulation-mode',choices=['total','per-component'],default='total',help='Total=1 split evenly or gamma=1 for each material link component')
    p.add_argument('--profile',choices=['pilot','fine'],default='pilot')
    p.add_argument('--b0',help='Comma-separated B0 values overriding profile')
    p.add_argument('--b-min',type=float);p.add_argument('--b-max',type=float);p.add_argument('--b-step',type=float)
    p.add_argument('--lambda-values',default=None,help='Comma-separated Lambda values; picks BOTH B0 and Lambda')
    p.add_argument('--seed-points',type=int,default=1024,help='Analytic initial G1/G2 seed points per component')
    p.add_argument('--screen-points',type=int,default=128,help='Reduced filament points per component')
    p.add_argument('--screen-steps',type=int,default=3)
    p.add_argument('--final-time',type=float,default=.015,help='Dimensionless fixed filament final time')
    p.add_argument('--max-segment-over-core',type=float,default=2.,help='Exploratory spatial resolution warning; not a mathematical convergence certificate')
    p.add_argument('--refine-points',default='128,256,512',help='G3 reduced-filament independent resolution samples')
    p.add_argument('--promote-points',default='2048',help='Export both nominal and perturbed high resolution geometries')
    p.add_argument('--euler',choices=['preview','off'],default='preview')
    p.add_argument('--background',default='single',help='none,single,triple,3x3,5x5 or comma-separated selection')
    p.add_argument('--max-g4',type=int,default=1,help='Number of top provisional winners to test in costly G4')
    p.add_argument('--euler-grid',type=int,default=20);p.add_argument('--euler-holdout',type=int,default=24)
    p.add_argument('--euler-curve-points',type=int,default=1024)
    p.add_argument('--euler-sigma',type=float,default=.12)
    p.add_argument('--euler-box',type=float,default=6.)
    p.add_argument('--gamma-background',type=float,default=.05)
    p.add_argument('--euler-dt',type=float,default=.001)
    p.add_argument('--run-id',default=None)
    p.add_argument('--dry-run',action='store_true',help='Print planned run count, no outputs')
    return p

def main(argv=None):
    args=create_parser().parse_args(argv)
    cfg=get_config();ff=families(cfg)
    ff.update({name:{'kind':'external_link','topology_id':'BORROMEAN_UNCERTIFIED'} for name in get_registry()})
    if args.list_families:
        for name,d in ff.items():print(f"{name:9s} {d.get('topology_id') or 'unspecified':12s} {'LINK' if d.get('kind')=='external_link' or math.gcd(d['p'],d['q'])>1 else 'KNOT'} components={(3 if d.get('kind')=='external_link' else math.gcd(d['p'],d['q']))}")
        return 0
    if args.screen_points<64 or args.seed_points<64 or args.screen_steps<1 or args.final_time<=0:raise ValueError('Invalid screening resolution/time')
    if args.euler_grid<12 or args.euler_holdout<=args.euler_grid:raise ValueError('Need grid >=12 and finer holdout')
    if args.euler_sigma<=0 or args.euler_box<=0:raise ValueError('Invalid Euler box/core width')
    selected=selected_families(args,cfg);bb,ll=values(args,cfg)
    if args.external_source=='reference' and any(is_external(f) and not verify_source(name).get('reference') for name,f in selected.items()):
        raise ValueError('--external-source reference requires one of the two supplied 1024/2048 composite link families.')
    if any(is_external(f) for f in selected.values()) and (args.b0 or args.b_min is not None):
        raise ValueError('Custom imported Borromean geometries have no torus B0. Do not pass --b0/--b-min for them.')
    scenarios=sum(len(parameter_b_for(name,f,bb)) for name,f in selected.items())*len(ll)*2
    print(f'PLAN: {len(selected)} families, {len(bb) if any(not is_external(f) for f in selected.values()) else 0} torus B0 (N/A for imported), {len(ll)} Lambda, {scenarios} nominal/perturbed reduced filament runs; per-family promoted N={args.promote_points}',flush=True)
    if args.dry_run:return 0
    timestamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    sign=hashlib.sha256(json.dumps(vars(args),sort_keys=True).encode()).hexdigest()[:8]
    selector=(('topology_'+args.topology) if args.topology else ('kind_'+args.kind if args.kind else args.family))
    run_id=args.run_id or f'{selector.replace(",","-")}_{args.profile}_{timestamp}_{sign}'
    if '/' in run_id or '\\' in run_id or '..' in run_id:raise ValueError('Unsafe run ID')
    out=OUTBASE/'runs'/run_id
    if out.exists():raise FileExistsError('No overwrite permitted: '+str(out))
    out.mkdir(parents=True)
    ledger={'schema':'GATE2-RUBAN-FAMILYWISE-V021','version':VERSION,'run_id':run_id,'family':list(selected),
       'profile':args.profile,'B0_values':([] if all(is_external(f) for f in selected.values()) else bb),'Lambda_values':ll,'screen_points':args.screen_points,
       'promotion_points':args.promote_points,'source_generator_sha256':fingerprint(GENER),
       'source_config_sha256':fingerprint(CONFIG),
       'imported_external_registry_sha256':fingerprint(REGISTRY),
       'external_source_hashes':{name:{'original':verify_source(name)['original_sha256'],
                         'reference':verify_source(name).get('reference_sha256'),
                         'declared_component_knots':verify_source(name)['component_knots'],
                         'source_status':imported_sidecar(name)}
                         for name,f in selected.items() if is_external(f)},
       'circulation_mode':args.circulation_mode,
       'external_source':args.external_source,'command_arguments':vars(args),
       'gates':{},'scientific_status':'G2_UNRESOLVED_NO_CERTIFIED_EQUILIBRIUM','winners':[]}
    ledger['runtime']={'python':sys.version.split()[0],'platform':platform.platform(),'numpy':np.__version__}
    ledger['source_file_sha256']={p.relative_to(ROOT).as_posix():fingerprint(p) for p in sorted((ROOT/'src').rglob('*.py'))}
    ledger['source_file_sha256']['configs/E010_ruban_family_v036.json']=fingerprint(CONFIG)
    ledger['source_file_sha256']['configs/external_borromean_registry.json']=fingerprint(REGISTRY)
    from .external_links import DATADIR
    for name,f in selected.items():
        if is_external(f):
            meta=verify_source(name)
            for key in ('original','reference'):
                if meta.get(key):
                    source=DATADIR/meta[key]
                    ledger['source_file_sha256'][source.relative_to(ROOT).as_posix()]=fingerprint(source)
    save_json(out/'RUN_CONFIG.json',ledger)
    print('G1: independent analytic construction and finite polygon checks',flush=True)
    g1,s1=stage1(selected,bb,out,args,cfg);ledger['gates']['G1']=s1
    imported_link_audit(selected,out)
    print('G2: reduced paired finite-time filament screening',flush=True)
    g2,s2=stage2(selected,bb,ll,out,args,cfg);ledger['gates']['G2']=s2
    print('G3: joint B/Lambda selection, resolution check and INTERNAL high-res seed promotion',flush=True)
    g3,s3=stage3(selected,bb,ll,g2,out,args,cfg);ledger['gates']['G3']=s3;ledger['winners']=g3
    print('G4: fully back-reacting Gaussian periodic Euler PILOT (or explicit off)',flush=True)
    g4,s4=stage4(selected,g3,out,args,cfg);ledger['gates']['G4']=s4
    save_json(out/'G0_G4_ASSESSMENT.json',ledger)
    (out/'FALSIFIER_REPORT.md').write_text('\n'.join([
       f'# Gate2 Ruban Familywise Coupled Falsifier {VERSION}',
       '\nScientific conclusion: **G2_UNRESOLVED_NO_CERTIFIED_EQUILIBRIUM**.\n',
       '## What this run tested',f'- Families: {list(selected)}',f'- B0: {bb if any(not is_external(f) for f in selected.values()) else "N/A (imported geometries)"}',f'- Lambda: {ll}',
       f'- Paired reduced-filament scenarios: {len(g2)*2}',f'- G3 promoted resolutions: {args.promote_points}',
       f'- G4 coupled Euler pilot runs: {len(g4)}','\n## Gate statuses',
       *[f'- {k}: {v["status"]}' for k,v in ledger['gates'].items()],
       '\n## Physical interpretation',
       'This pipeline screens analytic torus seeds and/or user-imported, provenance-verified link geometries. It neither solves a fully deformable stationary Euler boundary-value problem nor proves nonlinear stability. The 3D Euler pilot is a finite periodic Gaussian-mollified vortex field with back-reaction, not a continuum equilibrium certificate.',
       'Averaging or long survival under a reduced filament model is not a vanishing Euler residual.',
       'Frozen-parameter convergence of the full-component Euler residual and topology-preserving material simulation are required before G2 PASS.',
       '\n## Selected seeds',
       *[f'- {x["family"]} B0={x["B0"] if x["B0"] is not None else "N/A (imported fixed geometry)"}, Lambda={x["Lambda"]:.2f}; N={x["promoted_points"]}; score={x["score"]:.6g}' for x in g3],
       '\n## Provenance',f'- E010 v0.3.6 generator SHA-256: {ledger["source_generator_sha256"]}',
       f'- E010 v0.3.6 config SHA-256: {ledger["source_config_sha256"]}',
       'Analytic torus families: E010 v0.3.6; BORRO_* custom geometries: supplied imported XYZ/TXT, original hashes retained. The custom links have UNRESOLVED Milnor mu123 and full link isotopy. No Borromean identity or stable Euler equilibrium is asserted.'
    ])+'\n',encoding='utf-8')
    make_pdf(out/'FALSIFIER_REPORT.pdf',ledger)
    manifest(out)
    archive=pack_run(out)
    print('FINAL: ',ledger['scientific_status'],'results:',out,'archive:',archive,flush=True)
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('FALSIFIER ERROR (no scientific status promoted):',repr(exc),file=sys.stderr);raise
