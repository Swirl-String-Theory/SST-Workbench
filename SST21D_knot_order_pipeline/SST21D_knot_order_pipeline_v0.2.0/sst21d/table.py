from __future__ import annotations
from pathlib import Path
import csv, json, math
from .gilbert import parse_gilbert,sample_entry
from .geometry import analyze_components
from .util import sha256_file,write_json,json_safe

def read_metadata(path):
    if not path: return {}
    with Path(path).open(newline='',encoding='utf-8-sig') as f: return {r['topology_key']:r for r in csv.DictReader(f)}

def flatten_row(entry,g,db_hash,samples,metadata):
    cs=g['components']; source_ratio=(entry.source_L/entry.source_D) if entry.source_L is not None and entry.source_D else None
    sample_ratio=(g['total_length']/entry.source_D) if entry.source_D else None
    rel=(g['total_length']-entry.source_L)/entry.source_L if entry.source_L else None
    gates={
      'G0_PARSE':True,'G1_FINITE':all(math.isfinite(c['length']) for c in cs),
      'G2_EDGE_UNIFORMITY':max(c['edge_cv'] for c in cs)<=0.005,
      'G3_POSITIVE_REACH_PROXY':g['global_sampled_reach_proxy']>0,
      'G4_SOURCE_LENGTH_CONSISTENCY':abs(rel)<=0.01 if rel is not None else None,
      'G5_NATIVE_BACKEND_AVAILABLE':g['native_backend'],'G6_TOPOLOGY_SIDECAR_PRESENT':False,
      'G7_RIDGERUNNER_RESIDUAL_PRESENT':False,'G8_DYNAMIC_TRAJECTORY_PRESENT':False,
      'G9_PHASE_FIELD_PRESENT':False,'G10_CONVERGENCE_CERTIFIED':False}
    row={
      'schema':'sst21d.master-row.v0.1','catalog_id':entry.catalog_id,'topology_key':entry.topology_key,'knotplot_key':entry.knotplot_key,
      'conway':entry.conway,'component_count':entry.component_count,'coefficient_count_total':entry.coefficient_count,
      'source_database_sha256':db_hash,'source_entry_sha256':entry.entry_sha256,'source_L':entry.source_L,'source_D':entry.source_D,
      'source_length_over_D':source_ratio,'sample_count_per_component':samples,'sampled_total_length':g['total_length'],
      'sampled_length_over_source_D':sample_ratio,'source_length_relative_error':rel,
      'edge_cv_max':max(c['edge_cv'] for c in cs),'edge_ratio_max':max(c['edge_ratio'] for c in cs),'flatness_min':min(c['flatness'] for c in cs),
      'curvature_max':max(c['curvature_max'] for c in cs),'min_curvature_radius':min(c['min_curvature_radius'] for c in cs),
      'sampled_dcsd_proxy':min(c['sampled_dcsd_proxy'] for c in cs),
      'inter_component_min_distance':g['inter_component_min_distance'],'sampled_reach_proxy':g['global_sampled_reach_proxy'],
      'length_over_diameter_proxy':g['global_length_over_diameter_proxy'],'ropelength_radius_proxy':g['global_ropelength_radius_proxy'],
      'writhe_sum_midpoint_proxy':sum(c['writhe_midpoint_proxy'] for c in cs),'acn_self_sum_midpoint_proxy':sum(c['acn_midpoint_proxy'] for c in cs),
      'linking_matrix_midpoint_proxy':json.dumps(json_safe(g['linking_matrix_midpoint_proxy']),separators=(',',':')),
      'bishop_closure_mismatch_max_rad':max(c['bishop_closure_mismatch_rad'] for c in cs),
      'Q_geom_reference':1.0,'Q_phase':None,'Dmin_projected_det1':None,'phase_structure_ir_exponent':None,
      'catalog_topology_status':'CATALOG_LABEL_ONLY_NOT_RECOMPUTED','geometry_status':'FOURIER_CATALOG_SAMPLED',
      'dynamic_status':'NOT_MEASURED_REQUIRES_TRAJECTORY','epistemic_status':'RESEARCH_TRACK_DIAGNOSTIC_ONLY',
      'native_backend':g['native_backend'],'native_backend_error':g.get('native_backend_error'),'gates_json':json.dumps(gates,separators=(',',':'))}
    row.update(metadata.get(entry.topology_key,{})); return row,gates

