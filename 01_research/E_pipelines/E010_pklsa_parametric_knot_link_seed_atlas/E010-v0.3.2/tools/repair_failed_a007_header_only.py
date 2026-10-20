from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import shutil
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_production_atlas as prod
from pklsa_builder.builder import build_topology_registry
from pklsa_builder.campaign import run_topology_campaign
from pklsa_builder.models import QualificationConfig
from pklsa_builder.repo_finder import scan_repository, _is_comment_only_fseries


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')


def load_scan(path: Path) -> dict:
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def scan_fingerprint(scan: dict) -> tuple[str, int]:
    rows=[]
    for src in scan.get('source_results', []):
        cid=str(src.get('catalog_id',''))
        for inv in src.get('root_inventories', []):
            for rec in inv.get('files', []):
                sha=rec.get('sha256')
                if not sha:
                    raise RuntimeError(f"deep SHA-256 missing for {cid}:{rec.get('relative_path')}")
                rows.append((cid, str(rec.get('relative_path','')).replace('\\','/'), int(rec.get('size',0)), str(sha)))
    h=hashlib.sha256()
    for row in sorted(rows):
        h.update(('\t'.join(map(str,row))+'\n').encode('utf-8'))
    return h.hexdigest(), len(rows)


def current_file_role(scan: dict, absolute_path: Path) -> tuple[str | None, str | None]:
    target=str(absolute_path.resolve()).lower()
    for src in scan.get('source_results', []):
        for inv in src.get('root_inventories', []):
            for rec in inv.get('files', []):
                try:
                    p=str(Path(rec['path']).resolve()).lower()
                except Exception:
                    p=str(rec.get('path','')).lower()
                if p == target:
                    return rec.get('role'), rec.get('representation_hint')
    return None, None


def validate_scope(output: Path, failed: list[dict]) -> dict:
    if not failed:
        raise RuntimeError('repair refused: no failed topologies remain')
    ids=[]
    placeholder_paths=[]
    error_count=0
    for item in failed:
        topo=item.get('topology_id')
        summary=item.get('summary') or {}
        identity=item.get('identity') or {}
        if not topo or not identity.get('pass'):
            raise RuntimeError(f'repair refused: {topo or "UNKNOWN"} also has an identity failure')
        by_catalog=summary.get('qualification_errors_by_catalog_id') or {}
        if set(by_catalog) != {'A007'}:
            raise RuntimeError(f'repair refused: {topo} has errors outside A007: {by_catalog}')
        checks=load_json(output/'atlas'/topo/'qualification'/'topology_checks.json')
        errors=checks.get('errors') or []
        if not errors:
            raise RuntimeError(f'repair refused: {topo} has no explicit error records')
        for err in errors:
            c=err.get('carrier') or {}
            p=Path(c.get('source_path',''))
            if c.get('catalog_id')!='A007' or c.get('source_family')!='fremlin_fourier_mirror':
                raise RuntimeError(f'repair refused: {topo} has non-A007/Fremlin error carrier')
            if p.suffix.lower()!='.fseries':
                raise RuntimeError(f'repair refused: {topo} error is not an .fseries placeholder: {p}')
            if not p.exists():
                raise RuntimeError(f'repair refused: source file missing: {p}')
            if not _is_comment_only_fseries(p):
                raise RuntimeError(f'repair refused: failed .fseries is not comment/header-only: {p}')
            placeholder_paths.append(str(p.resolve()))
            error_count += 1
        ids.append(topo)
    return {
        'failed_topologies': ids,
        'failed_topology_count': len(ids),
        'error_carrier_count': error_count,
        'header_only_fseries_paths': sorted(set(placeholder_paths)),
        'interpretation': 'INCOMPLETE_MIRROR_NOT_GEOMETRY',
    }




