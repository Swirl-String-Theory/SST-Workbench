#!/usr/bin/env python3
"""Create a source-complete v1.1.0 (or RC2) instance using the user's local framework.

This distribution is a CREATE-ONLY instance builder; it never mutates an
existing framework, existing project family or an existing falsifier release.
The generated instance embeds its own framework runtime by official generator.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,re,shutil,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
OVERLAY=HERE/'overlay'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load_generator(framework):
    gen=framework/'tools'/'new_falsifier.py'
    if not gen.is_file() or not (framework/'instance_template').is_dir():
        raise FileNotFoundError('Not a v1.1.0 framework source tree: '+str(framework))
    spec=importlib.util.spec_from_file_location('framework_v110_generator',gen)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.generate

def verify_dataset(dataset,record_ids):
    if not dataset:return None
    if not record_ids:raise ValueError('--records required when --dataset is specified')
    from pklsa_bridge import ConsumerDataset
    ds=ConsumerDataset(Path(dataset))
    if ds.verification.get('status')!='PASS_DATASET_INTEGRITY_ONLY':
        raise RuntimeError('E010 export integrity check failed')
    got=sorted(ds.list_ids())
    if got!=sorted(record_ids):
        raise ValueError('Provided --records must exactly equal export list; '+str(got))
    for rec in record_ids:ds.load(rec) # force original/raw+float64 readback before creating anything
    return {'atlas':'E010-v0.4.0','adapter':'v0.1.0',
        'manifest_sha256':ds.verification['manifest_sha256'],
        'record_ids':record_ids,'geometry_is_dynamic_evidence':False,
        'consumer_export_scope':'local hash-verified immutable export'}

def build(args):
    framework=Path(args.framework).resolve()
    if not re.fullmatch(r'A[0-9]{3,4}',args.catalog_id):
        raise ValueError('catalog ID must be an existing user-approved new A### or A####; do not invent')
    if args.version!='v0.1.0':raise ValueError('this release only creates v0.1.0')
    dst=Path(args.destination).resolve()
    if dst.exists():raise FileExistsError('Destination already exists (create-only): '+str(dst))
    # Verify inputs and official generator *before* creating dst.
    generate=load_generator(framework)
    pin=verify_dataset(args.dataset,args.records)
    generate(args.catalog_id,'finite_core_spectral_abc',dst,version=args.version,profile=args.profile)
    try:
        for p in sorted(OVERLAY.rglob('*')):
            if not p.is_file():continue
            rel=p.relative_to(OVERLAY)
            target=dst/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,target)
        # Source pin has no unrestricted portable library roots; all source snapshots
        # and dataset exports live in the generated instance, and are immutable after FREEZE.
        sources=[]
        if pin:
            export=dst/'input'/'e010_export'
            src=Path(args.dataset).resolve()
            if src.is_dir():shutil.copytree(src,export)
            else:
                raise ValueError('PKLSA consumer export must be a directory (not the raw 1 GiB atlas)')
            (dst/'input'/'C_PKLSA_PIN.json').write_text(json.dumps(pin,indent=2,sort_keys=True)+'\n',encoding='utf8')
            sources.append({'source_id':'E010_ADAPTER_EXPORT',
              'catalog_id':'E010','version':'v0.4.0','relative_path':None,'override_path':str(export),
              'role':'software_reference','independence_family':'E010_PINNED_EXPORT_ONLY',
              'evidence_class':'simulation','provenance_family':'PKLSA_original_source_group'})
        source={'schema':'SST-SOURCE-CONTRACT-2',
                'independent_unit':'one analytic ring operator; E010 data are geometry carriers, not independent physical experiments',
                'sources':sources,'allow_no_external_sources':not bool(sources),
                'parser_contract':'PKLSA ConsumerDataset v0.1.0 on E010-v0.4.0; exact SHA256 readback',
                'translator_contract':'original coordinate arrays only, no resampling or SI calibration',
                'replication_policy':{'min_independent_groups':2,'synthetic_controls_may_close_cross_source':False}}
        (dst/'source_contract.json').write_text(json.dumps(source,indent=2,sort_keys=True)+'\n',encoding='utf8')
        tex=dst/'report'/'FALSIFIER_REPORT.tex'
        s=tex.read_text(encoding='utf8')
        s=s.replace('@@CATALOG-ID@@',args.catalog_id).replace('@@VERSION@@',args.version)
        tex.write_text(s,encoding='utf8',newline='\n')
        # Add explicit two-of-three numeric kernel tolerance, independent of
        # candidate physics. Use native C++ if present, GPU only as an optional category.
        cfg=dst/'falsifier.toml';t=cfg.read_text(encoding='utf8')
        if 'numeric_tolerance_cpp' not in t:t=t.replace('minimum_science_backends = 2',
            'minimum_science_backends = 2\nnumeric_tolerance_cpp = 1e-10\nnumeric_tolerance_gpu = 1e-4')
        cfg.write_text(t,encoding='utf8',newline='\n')
        # Package scientific native source at the path expected by the *original* module.
        assert (dst/'experiment'/'cpp'/'native.cpp').is_file()
        # Ensure no phantom passing metadata or implicit backend override.
        info={'schema':'ABC-SPECTRAL-SCALE-PACKAGE-1','catalog_id':args.catalog_id,
             'version':args.version,'framework':'v1.1.0 (source snapshot via official generator)',
             'framework_source_version':'v1.1.0/RC2',
             'model_source':'finite_core_spectral-v0.1.2.4 (full vendored source)',
             'pklsa_export_pinned':bool(pin),
             'scope':'A/B independent spectral follow-up + PKLSA C pilot; no physical claim',
             'required_execution_backends':2}
        (dst/'project.json').write_text(json.dumps(info,indent=2,sort_keys=True)+'\n',encoding='utf8')
        # Verify frozen scientific interfaces using generator source (not global install).
        sys.path.insert(0,str(framework))
        from sst_falsifier.science_contract import assert_science_contract
        from sst_falsifier.source_registry import assert_source_contract
        from sst_falsifier.gates import assert_gate_plan
        from sst_falsifier.report import assert_report
        assert_science_contract(dst/'science_contract.json')
        assert_source_contract(dst/'source_contract.json')
        assert_gate_plan(dst/'gate_plan.json')
        assert_report(dst/'report'/'FALSIFIER_REPORT.tex',require_complete=True)
        # Source inventory only. Frozen run outputs are independently managed by framework.
        inventory={p.relative_to(dst).as_posix():sha(p) for p in sorted((dst/'experiment').rglob('*')) if p.is_file()}
        (dst/'ABC_SCIENCE_SOURCES_SHA256.json').write_text(json.dumps(inventory,indent=2,sort_keys=True)+'\n',encoding='utf8')
        print(json.dumps({'status':'SCIENCE_READY_FOR_MANUAL_REVIEW_AND_FREEZE',
          'created':str(dst),'copied_source_files':len(inventory),
          'pklsa':bool(pin),'commands':['run_all.cmd BACKEND_PREFLIGHT',
          'run_all.cmd ATLAS_VERIFY (only with E010_ATLAS configured)',
          'run_all.cmd FREEZE','run_all.cmd BASIC','run_all.cmd FULL'],
          'warning':'No A, B, or C physical conclusion is currently certified.'},indent=2))
        return dst
    except BaseException:
        # Roll back *only* the newly created destination, never a user pre-existing folder.
        shutil.rmtree(dst)
        raise

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--framework',required=True,help='Local SST_Falsifier_Framework_v1.1.0_RC2 or v1.1.0 folder')
    ap.add_argument('--catalog-id',required=True,help='New available A### catalog ID approved by current SST-Workbench index')
    ap.add_argument('--destination',required=True,help='Create-only output version directory')
    ap.add_argument('--profile',choices=['cpu','gpu'],default='gpu')
    ap.add_argument('--version',default='v0.1.0')
    ap.add_argument('--dataset',help='Optional PKLSA verified ConsumerDataset EXPORT directory (not main atlas ZIP)')
    ap.add_argument('--records',nargs='*',default=[],help='All exact IDs in the supplied export; no implicit selection')
    args=ap.parse_args()
    build(args)
