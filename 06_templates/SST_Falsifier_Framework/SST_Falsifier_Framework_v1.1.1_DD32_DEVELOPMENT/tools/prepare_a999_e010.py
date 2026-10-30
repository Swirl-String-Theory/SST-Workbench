"""Create-only A999 complete E010 integration control using a real adapter export.
Do not execute FREEZE/FULL until the generated scientific contracts are inspected.
"""
from __future__ import annotations
import argparse, json, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.new_falsifier import generate
from sst_falsifier.pklsa_integration import _load_bridge,resolve_paths
from sst_falsifier.report import assert_report
from sst_falsifier.science_contract import assert_science_contract
from sst_falsifier.source_registry import assert_source_contract
from sst_falsifier.gates import assert_gate_plan


def science(record,manifest,precision):
    return {
      'schema':'SST-SCIENCE-CONTRACT-2',
      'research_question':'Can the frozen E010 source geometry yield matching static regularized Biot-Savart results on Python and one independently executed C++ or GPU backend?',
      'objective':'Verify integration, source integrity, backend execution, parity, standardized gates, report and immutable outputs; no physical dynamics.',
      'null_hypothesis':'Less than two implementation categories execute on identical input, or any executed implementation exceeds the declared numerical tolerance.',
      'alternative_hypothesis':'Python and at least one other implementation execute on identical pinned data with all pairwise errors below the preregistered thresholds.',
      'assumptions':['One historical E010 record, one continuous closed filament, ordered original vertices; no independent experimental sources',
         'Periodic-midpoint regularized Biot-Savart is a numerical control, not an Euler evolution solver.',
         'The dataset record and export-manifest SHA-256 are fixed, without resampling or SI calibration.'],
      'symbols':[{'symbol':'Gamma','meaning':'circulation numerical unit','si_unit':'numerical U_L^2/U_T','dimensions':'L^2 T^-1'},
                 {'symbol':'a','meaning':'smoothing core in native coordinates','si_unit':'numerical U_L','dimensions':'L'},
                 {'symbol':'v','meaning':'induced velocity in native numerical units','si_unit':'numerical U_L/U_T','dimensions':'L T^-1'}],
      'equations':[{'id':'E1','purpose':'periodic midpoint Biot-Savart sum','latex':r'\mathbf{v}(\mathbf{q})=\frac{\Gamma}{4\pi}\sum_j\frac{\Delta\mathbf{l}_j\times(\mathbf{q}-\mathbf{m}_j)}{(\|\mathbf{q}-\mathbf{m}_j\|^2+a^2)^{3/2}}',
            'inputs':['Gamma','vertices','query positions','a'],'outputs':['velocity vector'],'dimensional_check':'Circulation L2/T times kernel 1/L equals L/T'},
           {'id':'E2','purpose':'relative L2 parity error','latex':r'\epsilon_b=\frac{\|\mathbf{V}_b-\mathbf{V}_{\mathrm{Py64}}\|_2}{\|\mathbf{V}_{\mathrm{Py64}}\|_2}',
            'inputs':['Python reference','C++ or GPU observable'],'outputs':['relative error'],'dimensional_check':'Dimensionless ratio of matching numerical velocity norms'}],
      'observables':[{'id':'O1','definition':'Eight velocity vectors, 24 scalars in fixed query order','equation_refs':['E1'],'unit':'numerical U_L/U_T'},
                     {'id':'O2','definition':'Relative cross-backend L2 error','equation_refs':['E2'],'unit':'1'}],
      'steps':[{'id':'S1','operation':'Validate E010 export, record, finite shape and registered manifest digest '+manifest,'formula_refs':['E1'],'gate':'G1'},
               {'id':'S2','operation':'Compute Python float64 reference at eight fixed query positions','formula_refs':['E1'],'gate':'G2'},
               {'id':'S3','operation':'Execute independently compiled C++ and/or selected GPU at the identical input hash; measure parity against Python','formula_refs':['E1','E2'],'gate':'G10'}],
      'falsification_criteria':[{'id':'F1','criterion':'Python and >=1 other executed backend required; C++ relative L2 < 1e-10 and GPU relative L2 < '+('1e-8' if precision=='dd32' else '1e-4'),'conclusion_if_met':'NUMERICAL_INTEGRATION_PASS_ONLY'},
                                {'id':'F2','criterion':'If an independently executed backend exceeds its fixed tolerance, G10=FAIL','conclusion_if_met':'NUMERICAL_INTEGRATION_FAIL_ONLY'}],
      'edge_cases':['Zero reference norm invalid','Nonfinite source or output invalid','GPU/device unavailable is UNRESOLVED','No SI scale or dynamical clock'],
      'predictions':['Identical input hash across executed backends; observable shape (8,3); numerical agreement only'],
      'gpu_precision_policy':precision,
      'dataset_pin':{'record':record,'manifest_sha256':manifest,'gamma':1.0,'core_fraction':0.04,'atlas_version':'E010-v0.4.0','adapter_version':'v0.1.0'}
    }

