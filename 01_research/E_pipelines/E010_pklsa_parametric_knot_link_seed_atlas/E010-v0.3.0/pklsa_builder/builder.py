from __future__ import annotations
from pathlib import Path
import json, zipfile, datetime
from .models import QualificationConfig
from .topology_db import ingest_legacy_database, write_database_bundle
from .campaign import run_topology_campaign
from .hashing import write_json, sha256_file
from .repo_finder import scan_repository, write_scan_outputs, DEFAULT_CATALOG


def find_base_root(base):
    p=Path(base)
    if p.is_dir(): return p
    if p.is_file() and p.suffix.lower()=='.zip':
        out=p.parent/(p.stem+'_EXTRACTED_FOR_BUILDER')
        if not out.exists():
            with zipfile.ZipFile(p) as z:z.extractall(out)
        candidates=[x for x in out.iterdir() if x.is_dir() and (x/'pklsa').exists()]
        return candidates[0] if candidates else out
    raise FileNotFoundError(base)


def build_topology_registry(knotinfo_xls,linkinfo_xls,out):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    alias_maps=[]; summary={}
    for prefix,path,kind in [('knotinfo',knotinfo_xls,'knot'),('linkinfo',linkinfo_xls,'link')]:
        if not path or not Path(path).exists():
            summary[prefix]={'status':'MISSING'}; continue
        try:
            r=ingest_legacy_database(path,kind=kind); write_database_bundle(r,out,prefix); alias_maps.append(r['aliases'])
            summary[prefix]={'status':'INGESTED','records':len(r['records']),'sha256':r['source']['sha256'],'sheets':len(r['profiles'])}
        except Exception as e:
            summary[prefix]={'status':'ERROR','error_type':type(e).__name__,'error':str(e),'source_path':str(path)}
    write_json(out/'TOPOLOGY_DB_INGEST.json',summary)
    return alias_maps,summary


def build_release(*,base,output,config,workbench_root=None,knotinfo_xls=None,linkinfo_xls=None,topologies=('3_1',),source_catalog=None,strict_source_coverage=True,fail_on_unregistered=False,deep_source_hash=False,strict_topology_db=False):
    base_root=find_base_root(base); out=Path(output); out.mkdir(parents=True,exist_ok=True)

    repo_scan=None
    if workbench_root:
        repo_scan=scan_repository(workbench_root,source_catalog or DEFAULT_CATALOG,hash_files=deep_source_hash,find_unregistered=True)
        write_scan_outputs(repo_scan,out/'source_discovery')
        if strict_source_coverage and not repo_scan['coverage_gate']['pass']:
            # Write a release stub before failing so the source problem is inspectable.
            stub={
                'schema':'PKLSA-HIGH-RES-QUALIFICATION-2','atlas_version':'0.3.0','builder_version':'0.2.0',
                'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'status':'SOURCE_COVERAGE_BLOCKED','source_coverage':repo_scan['coverage_gate'],
                'scientific_boundary':'Geometry qualification and topology cross-checking only; no Euler/Biot-Savart stability claim.'}
            write_json(out/'RELEASE.json',stub)
            raise RuntimeError('A001-A008 source coverage gate failed; inspect source_discovery/A001_A008_COVERAGE.csv')
        if fail_on_unregistered and repo_scan.get('unregistered_review_required'):
            stub={
                'schema':'PKLSA-HIGH-RES-QUALIFICATION-2','atlas_version':'0.3.0','builder_version':'0.2.0',
                'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'status':'UNREGISTERED_SOURCES_BLOCKED','unregistered_count':len(repo_scan.get('unregistered_source_candidates',[])),
                'scientific_boundary':'Geometry qualification and topology cross-checking only; no Euler/Biot-Savart stability claim.'}
            write_json(out/'RELEASE.json',stub)
            raise RuntimeError('high-confidence unregistered source candidates require review; inspect source_discovery/UNREGISTERED_SOURCE_CANDIDATES.json')

    reg=out/'topology_registry'; aliases,db_summary=build_topology_registry(knotinfo_xls,linkinfo_xls,reg)
    topology_db_gate=all(v.get('status')=='INGESTED' for v in db_summary.values()) if db_summary else False
    if strict_topology_db and not topology_db_gate:
        stub={
            'schema':'PKLSA-HIGH-RES-QUALIFICATION-2','atlas_version':'0.3.0','builder_version':'0.2.0',
            'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'status':'TOPOLOGY_DATABASE_BLOCKED','topology_database':db_summary,
            'source_coverage_gate_pass':True if repo_scan is None else bool(repo_scan['coverage_gate']['pass']),
            'scientific_boundary':'Geometry qualification and topology cross-checking only; no Euler/Biot-Savart stability claim.'}
        write_json(out/'RELEASE.json',stub)
        raise RuntimeError('KnotInfo/LinkInfo topology database ingestion failed; inspect topology_registry/TOPOLOGY_DB_INGEST.json')
    summaries=[]
    for topo in topologies:
        summaries.append(run_topology_campaign(
            topo,out/'atlas',config,workbench_root=workbench_root,base_root=base_root,
            alias_maps=aliases,registry_dir=reg,repo_scan=repo_scan))

    campaign_gate=all(x.get('qualification_gate_pass',False) for x in summaries)
    source_gate=True if repo_scan is None else bool(repo_scan['coverage_gate']['pass'])
    release={
        'schema':'PKLSA-HIGH-RES-QUALIFICATION-2','atlas_version':'0.3.0','builder_version':'0.2.0',
        'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'base_root':str(base_root),'workbench_root':str(workbench_root) if workbench_root else None,
        'source_catalog':str(source_catalog or DEFAULT_CATALOG) if workbench_root else None,
        'config':config.to_dict(),'topology_database':db_summary,'campaigns':summaries,
        'source_coverage_gate_pass':source_gate,'campaign_qualification_gate_pass':campaign_gate,'topology_database_gate_pass':topology_db_gate,
        'publication_ready_geometry_layer':bool(source_gate and campaign_gate and topology_db_gate and not (fail_on_unregistered and repo_scan and repo_scan.get('unregistered_review_required'))),
        'unregistered_source_review_required':bool(repo_scan and repo_scan.get('unregistered_review_required')),
        'scientific_boundary':'Geometry qualification and topology cross-checking only; no Euler/Biot-Savart stability claim.',
    }
    write_json(out/'RELEASE.json',release)
    return release


def archive_release(output, archive_dir=None):
    out=Path(output); ad=Path(archive_dir) if archive_dir else out.parent
    ad.mkdir(parents=True,exist_ok=True); zpath=ad/(out.name+'.zip')
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(out.parent))
    sha=sha256_file(zpath); (zpath.with_suffix(zpath.suffix+'.sha256')).write_text(f'{sha}  {zpath.name}\n',encoding='ascii')
    return zpath,sha
