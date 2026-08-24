from __future__ import annotations
import argparse,csv,hashlib,json,math,os,random,re,sys,time
from pathlib import Path
from collections import Counter
import numpy as np

HERE=Path(__file__).resolve().parent
CONTRACT=json.loads((HERE/'CONTRACT.json').read_text(encoding='utf-8'))
PI=math.pi

def jdump(path,obj):
    def conv(x):
        if isinstance(x,np.ndarray): return x.tolist()
        if isinstance(x,(np.floating,np.integer)): return x.item()
        if isinstance(x,complex): return {'re':float(x.real),'im':float(x.imag)}
        if isinstance(x,Path): return str(x)
        if isinstance(x,dict): return {str(k):conv(v) for k,v in x.items()}
        if isinstance(x,(list,tuple)): return [conv(v) for v in x]
        return x
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(conv(obj),indent=2,sort_keys=True)+'\n',encoding='utf-8')

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def target_path(cli=None): return Path(cli or os.environ.get('SST_V048_DIR') or CONTRACT['target_default_path'])
def atlas_path(cli=None): return Path(cli or os.environ.get('SST_ATLAS_ROOT') or CONTRACT['atlas_default_path'])

def import_target(target):
    os.chdir(target)
    if str(target) not in sys.path: sys.path.insert(0,str(target))
    import sst_blind.multitopology as mt
    from sst_blind.io import load_xyz_text
    return mt,load_xyz_text

def preflight(target,atlas,strict_hash=False):
    req=['VERSION.json','sst_blind/multitopology.py','sst_blind/geometry.py','sst_blind/io.py','configs/panel_extended.json','configs/hr_ladder/05_R5_N720_K16_ROBUST_FULL.json']
    rows=[]
    for rel in req:
        p=target/rel; got=sha256_file(p) if p.is_file() else None; exp=CONTRACT['key_file_sha256'].get(rel)
        rows.append({'path':rel,'exists':p.is_file(),'sha256':got,'expected':exp,'hash_match':(got==exp if got and exp else None)})
    ver={}
    if (target/'VERSION.json').is_file(): ver=json.loads((target/'VERSION.json').read_text(encoding='utf-8'))
    screen=atlas/'sst_v048_outputs'/'01_screen_panel_extended_fp64'
    hand=atlas/'stability_handoff'/'raw_xyz'
    ok=(str(ver.get('version') or ver.get('package_version'))=='0.4.8' and all(r['exists'] for r in rows) and (screen/'unblind_manifest.json').is_file() and hand.is_dir())
    if strict_hash: ok=ok and all(r['hash_match'] is not False for r in rows)
    out={'target':str(target),'atlas':str(atlas),'version':ver,'rows':rows,'screen_exists':screen.is_dir(),'handoff_exists':hand.is_dir(),'strict_hash':strict_hash,'ok':ok}
    print('SST PERIOD-AWARE RPO FALSIFIER PREFLIGHT');print('='*78);print('Target:',target);print('Atlas :',atlas);print('Version:',ver.get('version') or ver.get('package_version'))
    for r in rows: print(('PASS' if r['exists'] else 'FAIL'),r['path'],('HASH_OK' if r['hash_match'] else ('HASH_DIFF' if r['hash_match'] is False else '')))
    print('Screen:', 'PASS' if out['screen_exists'] else 'FAIL');print('Handoff:', 'PASS' if out['handoff_exists'] else 'FAIL');print('='*78);print('PREFLIGHT PASS' if ok else 'PREFLIGHT FAIL')
    return out