def write_csv(path,rows):
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows([{k:json_safe(v) for k,v in r.items()} for r in rows])

def static_campaign(database,out,samples=600,ids=None,metadata_path=None,require_native=False):
    out=Path(out); out.mkdir(parents=True,exist_ok=True); entries=parse_gilbert(database); wanted=set(ids or [])
    if wanted: entries=[e for e in entries if e.catalog_id in wanted or e.topology_key in wanted]
    meta=read_metadata(metadata_path); db_hash=sha256_file(database); rows=[]; details={}
    for e in entries:
        comps=sample_entry(e,samples); g=analyze_components(comps,auto_build_native=True)
        if require_native and not g['native_backend']: raise RuntimeError('native backend required but unavailable')
        row,gates=flatten_row(e,g,db_hash,samples,meta); rows.append(row)
        details[e.topology_key]={'entry':e.__dict__,'geometry':g,'gates':gates}
        write_json(out/'geometry'/f'{e.topology_key}.json',details[e.topology_key])
    write_csv(out/'sst21d_master.csv',rows); write_json(out/'sst21d_master.json',{'schema':'sst21d.master.v0.1','rows':rows})
    manifest={'schema':'sst21d.manifest.v0.1','database':str(Path(database).resolve()),'database_sha256':db_hash,'entry_count':len(rows),'samples':samples,
              'claim_guard':'Static geometry and catalogue provenance only; no independent knot certification and no dynamical phase-order inference.'}
    write_json(out/'manifest.json',manifest); return manifest

def convergence_campaign(database,out,resolutions=(128,256,512),ids=None,require_native=False):
    out=Path(out); out.mkdir(parents=True,exist_ok=True); entries=parse_gilbert(database); wanted=set(ids or [])
    if wanted: entries=[e for e in entries if e.catalog_id in wanted or e.topology_key in wanted]
    raw=[]; summaries=[]
    for e in entries:
        erows=[]
        for n in sorted(set(int(x) for x in resolutions)):
            g=analyze_components(sample_entry(e,n),auto_build_native=True)
            if require_native and not g['native_backend']: raise RuntimeError('native backend required but unavailable')
            row={'catalog_id':e.catalog_id,'topology_key':e.topology_key,'samples':n,'total_length':g['total_length'],
                 'sampled_reach_proxy':g['global_sampled_reach_proxy'],'length_over_diameter_proxy':g['global_length_over_diameter_proxy'],
                 'writhe_sum_midpoint_proxy':sum(c['writhe_midpoint_proxy'] for c in g['components']),
                 'edge_cv_max':max(c['edge_cv'] for c in g['components']),'native_backend':g['native_backend']}
            raw.append(row); erows.append(row)
        if len(erows)>=2:
            a,b=erows[-2],erows[-1]
            rel=lambda x,y: abs(y-x)/max(abs(y),1e-15)
            length_rel=rel(a['total_length'],b['total_length']); reach_rel=rel(a['sampled_reach_proxy'],b['sampled_reach_proxy'])
            wr_abs=abs(b['writhe_sum_midpoint_proxy']-a['writhe_sum_midpoint_proxy'])
            status='PASS_DIAGNOSTIC_THRESHOLDS' if length_rel<=1e-3 and reach_rel<=2e-2 and wr_abs<=5e-2 else 'NOT_CONVERGED_AT_REQUESTED_LEVELS'
        else:
            length_rel=reach_rel=wr_abs=None; status='INSUFFICIENT_RESOLUTIONS'
        summaries.append({'catalog_id':e.catalog_id,'topology_key':e.topology_key,'resolutions_json':json.dumps([r['samples'] for r in erows]),
                          'last_length_relative_change':length_rel,'last_reach_relative_change':reach_rel,'last_writhe_absolute_change':wr_abs,
                          'convergence_status':status,'thresholds':'length<=1e-3; reach<=2e-2; |dWr|<=5e-2'})
    write_csv(out/'convergence_raw.csv',raw); write_csv(out/'convergence_summary.csv',summaries)
    result={'schema':'sst21d.convergence.v0.1','database':str(Path(database).resolve()),'resolutions':list(resolutions),'rows':summaries,
            'status_note':'Diagnostic thresholds are preregistered defaults, not theorem-level error bounds.'}
    write_json(out/'convergence_summary.json',result); return {'entry_count':len(summaries),'out':str(out)}
