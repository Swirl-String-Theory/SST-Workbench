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
from pklsa_builder.repo_finder import scan_repository


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')


def load_scan(path: Path) -> dict:
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def scan_fingerprint(scan: dict) -> tuple[str, int]:
    """Digest the registered A001-A008 byte inventory, independent of absolute root paths."""
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


def validate_repair_scope(release: dict, campaign: dict, failed: list[dict]) -> dict:
    if not release.get('source_contract_gate_pass') or not release.get('a001_a008_coverage_gate_pass'):
        raise RuntimeError('repair refused: original source coverage gate was not green')
    if not release.get('topology_database_ingest_gate_pass') or not release.get('identity_database_gate_pass'):
        raise RuntimeError('repair refused: original topology identity/database gates were not green')
    if not release.get('trefoil_poc_gate_pass'):
        raise RuntimeError('repair refused: original trefoil POC was not green')
    if campaign.get('failed_count') != len(failed) or campaign.get('passed_count',0) + len(failed) != campaign.get('topology_count'):
        raise RuntimeError('repair refused: campaign index and FAILED_TOPOLOGIES disagree')
    if not failed:
        raise RuntimeError('repair refused: there are no failed topologies to repair')

    error_carriers=0
    failed_ids=[]
    for item in failed:
        topo=item.get('topology_id')
        summary=item.get('summary')
        identity=item.get('identity')
        if not topo or not isinstance(summary,dict) or not isinstance(identity,dict):
            raise RuntimeError('repair refused: failed topology lacks summary/identity evidence')
        if not identity.get('pass'):
            raise RuntimeError(f'repair refused: {topo} also has an identity failure')
        by_catalog=summary.get('qualification_errors_by_catalog_id') or {}
        if set(by_catalog) != {'A007'}:
            raise RuntimeError(f'repair refused: {topo} has errors outside A007: {by_catalog}')
        bad_rows=[r for r in summary.get('source_matrix',[]) if int(r.get('errors',0)) > 0]
        if not bad_rows or any(r.get('source_family') != 'fremlin_fourier_mirror' for r in bad_rows):
            raise RuntimeError(f'repair refused: {topo} has a non-Fremlin-mirror error source')
        error_carriers += int(summary.get('error_carriers',0))
        failed_ids.append(topo)

    return {
        'failed_topology_count': len(failed_ids),
        'failed_topologies': failed_ids,
        'error_carrier_count': error_carriers,
        'scope': 'A007 fremlin_fourier_mirror only',
    }


def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description='Repair only prior A007/Fremlin optional-a0 failures without recomputing green topology campaigns')
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
    scope=validate_repair_scope(old_release, old_campaign, old_failed)

    if Path(old_context.get('workbench_root','')).resolve() != workbench:
        raise RuntimeError('repair refused: Workbench root differs from original production context')

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
            raise RuntimeError(f'repair refused: {label} is missing: {path}')
        if prod.sha256_file(path) != expected:
            raise RuntimeError(f'repair refused: {label} hash changed since original run')

    print('[repair 1/5] verifying registered source bytes with a fresh deep SHA-256 scan', flush=True)
    old_scan=load_scan(output/'source_discovery'/'REPO_SOURCE_DISCOVERY.json.gz')
    fresh_scan=scan_repository(workbench,source_catalog,hash_files=True,search_depth=10,find_unregistered=False)
    if not fresh_scan.get('coverage_gate',{}).get('pass'):
        raise RuntimeError('repair refused: fresh A001-A008 source coverage gate failed')
    old_fp,old_n=scan_fingerprint(old_scan)
    new_fp,new_n=scan_fingerprint(fresh_scan)
    if (old_fp,old_n)!=(new_fp,new_n):
        raise RuntimeError('repair refused: registered source byte inventory changed since original production run')

    print('[repair 2/5] rebuilding KnotInfo/LinkInfo registry', flush=True)
    registry_dir=output/'topology_registry'
    knotinfo=PACKAGE_ROOT/'data'/'topology_sources'/'knotinfo_data_complete.xls.zip'
    linkinfo=PACKAGE_ROOT/'data'/'topology_sources'/'linkinfo_data_complete.xls'
    aliases,db_summary=build_topology_registry(knotinfo,linkinfo,registry_dir)
    if not db_summary or not all(v.get('status')=='INGESTED' for v in db_summary.values()):
        raise RuntimeError('repair refused: topology database rebuild failed')

    topologies=[x.strip() for x in (output/'TOPOLOGIES.txt').read_text(encoding='utf-8').splitlines() if x.strip()]
    failed_ids=list(scope['failed_topologies'])
    full_config=QualificationConfig.load(full_cfg)

    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    history=output/'repair_history'/stamp
    history.mkdir(parents=True,exist_ok=True)
    write_json(history/'OLD_RUN_CONTEXT.json',old_context)
    write_json(history/'OLD_RELEASE.json',old_release)
    write_json(history/'OLD_CAMPAIGN_INDEX.json',old_campaign)
    write_json(history/'OLD_FAILED_TOPOLOGIES.json',old_failed)

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
            'repair':'FREMLIN_OPTIONAL_A0_RERUN',
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
    repair_provenance={
        'schema':'E010-PKLSA-FREMLIN-A0-REPAIR-1',
        'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'reason':'Archived Fremlin .fseries may encode j=0 as one initial three-value constant term followed by six-value harmonic rows.',
        'old_scientific_code_sha256':old_context.get('scientific_code_sha256'),
        'new_scientific_code_sha256':current_context.get('scientific_code_sha256'),
        'registered_source_inventory_sha256':new_fp,
        'registered_source_file_count':new_n,
        'reused_prior_pass_topology_count':old_campaign.get('passed_count'),
        'rerun_topology_count':len(failed_ids),
        'rerun_topologies':failed_ids,
        'rerun_error_carrier_count_before':scope['error_carrier_count'],
        'reuse_argument':(
            'The parser change is conditional on an initial three-value numeric row. '
            'Any previously PASS topology containing such a row would have failed under the old parser; '
            'therefore old PASS topology campaigns exercised only the unchanged six-column code path.'
        ),
        'source_bytes_verified_unchanged':True,
        'repair_results_pass':all(x['gate']['pass'] for x in repair_results),
    }
    write_json(output/'REPAIR_PROVENANCE_FREMLIN_A0.json',repair_provenance)
    write_json(output/'RUN_CONTEXT.json',current_context)

    release=dict(old_release)
    campaign_gate=len(failed)==0 and len(passed)==len(topologies) and len(topologies)>0
    identity_gate=len(identities)==len(topologies) and all(x.get('pass') for x in identities)
    source_gate=bool(old_release.get('source_contract_gate_pass') and old_release.get('a001_a008_coverage_gate_pass'))
    db_gate=bool(old_release.get('topology_database_ingest_gate_pass'))
    release.update({
        'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'full_campaign_gate_pass':campaign_gate,
        'identity_database_gate_pass':identity_gate,
        'publication_ready_geometry_layer':bool(source_gate and db_gate and campaign_gate and identity_gate and len(topologies)>0),
        'failed_topology_count':len(failed),
        'repair_applied':'FREMLIN_OPTIONAL_A0',
        'repair_provenance':'REPAIR_PROVENANCE_FREMLIN_A0.json',
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
