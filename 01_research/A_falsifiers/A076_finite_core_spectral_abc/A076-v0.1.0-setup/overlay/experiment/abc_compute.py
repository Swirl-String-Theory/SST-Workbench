"""A/B: native/preferential finite-core periodic-ring C4-mode convergence.

The original v0.1.2.4 numerical operator is bundled and hashed. Science is
restricted to a selected *m=2 sector*, not full-field dynamic equilibration.
"""
from __future__ import annotations
import json,hashlib,os,time
from pathlib import Path
from .finite_core_spectral.fourier import FourierSettings,fourier_scan
from .finite_core_spectral.core import independence_manifest
from .abc_logic import adjudicate

BASE = dict(n_nodes=48,ring_radius_over_core=4.0,q_min=2.47,q_max=2.59,
            q_step=.01,image_shell=2,fd_eps_over_core=1e-4,core_model=0,
            threads=16,neutral_modes=6,eig_zero_tol=1e-8,residual_max=.05)

SETTINGS=FourierSettings(max_m=12,symmetry_order=4,low_mode_leakage_max=.10,
         sector_leakage_max=1e-8,dominant_mode_weight_min=.5,
         branch_overlap_min=.8,candidate_abs_m_min=2,growth_rate_floor=1e-8)

# FULL probes are expensive; truncating/resuming is deliberate and explicit.
CASES_BASIC=[('resolution','N32',32),('resolution','N48',48),
             ('image_shell','S1',1),('image_shell','S2',2)]
CASES_FULL=[('resolution','N64',64),('resolution','N96',96),
            ('resolution','N128',128),('resolution','N160',160),('resolution','N192',192),
            ('image_shell','S2',2),('image_shell','S3',3),
            ('fd_eps','H3e-4',3e-4),('fd_eps','H1e-4',1e-4),
            ('fd_eps','H3e-5',3e-5),('core_model','C1',1),('core_model','C2',2)]


def canonical_json(x): return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def shaval(x): return hashlib.sha256(canonical_json(x).encode('utf8')).hexdigest()


def run_abc(out:Path,mode:str,*,threads=16,force_python=False,override=None):
    out=Path(out);dst=out/'abc_science';dst.mkdir(parents=True,exist_ok=True)
    full=mode.upper() in ('FULL','CERTIFY')
    cases=CASES_FULL if full else CASES_BASIC
    # Full numerical claims require the original compiled operator; do not
    # silently spend hours in the Python fallback or promote it as parity.
    if full and not force_python:
        from .finite_core_spectral.core import _backend
        _mod, name = _backend(force_python=False)
        if name != 'cpp':
            raise RuntimeError('FULL requires importable compiled C++ spectral kernel; '
                               'run BACKEND_PREFLIGHT first (Python is diagnostic only)')
    base={**BASE,'threads':int(threads)}
    if override: base.update(override)
    settings=SETTINGS
    results=[]; memo={}
    for axis,label,val in cases:
        cfg=dict(base)
        if axis=='resolution':cfg['n_nodes']=val
        elif axis=='image_shell':cfg['image_shell']=val
        elif axis=='fd_eps':cfg['fd_eps_over_core']=val
        elif axis=='core_model':cfg['core_model']=val
        # Original q bounds are blind internal follow-up interval, not physical target.
        key=shaval({'config':cfg,'settings':settings.__dict__,'native':not force_python})
        f=dst/f'case_{axis}_{label}.json'
        if key in memo:
            result=memo[key]
        elif f.exists():
            cached=json.loads(f.read_text(encoding='utf8'))
            if cached.get('input_hash')==key:
                result=cached['result'];memo[key]=result
            else: raise RuntimeError(f'Existing case has different hash; create a new run instead: {f}')
        else:
            print(f'[ABC][{mode}] {axis} {label}: N={cfg["n_nodes"]} '+
                  f'shell={cfg["image_shell"]} core={cfg["core_model"]}',flush=True)
            tic=time.monotonic()
            result=fourier_scan(cfg,settings,force_python=force_python,
                         progress=False,use_c4_accel=not full,audit_c4_accel=True)
            # Scientific full requires native independent kernel; refuse promotion if fallback.
            used={r.get('backend') for r in result['rows']}
            result['backend_policy_status']='NATIVE_EXECUTED' if used=={'cpp'} else 'PYTHON_ONLY_DIAGNOSTIC'
            result['elapsed_seconds']=time.monotonic()-tic
            memo[key]=result
            f.write_text(json.dumps({'input_hash':key,'axis':axis,'case':label,'value':val,
                'result':result},indent=2,allow_nan=False)+'\n',encoding='utf8')
        results.append({'axis':axis,'case':label,'value':val,'result':result})
    verdict=adjudicate(results)
    native_all=all(c['result'].get('backend_policy_status')=='NATIVE_EXECUTED' for c in results)
    # Additional required N160/N192 & regularization gates never silently waived.
    if not full or not native_all:
        verdict['B']='UNRESOLVED'
    if full and verdict['B']=='B_SPECTRAL_ONLY':
        for cluster in verdict['m2_promoted']:
            cs=[e for e in cluster.get('entries',[]) if e.get('axis')=='resolution']
            q160=[e['q'] for e in cs if e.get('value')==160]
            q192=[e['q'] for e in cs if e.get('value')==192]
            if not (q160 and q192 and abs(q160[0]-q192[0])<=.005):
                verdict['B']='UNRESOLVED'
        if not verdict['m2_promoted']:verdict['B']='UNRESOLVED'
    # A is a strictly *grid-scoped* high-resolution negative finding, not a
    # global no-go theorem and not the logical negation of B's promotion gate.
    if full and native_all and verdict['B']!='B_SPECTRAL_ONLY':
        highest=[x for x in results if x['axis']=='resolution' and x['value'] in (160,192)]
        checked=len(highest)==2 and all(x['result'].get('rows') and
            all(row.get('fourier_quality_gate_ok') is True for row in x['result']['rows'])
            for x in highest)
        from .abc_logic import events_of
        absent=all(not events_of([x]) for x in highest)
        if checked and absent:
            verdict['A']='A_SUPPORTED_WITHIN_GRID_SCOPE'
            verdict['A_limits']='No resolved m2 crossings at N160/N192 in frozen finite q grid; narrower or out-of-range transitions remain possible'
    verdict['A_quality_rows_required']=True
    # CORE_MODEL sensitivity is recorded but not assumed equivalent physics.
    verdict['numeric_backend']='C++' if native_all else 'PYTHON_ONLY_DIAGNOSTIC'
    verdict['status']='DIAGNOSTIC_ONLY' if not full else 'FULL_NUMERICAL_ADJUDICATION'
    verdict['independence_manifest']=independence_manifest(base)
    verdict['resolved_q_interval']=[base['q_min'],base['q_max']]
    verdict['n_cases']=len(results)
    # Summary kept small; individual case JSON retains raw intermediate data.
    (dst/'ABC_VERDICT.json').write_text(json.dumps(verdict,indent=2,allow_nan=False)+'\n',encoding='utf8')
    return verdict
