"""Source-frozen static metadata audit. Never claims physical dynamics."""
import hashlib,json,zipfile
from pathlib import Path

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as fh:
        for block in iter(lambda:fh.read(2**20),b''):h.update(block)
    return h.hexdigest()

def audit(archive_path,checksum_path=None):
    path=Path(archive_path).resolve()
    if not path.is_file():return {'status':'BLOCKED_SOURCE','reason':'Archive not found: '+str(path)}
    digest=sha256(path)
    checked=False
    if checksum_path:
        side=Path(checksum_path)
        if not side.is_file():return {'status':'BLOCKED_SOURCE','reason':'Source checksum missing'}
        expected=side.read_text(encoding='utf-8-sig').split()[0].lower()
        if expected!=digest:return {'status':'BLOCKED_SOURCE','reason':'SHA256_MISMATCH','expected':expected,'actual':digest}
        checked=True
    result={'status':'PENDING','archive_sha256':digest,'external_sha256_verified':checked,
            'source':'E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs',
            'scope':'read-only, metadata-only, source-qualified static geometry; NOT physical Euler dynamics'}
    with zipfile.ZipFile(path,'r') as z:
        if z.testzip() is not None:return {'status':'BLOCKED_SOURCE','reason':'ZIP_CRC_ERROR'}
        names=z.namelist()
        roots={x.split('/')[0] for x in names}
        if len(roots)!=1:return {'status':'BLOCKED_SOURCE','reason':'AMBIGUOUS_ROOT'}
        root=next(iter(roots))+'/'
        def obj(n):return json.loads(z.read(root+n).decode('utf-8'))
        def lines(n):return [json.loads(s) for s in z.read(root+n).decode('utf-8').splitlines() if s.strip()]
        summary=obj('RUN_SUMMARY.json')
        contract=obj('SEED_CONTRACT_SCHEMA.json')
        parent=obj('PARENT_RELEASE.json')
        anchors=lines('STATIC_READY_PROVIDER_ANCHORS.jsonl')
        primary=lines('STATIC_READY_PRIMARY_SEEDS.jsonl')
        ok=(summary.get('schema')=='E011-SKLSA-STATIC-READY-ATLAS-1' and
            summary.get('execution_gate')=='PASS' and summary.get('operational_error_count')==0 and
            summary.get('e010_release_version')=='0.3.1' and
            contract.get('schema')=='E011-STATIC-SEED-CONTRACT-1' and
            contract.get('dynamics_ready') is False and
            parent.get('e010_version')=='0.3.1' and
            len(anchors)==summary.get('provider_anchor_count') and
            len(primary)==summary.get('primary_static_seed_count'))
        result['status']='STATIC_METADATA_PRECHECK_PASS' if ok else 'BLOCKED_SOURCE'
        if not ok:
            result['reason']='INVALID_E011_STATIC_ADMISSION_CONTRACT'
            result['summary']={k:summary.get(k) for k in ['e010_release_version','e011_version','provider_anchor_count','primary_static_seed_count','selected_topology_count','execution_gate','operational_error_count']}
            return result
        result['summary']={k:summary.get(k) for k in ['e010_release_version','e011_version','provider_anchor_count','primary_static_seed_count','selected_topology_count','execution_gate','operational_error_count']}
        result['parent_physics_certification']='NOT_CERTIFIED'
        result['three_knot_writhe_audit']=[]
        for topo in ('3_1','5_2','6_1'):
            arr=[a for a in anchors if a.get('topology_id')==topo]
            provider_dict={a['provider_group']:a for a in arr}
            ag=obj('topologies/'+topo+'/PROVIDER_AGREEMENT.json')
            status={i['metric']:i for i in ag if i['metric'] in ['Wr','Wr_abs']}
            result['three_knot_writhe_audit'].append({
                'topology':topo,
                'providers':{k:{'writhe':v['finest_metrics']['Wr'],'writhe_ready':v['capabilities'].get('writhe_ready'),
                                'geometry_sha256':v['source_locator'].get('geometry_sha256')} for k,v in provider_dict.items()},
                'full_E011_agreement':{k:{'status':v['status'],'between_provider_relative_span':v['between_provider_relative_span'],
                                           'provider_count':v['provider_count']} for k,v in status.items()},
                'physical_dynamics':'NOT_EVALUATED'
            })
    return result
