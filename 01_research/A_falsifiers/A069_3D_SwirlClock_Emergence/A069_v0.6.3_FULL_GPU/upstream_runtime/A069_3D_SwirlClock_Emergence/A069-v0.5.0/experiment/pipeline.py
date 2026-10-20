"""v0.5.0: real 3D GP initial-value evolution plus nonpromotable BdG controls.

Framework v1.0.9 remains the external authority. The ordinary analog gates
from v0.4.0 remain, and new gates cannot upgrade G4--G11 or G24--G25.
"""
from __future__ import annotations
import hashlib,hmac,json
from .pipeline_v040 import run_scientific_pipeline as inherited_pipeline
from .knotted_gp3d import simulate,bogoliubov_bulk_control,tangent_validation,candidate_frequency
from .science import write_json


def run_scientific_pipeline(root,cfg,ledger,mode):
    # Fail closed if any scientific module differs from the exact preregistration.
    spec=json.loads((root/'science_contract.json').read_text(encoding='utf-8'))
    for file, pinned in spec['scientific_source_sha256'].items():
        actual=hashlib.sha256((root/'experiment'/file).read_bytes()).hexdigest()
        if actual!=pinned:raise RuntimeError('Scientific code SHA mismatch (frozen protocol): '+file)
    original=inherited_pipeline(root,cfg,ledger,mode)
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"
    conf=root/'configs'/'GP3D_CAMPAIGN_V050.json'
    payload=conf.read_bytes(); pin=json.loads((root/'science_contract.json').read_text())['gp3d_campaign_sha256']
    if hashlib.sha256(payload).hexdigest()!=pin:
        raise RuntimeError('GP3D campaign config SHA mismatches frozen science contract')
    campaign=json.loads(payload)
    if campaign['version']!='v0.5.0':raise RuntimeError('invalid campaign version')
    token=(root/'private'/'OPAQUE_ID_KEY.bin').read_bytes()
    hidden={}
    cases=[]
    for d in campaign['cases']:
        kind=d['kind'];mirror=d['mirror'];n=d['n']
        alias=hmac.new(token, f'A069-v0.5.0/{kind}/{int(mirror)}/{n}'.encode(),hashlib.sha256).hexdigest()[:24].upper()
        result=simulate(kind,mirror,n,campaign['box'],campaign['xi'],campaign['dt'],campaign['steps'],campaign['segments'],campaign['diag_every'])
        blind={k:v for k,v in result.items() if k not in ('kind','mirror')}
        # Remove labels from user-facing snapshots; provenance mapping stays private.
        blind['parameters'].pop('source',None)
        blind['opaque_id']=alias
        blind['mode_assessment']=candidate_frequency(result['trace'])
        hidden[alias]={'kind':kind,'mirror':mirror,'n':n}
        write_json(out/f'D5_GP3D_KNOT_{alias}.json',blind)
        cases.append({'opaque_id':alias,'n':n,'max_mass_drift':blind['max_mass_drift'],
            'max_energy_drift':blind['max_energy_drift'],
            'initial_plaquettes':sum(x['count'] for x in blind['initial_vortices'].values()),
            'final_plaquettes':sum(x['count'] for x in blind['final_vortices'].values()),
            'candidate_mode':blind['mode_assessment']['status']})
    write_json(root/'private'/'GP3D_CASE_KEY_V050.json',hidden)
    bulk=bogoliubov_bulk_control(**campaign['bogoliubov_control'])
    tangent=tangent_validation(**campaign['tangent_control'])
    write_json(out/'D6_GP3D_BOGOLIUBOV_BULK_REFERENCE.json',bulk)
    write_json(out/'D7_GP3D_TIME_DEPENDENT_BDG_TANGENT.json',tangent)
    status=all(v['initial_plaquettes']>0 and v['max_mass_drift']<1e-9 and v['max_energy_drift']<1e-3 for v in cases)
    ledger.record('G26','PASS' if status else 'FAIL',
        metrics={'3d_evolutions':len(cases),'grid_sizes':sorted(set(d['n'] for d in cases)),
                 'max_mass_drift':max(v['max_mass_drift'] for v in cases),
                 'max_energy_drift':max(v['max_energy_drift'] for v in cases)},
        reason='Genuine GP x-y-z finite-volume FFT evolution; knots are initial phase defects; dynamics/cross-grid knot topology not certified')
    ledger.record('G27',bulk['status'],metrics={'bulk_frequency_rel_error':bulk['relative_error']},
        reason='Independent bulk GP Bogoliubov dispersion: genuine reference eigenmode, NOT a trefoil mode')
    ledger.record('G28',tangent['status'],metrics={'tangent_vs_finite_difference':tangent['relative_linearization_error']},
        reason='Time-dependent 3D GP tangent/BdG response validated against finite-difference independent evolution; no stationary base')
    ledger.record('G29','UNRESOLVED',reason='No stationary/relative-periodic knot base, reduced Floquet spectrum or >=4 converged frame-invariant cycles; no internal knot eigenfrequency')
    ledger.record('G30','UNRESOLVED',reason='3D knot topology tracking across time and spatial/time/core convergence not certified; GP compressible, not Euler')
    ledger.record('G31','UNRESOLVED',reason='No independent physical source, experimental clock, or A061-ready proper-time closure')
    write_json(out/'D5_GP3D_BLIND_CAMPAIGN_SUMMARY.json',{
         'schema':'A069-V050-3D-GP-PREFLIGHT-1','cases':cases,'source_sha256_campaign':pin,
         'bulk_bdg_reference':bulk,'tangent_response':tangent,
         'result':'3D_GP_TIME_EVOLUTION_EXECUTED_NO_QUALIFIED_KNOT_EIGENMODE',
         'scope':'DEVELOPMENT_CONTROL_NO_PHYSICAL_CLOCK',
         'external_independent_physical_provider_count':0,
         'parity_samples_are_correlated':True})
    original['3D_GP_KNOT_EVOLUTION']='PASS_NUMERICAL_PREFLIGHT' if status else 'FAIL'
    original['GP_BULK_BDG']='PASS' if bulk['status']=='PASS' else 'FAIL'
    original['GP_KNOT_INTRINSIC_EIGENMODE']='UNRESOLVED'
    original['full_Euler_knotted_dynamics']='UNRESOLVED'
    original['authority']='GP3D_SIMULATION_PREFLIGHT_NOT_CLOCK_CERTIFICATION'
    return original
