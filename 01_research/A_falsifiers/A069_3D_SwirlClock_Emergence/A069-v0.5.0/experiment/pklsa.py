"""Fail-closed static E011 geometry eligibility audit for A069 v0.3.0.

No old KnotPlot relaxed provider contributes to admissible physical science.
This module DOES NOT load a dynamic field, reconstruct a knot speed, or certify a clock.
"""
from __future__ import annotations
from pathlib import Path
import argparse,hashlib,json,os,zipfile

PIN='97cd1acbf23c102e4564f2d74fd329a2d03f32a29b8bd376ffa8b806c14246cc'
ARCHIVE_NAME='E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs.zip'
REQUIRED_CAPABILITIES=('writhe_ready','acn_ready')
LEGACY=('knotplot','legacy','vortexlab','historical')

def _sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as fp:
        for x in iter(lambda:fp.read(1<<20),b''):h.update(x)
    return h.hexdigest()

def _read(z,name):
    x=[p for p in z.namelist() if p.endswith('/'+name)]
    if len(x)!=1:raise ValueError(f'ambiguous/missing atlas member {name}: {len(x)}')
    return z.read(x[0])

def scan(atlas_path,topology='3_1',allow_historical=False):
    p=Path(atlas_path)
    report={'schema':'A069-PKLSA-STATIC-AUDIT-1','atlas_version':'E011-v0.3.0','topology_id':topology,
       'expected_archive_sha256':PIN,'archive_present':p.is_file(),
       'qualified_dynamics':False,'real_3d_trajectory_loaded':False,
       'physical_clock_supported':False,'physical_gate':'UNRESOLVED',
       'historic_inference_prohibited':True,'requested_mode':'STATIC_GEOMETRY_DIAGNOSTIC'}
    if not p.is_file():return dict(report,status='UNRESOLVED_MISSING_ATLAS')
    actual=_sha(p);report['archive_sha256']=actual
    if actual!=PIN:return dict(report,status='FAIL_INTEGRITY_SHA256')
    try:
      with zipfile.ZipFile(p) as z:
        schema=json.loads(_read(z,'SEED_CONTRACT_SCHEMA.json'))
        if schema.get('schema')!='E011-STATIC-SEED-CONTRACT-1' or schema.get('dynamics_ready') is not False:
            return dict(report,status='FAIL_ATLAS_SCHEMA')
        index=json.loads(_read(z,'STATIC_READY_INDEX.json'))
        matches=[t for t in index if t.get('topology_id')==topology]
        if len(matches)!=1:return dict(report,status='UNRESOLVED_TOPOLOGY_NOT_INDEXED')
        info=matches[0]
        rows=[json.loads(s) for s in _read(z,'STATIC_READY_PROVIDER_ANCHORS.jsonl').splitlines() if s.strip()]
        anchors=[r for r in rows if r.get('topology_id')==topology]
        if len(anchors)<1:return dict(report,status='UNRESOLVED_NO_ANCHORS')
        qualifying=[];excluded=[]
        for r in anchors:
            source=r.get('source_locator',{})
            family=str(r.get('provider_group','')).casefold()
            method=str(source.get('source_family','')).casefold()
            historic=any(x in family or x in method for x in LEGACY)
            flags=r.get('capabilities',{})
            reasons=[]
            if historic:reasons.append('LEGACY_PROVIDER_EXCLUDED')
            if r.get('seed_role')!='PRIMARY_REFERENCE':reasons.append('NON_PRIMARY_SEED')
            if r.get('evidence_class')!='UPSTREAM_INDEPENDENT':reasons.append('NOT_UPSTREAM_INDEPENDENT')
            for c in REQUIRED_CAPABILITIES:
                if flags.get(c) is not True:reasons.append('MISSING_'+c)
            if not source.get('raw_sha256') or not source.get('geometry_sha256'):reasons.append('MISSING_HASH')
            if source.get('representation') not in ('gilbert_ab_record','xyz','vect'):
                reasons.append('UNSUPPORTED_REPRESENTATION')
            payload={'provider_group':r.get('provider_group'), 'carrier_id':r.get('carrier_id'),
               'seed_id':r.get('static_seed_id'),'source_family':source.get('source_family'),
               'source_representation':source.get('representation'),
               'source_record_reference':source.get('reference_id'),
               'raw_sha256':source.get('raw_sha256'), 'geometry_sha256':source.get('geometry_sha256'),
               'source_locator_status':source.get('status'),
               'source_file_bytes_verified':False,
               'dynamics_ready':False}
            if reasons:
                payload['rejection_reasons']=reasons
                excluded.append(payload)
            else:qualifying.append(payload)
        eligible_families=sorted({a['provider_group'] for a in qualifying})
        report.update({'static_ready_index_status':info.get('status'),
           'static_ready_atlas_provider_groups':sorted({a['provider_group'] for a in anchors}),
           'eligible_provider_groups':eligible_families,
           'eligible_provider_count':len(eligible_families),
           'eligible_anchors':qualifying,'excluded_anchors':excluded,
           'required_independent_providers':2,'independent_physics_providers_met':False,
           'geometry_file_is_bundled':False,
           'upstream_source_bytes_verified':False,
           'atlas_integrity_pass':True,
           'physics_scope':'Neither source geometry nor physical trajectory or phase available in E011 output ZIP',
           'historical_mode_requested':bool(allow_historical)})
        # Historical flag never changes admitted list; it ONLY adds a view for diagnostics.
        if allow_historical:report['historical_diagnostic_anchors']=excluded
        # E011 index != independent physics source; never award two-source physical closure.
        if len(eligible_families)<1:
            report['status']='UNRESOLVED_NO_ELIGIBLE_GEOMETRY'
        else:
            report['status']='PASS_STATIC_MANIFEST_ONLY'
        return report
    except (OSError,zipfile.BadZipFile,ValueError,KeyError,json.JSONDecodeError) as exc:
        return dict(report,status='FAIL_ATLAS_PARSE',parse_error=str(exc))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--atlas',default=str(Path(__file__).resolve().parents[1]/'sources'/ARCHIVE_NAME))
    p.add_argument('--topology',default='3_1')
    p.add_argument('--historical-diagnostic',action='store_true')
    p.add_argument('--output')
    args=p.parse_args()
    r=scan(args.atlas,args.topology,args.historical_diagnostic)
    payload=json.dumps(r,sort_keys=True,indent=2)
    if args.output:Path(args.output).write_text(payload+'\n',encoding='utf8')
    print(payload)
    return 1 if r['status'].startswith('FAIL_') else 0
if __name__=='__main__':raise SystemExit(main())
