from __future__ import annotations
import json
from pathlib import Path
from .common import dump_json, sha256_file
from .core import centered_group_velocity

DYNAMIC_TERMS=('omega','frequency','eigenmode','eigenvalue','time_series','timeseries','velocity_field','vorticity_field','linearized_operator','floquet','monodromy')

def _scan_json(obj):
    s=json.dumps(obj, sort_keys=True).lower()
    return {t:s.count(t) for t in DYNAMIC_TERMS}

def _validate_candidate(c):
    gates=[]
    independent=bool(c.get('derived_without_GRB_target_fit',False))
    gates.append({'id':'R10_INDEPENDENT_DERIVATION','status':'PASS' if independent else 'FAIL'})
    k=c.get('k',[]); omega=c.get('omega',[])
    samples_ok=len(k)>=3 and len(k)==len(omega)
    gates.append({'id':'R11_K_OMEGA_SAMPLES','status':'PASS' if samples_ok else 'FAIL','count':len(k)})
    dyn=bool(c.get('dynamical_generator')) and bool(c.get('mode_identity'))
    gates.append({'id':'R12_DYNAMICAL_GENERATOR_AND_MODE','status':'PASS' if dyn else 'FAIL'})
    conv=bool(c.get('convergence_evidence'))
    gates.append({'id':'R13_CONVERGENCE','status':'PASS' if conv else 'FAIL'})
    meta=bool(c.get('propagation_branch_metadata'))
    gates.append({'id':'R14_PROPAGATION_METADATA','status':'PASS' if meta else 'FAIL'})
    return gates, samples_ok and independent and dyn and conv and meta

def run(root: Path, outroot: Path):
    if not (outroot/'blind/verdict.json').exists(): raise RuntimeError('run blind first')
    cfg=json.loads((root/'configs/reveal_config.json').read_text(encoding='utf-8'))
    release=json.loads((root/cfg['pklsa_release']).read_text(encoding='utf-8'))
    ctx=json.loads((root/cfg['pklsa_run_context']).read_text(encoding='utf-8'))
    idx=json.loads((root/cfg['pklsa_campaign_index']).read_text(encoding='utf-8'))
    out=outroot/'revealed'; out.mkdir(parents=True,exist_ok=True)
    counts=_scan_json(idx)
    boundary=str(release.get('scientific_boundary',''))
    geometry_only=('geometry/source/topology' in boundary.lower())
    gates=[
      {'id':'R01_PKLSA_SOURCE_PROVENANCE','status':'PASS','e010_version':release.get('e010_version'),'release_sha256':sha256_file(root/cfg['pklsa_release']),'run_context_sha256':sha256_file(root/cfg['pklsa_run_context']),'campaign_index_sha256':sha256_file(root/cfg['pklsa_campaign_index'])},
      {'id':'R02_PKLSA_SCIENTIFIC_BOUNDARY','status':'BLOCKING' if geometry_only else 'PASS','boundary':boundary},
      {'id':'R03_DYNAMIC_ARTIFACT_DISCOVERY','status':'BLOCKING' if sum(counts.values())==0 else 'PASS','term_counts':counts},
      {'id':'R04_GEOMETRY_ONLY_PROMOTION','status':'PASS','policy':'REFUSED'},
    ]
    cand_path=root/cfg['optional_dynamic_candidate']
    candidate_emitted=False
    if cand_path.exists():
        c=json.loads(cand_path.read_text(encoding='utf-8'))
        cg,ok=_validate_candidate(c); gates.extend(cg)
        if ok:
            vg=centered_group_velocity([float(x) for x in c['k']],[float(x) for x in c['omega']])
            c0=float(c['c_reference_m_s'])
            energies=c.get('energy_TeV',[])[1:-1]
            if len(energies)!=len(vg):
                gates.append({'id':'R15_ENERGY_MAPPING','status':'FAIL','reason':'energy_TeV must align with interior group-velocity samples'})
            else:
                payload={'candidate_id':c.get('candidate_id','A052_DYNAMIC_MODE'), 'provenance':{'a052_source':str(cand_path),'a052_candidate_sha256':sha256_file(cand_path)}, 'derived_without_GRB_target_fit':True, 'birefringent':bool(c.get('birefringent',False)), 'samples':[{'energy_TeV':float(E),'delta_v_over_c':1.0-float(v)/c0} for E,v in zip(energies,vg)]}
                dump_json(out/'a044_candidate.json',payload); candidate_emitted=True
                gates.append({'id':'R15_ENERGY_MAPPING','status':'PASS','exported_samples':len(payload['samples'])})
    hard_block=geometry_only or sum(counts.values())==0
    if candidate_emitted:
        verdict_name='DYNAMIC_DISPERSION_CANDIDATE_EXPORTED_TO_A044'
    elif hard_block:
        verdict_name='BLOCKED_NO_DYNAMICAL_EIGENMODE_DATA'
    else:
        verdict_name='OPEN_DYNAMIC_CANDIDATE_INCOMPLETE'
    verdict={'verdict':verdict_name,'pklsa_version':release.get('e010_version'),'candidate_emitted':candidate_emitted,'gates':gates,'interpretation':'Current PKLSA evidence is geometry/topology qualification unless a separate dynamical candidate passes all frozen gates.'}
    dump_json(out/'verdict.json',verdict)
    lines=['# Reveal verdict','',f'**{verdict_name}**','',f"PKLSA release: `{release.get('e010_version')}`",'',f"Scientific boundary: {boundary}",'',f'Dynamic-key count in campaign index: `{sum(counts.values())}`.','', 'No A044 candidate is emitted unless a dynamical $k$-$\\omega$ branch with convergence and independent provenance passes the frozen gates.']
    (out/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return verdict