def validate_already_complete(output: Path, release: dict, campaign: dict) -> dict:
    """Fail-closed verification for an idempotent rerun after the repair is already green.

    A second invocation must not fail merely because FAILED_TOPOLOGIES.json is empty.
    It may return success only when the global ledgers and every per-topology production
    gate agree that the atlas is complete.
    """
    failed = load_json(output/'FAILED_TOPOLOGIES.json')
    if failed:
        raise RuntimeError('already-complete validation called while failures still exist')
    topologies=[x.strip() for x in (output/'TOPOLOGIES.txt').read_text(encoding='utf-8').splitlines() if x.strip()]
    n=len(topologies)
    if n <= 0:
        raise RuntimeError('repair refused: topology set is empty')
    if campaign.get('failed_count') != 0:
        raise RuntimeError('repair refused: FAILED_TOPOLOGIES is empty but campaign failed_count is non-zero')
    if campaign.get('topology_count') != n or campaign.get('passed_count') != n:
        raise RuntimeError('repair refused: no failures remain but campaign counts are not fully green')
    if set(campaign.get('failed') or []):
        raise RuntimeError('repair refused: campaign failed list is non-empty')

    bad=[]
    for topo in topologies:
        gp=output/'atlas'/topo/'qualification'/'PRODUCTION_GATE.json'
        sp=output/'atlas'/topo/'qualification'/'summary.json'
        ip=output/'atlas'/topo/'topology'/'PRODUCTION_IDENTITY_DATABASE.json'
        if not gp.exists() or not sp.exists() or not ip.exists():
            bad.append({'topology_id':topo,'reason':'missing gate/summary/identity artifact'})
            continue
        gate=load_json(gp); summary=load_json(sp); identity=load_json(ip)
        if gate.get('pass') is not True or summary.get('qualification_gate_pass') is not True or identity.get('pass') is not True:
            bad.append({
                'topology_id':topo,
                'gate_pass':gate.get('pass'),
                'qualification_gate_pass':summary.get('qualification_gate_pass'),
                'identity_pass':identity.get('pass'),
            })
    if bad:
        raise RuntimeError(f'repair refused: {len(bad)} per-topology production gate(s) are not green despite empty FAILED_TOPOLOGIES')

    required_release={
        'source_contract_gate_pass':True,
        'a001_a008_coverage_gate_pass':True,
        'topology_database_ingest_gate_pass':True,
        'trefoil_poc_gate_pass':True,
        'full_campaign_gate_pass':True,
        'identity_database_gate_pass':True,
        'publication_ready_geometry_layer':True,
    }
    bad_release={k:release.get(k) for k,v in required_release.items() if release.get(k) is not v}
    if release.get('failed_topology_count') != 0:
        bad_release['failed_topology_count']=release.get('failed_topology_count')
    if bad_release:
        raise RuntimeError(f'repair refused: failure ledger is empty but RELEASE.json is not publication-green: {bad_release}')
    return {'topology_count':n,'passed_count':n,'failed_count':0,'status':'ALREADY_COMPLETE_VERIFIED'}

