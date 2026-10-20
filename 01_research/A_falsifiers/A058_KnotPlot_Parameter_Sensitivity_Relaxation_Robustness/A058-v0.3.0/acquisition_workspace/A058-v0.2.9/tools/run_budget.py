"""Budgeted A058 launcher. Invoke through run_all.cmd BASIC|2048|32768.

Framework v1.0.8 is called only *after* acquisition so its archived
BLIND ZIP/PDF contain the scientific run, not empty pre-campaign results.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,json,math,os,shutil,subprocess,sys,datetime
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiment.metrics import read_xyz,curve_metrics,shape_distance
from tools.budget_acquisition import run_budget,loadj,savej

def _cmd(path:Path):
    print('RUN',path.name,flush=True)
    if os.name!='nt':raise RuntimeError('Native KnotPlot campaign requires Windows cmd.exe')
    return subprocess.call(['cmd.exe','/c',str(path)],cwd=ROOT)

def _verify_calibration():
    calp=ROOT/'private/install_test_runtime/defaults.json'
    seed=ROOT/'private/install_test_runtime/trefoil_install_test.txt'
    if not calp.is_file() or not seed.is_file():return False
    cal=loadj(calp)
    return bool(cal.get('pass') and cal.get('setter_verification') and cal.get('safe_start') and
        hashlib.sha256(seed.read_bytes()).hexdigest()==cal.get('shared_seed_sha256'))

def _ensure_calibrated():
    if _verify_calibration():
        print('INSTALL: reusing verified installation and immutable shared seed',flush=True)
        return
    if _cmd(ROOT/'run_install.cmd')!=0:raise RuntimeError('run_install.cmd failed; campaign not started')
    if not _verify_calibration():raise RuntimeError('calibration/seed integrity check failed after installation')

def _ensure_design():
    path=ROOT/'campaign/manifest_pilot.json'
    if path.is_file():
        obj=loadj(path)
        if obj.get('condition_count')==271 and obj.get('shared_seed_sha256')==loadj(ROOT/'private/install_test_runtime/defaults.json')['shared_seed_sha256']:
            return obj
    print('GENERATING frozen 271-condition design',flush=True)
    rc=subprocess.call([sys.executable,str(ROOT/'tools/generate_campaign.py')],cwd=ROOT)
    if rc!=0:raise RuntimeError('generate_campaign.py failed')
    obj=loadj(path)
    if len(obj['conditions'])!=271:raise RuntimeError('design condition count is not 271')
    return obj

def _condition_score(x,xref):
    shape=float(shape_distance(x,xref,m=128))
    a=curve_metrics(x);b=curve_metrics(xref)
    scalar=max(abs(float(a[k])-float(b[k]))/max(abs(float(a[k])),abs(float(b[k])),1e-12) for k in ('length','rg','edge_cv'))
    return 0.7*shape+0.3*scalar,shape,scalar

def heavy_selection(man:dict, previous:Path):
    """Deterministic, blinded selection; never references heavy outcomes.

    For each viable anonymous slider: one local perturbation (k=+-1),
    one strongest observed response, and one orthogonal sentinel (m=0 or
    most distant extreme).  Exact primary-selection provenance is stored.
    """
    previous=Path(previous)
    runlog=loadj(previous/'runlog.json')
    by={r['condition_id']:r for r in runlog['conditions']}
    entries=man['conditions']; byid={c['condition_id']:c for c in entries}
    refs={c['reference_id']:c for c in entries if c['role']=='reference'}
    selected=[];details=[]
    for c in entries:
        if c['role']=='reference' and by.get(c['condition_id'],{}).get('status')=='PASS':
            selected.append(c['condition_id']);details.append({'condition_id':c['condition_id'],'reason':'successful reference necessary for matched comparison'})
        elif c['role']=='activation_control' and by.get(c['condition_id'],{}).get('status')=='PASS' and refs[c['reference_id']]['condition_id'] in selected:
            selected.append(c['condition_id']);details.append({'condition_id':c['condition_id'],'reason':'successful registered activation control'})
    for axis in sorted({c['axis_id'] for c in entries if c['role']=='sweep'}):
        candidates=[c for c in entries if c['role']=='sweep' and c['axis_id']==axis]
        rid=refs[candidates[0]['reference_id']]['condition_id']
        if rid not in selected:continue
        ref=read_xyz(previous/'results'/rid/'final.txt')
        valid=[]
        for c in candidates:
            cid=c['condition_id']
            if by.get(cid,{}).get('status')!='PASS':continue
            try:score,shape,scal=_condition_score(read_xyz(previous/'results'/cid/'final.txt'),ref)
            except Exception:continue
            if not all(math.isfinite(z) for z in (score,shape,scal)):continue
            valid.append((c,score,shape,scal))
        if not valid:continue
        chosen={}
        local=[v for v in valid if v[0].get('k') in (-1,1)]
        if local:
            v=sorted(local,key=lambda r:(-r[1],r[0]['condition_id']))[0]
            chosen[v[0]['condition_id']]=(v,'nearest-default local slope')
        best=sorted(valid,key=lambda r:(-r[1],r[0]['condition_id']))[0]
        chosen.setdefault(best[0]['condition_id'],(best,'largest measured shape/scalar response'))
        endpoint=[v for v in valid if v[0]['level_kind']=='zero']
        if not endpoint:endpoint=[v for v in valid if v[0].get('k') in (-16,16)]
        if endpoint:
            e=sorted(endpoint,key=lambda r:(-r[1],r[0]['condition_id']))[0]
            chosen.setdefault(e[0]['condition_id'],(e,'zero/endpoint robustness sentinel'))
        for v in sorted(valid,key=lambda r:(-r[1],r[0]['condition_id'])):
            if len(chosen)>=3:break
            chosen.setdefault(v[0]['condition_id'],(v,'additional diagnostic response'))
        for cid,(v,reason) in chosen.items():
            selected.append(cid);details.append({'condition_id':cid,'axis_id':axis,'reason':reason,
               'source_score':v[1],'source_shape_distance':v[2],'source_scalar_rel':v[3],
               'source_tier':previous.name})
    if len(selected)>31:raise RuntimeError('heavy-selection invariant violated: >31 selections')
    if not any(c.get('axis_id') for c in details):raise RuntimeError('No valid earlier slope responses; refusing expensive tier')
    if not (previous/'summary.json').is_file():raise RuntimeError('source summary unavailable')
    cfg=loadj(ROOT/'configs/default.json'); source_runtime=loadj(previous/'runtime.json')
    cal=loadj(ROOT/'private/install_test_runtime/defaults.json')
    if source_runtime.get('shared_seed_sha256')!=cal['shared_seed_sha256']:
        raise RuntimeError('prior source run used a different seed; cannot select heavy cases')
    selected_order=[c['condition_id'] for c in entries if c['condition_id'] in set(selected)]
    selection={'schema':'A058-PRECOMMITTED-HEAVY-SELECTION-1','selection_from':str(previous.relative_to(ROOT)),
       'source_budget':source_runtime['iterations_per_condition'],
       'source_runlog_sha256':hashlib.sha256((previous/'runlog.json').read_bytes()).hexdigest(),
       'source_manifest_sha256':hashlib.sha256((previous/'manifest.json').read_bytes()).hexdigest(),
       'seed_sha256':cal['shared_seed_sha256'],'selected_ids':selected_order,'selected_count':len(selected_order),
       'rules':'all successful references and activation control; per axis three of: strongest local k ±1, strongest measured response, zero/endpoint; fill duplicate with next largest finite response; no heavy outcome used',
       'selection_details':details,'registered_population_count':271,'no_pvalues_or_physical_claims':True}
    return [byid[cid] for cid in selected_order],selection

def _previous_source():
    runs=ROOT/'campaign/runs'
    for tier in ('2048','BASIC'):
        p=runs/tier
        if (p/'summary.json').exists() and (p/'runlog.json').exists():return p
    raise RuntimeError('32768 requires at least one completed 2048 or BASIC run for blinded selection')

def main():
    mode=sys.argv[1].upper() if len(sys.argv)>1 else 'BASIC'
    if mode=='512':mode='BASIC'
    if mode not in {'BASIC','2048','32768'}:raise SystemExit('valid budgets: BASIC, 512, 2048, 32768')
    # Do not change the existing scientific freeze after beginning experimental work.
    _ensure_calibrated();man=_ensure_design()
    if mode=='32768':
        source=_previous_source()
        try:
            selected,selection=heavy_selection(man,source)
        except RuntimeError as exc:
            fallback=ROOT/'campaign/runs/BASIC'
            if source.name!='BASIC' and (fallback/'summary.json').is_file() and (fallback/'runlog.json').is_file():
                print('No qualified response in longer budget; trying eligible BASIC evidence',flush=True)
                selected,selection=heavy_selection(man,fallback)
            else:raise
    else:
        selected=list(man['conditions']);selection={'schema':'A058-ALL-CONDITIONS-1','tier':mode,
            'selected_ids':[x['condition_id'] for x in selected],
            'selected_count':len(selected),'registered_population_count':271,'rule':'all registered conditions'}
    print(f'BUDGET {mode}: {len(selected)}/271 selected, horizons {loadj(ROOT/"configs/default.json")["response_budgets"][mode]["checkpoints"]}',flush=True)
    # SELFTEST + FREEZE run without rotating framework v1.0.8 output trees.
    if _cmd(ROOT/'run_freeze.cmd')!=0:raise RuntimeError('framework protocol FREEZE validation failed')
    rundir=ROOT/'campaign/runs'/mode;rundir.parent.mkdir(parents=True,exist_ok=True)
    if rundir.exists():
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        archive=rundir.with_name(mode+'__'+stamp)
        rundir.rename(archive)
        print('Previous tier preserved at',archive.relative_to(ROOT),flush=True)
    summary=run_budget(mode,selected,selection,rundir)
    savej(ROOT/'campaign/active_run.json',{'schema':'A058-ACTIVE-BUDGET-1','tier':mode,
        'run_path':str(rundir.relative_to(ROOT)),'selection_path':str((rundir/'selection.json').relative_to(ROOT)),
        'budget':loadj(ROOT/'configs/default.json')['response_budgets'][mode]['max_iterations']})
    # run FULL is framework's analysis/packaging mode; it is NOT a request for
    # another 271 physical KnotPlot conditions.
    rc=subprocess.call([sys.executable,str(ROOT/'run_instance.py'),'FULL'],cwd=ROOT)
    if rc!=0:
        print('FRAMEWORK REPORT ERROR: data retained in',rundir,file=sys.stderr)
        return rc
    print('ANALYSIS + Framework-v1.0.8 report published; budget:',mode,flush=True)
    # Partial failures are not silently relabeled as success; the gate ledger contains them.
    if not summary['complete']:print('PARTIAL RESULTS: failed/unsupported sectors; inspect summary.json and gate ledger',flush=True)
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:
        print('A058 BUDGET FAIL:',type(e).__name__+':',str(e),file=sys.stderr)
        raise SystemExit(2)
