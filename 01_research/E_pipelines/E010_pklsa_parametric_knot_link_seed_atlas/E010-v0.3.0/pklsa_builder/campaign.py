from __future__ import annotations
from pathlib import Path
import json, csv, traceback, numpy as np
from collections import Counter
from .source_discovery import discover_workbench, discover_from_v020, discover_from_repo_scan, dedupe_carriers
from .io_geometry import load_geometry
from .gilbert import find_gilbert_record, sample_gilbert_components
from .base_adapter import load_v020_carrier
from .qualification import qualify_components
from .hashing import geometry_sha256, write_json
from .independence import build_independence_ledger
from .topology_crosscheck import crosscheck_carrier
from .topology_reference import build_topology_reference_files


def source_rank(sf):
    order=[
        'knotplot_relaxed','knotplot_ideal','knotplot_fourier_series','knotplot_qhp',
        'fremlin_fourier','gilbert_ideal','katlas_source_derived','katlas_braid_derived',
        'ridgerunner','knotinfo_3d','ptsa','ptsa_control','siaf',
        'knot_library_source','knot_library_derived','fremlin_fourier_mirror',
        'knotplot_library_mirror','gilbert_ideal_mirror'
    ]
    try:return order.index(sf)
    except ValueError:return len(order)


def load_carrier_geometry(carrier,base_root=None):
    if carrier.source_path:
        if carrier.representation=='gilbert_ab_record':
            rec=find_gilbert_record(carrier.source_path,carrier.topology_id)
            return sample_gilbert_components(rec,n=max(4096,max(getattr(carrier,'metadata',{}).get('native_sample_n',4096),4096)))
        return load_geometry(carrier.source_path,representation=carrier.representation)
    if base_root and carrier.reference_id:
        return load_v020_carrier(base_root,carrier)
    raise RuntimeError('carrier has neither local source_path nor supported base reference')


def _family_dir_name(sf):
    return {
        'fremlin_fourier':'fseries','fremlin_fourier_mirror':'fseries_mirrors',
        'knotplot_fourier_series':'knotplot_fourier_series','gilbert_ideal':'gilbert_fourier',
        'ptsa':'ptsa_parameter_family','ptsa_control':'ptsa_controls','siaf':'siaf_controls',
        'katlas_braid_derived':'katlas_braid_derived','katlas_source_derived':'katlas_source_derived',
    }.get(sf,sf.replace('/','_').replace(' ','_'))


def _catalog_scan_summary(repo_scan):
    if not repo_scan: return None
    return {
        'coverage_gate':repo_scan.get('coverage_gate'),
        'unregistered_review_required':repo_scan.get('unregistered_review_required'),
        'source_status':{x['catalog_id']:x['status'] for x in repo_scan.get('source_results',[])},
    }