def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description='Final targeted A007 header-only .fseries repair')
    ap.add_argument('--workbench', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--archive-dir', required=True)
    args=ap.parse_args(argv)

    workbench=Path(args.workbench).resolve()
    output=Path(args.output).resolve()
    archive_dir=Path(args.archive_dir).resolve()

    required=[
        output/'RUN_CONTEXT.json', output/'RELEASE.json', output/'CAMPAIGN_INDEX.json',
        output/'FAILED_TOPOLOGIES.json', output/'TOPOLOGIES.txt',
        output/'source_discovery'/'REPO_SOURCE_DISCOVERY.json.gz',
    ]
    missing=[str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f'repair refused: missing prior production artifacts: {missing}')

    old_context=load_json(output/'RUN_CONTEXT.json')
    old_release=load_json(output/'RELEASE.json')
    old_campaign=load_json(output/'CAMPAIGN_INDEX.json')
    old_failed=load_json(output/'FAILED_TOPOLOGIES.json')

    if not old_release.get('source_contract_gate_pass') or not old_release.get('a001_a008_coverage_gate_pass'):
        raise RuntimeError('repair refused: prior source coverage gate was not green')
    if not old_release.get('topology_database_ingest_gate_pass') or not old_release.get('identity_database_gate_pass'):
        raise RuntimeError('repair refused: prior topology database/identity gates were not green')
    if not old_release.get('trefoil_poc_gate_pass'):
        raise RuntimeError('repair refused: prior trefoil POC was not green')
    if old_campaign.get('failed_count') != len(old_failed):
        raise RuntimeError('repair refused: campaign index and FAILED_TOPOLOGIES disagree')
    if old_campaign.get('passed_count',0)+len(old_failed) != old_campaign.get('topology_count'):
        raise RuntimeError('repair refused: campaign counts are inconsistent')
    if Path(old_context.get('workbench_root','')).resolve() != workbench:
        raise RuntimeError('repair refused: Workbench root differs from prior production context')

    already_complete = not old_failed
    if already_complete:
        complete_state = validate_already_complete(output, old_release, old_campaign)
    else:
        complete_state = None

    source_catalog=Path(old_context['source_catalog'])
    contract=Path(old_context['source_contract'])
    full_cfg=PACKAGE_ROOT/'configs'/'qualification_publication.json'
    poc_cfg=PACKAGE_ROOT/'configs'/'qualification_extended.json'
    manifest=PACKAGE_ROOT/'PACKAGE_MANIFEST.json'

    for label,path,expected in [
        ('source catalog',source_catalog,old_context.get('source_catalog_sha256')),
        ('source contract',contract,old_context.get('source_contract_sha256')),
        ('full config',full_cfg,old_context.get('full_config_sha256')),
        ('poc config',poc_cfg,old_context.get('poc_config_sha256')),
        ('package manifest',manifest,old_context.get('package_manifest_sha256')),
    ]:
        if not path.exists():
            raise RuntimeError(f'repair refused: {label} missing: {path}')
        if prod.sha256_file(path) != expected:
            raise RuntimeError(f'repair refused: {label} hash changed since prior production run')

    if already_complete:
        print('[repair] no failed topologies remain; verifying current source snapshot before idempotent success', flush=True)
        old_scan=load_scan(output/'source_discovery'/'REPO_SOURCE_DISCOVERY.json.gz')
        fresh_scan=scan_repository(workbench,source_catalog,hash_files=True,search_depth=10,find_unregistered=False)
        if not fresh_scan.get('coverage_gate',{}).get('pass'):
            raise RuntimeError('repair refused: fresh A001-A008 source coverage gate failed')
        old_fp,old_n=scan_fingerprint(old_scan); new_fp,new_n=scan_fingerprint(fresh_scan)
        if (old_fp,old_n)!=(new_fp,new_n):
            raise RuntimeError('repair refused: registered source byte inventory changed since completed production run')
        audit={
            'schema':'E010-PKLSA-IDEMPOTENT-REPAIR-VERIFY-1',
            'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'status':'ALREADY_COMPLETE_VERIFIED',
            'reason':'FAILED_TOPOLOGIES.json is empty and all global/per-topology production gates are green.',
            'topology_count':complete_state['topology_count'],
            'registered_source_inventory_sha256':new_fp,
            'registered_source_file_count':new_n,
            'release_publication_ready_geometry_layer':True,
        }
        write_json(output/'REPAIR_ALREADY_COMPLETE.json',audit)
        print('[repair] atlas is already publication-green; no topology rerun required', flush=True)
        print('[repair] packaging verified atlas', flush=True)
        zpath,zsha=prod.archive_tree(output,archive_dir)
        result=dict(old_release); result.update(audit); result['archive']=str(zpath); result['archive_sha256']=zsha
        print(json.dumps(result,indent=2),flush=True)
        return 0

    scope=validate_scope(output, old_failed)
    failed_ids=scope['failed_topologies']

    print('[repair 1/5] verifying registered source bytes with fresh deep SHA-256 scan', flush=True)
    old_scan=load_scan(output/'source_discovery'/'REPO_SOURCE_DISCOVERY.json.gz')
    fresh_scan=scan_repository(workbench,source_catalog,hash_files=True,search_depth=10,find_unregistered=False)
    if not fresh_scan.get('coverage_gate',{}).get('pass'):
        raise RuntimeError('repair refused: fresh A001-A008 source coverage gate failed')
    old_fp,old_n=scan_fingerprint(old_scan)
    new_fp,new_n=scan_fingerprint(fresh_scan)
    if (old_fp,old_n)!=(new_fp,new_n):
        raise RuntimeError('repair refused: registered source byte inventory changed since prior production run')

    for raw in scope['header_only_fseries_paths']:
        role,rep=current_file_role(fresh_scan,Path(raw))
        if role not in {'source_metadata','derived_metadata'} or rep not in {'fseries_header_only_incomplete_mirror','fseries_header_only'}:
            raise RuntimeError(f'repair refused: patched scanner did not demote header-only placeholder: {raw} -> {role}/{rep}')

    print('[repair 2/5] rebuilding KnotInfo/LinkInfo registry', flush=True)
    registry_dir=output/'topology_registry'
    knotinfo=PACKAGE_ROOT/'data'/'topology_sources'/'knotinfo_data_complete.xls.zip'
    linkinfo=PACKAGE_ROOT/'data'/'topology_sources'/'linkinfo_data_complete.xls'
    aliases,db_summary=build_topology_registry(knotinfo,linkinfo,registry_dir)
    if not db_summary or not all(v.get('status')=='INGESTED' for v in db_summary.values()):
        raise RuntimeError('repair refused: topology database rebuild failed')

    topologies=[x.strip() for x in (output/'TOPOLOGIES.txt').read_text(encoding='utf-8').splitlines() if x.strip()]
    full_config=QualificationConfig.load(full_cfg)

    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    history=output/'repair_history'/stamp
    history.mkdir(parents=True,exist_ok=True)
    write_json(history/'OLD_RUN_CONTEXT.json',old_context)
    write_json(history/'OLD_RELEASE.json',old_release)
    write_json(history/'OLD_CAMPAIGN_INDEX.json',old_campaign)
    write_json(history/'OLD_FAILED_TOPOLOGIES.json',old_failed)
    write_json(history/'HEADER_ONLY_FSERIES_SCOPE.json',scope)

    print(f"[repair 3/5] rerunning {len(failed_ids)} failed topology campaign(s) only", flush=True)
    repair_results=[]
    for idx,topo in enumerate(failed_ids,1):
        old_dir=output/'atlas'/topo
        if old_dir.exists():
            target=history/'atlas'/topo
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.move(str(old_dir),str(target))
        print(f"[{idx:02d}/{len(failed_ids):02d}] {topo}: qualification", flush=True)
        summary=run_topology_campaign(
            topo, output/'atlas', full_config,
            workbench_root=workbench, base_root=None, alias_maps=aliases,
            registry_dir=registry_dir, repo_scan=fresh_scan,
        )
        identity=prod.topology_db_identity(registry_dir,topo)
        gate={
            'topology_id':topo,
            'geometry_qualification_pass':bool(summary.get('qualification_gate_pass')),
            'identity_database_pass':bool(identity.get('pass')),
            'pass':bool(summary.get('qualification_gate_pass') and identity.get('pass')),
            'repair':'A007_HEADER_ONLY_FSERIES_PLACEHOLDER',
        }
        write_json(output/'atlas'/topo/'qualification'/'PRODUCTION_GATE.json',gate)
        write_json(output/'atlas'/topo/'topology'/'PRODUCTION_IDENTITY_DATABASE.json',identity)
        repair_results.append({'topology_id':topo,'summary':summary,'identity':identity,'gate':gate})

    print('[repair 4/5] rebuilding global campaign/identity/release ledgers', flush=True)
    passed=[]; failed=[]; identities=[]
    for topo in topologies:
        gate_path=output/'atlas'/topo/'qualification'/'PRODUCTION_GATE.json'
        summary_path=output/'atlas'/topo/'qualification'/'summary.json'
        if not gate_path.exists() or not summary_path.exists():
            failed.append({'topology_id':topo,'error':'missing production gate or summary after repair'})
            continue
        gate=load_json(gate_path); summary=load_json(summary_path)
        identity=prod.topology_db_identity(registry_dir,topo)
        identities.append(identity)
        if gate.get('pass') is True and identity.get('pass') is True:
            passed.append(topo)
        else:
            failed.append({'topology_id':topo,'summary':summary,'identity':identity})

    write_json(output/'IDENTITY_DATABASE_LEDGER.json',identities)
    write_json(output/'FAILED_TOPOLOGIES.json',failed)
    write_json(output/'CAMPAIGN_INDEX.json',{
        'topology_count':len(topologies),
        'passed_count':len(passed),
        'failed_count':len(failed),
        'passed':passed,
        'failed':[x.get('topology_id') for x in failed],
    })

    current_context=prod.run_context(PACKAGE_ROOT,workbench,source_catalog,contract,poc_cfg,full_cfg)
    provenance={
        'schema':'E010-PKLSA-A007-HEADER-ONLY-FSERIES-REPAIR-1',
        'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'reason':'A007 historical mirror contains comment/header-only .fseries placeholders beside valid .short sampled geometry; placeholders are provenance metadata, not geometry carriers.',
        'old_scientific_code_sha256':old_context.get('scientific_code_sha256'),
        'new_scientific_code_sha256':current_context.get('scientific_code_sha256'),
        'registered_source_inventory_sha256':new_fp,
        'registered_source_file_count':new_n,
        'reused_prior_pass_topology_count':old_campaign.get('passed_count'),
        'rerun_topology_count':len(failed_ids),
        'rerun_topologies':failed_ids,
        'header_only_fseries_paths':scope['header_only_fseries_paths'],
        'source_bytes_verified_unchanged':True,
        'reuse_argument':(
            'Only comment/header-only A007 .fseries records are demoted from geometry to metadata. '
            'Such a record necessarily failed the prior Fourier parser and therefore cannot occur in any previously PASS topology campaign.'
        ),
        'repair_results_pass':all(x['gate']['pass'] for x in repair_results),
        'prior_repair_applied':old_release.get('repair_applied'),
    }
    write_json(output/'REPAIR_PROVENANCE_A007_HEADER_ONLY_FSERIES.json',provenance)
    write_json(output/'RUN_CONTEXT.json',current_context)

    campaign_gate=len(failed)==0 and len(passed)==len(topologies) and len(topologies)>0
    identity_gate=len(identities)==len(topologies) and all(x.get('pass') for x in identities)
    source_gate=bool(old_release.get('source_contract_gate_pass') and old_release.get('a001_a008_coverage_gate_pass'))
    db_gate=bool(old_release.get('topology_database_ingest_gate_pass'))

    release=dict(old_release)
    prior_chain=release.get('repair_chain')
    if not isinstance(prior_chain,list):
        prior_chain=[]
        if old_release.get('repair_applied'):
            prior_chain.append(old_release.get('repair_applied'))
    repair_name='A007_HEADER_ONLY_FSERIES_PLACEHOLDER'
    if repair_name not in prior_chain:
        prior_chain.append(repair_name)
    release.update({
        'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'full_campaign_gate_pass':campaign_gate,
        'identity_database_gate_pass':identity_gate,
        'publication_ready_geometry_layer':bool(source_gate and db_gate and campaign_gate and identity_gate and len(topologies)>0),
        'failed_topology_count':len(failed),
        'repair_applied':repair_name,
        'repair_chain':prior_chain,
        'repair_provenance':'REPAIR_PROVENANCE_A007_HEADER_ONLY_FSERIES.json',
        'repair_rerun_topology_count':len(failed_ids),
        'repair_reused_pass_topology_count':old_campaign.get('passed_count'),
    })
    write_json(output/'RELEASE.json',release)

    if not release['publication_ready_geometry_layer']:
        print(json.dumps(release,indent=2),flush=True)
        raise RuntimeError(f"repair completed fail-closed with {len(failed)} topology failure(s); inspect FAILED_TOPOLOGIES.json")

    print('[repair 5/5] publication gates green; packaging repaired atlas', flush=True)
    zpath,zsha=prod.archive_tree(output,archive_dir)
    result=dict(release); result['archive']=str(zpath); result['archive_sha256']=zsha
    print(json.dumps(result,indent=2),flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