def make(dataset,out,record,provider,precision='dd32'):
    dataset=Path(dataset).expanduser().resolve();out=Path(out).expanduser().resolve()
    if out.exists():raise FileExistsError('Create-only destination exists: '+str(out))
    paths=resolve_paths(ROOT,{})
    bridge=_load_bridge(paths['adapter'])
    ds=bridge.ConsumerDataset(dataset)
    if ds.verification['status']!='PASS_DATASET_INTEGRITY_ONLY':raise RuntimeError('Unverified E010 export')
    if ds.list_ids()!=[record]:raise ValueError('One exact preselected record is required')
    parts=ds.load(record)
    if len(parts)!=1:raise ValueError('This control requires a single filament')
    generate('A999','e010_backend_integrity',out,version='v0.1.0',profile='gpu')
    try:
        target=out/'input'/'e010_export';target.parent.mkdir(exist_ok=True)
        shutil.copytree(dataset,target)
        pin={'schema':'SST-A999-E010-INPUT-PIN-1','record':record,'manifest_sha256':ds.verification['manifest_sha256'],
            'gamma':1.0,'core_fraction':.04,'atlas':'E010-v0.4.0','adapter':'v0.1.0'}
        (out/'input'/'CONTROL_PIN.json').write_text(json.dumps(pin,indent=2,sort_keys=True)+'\n',encoding='utf8')
        template=ROOT/'integration'/'a999_control'
        shutil.copyfile(template/'backend_matrix.py',out/'experiment'/'backend_matrix.py')
        shutil.copyfile(template/'pipeline.py',out/'experiment'/'pipeline.py')
        shutil.copyfile(template/'gate_plan.json',out/'gate_plan.json')
        report_text=(template/'report.tex').read_text(encoding='utf-8')
        report_text=report_text.replace('@@GPU_PRECISION_TEXT@@','DD32 (two-component binary32 arithmetic)' if precision=='dd32' else 'FP32').replace('@@GPU_TOL_LATEX@@','10^{-8}' if precision=='dd32' else '10^{-4}')
        (out/'report'/'FALSIFIER_REPORT.tex').write_text(report_text,encoding='utf-8')
        (out/'science_contract.json').write_text(json.dumps(science(record,pin['manifest_sha256'],precision),indent=2)+'\n',encoding='utf8')
        source={'schema':'SST-SOURCE-CONTRACT-2','independent_unit':'single E010 historical geometry record; no independent physical replication',
           'sources':[{'source_id':'E010_CONTROL','catalog_id':'E010','version':'v0.4.0','relative_path':None,
             'override_path':str(target),'role':'software_reference','independence_family':'E010_historical_single_record',
             'evidence_class':'simulation','provenance_family':'E010_historical_v031'}],
           'parser_contract':'PKLSA Universal Atlas Adapter v0.1.0 ConsumerDataset with exact SHA-256 readback',
           'translator_contract':'Native numerical coordinates only; no SI calibration, no resampling',
           'allow_no_external_sources':False,
           'replication_policy':{'require_explicit_evidence_class':True,'min_independent_groups':2,'synthetic_controls_may_close_cross_source':False}}
        (out/'source_contract.json').write_text(json.dumps(source,indent=2)+'\n',encoding='utf8')
        cfg=out/'falsifier.toml';c=cfg.read_text();
        c=c.replace('provider = "intel"','provider = "'+provider+'"')
        c=c.replace('precision = "dd32"','precision = "'+precision+'"')
        c=c.replace('minimum_science_backends = 2','minimum_science_backends = 2\nnumeric_tolerance_cpp = 1e-10\nnumeric_tolerance_gpu = '+('1e-8' if precision=='dd32' else '1e-4'))
        cfg.write_text(c)
        # The source and report are fully registered before FREEZE. No old source is modified.
        assert_science_contract(out/'science_contract.json')
        assert_source_contract(out/'source_contract.json')
        assert_gate_plan(out/'gate_plan.json')
        assert_report(out/'report'/'FALSIFIER_REPORT.tex',require_complete=True)
        from sst_falsifier.auto_backend_matrix import assess_numeric_control
        print(json.dumps({'status':'READY_FOR_LOCAL_FREEZE','instance':str(out),'record':record,'manifest_sha256':pin['manifest_sha256'],
             'gpu_provider':provider,'gpu_precision':precision,'run_order':['run_all.cmd FREEZE','run_all.cmd FULL'],
             'scope':'NUMERICAL_INTEGRATION_CONTROL_ONLY'},indent=2))
    except BaseException:
        shutil.rmtree(out)
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--record',default='CAR_0081c5a310c30e50')
    parser.add_argument('--gpu',choices=('intel','cuda'),default='intel')
    parser.add_argument('--precision',choices=('dd32','float32'),default='dd32')
    a=parser.parse_args()
    make(a.dataset,a.output,a.record,a.gpu,a.precision)