def run_topology_campaign(topology_id,out_root,config,workbench_root=None,base_root=None,alias_maps=(),registry_dir=None,extra_carriers=(),repo_scan=None):
    carriers=[]
    # Source-native repository scan is authoritative when available.
    if repo_scan:
        carriers+=discover_from_repo_scan(repo_scan,topology_id)
    elif workbench_root:
        carriers+=discover_workbench(workbench_root,topology_id)
    # v0.2.0 is a compact/fallback layer, not allowed to override source-native records.
    if base_root: carriers+=discover_from_v020(base_root,topology_id)
    carriers+=list(extra_carriers)
    carriers=dedupe_carriers(carriers); carriers.sort(key=lambda c:(source_rank(c.source_family),c.source_family,c.carrier_id))

    top=Path(out_root)/topology_id
    for d in (top/'topology',top/'qualification',top/'sources',top/'generated'): d.mkdir(parents=True,exist_ok=True)
    source_dirs=(
        'knotplot_relaxed','knotplot_ideal','knotplot_fourier_series','knotplot_qhp','fseries','fseries_mirrors',
        'gilbert_fourier','ridgerunner','knotinfo_3d','knot_library_source','knot_library_derived','katlas'
    )
    generated_dirs=('ptsa_parameter_family','ptsa_controls','siaf_controls','katlas_braid_derived','katlas_source_derived')
    for d in source_dirs: (top/'sources'/d).mkdir(parents=True,exist_ok=True)
    for d in generated_dirs: (top/'generated'/d).mkdir(parents=True,exist_ok=True)
    write_json(top/'sources'/'katlas'/'REFERENCE_ONLY.json',{
        'topology_id':topology_id,'role':'topology_reference_only',
        'guard':'KAtlas supplies topology/diagram/braid reference data. Any derived 3-D curve is stored under generated and is not counted as an upstream KAtlas embedding.'})

    rows=[]; errors=[]
    for c in carriers:
        try:
            comps=load_carrier_geometry(c,base_root)
            gh=geometry_sha256(comps)
            refs={}; md=c.metadata or {}
            if md.get('reference_ropelength') is not None:
                refs['ropelength_upstream']={'value':md['reference_ropelength'],'status':'REFERENCE_VALUE','source':'Brian Gilbert catalog L attribute','normalization_note':'Upstream L/D convention; kept separate from recomputed normalized ropelength.'}
            if md.get('reference_diameter') is not None:
                refs['diameter_upstream']={'value':md['reference_diameter'],'status':'REFERENCE_VALUE','source':'Brian Gilbert catalog D attribute'}
            q=qualify_components(comps,config,reference_observables=refs)
            row={'carrier':c.to_dict(),'geometry_sha256':gh,'qualification':q}
            rows.append(row)
            dest=(top/'generated' if (c.source_role.startswith('generated') or c.source_family in ('ptsa','ptsa_control','siaf','katlas_braid_derived','katlas_source_derived')) else top/'sources')/_family_dir_name(c.source_family)
            dest.mkdir(parents=True,exist_ok=True)
            safe=c.carrier_id.replace(':','_').replace('/','_')
            write_json(dest/f'{safe}.json',{'carrier':c.to_dict(),'geometry_sha256':gh})
            if config.copy_source_geometry:
                np.savez_compressed(dest/f'{safe}.npz',**{f'component_{i}':a for i,a in enumerate(comps)})
        except Exception as e:
            errors.append({'carrier':c.to_dict(),'error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()})

    topology_refs=build_topology_reference_files(top/'topology',topology_id,base_root,registry_dir)
    with (top/'qualification'/'geometry_metrics.jsonl').open('w',encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r,sort_keys=True,ensure_ascii=False)+'\n')
    metrics_index={'schema':'PKLSA-GEOMETRY-METRICS-INDEX-2','topology_id':topology_id,'records_file':'geometry_metrics.jsonl','record_count':len(rows),'carriers':[]}
    for r in rows:
        q=r['qualification']; finest=q['levels'][-1] if q.get('levels') else {}
        metrics_index['carriers'].append({
            'carrier_id':r['carrier']['carrier_id'],'source_family':r['carrier']['source_family'],
            'catalog_id':r['carrier'].get('catalog_id'),'finest_resolution':finest.get('resolution'),
            'finest_metrics':finest.get('metrics',{}),'overall_convergence':q.get('overall_convergence'),
            'observable_status':{k:v.get('status') for k,v in q.get('convergence',{}).items()},
            'reference_observables':q.get('reference_observables',{}),'scale_context':q.get('scale_context',{})})
    write_json(top/'qualification'/'geometry_metrics.json',metrics_index)
    conv={r['carrier']['carrier_id']:{'source_family':r['carrier']['source_family'],'catalog_id':r['carrier'].get('catalog_id'),'overall':r['qualification']['overall_convergence'],'observables':r['qualification']['convergence']} for r in rows}
    write_json(top/'qualification'/'convergence.json',conv)
    checks=[crosscheck_carrier(type('C',(),r['carrier'])(),r['qualification'],alias_maps) for r in rows]
    write_json(top/'qualification'/'topology_checks.json',{'checks':checks,'errors':errors})
    indep=build_independence_ledger(rows); write_json(top/'qualification'/'source_independence.json',indep); write_json(top/'qualification'/'source_independence_ledger.json',indep)
    write_json(top/'topology'/'cross_checks.json',{
        'topology_id':topology_id,'carrier_checks':checks,
        'independence_summary':{
            'carrier_count':indep['carrier_count'],'independent_group_count':indep['independent_group_count'],
            'strict_upstream_independent_provider_count':indep.get('strict_upstream_independent_provider_count')},
        'errors':errors})

    expected_fams=['knotplot_relaxed','knotplot_ideal','knotplot_fourier_series','knotplot_qhp','fremlin_fourier','gilbert_ideal','katlas_source_derived','katlas_braid_derived','ridgerunner','ptsa','ptsa_control','siaf','knotinfo_3d']
    fams=expected_fams + sorted(set(c.source_family for c in carriers)-set(expected_fams))
    matrix=[]
    for sf in fams:
        cs=[c for c in carriers if c.source_family==sf]; ok=[r for r in rows if r['carrier']['source_family']==sf]
        matrix.append({
            'source_family':sf,'discovered':len(cs),'qualified':len(ok),'errors':len(cs)-len(ok),
            'independence_groups':len(set(c.independence_group for c in cs)),
            'provider_groups':len(set(c.provider_group for c in cs if c.provider_group)),
            'catalog_ids':';'.join(sorted(set(c.catalog_id for c in cs if c.catalog_id)))})
    fields=['source_family','discovered','qualified','errors','independence_groups','provider_groups','catalog_ids']
    with (top/'qualification'/'source_matrix.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(matrix)

    err_by_catalog=Counter((e['carrier'].get('catalog_id') or 'UNREGISTERED') for e in errors)
    repo_cov=_catalog_scan_summary(repo_scan)
    summary={
        'topology_id':topology_id,
        'topology_reference_status':{'database':bool(topology_refs.get('database')),'database_kind':'linkinfo' if str(topology_id).upper().startswith('L') else 'knotinfo','katlas':bool(topology_refs.get('katlas'))},
        'discovered_carriers':len(carriers),'qualified_carriers':len(rows),'error_carriers':len(errors),
        'source_matrix':matrix,'independent_group_count':indep['independent_group_count'],
        'strict_upstream_independent_provider_count':indep.get('strict_upstream_independent_provider_count'),
        'qualification_errors_by_catalog_id':dict(sorted(err_by_catalog.items())),
        'repo_source_coverage':repo_cov,
        'qualification_gate_pass':len(errors)==0 and len(rows)>0,
        'all_error_records_fail_closed':True,
    }
    write_json(top/'qualification'/'summary.json',summary)
    return summary