def load_cfg(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def source_from_spectral(atlas):
    p=atlas/'sst_v048_outputs'/'02_adaptive_spectral_v048'/'SPECTRAL_EXTENSION_RESULTS.json'
    if not p.is_file(): return None
    d=json.loads(p.read_text(encoding='utf-8'))
    return {r['source']:r for r in d.get('records',[])}

def select_candidates(atlas,cfg):
    screen=atlas/cfg['runtime']['screen_output_rel']
    mani=json.loads((screen/'unblind_manifest.json').read_text(encoding='utf-8'))
    spectral=source_from_spectral(atlas)
    require_spec=bool(cfg['selection'].get('if_spectral_results_exist_require_converged_P2_PASS',True)) and spectral is not None
    excl=set(cfg['selection'].get('exclude_families',[])); incl=set(cfg['selection'].get('include_families_only',[]))
    rows=[]
    for bid,m in mani.items():
        a=json.loads((screen/'pre_unblind'/f'{bid}_analysis.json').read_text(encoding='utf-8'))
        fam=m.get('atlas_family','')
        if incl and fam not in incl: continue
        if fam in excl: continue
        if a.get('status')!=cfg['selection'].get('require_screen_status','PASS'): continue
        if not all(a.get('gates',{}).get(g) is True for g in cfg['selection'].get('require_gates',[])): continue
        sp=(spectral or {}).get(m['source'])
        spec_state='PENDING' if spectral is None else 'NOT_SELECTED'
        if sp:
            spec_state=f"{sp.get('classification')}:{sp.get('growth_verdict')}"
        if require_spec:
            if not sp or not str(sp.get('classification','')).startswith('SPECTRAL_CONVERGED') or sp.get('growth_verdict')!='PASS': continue
        p=Path(m['path'])
        if not p.is_file():
            p=atlas/'stability_handoff'/'raw_xyz'/f"{m['source']}.txt"
        if not p.is_file(): raise FileNotFoundError(p)
        rows.append({'screen_blind_id':bid,'source':m['source'],'family':fam,'value':m.get('atlas_value'),'path':str(p),'sha256':sha256_file(p),'screen_growth':a['metrics']['normalized_growth'],'screen_gates':a['gates'],'spectral_state':spec_state,'screen_arrays':str(screen/'pre_unblind'/f'{bid}_arrays.npz')})
    rows.sort(key=lambda r:(float(mani[r['screen_blind_id']].get('atlas_priority_tier','9')),r['screen_growth'],r['source']))
    rows=rows[:int(cfg['selection'].get('max_candidates',999))]
    rng=random.Random(int(cfg.get('blind_seed',58117))); order=list(range(len(rows)));rng.shuffle(order); blind={i:f'R{k+1:02d}' for k,i in enumerate(order)}
    for i,r in enumerate(rows): r['blind_id']=blind[i]
    return rows

def context_for(row,target,cfg,mt):
    pcfg=json.loads((target/cfg['runtime']['screen_config']).read_text(encoding='utf-8'))
    comps_raw,meta0=mt.load_multicurve(row['path'],'knotplot',None,n_raw=int(pcfg.get('fseries_raw_samples',8192)))
    comps,norm=mt.normalize_components(comps_raw,n_total=int(pcfg.get('panel_n_total',180)),target_total_length=2*PI)
    meta={**meta0,**norm}; core,coreinfo=mt.estimate_multicore(comps,meta,pcfg)
    mi=mt.build_generic_modes(comps,kelvin_harmonics=tuple(pcfg.get('panel_kelvin_harmonics',[2,3,4])))
    J=np.load(row['screen_arrays'])['J_total']
    if J.shape!=(len(mi['modes']),len(mi['modes'])): raise RuntimeError(f"saved J shape {J.shape} != rebuilt mode basis {len(mi['modes'])}")
    return {'pcfg':pcfg,'comps':comps,'meta':meta,'core':core,'coreinfo':coreinfo,'mi':mi,'J':J,'gamma':1.0}

def oscillatory_pairs(J,n):
    vals,vec=np.linalg.eig(np.asarray(J,float)); ids=[i for i,z in enumerate(vals) if z.imag>1e-8]
    ids=sorted(ids,key=lambda i:(vals[i].real,abs(vals[i].imag)),reverse=True)[:int(n)]
    return [{'eig_index':int(i),'re':float(vals[i].real),'im':float(vals[i].imag),'period_pred':float(2*PI/abs(vals[i].imag)),'coeff':vec[:,i]} for i in ids]

def make_initial(ctx,ep,amp,phase,mt):
    fr,fi=mt.combine_mode(ctx['mi'],ep['coeff']); field=[math.cos(phase)*a-math.sin(phase)*b for a,b in zip(fr,fi)]
    return mt.apply_multi_mode(ctx['comps'],field,float(amp))

def evolve_to_time(x0,target_time,ctx,cfg,mt,stride):
    x=[a.copy() for a in x0]; ref=[a.copy() for a in x0]; t0=0.; step0=0; hist=[]; event=None
    dtmax=float(ctx['pcfg'].get('panel_dt_max',3.5e-4)); maxsteps=int(cfg['runtime'].get('max_total_steps_per_scan',12000)); minchunk=int(cfg['runtime'].get('chunk_min_steps',160))
    while t0 < target_time and step0 < maxsteps:
        est=int(math.ceil(max(0.,target_time-t0)/max(dtmax,1e-12)*1.08)); n=max(minchunk,est); n=min(n,maxsteps-step0)
        if n<=0: break
        ev=mt.evolve_multi(x,steps=n,dt_max=dtmax,cfl=float(ctx['pcfg'].get('panel_cfl',0.1)),gamma=ctx['gamma'],core=ctx['core'],backend=cfg['runtime'].get('backend','openmp'),allow_sycl_cpu=False,mod=ctx['mod'],local_span=int(ctx['pcfg'].get('panel_local_span',5)),stride=int(stride),ref=ref,modes=ctx['mi']['modes'],core_event_factor=float(cfg['certification']['core_event_factor']))
        hh=ev['history']
        for j,z in enumerate(hh):
            if hist and j==0: continue
            q=dict(z);q['step']=int(q['step'])+step0;q['t']=float(q['t'])+t0;hist.append(q)
        actual_step=int(hh[-1]['step']) if hh else n; actual_t=float(hh[-1]['t']) if hh else 0.
        x=ev['final']; step0+=actual_step;t0+=actual_t
        if ev['core_event'] is not None:
            event=dict(ev['core_event']);event['step']=int(event['step'])+(step0-actual_step);event['t']=float(event['t'])+(t0-actual_t);break
        if actual_t<=0: break
    return {'final':x,'history':hist,'core_event':event,'achieved_time':t0,'total_steps':step0,'target_time':target_time,'horizon_reached':t0>=0.98*target_time}

def return_metrics(hist,Tpred,cert):
    ex=float(cert['excursion_min']); first=next((z for z in hist if float(z['recurrence'])>=ex),None)
    if first is None: return {'excursion_reached':False,'best_recurrence':float('inf'),'best_step':None,'best_time':None,'return_ratio':float('inf'),'peak':0.,'direct_pass':False}
    start=max(float(cert.get('return_window_start_periods',0.5))*Tpred,float(first['t']))
    elig=[z for z in hist if float(z['t'])>=start]
    if not elig: return {'excursion_reached':True,'best_recurrence':float('inf'),'best_step':None,'best_time':None,'return_ratio':float('inf'),'peak':max(float(z['recurrence']) for z in hist),'direct_pass':False}
    cand=min(elig,key=lambda z:float(z['recurrence'])); pre=[z for z in hist if float(z['t'])<=float(cand['t'])]; peak=max(float(z['recurrence']) for z in pre); ratio=float(cand['recurrence'])/max(peak,1e-12)
    ok=float(cand['recurrence'])<=float(cert['recurrence_max']) and ratio<=float(cert['return_ratio_max'])
    return {'excursion_reached':True,'best_recurrence':float(cand['recurrence']),'best_step':int(cand['step']),'best_time':float(cand['t']),'return_ratio':float(ratio),'peak':float(peak),'direct_pass':bool(ok)}

def scan_cell(row,ctx,ep,rank,amp,phase,horizon_periods,max_time,stride,cfg,mt):
    T=float(ep['period_pred']); target=min(float(max_time),float(horizon_periods)*T); capped=target+1e-12 < float(horizon_periods)*T
    x0=make_initial(ctx,ep,amp,phase,mt); ev=evolve_to_time(x0,target,ctx,cfg,mt,stride); rm=return_metrics(ev['history'],T,cfg['certification']); rm['direct_pass']=bool(rm['direct_pass'] and ev['core_event'] is None)
    return {'blind_id':row['blind_id'],'eigen_rank':rank,'eig_index':ep['eig_index'],'eigenvalue':{'re':ep['re'],'im':ep['im']},'period_pred':T,'amp':float(amp),'phase':float(phase),'horizon_periods_requested':float(horizon_periods),'target_time':target,'horizon_capped':capped,'horizon_reached':ev['horizon_reached'],'achieved_time':ev['achieved_time'],'total_steps':ev['total_steps'],'core_event':ev['core_event'],**rm}

def score_cell(r):
    if r.get('core_event') is not None: return (9,1e9,1e9)
    return (0 if r.get('direct_pass') else 1,float(r.get('best_recurrence',1e9)),float(r.get('return_ratio',1e9)))

def run_scan(rows,target,cfg,out,stage):
    mt,_=import_target(target); mod=mt.load_native(); cache=out/'cache'/stage;cache.mkdir(parents=True,exist_ok=True); summaries=[]
    for pos,row in enumerate(sorted(rows,key=lambda r:r['blind_id']),1):
        print(f"[{stage}] [{pos}/{len(rows)}] {row['blind_id']} START",flush=True);ctx=context_for(row,target,cfg,mt);ctx['mod']=mod; eps=oscillatory_pairs(ctx['J'],cfg['coarse' if stage=='coarse' else 'coarse']['oscillatory_eigenpairs'])
        cells=[]
        if stage=='coarse':
            specs=[]
            for er,ep in enumerate(eps):
                for amp in cfg['coarse']['amplitudes']:
                    for p in range(int(cfg['coarse']['phase_count'])): specs.append((er,ep,float(amp),2*PI*p/int(cfg['coarse']['phase_count'])))
            sect=cfg['coarse']
        else:
            coarse=json.loads((out/'pre_unblind'/row['blind_id']/'coarse_summary.json').read_text(encoding='utf-8'))['cells']
            seeds=sorted(coarse,key=score_cell)[:int(cfg['refine']['top_seeds_per_candidate'])]
            specs=[];seen=set(); sect=cfg['refine']; grid=int(sect['phase_grid_count']); hw=int(sect['phase_halfwidth_steps'])
            for s in seeds:
                er=int(s['eigen_rank']);ep=eps[er]
                center=float(s['phase'])
                for amp in sect['amplitudes']:
                    for off in range(-hw,hw+1):
                        ph=(center+off*2*PI/grid)%(2*PI); key=(er,round(float(amp),12),round(ph,12))
                        if key not in seen: seen.add(key);specs.append((er,ep,float(amp),ph))
        for k,(er,ep,amp,ph) in enumerate(specs,1):
            key=f"{row['blind_id']}_e{er}_a{amp:.8g}_p{ph:.10f}".replace('.','p').replace('-','m');fp=cache/f'{key}.json'
            if fp.is_file(): rec=json.loads(fp.read_text(encoding='utf-8'))
            else:
                rec=scan_cell(row,ctx,ep,er,amp,ph,sect['horizon_periods'],sect['max_physical_time'],sect['history_stride'],cfg,mt);jdump(fp,rec)
            cells.append(rec)
            if k%max(1,len(specs)//10)==0 or rec.get('direct_pass'): print(f"  {k}/{len(specs)} best={rec['best_recurrence']:.5g} ratio={rec['return_ratio']:.4g} pass={rec['direct_pass']}",flush=True)
        summ={'blind_id':row['blind_id'],'stage':stage,'cells':sorted(cells,key=score_cell),'direct_pass_count':sum(bool(x.get('direct_pass')) for x in cells),'best':min(cells,key=score_cell) if cells else None}
        pd=out/'pre_unblind'/row['blind_id'];pd.mkdir(parents=True,exist_ok=True);jdump(pd/f'{stage}_summary.json',summ);summaries.append(summ);print(f"[{stage}] {row['blind_id']} DONE direct_pass={summ['direct_pass_count']}",flush=True)
    return summaries

def split_steps(total,S):
    base=total//S; rem=total%S; return [base+(1 if i<rem else 0) for i in range(S)]

def apply_correction(node,modes,idx,coeff,mt):
    out=[]
    for ci,x in enumerate(node):
        d=np.zeros_like(x)
        for a,k in zip(coeff,idx): d+=float(a)*modes[k][ci]
        out.append(x+d)
    return mt._rescale_total(out)

def evolve_steps(x,steps,ctx,cfg,mt,stride=None):
    return mt.evolve_multi(x,steps=int(steps),dt_max=float(ctx['pcfg'].get('panel_dt_max',3.5e-4)),cfl=float(ctx['pcfg'].get('panel_cfl',0.1)),gamma=ctx['gamma'],core=ctx['core'],backend=cfg['runtime'].get('backend','openmp'),allow_sycl_cpu=False,mod=ctx['mod'],local_span=int(ctx['pcfg'].get('panel_local_span',5)),stride=int(stride or max(1,steps)),ref=x,modes=None,core_event_factor=float(cfg['certification']['core_event_factor']))

def shooting_residual(nodes,segsteps,C,idx,ctx,cfg,mt):
    corrected=[apply_correction(n,ctx['mi']['modes'],idx,C[j],mt) for j,n in enumerate(nodes)]; res=[];full=[];core=False
    for j,x in enumerate(corrected):
        ev=evolve_steps(x,segsteps[j],ctx,cfg,mt);target=corrected[(j+1)%len(corrected)]
        if ev['core_event'] is not None: core=True
        al=mt.align_multi(target,ev['final']);diff=mt._shape_project(target,[a-b for a,b in zip(al,target)])
        res.extend([mt._flat_inner(ctx['mi']['modes'][k],diff) for k in idx]);full.append(mt.recurrence(target,ev['final']))
    r=np.asarray(res,float)
    if core: r=r+np.sign(r+1e-30)*1.0
    return r,full,core,corrected

def seed_initial_and_ep(ctx,cell,mt,cfg):
    eps=oscillatory_pairs(ctx['J'],cfg['coarse']['oscillatory_eigenpairs']);ep=eps[int(cell['eigen_rank'])];return make_initial(ctx,ep,cell['amp'],cell['phase'],mt),ep

def shooting_one(row,ctx,cell,cfg,mt):
    x0,ep=seed_initial_and_ep(ctx,cell,mt,cfg); beststep=int(cell['best_step']); sh=cfg['shooting'];
    # Discrete period refinement before multiple shooting.
    grid=[]
    for sc in sh['period_scale_grid']:
        T=max(3,int(round(beststep*float(sc))));ev=evolve_steps(x0,T,ctx,cfg,mt,stride=max(1,T//80));rm=return_metrics(ev['history'],ep['period_pred'],cfg['certification']);grid.append({'scale':sc,'steps':T,'closure':mt.recurrence(x0,ev['final']),'return':rm,'core_event':ev['core_event']})
    viable=[g for g in grid if g['core_event'] is None];g0=min(viable or grid,key=lambda g:(float(g['closure']),float(g['return'].get('best_recurrence',1e9))));T=int(g0['steps']);S=int(sh['segments']);seg=split_steps(T,S)
    nodes=[x0];x=x0
    for j in range(S-1): ev=evolve_steps(x,seg[j],ctx,cfg,mt);x=ev['final'];nodes.append(x)
    eps_all=oscillatory_pairs(ctx['J'],cfg['coarse']['oscillatory_eigenpairs']); coeff=eps_all[int(cell['eigen_rank'])]['coeff'];idx=list(np.argsort(np.abs(coeff))[::-1][:int(sh['mode_count'])]);C=np.zeros((S,len(idx)));ledger=[]
    r,full,core,corr=shooting_residual(nodes,seg,C,idx,ctx,cfg,mt);norm=float(np.linalg.norm(r)/math.sqrt(max(1,len(r))))
    for it in range(int(sh['max_iterations'])):
        ledger.append({'iteration':it,'residual_rms':norm,'segment_full_recurrence':full,'core_event':core})
        if norm<=float(sh['continuity_tol']) or core: break
        m=C.size; J=np.zeros((len(r),m));fd=float(sh['fd_eps'])
        flat=C.reshape(-1)
        for k in range(m):
            q=flat.copy();q[k]+=fd;rp,_,_,_=shooting_residual(nodes,seg,q.reshape(C.shape),idx,ctx,cfg,mt);J[:,k]=(rp-r)/fd
        reg=float(sh.get('regularization',0.0)); A=np.vstack([J,math.sqrt(reg)*np.eye(m)]) if reg>0 else J; b=np.r_[-r,np.zeros(m)] if reg>0 else -r
        dx,*_=np.linalg.lstsq(A,b,rcond=None);mx=float(sh['max_coeff_step']);dx=np.clip(dx,-mx,mx);damp=float(sh['damping']);accepted=False
        for fac in (damp,damp*0.5,damp*0.25):
            Cn=(flat+fac*dx).reshape(C.shape);rn,fn,cn,corrn=shooting_residual(nodes,seg,Cn,idx,ctx,cfg,mt);nn=float(np.linalg.norm(rn)/math.sqrt(max(1,len(rn))))
            if nn<norm: C,r,full,core,corr,norm=Cn,rn,fn,cn,corrn,nn;accepted=True;break
        if not accepted: break
    ledger.append({'iteration':'final','residual_rms':norm,'segment_full_recurrence':full,'core_event':core})
    xshoot=corr[0]; ev=mt.evolve_multi(xshoot,steps=T,dt_max=float(ctx['pcfg'].get('panel_dt_max',3.5e-4)),cfl=float(ctx['pcfg'].get('panel_cfl',0.1)),gamma=ctx['gamma'],core=ctx['core'],backend=cfg['runtime'].get('backend','openmp'),allow_sycl_cpu=False,mod=ctx['mod'],local_span=int(ctx['pcfg'].get('panel_local_span',5)),stride=max(1,T//160),ref=xshoot,modes=ctx['mi']['modes'],core_event_factor=float(cfg['certification']['core_event_factor']))
    rm=return_metrics(ev['history'],ep['period_pred'],cfg['certification']); closure=float(mt.recurrence(xshoot,ev['final'])); passed=bool(norm<=float(sh['continuity_tol']) and rm['direct_pass'] and ev['core_event'] is None)
    return {'seed_cell':cell,'period_grid':grid,'period_steps':T,'segment_steps':seg,'mode_indices':idx,'mode_names':[ctx['mi']['names'][k] for k in idx],'coefficients':C,'ledger':ledger,'continuity_residual_rms':norm,'closure_recurrence_at_T':closure,'return_metrics':rm,'core_event':ev['core_event'],'shooting_pass':passed,'period_time':float(ev['history'][-1]['t']) if ev['history'] else None,'initial_geometry':xshoot,'final_geometry':ev['final']}

def write_xyz(p,a):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);x=np.asarray(a,float);p.write_text(''.join(f'{r[0]:.17g} {r[1]:.17g} {r[2]:.17g}\n' for r in x),encoding='utf-8')

def run_shoot(rows,target,cfg,out):
    mt,_=import_target(target);mod=mt.load_native();outs=[]
    for row in sorted(rows,key=lambda r:r['blind_id']):
        ctx=context_for(row,target,cfg,mt);ctx['mod']=mod;pd=out/'pre_unblind'/row['blind_id'];refp=pd/'refine_summary.json';cp=pd/'coarse_summary.json';src=json.loads((refp if refp.is_file() else cp).read_text(encoding='utf-8')); cells=src['cells']; sh=cfg['shooting'];eligible=[c for c in cells if c.get('best_step') is not None and c.get('core_event') is None and (c.get('direct_pass') or (float(c.get('best_recurrence',1e9))<=float(sh['seed_recurrence_max']) and float(c.get('return_ratio',1e9))<=float(sh['seed_return_ratio_max'])))]
        eligible=sorted(eligible,key=score_cell)[:int(sh['top_seeds_per_candidate'])]; trials=[]
        print(f"[shoot] {row['blind_id']} seeds={len(eligible)}",flush=True)
        for i,c in enumerate(eligible):
            fp=pd/f'shooting_trial_{i:02d}.json'
            if fp.is_file(): q=json.loads(fp.read_text(encoding='utf-8'));q['_geometry_path']=q.get('initial_geometry_path')
            else:
                q=shooting_one(row,ctx,c,cfg,mt);gp=pd/f'shooting_trial_{i:02d}_initial.xyz';write_xyz(gp,q.pop('initial_geometry')[0]);q.pop('final_geometry',None);q['initial_geometry_path']=str(gp);jdump(fp,q)
            trials.append(q)
        best=min(trials,key=lambda q:(0 if q.get('shooting_pass') else 1,float(q.get('continuity_residual_rms',1e9)),float(q.get('closure_recurrence_at_T',1e9)))) if trials else None
        summ={'blind_id':row['blind_id'],'trials':trials,'best':best,'shooting_pass':bool(best and best.get('shooting_pass'))};jdump(pd/'shooting_summary.json',summ);outs.append(summ);print(f"[shoot] {row['blind_id']} PASS={summ['shooting_pass']}",flush=True)
    return outs

def run_floquet(rows,target,cfg,out):
    mt,load_xyz=import_target(target);mod=mt.load_native();fcfg=json.loads((target/cfg['runtime']['floquet_config']).read_text(encoding='utf-8')); results=[]
    for row in sorted(rows,key=lambda r:r['blind_id']):
        pd=out/'pre_unblind'/row['blind_id'];sp=pd/'shooting_summary.json'
        if not sp.is_file(): continue
        sh=json.loads(sp.read_text(encoding='utf-8'));best=sh.get('best')
        if not best or not best.get('shooting_pass'):jdump(pd/'floquet_summary.json',{'blind_id':row['blind_id'],'evaluated':False,'reason':'no_shooting_rpo_pass'});continue
        ctx=context_for(row,target,cfg,mt);ctx['mod']=mod;x0=[load_xyz(best['initial_geometry_path'])];rpo={'candidate':{'initial_geometry':x0,'best_step':int(best['period_steps']),'best_time':best.get('period_time'),'best_recurrence':best.get('return_metrics',{}).get('best_recurrence')}}
        epsvals=[float(e) for e in cfg['floquet'].get('eps_values',[fcfg.get('panel_floquet_eps',0.00075)])];runs=[]
        for e in epsvals:
            qcfg=dict(fcfg);qcfg['panel_floquet_eps']=e;fl=mt.floquet_multi(ctx['comps'],ctx['mi'],rpo,cfg=qcfg,gamma=ctx['gamma'],core=ctx['core'],backend=cfg['runtime'].get('backend','openmp'),allow_sycl_cpu=False,mod=mod);runs.append({'eps':e,'floquet':fl})
        cert=float(cfg['floquet'].get('certification_eps',fcfg.get('panel_floquet_eps',0.00075)));central=min(runs,key=lambda z:abs(z['eps']-cert));fl=central['floquet'];bounded=bool(fl.get('valid') and float(fl.get('spectral_radius_excluding_neutral',float('inf')))<=float(cfg['certification']['floquet_spectral_radius_max']))
        q={'blind_id':row['blind_id'],'evaluated':True,'certification_eps':central['eps'],'runs':runs,'floquet_bounded':bounded};jdump(pd/'floquet_summary.json',q);results.append(q);print(f"[floquet] {row['blind_id']} valid={fl.get('valid')} rho_non={fl.get('spectral_radius_excluding_neutral')} bounded={bounded}",flush=True)
    return results

def final_report(rows,cfg,out):
    unblind={r['blind_id']:r for r in rows};jdump(out/'unblind_manifest.json',unblind);lines=['# Adaptive Period-Aware RPO + Multiple-Shooting + Floquet Report','',f"Campaign: **{cfg['campaign_name']}**",'', '> RPO/Floquet is an additional dynamical-coherence gate. It does not replace the N=720 adaptive spectral stability ladder.','', '| source | family | screen growth | spectral | direct RPO | shooting RPO | Floquet | class |','|---|---|---:|---|---:|---:|---:|---|'];csvrows=[]
    for r in sorted(rows,key=lambda z:z['source']):
        pd=out/'pre_unblind'/r['blind_id']; coarse=json.loads((pd/'coarse_summary.json').read_text(encoding='utf-8')) if (pd/'coarse_summary.json').is_file() else {}; refine=json.loads((pd/'refine_summary.json').read_text(encoding='utf-8')) if (pd/'refine_summary.json').is_file() else {}; shoot=json.loads((pd/'shooting_summary.json').read_text(encoding='utf-8')) if (pd/'shooting_summary.json').is_file() else {}; floq=json.loads((pd/'floquet_summary.json').read_text(encoding='utf-8')) if (pd/'floquet_summary.json').is_file() else {}
        direct=bool((refine or coarse).get('direct_pass_count',0)>0);spass=bool(shoot.get('shooting_pass'));fb=bool(floq.get('floquet_bounded'));spec=r['spectral_state']
        if fb and spec!='PENDING' and 'SPECTRAL_CONVERGED' in spec and spec.endswith(':PASS'): cls='RPO_FLOQUET_BOUNDED_AND_SPECTRAL_PASS'
        elif fb: cls='RPO_FLOQUET_BOUNDED_SPECTRAL_PENDING'
        elif spass: cls='RPO_SHOOTING_PASS_FLOQUET_NOT_BOUNDED_OR_NOT_VALID'
        elif direct: cls='DIRECT_RECURRENCE_PASS_NOT_SHOOTING_CERTIFIED'
        else: cls='NO_CERTIFIED_RPO'
        best=(refine or coarse).get('best') or {}; sb=shoot.get('best') or {};rho=None
        if floq.get('evaluated'):
            ce=min(floq['runs'],key=lambda z:abs(float(z['eps'])-float(floq['certification_eps'])));rho=ce['floquet'].get('spectral_radius_excluding_neutral')
        lines.append(f"| {r['source']} | {r['family']} | {r['screen_growth']:.6g} | {spec} | {'YES' if direct else 'NO'} | {'YES' if spass else 'NO'} | {'PASS' if fb else ('FAIL' if floq.get('evaluated') else 'N/A')} | **{cls}** |")
        csvrows.append({'source':r['source'],'family':r['family'],'value':r['value'],'screen_growth':r['screen_growth'],'spectral_state':spec,'direct_rpo_pass':direct,'shooting_rpo_pass':spass,'best_scan_recurrence':best.get('best_recurrence'),'best_scan_return_ratio':best.get('return_ratio'),'shooting_continuity_rms':sb.get('continuity_residual_rms'),'shooting_closure_at_T':sb.get('closure_recurrence_at_T'),'floquet_bounded':fb,'floquet_rho_non':rho,'classification':cls})
    lines += ['','## Fixed certification gates','',f"- excursion >= {cfg['certification']['excursion_min']}",f"- recurrence <= {cfg['certification']['recurrence_max']}",f"- return/peak <= {cfg['certification']['return_ratio_max']}",f"- Floquet rho(non-neutral) <= {cfg['certification']['floquet_spectral_radius_max']}",'','## Interpretation','', '- `NO_CERTIFIED_RPO` does **not** prove that no RPO exists; it means none was certified inside the preregistered eigenmode/amplitude/phase/horizon domain.', '- `SPECTRAL_PENDING` means an RPO result may be interesting dynamical evidence but is not yet a complete SST stability certification.', '- The period horizon was measured from `Im(lambda)` and never introduced as a free restoring frequency.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if csvrows:
        with (out/'RPO_FLOQUET_MATRIX.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(csvrows[0].keys()));w.writeheader();w.writerows(csvrows)
    print((out/'REPORT.md').read_text(encoding='utf-8'))

def campaign(config,outdir,target,atlas,stages):
    cfg=load_cfg(config);out=Path(outdir).resolve();out.mkdir(parents=True,exist_ok=True);pre=preflight(target,atlas,False);jdump(out/'PREFLIGHT.json',pre)
    if not pre['ok']: return 2
    prereg=out/'00_PREREGISTERED_CONFIG.json'
    if prereg.is_file() and json.loads(prereg.read_text(encoding='utf-8'))!=cfg: raise RuntimeError('Refusing resume: preregistered config differs')
    jdump(prereg,cfg);rows=select_candidates(atlas,cfg);jdump(out/'SELECTION_BLINDED.json',[{k:v for k,v in r.items() if k not in ('source','family','value','path')} for r in rows]);priv=out/'private';priv.mkdir(exist_ok=True);jdump(priv/'selection_unblind_private.json',rows)
    print(f"Selected {len(rows)} candidates; source names withheld during dynamic stages.")
    if not rows:return 3
    if 'coarse' in stages:run_scan(rows,target,cfg,out,'coarse')
    if 'refine' in stages:run_scan(rows,target,cfg,out,'refine')
    if 'shoot' in stages and cfg['shooting'].get('enabled',True):run_shoot(rows,target,cfg,out)
    if 'floquet' in stages and cfg['floquet'].get('enabled',True):run_floquet(rows,target,cfg,out)
    if 'report' in stages:final_report(rows,cfg,out)
    return 0

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--out-dir',required=True);ap.add_argument('--target');ap.add_argument('--atlas');ap.add_argument('--stages',default='coarse,refine,shoot,floquet,report');ap.add_argument('--preflight-only',action='store_true');a=ap.parse_args();target=target_path(a.target);atlas=atlas_path(a.atlas)
    if a.preflight_only:
        q=preflight(target,atlas,False);return 0 if q['ok'] else 2
    return campaign(a.config,a.out_dir,target,atlas,[s.strip() for s in a.stages.split(',') if s.strip()])
if __name__=='__main__':raise SystemExit(main())
