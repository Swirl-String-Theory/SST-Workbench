from __future__ import annotations
from pathlib import Path
import json, statistics
from .seal import sha256_file


def _verify(c):
    seal=json.loads((c/'BLIND_SEAL.json').read_text())
    checks={'manifest_sha256':'BLIND_MANIFEST.json','results_sha256':'BLIND_RESULTS.json','analysis_sha256':'ANALYSIS_BLIND.json','report_sha256':'REPORT_BLIND.md','config_sha256':'BLIND_CONFIG.json','backend_qualification_sha256':'BACKEND_QUALIFICATION.json'}
    for k,f in checks.items():
        if sha256_file(c/f)!=seal[k]: raise RuntimeError('blind seal mismatch: '+f)
    p=c/'_private/PRIVATE_MAPPING.json'
    if sha256_file(p)!=seal['private_mapping_commitment']: raise RuntimeError('private mapping commitment mismatch')
    return p


def _m(summary,key):
    table={'rel_eq_residual':'median_rel_eq','cross_stabilization':'median_cross_stabilization','farfield_anisotropy_r6':'median_farfield_anisotropy_r6'}
    return summary.get(table[key])


def reveal_discovery(campaign:Path):
    c=Path(campaign); pp=_verify(c); priv=json.loads(pp.read_text()); ana=json.loads((c/'ANALYSIS_BLIND.json').read_text())
    rows=[]
    for aid,s in ana['summaries'].items():
        m=priv['mapping'][aid]
        rows.append({'anonymous_id':aid,**m,'blind_summary':s})

    hom=[r for r in rows if r['semantic_kind']=='homogeneous_decorated']
    unl=[r for r in rows if r['semantic_kind']=='unlinked_homogeneous']
    direct=[r for r in rows if r['semantic_kind']=='source_native_link']
    mixed=[r for r in rows if r['semantic_kind']=='historical_mixed_control']

    # Pair each linked homogeneous case with same-knot unlinked control.
    uidx={r['component_knots'][0]:r for r in unl}
    linked_contrasts=[]
    for r in hom:
        k=r['component_knots'][0]; u=uidx[k]; a=r['blind_summary']; b=u['blind_summary']
        linked_contrasts.append({'knot':k,'architecture_code':r['architecture_code'],
          'status_pair':[a['status'],b['status']],
          'delta_rel_eq':None if _m(a,'rel_eq_residual') is None else _m(a,'rel_eq_residual')-_m(b,'rel_eq_residual'),
          'delta_cross_stabilization':None if _m(a,'cross_stabilization') is None else _m(a,'cross_stabilization')-_m(b,'cross_stabilization'),
          'delta_farfield_anisotropy':None if _m(a,'farfield_anisotropy_r6') is None else _m(a,'farfield_anisotropy_r6')-_m(b,'farfield_anisotropy_r6'),
          'polarity_gate':a.get('polarity',{}).get('both_normalizations_gate')})

    # Per knot robust summary across skeleton embeddings; no weighted winner score.
    knot_summary=[]
    for k in sorted({r['component_knots'][0] for r in hom}):
        rr=[r for r in hom if r['component_knots'][0]==k]
        knot_summary.append({'knot':k,'n_linked_embeddings':len(rr),
          'numerically_qualified':sum(r['blind_summary']['status']=='NUMERICALLY_QUALIFIED' for r in rr),
          'polarity_gate_passes':sum(bool(r['blind_summary'].get('polarity',{}).get('both_normalizations_gate')) for r in rr),
          'median_rel_eq':statistics.median([_m(r['blind_summary'],'rel_eq_residual') for r in rr]),
          'median_cross_stabilization':statistics.median([_m(r['blind_summary'],'cross_stabilization') for r in rr]),
          'median_farfield_anisotropy':statistics.median([_m(r['blind_summary'],'farfield_anisotropy_r6') for r in rr])})

    pareto_file=c/'PRE_REVEAL_STAGEA_PARETO.json'
    pareto_revealed=[]
    if pareto_file.exists():
        ppj=json.loads(pareto_file.read_text())
        byid={r['anonymous_id']:r for r in rows}
        for pt in ppj.get('pareto_points',[]):
            sem=byid[pt['anonymous_id']]
            pareto_revealed.append({**pt,'semantic_kind':sem['semantic_kind'],'architecture_code':sem.get('architecture_code'),'component_knots':sem.get('component_knots'),'direct_link':sem.get('direct_link')})

    out={'schema':'A054-REVEAL-3.0','blind_seal_verified':True,'cases':rows,'homogeneous_linked_vs_unlinked':linked_contrasts,
         'knot_candidate_summary':knot_summary,
         'direct_source_link_cases':direct,'historical_mixed_controls':mixed,'pareto_revealed_operating_points':pareto_revealed,
         'interpretation_guard':'This is a broad finite-core discovery screen. No single weighted winner score is defined. Surviving candidates require v0.2-style restoring/Kelvin/ringdown/RPO-Floquet certification and provider/embedding replication.'}
    (c/'REVEALED_RESULTS.json').write_text(json.dumps(out,indent=2)+'\n')
    lines=['# A054 v0.3.0 — REVEALED broad topology discovery','','Blind results were sealed before semantic identity attachment.','','## Knot candidates (homogeneous three-component decorations)','',
           '| knot | qualified/4 | polarity pass/4 | median rel-eq | median cross-stabilization | median anisotropy |','|---|---:|---:|---:|---:|---:|']
    for x in knot_summary:
        lines.append(f"| {x['knot']} | {x['numerically_qualified']}/4 | {x['polarity_gate_passes']}/4 | {x['median_rel_eq']:.6g} | {x['median_cross_stabilization']:.6g} | {x['median_farfield_anisotropy']:.6g} |")
    lines += ['','No particle identity is assigned at this stage.']
    (c/'REPORT_REVEALED.md').write_text('\n'.join(lines)+'\n')
    return out
