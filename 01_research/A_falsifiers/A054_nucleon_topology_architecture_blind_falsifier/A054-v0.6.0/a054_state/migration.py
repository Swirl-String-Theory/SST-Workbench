"""Bounded admission runner using the existing qualified scientific renderer."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys

from .admission import read, digest, require, validate_manifest

PREFIX='A054_E013_State_Selection_Provider_Convergence_Falsifier'
VERSION='v0.6.0'


def qualified_framework(root):
    wb=root.parents[3]
    pin=read(root/'FRAMEWORK_SOURCE_PIN.json')
    framework=wb/pin['selected_source']
    explicit=os.environ.get('SST_FALSIFIER_FRAMEWORK_ROOT')
    require(not explicit or Path(explicit).resolve()==framework.resolve(),'framework override conflicts with qualified source')
    require(Path((root/'.sst_framework_root').read_text(encoding='utf-8').strip()).resolve()==framework.resolve(),'framework locator mismatch')
    require(len(pin['verification'])==112,'incomplete framework manifest')
    for row in pin['verification']:
        require(digest(framework/row['path'])==row['sha256'],'framework integrity mismatch: '+row['path'])
    sys.path.insert(0,str(root))
    from framework_bootstrap import load_framework
    require(load_framework()==framework.resolve(),'qualified framework import mismatch')
    return framework


def verify_protocol(root):
    protocol=read(root/'preregistration/MIGRATION_PROTOCOL.json')
    rows=protocol['files']
    actual={}
    for row in rows:
        p=(root/row['path']).resolve()
        require(p.is_relative_to(root),'protocol path escape')
        actual[row['path']]=digest(p)
        require(actual[row['path']]==row['sha256'],'migration protocol changed: '+row['path'])
    bundle=hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    require(bundle==protocol['bundle_sha256'],'migration protocol bundle mismatch')
    return protocol


def adapter_tex(out, data):
    from sst_falsifier.report import latex_escape as esc, latex_breakable as wrap
    lines=[r'\subsection*{Controlled migration scope}',
      r'This run only verifies source admission and reloads exact geometry. State selection, native parity, Hessian, ringdown and reveal were not executed. A software PASS is not scientific certification.',
      r'\begin{longtable}{p{0.24\linewidth}p{0.68\linewidth}}\toprule Axis & Status\\\midrule']
    for k,v in data['gate_axes'].items():lines.append(wrap(k)+' & '+wrap(v)+r' \\')
    lines += [r'\bottomrule\end{longtable}',r'\subsection*{Exact admitted carrier reloads}',
      r'\begin{longtable}{p{0.10\linewidth}p{0.24\linewidth}p{0.32\linewidth}r}\toprule Topology & Provider & Static seed & Points\\\midrule']
    for row in data['geometry']:
        lines.append(' & '.join([esc(row['topology_id']),esc(row['provider_group']),wrap(row['static_seed_id']),str(row['points'])])+r' \\')
    lines += [r'\bottomrule\end{longtable}',
      r'\begin{figure}[htbp]\centering\includegraphics[width=0.85\linewidth]{figures/source_points.pdf}\caption{Actual source-native point counts reloaded in this admission smoke. Counts are not a convergence or physical-quality score.}\end{figure}',
      r'\subsection*{Unresolved scientific evidence}',
      r'Each BASIC topology has one selected provider. Independent provider convergence cannot close, including L2a1. No stationary endpoint, converged Hessian, ringdown or state-selected handoff was computed. Existing scientific thresholds remain unchanged.']
    (out/'report/AUTO_MIGRATION_AXES.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def run(root):
    root=Path(root).resolve()
    wb=root.parents[3]
    framework=qualified_framework(root)
    protocol=verify_protocol(root)
    require(not os.environ.get('SST_WORKBENCH_ROOT') or Path(os.environ['SST_WORKBENCH_ROOT']).resolve()==wb,'workbench override mismatch')
    pins=read(root/'admission/RUNTIME_PINS.json')
    manifest=Path(os.environ.get('SST_CROSS_CARRIER_MANIFEST',str(root/'admission/CROSS_CARRIER_MANIFEST.json')))
    admitted=validate_manifest(manifest,wb,pins)
    binding=read(root/'admission/MEMBER_BINDING.json')
    require(binding['manifest_sha256']==digest(manifest),'member manifest mismatch')
    require(binding['member_contract_sha256']==digest(root/'cross_falsifier_contract.json'),'member selection changed')
    from .commitment import compute_implementation_bundle, expected_commitment
    require(compute_implementation_bundle(root)[0]==expected_commitment(root),'implementation commitment mismatch')
    from sst_falsifier.gates import GateLedger,load_gate_plan
    from sst_falsifier.output_policy import instance_lock,reserve_blind_output
    from sst_falsifier.report import assert_report,write_auto_science_tex,write_auto_results_tex,publish_instance_report
    from sst_falsifier.outputs import make_science_evidence_manifest,verify_science_evidence_manifest,make_output_manifest,verify_output_manifest,deterministic_zip
    from sst_falsifier.source_registry import assert_source_contract,resolve_source_contract
    from sst_falsifier.util import write_json
    from .pklsa import _load_manifest_geometry
    import numpy as np
    source_contract=assert_source_contract(root/'source_contract.json')
    sources=resolve_source_contract(root/'source_contract.json',root=wb)
    for expected,actual in zip(source_contract['sources'],sources['sources']):
        require(actual['exists'] and actual.get('sha256')==expected['raw_sha256'],'scientific report source does not resolve to admitted bytes')
    cfg={'project':{'name':PREFIX,'version':VERSION}}
    out=root/f'{PREFIX}_{VERSION}_outputs'
    with instance_lock(root):
        rid,previous=reserve_blind_output(root,out,cfg,'ADMISSION_SMOKE')
        try:
            ledger=GateLedger(load_gate_plan(root/'gate_plan.json'))
            ledger.record('G0','PASS',reason='112 qualified framework files and public scoped migration protocol verified; not a complete physical blind FREEZE.',metrics={'scope':'ADMISSION_SMOKE','framework_files':112})
            geometry=[]
            for row in admitted['manifest']['carriers']:
                comps,source,gh=_load_manifest_geometry(row,admitted['loader'],wb)
                require(all(np.isfinite(c).all() for c in comps),'nonfinite source geometry')
                geometry.append({k:row[k] for k in ['topology_id','provider_group','static_seed_id','carrier_id','raw_sha256','geometry_sha256']}|
                    {'source_path':str(source),'verified_geometry_sha256':gh,'points':sum(len(c) for c in comps),'component_count':len(comps)})
            ledger.record('G1','PASS',reason='Fresh E013 selector binding; exact current E011 joins, raw hashes and parsed geometry hashes verified.',metrics={'admitted_carriers':len(geometry),'manifest_sha256':digest(manifest),'provider_counts':admitted['provider_counts']})
            # Enabled but unexecuted evaluators remain explicitly unexecuted and unresolved.
            for gid,definition in ledger.defs.items():
                if gid in {'G0','G1','G9'}:continue
                if definition.enabled:
                    ledger.record(gid,'UNRESOLVED',execution_status='NOT_EXECUTED',reason='Registered scientific evaluator not executed in the bounded admission lane; no scientific result is asserted.')
                else:
                    ledger.record(gid,'NOT_APPLICABLE',reason='Disabled by registered gate plan.')
            ledger.record('G9','DEFERRED',reason='Reveal is outside the authorized admission-smoke scope.')
            ledger.write(out/'GATE_LEDGER.json')
            write_json(out/'GEOMETRY_RELOADS.json',geometry)
            axes={'migration_gate':'PASS_SOURCE_AND_ADAPTER','execution_gate':'PASS_BOUNDED_ADMISSION_SMOKE','scientific_gate':'NOT_RUN','scientific_status_promoted':False}
            write_json(out/'GATE_AXES.json',axes)
            data={'run_id':rid,'gate_axes':axes,'gates':read(out/'GATE_LEDGER.json')['records'],'geometry':geometry,
                  'provider_counts':admitted['provider_counts'],'cross_provider_science_ready':admitted['cross_provider_science_ready']}
            write_json(out/'REPORT_DATA.json',data)
            env={'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'framework_path':str(framework),'source_manifest_sha256':digest(root/'FRAMEWORK_SOURCE_PIN.json')}
            write_json(out/'ENVIRONMENT_PUBLIC.json',env)
            write_json(out/'BACKEND_MANIFEST.json',{'schema':'SST-BACKEND-MANIFEST-2','actual_backend':'Python/NumPy FP64 source parsing','authority':'SOURCE_ADMISSION_ONLY','native_executed':False,'gpu_used':False,'physical_qualification':'NOT_RUN'})
            write_json(out/'SOURCE_MANIFEST.json',sources)
            write_json(out/'RUN_SUMMARY.json',{'schema':'SST-RUN-SUMMARY-2','run_id':rid,'mode':'ADMISSION_SMOKE','revealed':False,
              'protocol_bundle_sha256':protocol['bundle_sha256'],'gate_ledger_sha256':ledger.to_dict()['ledger_sha256'],**axes})
            report=out/'report';report.mkdir()
            assert_report(root/'report/FALSIFIER_REPORT.tex',require_complete=True)
            shutil.copy2(root/'report/FALSIFIER_REPORT.tex',report/'FALSIFIER_REPORT.tex')
            write_auto_science_tex(root,report/'AUTO_SCIENCE_CONTRACT.tex')
            make_science_evidence_manifest(out,out/'SCIENCE_EVIDENCE_MANIFEST.json')
            write_auto_results_tex(root,out,report/'AUTO_RESULTS.tex')
            adapter_tex(out,data)
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            (report/'figures').mkdir()
            fig,ax=plt.subplots(figsize=(7,2.6),layout='constrained')
            ax.bar([r['topology_id'] for r in geometry],[r['points'] for r in geometry])
            ax.set(xlabel='Selected topology',ylabel='Reloaded source points',title='Bounded geometry admission; no state selection')
            fig.savefig(report/'figures/source_points.pdf');plt.close(fig)
            pdf=root.parent/f'{PREFIX}_{VERSION}__{rid}_FALSIFIER_REPORT.pdf'
            rendered=publish_instance_report(root,report/'FALSIFIER_REPORT.tex',destination=pdf,strict=True,engine='pdflatex')
            shutil.copy2(pdf,report/'FALSIFIER_REPORT.pdf')
            write_json(out/'REPORT_RENDER_BLIND.json',rendered)
            require(verify_science_evidence_manifest(out,out/'SCIENCE_EVIDENCE_MANIFEST.json')[0],'science evidence changed during rendering')
            make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
            require(verify_output_manifest(out,out/'OUTPUT_MANIFEST.json')[0],'output manifest mismatch')
            archive=root.parent/f'{PREFIX}_{VERSION}_outputs__{rid}.zip'
            packed=deterministic_zip(out,archive)
            with archive.with_suffix('.zip.sha256').open('x',encoding='ascii') as stream:stream.write(packed['sha256']+'  '+archive.name+'\n')
            record={'schema':'SST-REPORT-OUTPUT-PUBLICATION-1','version':VERSION,'run_id':rid,'output_prefix':PREFIX,'output_root':str(out),
              'report_pdf':str(pdf),'report_sha256':digest(pdf),'archive':packed,'gate_axes':axes,'report_contract':'PASS','packaging_contract':'PASS',
              'ledger_sha256':digest(out/'GATE_LEDGER.json'),'archived_previous':str(previous) if previous else None,'published_utc':datetime.now(timezone.utc).isoformat()}
            with (root/'PUBLICATIONS.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(record)+'\n')
            sys.path.insert(0,str(wb/'07_scripts/sst_migration'))
            from preflight import atomic
            atomic(root/'LATEST_RUN.json',record)
            return record
        except BaseException as error:
            write_json(out/'RUN_ERROR.json',{'run_id':rid,'error':str(error),'scientific_status_promoted':False})
            raise
