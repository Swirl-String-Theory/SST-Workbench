"""Framework v1.0.10 scientific pipeline. Executed only after frozen protocol verification.
GPU parity is XPU torch operator screening, NEVER framework-native SYCL/C++ parity.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,json,os
from typing import Any
from .gpe_engine import plane_wave_test,convergence_test,reversibility_test,xpu_parity
from .fetch_data import RECORD,digest
import zipfile
from sst_falsifier.gates import GateInputsUnavailable


def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    ledger.record('G0','PASS',metrics={'mode':mode,'framework_version':'1.0.10'},
                  reason='SST framework verified the frozen protocol before invoking pipeline.')
    out=root/'diagnostics';out.mkdir(exist_ok=True)
    state={}
    def gate1():
        data=root/'data'/'external'/'DATA_PROVENANCE.json'
        if not data.is_file():raise GateInputsUnavailable('Missing downloaded research dataset provenance')
        v=json.loads(data.read_text(encoding='utf8'))
        if not v.get('exists'):raise GateInputsUnavailable('Research dataset is not present: run_all.cmd DATA')
        archive=root/'data'/'external'/RECORD['name']
        current_present=archive.is_file()
        checksum_ok=current_present and digest(archive,'md5')==RECORD['md5']
        sha_ok=current_present and digest(archive,'sha256')==v.get('sha256')
        try:
            with zipfile.ZipFile(archive) as z:
                crc_ok=z.testzip() is None and len(z.infolist())>0
        except (OSError,zipfile.BadZipFile):
            crc_ok=False
        verified=bool(v.get('verified') and checksum_ok and sha_ok and crc_ok)
        stat={'verified':verified,'checksum_ok':bool(checksum_ok),'sha256_match':bool(sha_ok),'crc_ok':bool(crc_ok),
              'sha256':digest(archive,'sha256') if current_present else None,'bytes':archive.stat().st_size if current_present else 0,
              'file_count':v.get('file_count'),'doi':RECORD['doi']}
        state['source']=stat
        return {'status':'PASS' if verified else 'FAIL','metrics':stat,
                'authority':'SOURCE_INTEGRITY_ONLY', 'reason':'Published Zenodo MD5 + ZIP CRC; not a wavefunction reference'}
    def gate2():
        a=plane_wave_test(n=32 if mode=='BASIC' else 64, steps=24 if mode=='BASIC' else 96)
        b=reversibility_test()
        state['analytic']={'plane_wave':a,'reversibility':b}
        passed=a['plane_wave_relative_l2']<1e-10 and a['norm_relative_drift']<1e-10 and b['roundtrip_relative_l2']<1e-10 and b['norm_relative_drift']<1e-10
        return {'status':'PASS' if passed else 'FAIL','metrics':{
            'plane_wave_relative_l2':a['plane_wave_relative_l2'],
            'norm_relative_drift':a['norm_relative_drift'],
            'roundtrip_relative_l2':b['roundtrip_relative_l2']},
            'authority':'NUMERICAL_REFERENCE','reason':'Periodic plane-wave exact solution, mass invariance, time reversal'}
    def gate3():
        q=convergence_test(n=24 if mode=='BASIC' else 32)
        state['convergence']=q
        passed=q['min_order']>1.75 and max(q['errors_l2'])<0.1
        return {'status':'PASS' if passed else 'FAIL','metrics':{
            'min_order':q['min_order'],'errors_l2':q['errors_l2'],
            'reference_kind':q['reference_kind']},'authority':'NUMERICAL_DIAGNOSTIC',
            'reason':'Strang splitting dt refinement at fixed final time; numerical surrogate, not physical discovery'}
    def gate6():
        # Deliberate hard check. If XPU unavailable no invented CPU fallback.
        try:
            val=xpu_parity(n=32 if mode=='BASIC' else 64,steps=16 if mode=='BASIC' else 48, full3d=(mode!='BASIC'))
        except (ImportError,ModuleNotFoundError) as e:
            raise GateInputsUnavailable('torch with Intel XPU support missing: '+str(e)) from e
        except RuntimeError as e:
            if 'unavailable' in str(e).lower():
                raise GateInputsUnavailable(str(e)) from e
            raise  # real failed FFT/runtime != absence
        state['gpu']=val
        ok=val['gpu_cpu_relative_l2']<7e-4 and val['gpu_norm_relative_drift']<7e-4
        if 'ring3d' in val:ok=ok and val['ring3d']['gpu_cpu_relative_l2']<7e-4
        return {'status':'PASS' if ok else 'FAIL','metrics':val,'authority':'GPU_SCREENING_ONLY',
                'requested_backend':'pytorch-xpu-fp32','actual_backend':'pytorch-xpu-fp32',
                'reason':'Actual Intel GPU FFT/pointwise GPE solver compared to independent NumPy FP64'}
    ledger.run_evaluators({'G1':gate1,'G2':gate2,'G3':gate3,'G6':gate6})
    # Preserve diagnostics as instance-local files, and return snapshot inside the framework's evidence manifests.
    (out/'SCIENTIFIC_DIAGNOSTICS.json').write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    return {'schema':'SST-BACKEND-MANIFEST-2','gpe_scheme':'strang-split-step-FFT-periodic',
            'python_reference':{'actual_backend':'numpy-fp64','authority':'NUMERICAL_REFERENCE'},
            'gpu':state.get('gpu',{'status':'NOT_AVAILABLE_OR_NOT_EXECUTED','authority':'SCREENING_ONLY'}),
            'dataset':state.get('source',{'status':'UNAVAILABLE'}),
            'status':'DEVELOPMENT_NOT_PHYSICAL_CERTIFICATION',
            'no_pklsa_equivalence_claim':True}
