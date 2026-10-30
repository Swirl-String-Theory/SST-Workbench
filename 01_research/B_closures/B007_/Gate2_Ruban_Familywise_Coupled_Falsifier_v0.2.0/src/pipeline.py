"""Gate2 Ruban Familywise Coupled Falsifier v0.2.0.

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

VERSION='v0.2.0';PREFIX='Gate2_Ruban_Familywise_Coupled_Falsifier'
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
    if args.topology is not None:
        if args.family!='T_2_3':raise ValueError('Use --topology without --family; selectors are exclusive')
        found={name:meta for name,meta in fs.items() if meta.get('topology_id')==args.topology}
        if not found:raise ValueError('Topology not found: '+args.topology)
        return found
    if args.kind is not None:
        if args.family!='T_2_3':raise ValueError('Use --kind without --family; selectors are exclusive')
        return {name:meta for name,meta in fs.items() if (math.gcd(meta['p'],meta['q'])>1)==(args.kind=='links')}
    if args.family.lower()=='all':return fs
    a=[x.strip() for x in args.family.split(',') if x.strip()]
    for f in a:
        if f not in fs:raise ValueError(f'Unknown {f}. Select from --list-families.')
    return {f:fs[f] for f in a}

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

def stage1(selected,bb,out,args,cfg):
    rows=[]
    for name,f in selected.items():
        for b in bb:
            part=generate(f['p'],f['q'],b,args.seed_points,False,cfg)
            g=metrics(part)
            rows.append({'family':name,'topology':f.get('topology_id'),'B0':b,'p':f['p'],'q':f['q'],
             'kind':'knot' if len(part)==1 else 'link','components':len(part),
             'source':'ANALYTIC_E010_V036','seed_geometry_sha256':hashlib.sha256(b''.join(p.tobytes() for p in part)).hexdigest(),
             **g,'gate':'SCREENED_NOT_FINITE_CORE_CERTIFIED'})
    save_csv(out/'G1_GEOMETRY.csv',rows)
    stat={'status':'PASS_ANALYTIC_GEOMETRY_SCREEN_ONLY','count':len(rows),'families':len(selected),
          'unproven':['Exact reach','Continuous polygon segment nonintersection','Finite-core vortex equilibrium']}
    save_json(out/'G1_GATE.json',stat)
    return rows,stat

def stage2(selected,bb,ll,out,args,cfg):
    rows=[];allcount=len(selected)*len(bb)*len(ll)
    count=0
    for name,f in selected.items():
        for b in bb:
            o=generate(f['p'],f['q'],b,args.seed_points,False,cfg)
            p=generate(f['p'],f['q'],b,args.seed_points,True,cfg)
            for lam in ll:
                r=run_pair(o,p,lam,args.screen_points,args.screen_steps,args.final_time)
                seg_over_xi=max(float(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1).sum()/args.screen_points) for c in o)/math.exp(-lam)
                dt_over_xi2=(args.final_time/args.screen_steps)*math.exp(2*lam)
                spatial_eligible=seg_over_xi<=args.max_segment_over_core
                rows.append({'family':name,'topology':f.get('topology_id'),'B0':b,'Lambda':lam,
                   'component_count':len(o),'xi_over_R0':math.exp(-lam),
                   'segment_over_xi':seg_over_xi,
                   'dt_over_xi2':dt_over_xi2,
                   'spatial_preflight_pass':spatial_eligible,
                   'thin_tube_screen_warning': 'B0_OVER_XI_LT_4' if b*math.exp(lam)<4 else 'UNQUALIFIED_AS_THIN_CORE',
                   'score':exploratory_score(r),**r,
                   'status':'REDUCED_FILAMENT_EXPLORATORY_NOT_3D_EULER'})
                count+=1
            if count%max(1,len(bb)*len(ll))==0:
                print(f'  G2: {count}/{allcount} nominal+perturbed matched scenarios, family={name}',flush=True)
    save_csv(out/'G2_FILAMENT_SCAN.csv',rows)
    eligible_count=sum(1 for r in rows if r['spatial_preflight_pass'])
    stat={'status':'PASS_REDUCED_SCREEN_EXECUTED_RESOLUTION_LIMITED','count':len(rows)*2,
          'spatial_preflight_eligible_pairs':eligible_count,'spatial_preflight_ineligible_pairs':len(rows)-eligible_count,
          'max_segment_over_core_heuristic':args.max_segment_over_core,
          'paired_cases':len(rows),'final_time_star':args.final_time,'filament_points':args.screen_points,
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
        best=min(qualified if qualified else local,key=lambda r:(r['score'],r['B0'],r['Lambda']))
        b=best['B0'];lam=best['Lambda'];res={}
        for n in ns:
            o=generate(f['p'],f['q'],b,n,False,cfg)
            p=generate(f['p'],f['q'],b,n,True,cfg)
            test=run_pair(o,p,lam,n,args.screen_steps,args.final_time)
            res[str(n)]={'score':exploratory_score(test),'measurements':test}
        last=res[str(ns[-1])]['score'];previous=res[str(ns[-2])]['score'] if len(ns)>1 else last
        shift=abs(last-previous)
        row={'family':name,'topology':f.get('topology_id'),'p':f['p'],'q':f['q'],
         'B0':b,'Lambda':lam,'score':float(best['score']),
         'selected_from_spatial_eligible_candidates':bool(qualified),
         'segment_over_xi_at_screening':best['segment_over_xi'],
         'dt_over_xi2_at_screening':best['dt_over_xi2'],
         'B_at_scanned_edge':b in (bb[0],bb[-1]),'Lambda_at_scanned_edge':lam in (min(ll),max(ll)),
         'score_last_refinement':last,'holdout_difference':shift,
         'holdout_relative_change':shift/max(abs(last),1e-30),
         'holdout_points':ns,'promoted_points':promote,
         'status':'PROVISIONAL_SPATIALLY_UNRESOLVED' if not qualified else 'PROVISIONAL_AWAITING_INDEPENDENT_CONVERGENCE'}
        winners.append(row)
        hold.append({'family':name,'B0':b,'Lambda':lam,'resolution_evidence':res,'status':row['status']})
        for n in promote:
            o=generate(f['p'],f['q'],b,n,False,cfg)
            p=generate(f['p'],f['q'],b,n,True,cfg)
            name_id=f'{name}_B{round(b*10000):04d}_N{n}'
            exports += [*export(o,out,name_id,'nominal'),*export(p,out,name_id,'perturbed')]
    winners.sort(key=lambda r:(r['score'],r['holdout_difference']))
    for i,r in enumerate(winners,1):r['provisional_rank']=i
    save_csv(out/'G3_FAMILY_WINNERS.csv',winners)
    save_json(out/'G3_HOLDOUT.json',hold)
    save_json(out/'G3_PROMOTED_FILES.json',exports)
    stat={'status':'RANKING_PROVISIONAL_NUMERICAL_CONVERGENCE_UNRESOLVED','count':len(winners),
          'spatially_ineligible_family_count':sum(not w['selected_from_spatial_eligible_candidates'] for w in winners),
          'promoted_xyz_files':len(exports),'resolution_checks':ns,'promoted_points':promote,
          'note':'Promoted high-resolution geometry generated internally from frozen analytic E010 v0.3.6 formula. Promoted N does not imply N-point dynamics tested.',
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
        parts=generate(fam['p'],fam['q'],b,args.euler_curve_points,False,cfg)
        for style in bgstyles:
            r=evaluate(parts,style,args.euler_grid,args.euler_holdout,args.euler_sigma,args.euler_box,args.gamma_background,args.euler_dt)
            r.update({'family':winner['family'],'B0':b,'Lambda_selected_for_filament_only':winner['Lambda'],
                  'source_geometry_points_euler':args.euler_curve_points,
                  'independent_numerical_backend':False,'full_field_root_finder':False})
            print(f"  G4: {winner['family']} B={b:.4f} {style} -> {r['status']}; holdout R*={r['holdout']['max_Rstar']:.4g}",flush=True)
            records.append(r)
    save_json(out/'G4_COUPLED.json',records)
    save_csv(out/'G4_COUPLED.csv',[{'family':r['family'],'B0':r['B0'],'background':r['background'],
       'train_Rstar':r['train']['max_Rstar'],'holdout_Rstar':r['holdout']['max_Rstar'],
       'filter_train':r['projection_change_train_max'],
       'filter_holdout':r['projection_change_holdout_max'],
       'separation_lower':r['geometry']['clearance_lower_bound'],'status':r['status']} for r in records])
    stat={'status':'G2_UNRESOLVED_NO_CERTIFIED_EQUILIBRIUM','count':len(records),
     'blocked_count':sum(r['status'].startswith('BLOCKED') for r in records),
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
    p.add_argument('--kind',choices=['knots','links'],default=None,help='Select only the 24 knots or only 6 links')
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
    if args.list_families:
        for name,d in ff.items():print(f"{name:9s} {d.get('topology_id') or 'unspecified':12s} {'LINK' if math.gcd(d['p'],d['q'])>1 else 'KNOT'} components={math.gcd(d['p'],d['q'])}")
        return 0
    if args.screen_points<64 or args.seed_points<64 or args.screen_steps<1 or args.final_time<=0:raise ValueError('Invalid screening resolution/time')
    if args.euler_grid<12 or args.euler_holdout<=args.euler_grid:raise ValueError('Need grid >=12 and finer holdout')
    if args.euler_sigma<=0 or args.euler_box<=0:raise ValueError('Invalid Euler box/core width')
    selected=selected_families(args,cfg);bb,ll=values(args,cfg)
    scenarios=len(selected)*len(bb)*len(ll)*2
    print(f'PLAN: {len(selected)} families, {len(bb)} B0, {len(ll)} Lambda, {scenarios} nominal/perturbed reduced filament runs; per-family promoted N={args.promote_points}',flush=True)
    if args.dry_run:return 0
    timestamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    sign=hashlib.sha256(json.dumps(vars(args),sort_keys=True).encode()).hexdigest()[:8]
    selector=(('topology_'+args.topology) if args.topology else ('kind_'+args.kind if args.kind else args.family))
    run_id=args.run_id or f'{selector.replace(",","-")}_{args.profile}_{timestamp}_{sign}'
    if '/' in run_id or '\\' in run_id or '..' in run_id:raise ValueError('Unsafe run ID')
    out=OUTBASE/'runs'/run_id
    if out.exists():raise FileExistsError('No overwrite permitted: '+str(out))
    out.mkdir(parents=True)
    ledger={'schema':'GATE2-RUBAN-FAMILYWISE-V020','version':VERSION,'run_id':run_id,'family':list(selected),
       'profile':args.profile,'B0_values':bb,'Lambda_values':ll,'screen_points':args.screen_points,
       'promotion_points':args.promote_points,'source_generator_sha256':fingerprint(GENER),
       'source_config_sha256':fingerprint(CONFIG),'command_arguments':vars(args),
       'gates':{},'scientific_status':'G2_UNRESOLVED_NO_CERTIFIED_EQUILIBRIUM','winners':[]}
    ledger['runtime']={'python':sys.version.split()[0],'platform':platform.platform(),'numpy':np.__version__}
    ledger['source_file_sha256']={p.relative_to(ROOT).as_posix():fingerprint(p) for p in sorted((ROOT/'src').rglob('*.py'))}
    ledger['source_file_sha256']['configs/E010_ruban_family_v036.json']=fingerprint(CONFIG)
    save_json(out/'RUN_CONFIG.json',ledger)
    print('G1: independent analytic construction and finite polygon checks',flush=True)
    g1,s1=stage1(selected,bb,out,args,cfg);ledger['gates']['G1']=s1
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
       '## What this run tested',f'- Families: {list(selected)}',f'- B0: {bb}',f'- Lambda: {ll}',
       f'- Paired reduced-filament scenarios: {len(g2)*2}',f'- G3 promoted resolutions: {args.promote_points}',
       f'- G4 coupled Euler pilot runs: {len(g4)}','\n## Gate statuses',
       *[f'- {k}: {v["status"]}' for k,v in ledger['gates'].items()],
       '\n## Physical interpretation',
       'This pipeline screens analytic torus seed families. It neither solves a fully deformable stationary Euler boundary-value problem nor proves nonlinear stability. The 3D Euler pilot is a finite periodic Gaussian-mollified vortex field with back-reaction, not a continuum equilibrium certificate.',
       'Averaging or long survival under a reduced filament model is not a vanishing Euler residual.',
       'Frozen-parameter convergence of the full-component Euler residual and topology-preserving material simulation are required before G2 PASS.',
       '\n## Selected seeds',
       *[f'- {x["family"]} B0={x["B0"]:.5f}, Lambda={x["Lambda"]:.2f}; N={x["promoted_points"]}; score={x["score"]:.6g}' for x in g3],
       '\n## Provenance',f'- E010 v0.3.6 generator SHA-256: {ledger["source_generator_sha256"]}',
       f'- E010 v0.3.6 config SHA-256: {ledger["source_config_sha256"]}',
       'KnotPlot labels for six links are metadata only; corresponding curves were analytically generated, not imported.'
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
