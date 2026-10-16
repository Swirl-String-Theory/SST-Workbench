"""A061 v0.1.1: scientific gates executed through the real v1.0.7 GateLedger.

Every physical/algorithm gate is independent (requires = []) by preregistration;
framework source-integrity or protocol-integrity errors remain fatal.
"""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from typing import Any
import numpy as np
from a061.science import (sst28_ratio,sst28_omega_scaled,plateau_s,crystal_reconstruction,
                          oscillator_feedback,max_sinusoid_periodogram,monte_carlo_search,load_two_col_csv)
from sst_falsifier.util import write_json,sha256_file


def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    root=Path(root);out=root/(f"{cfg['project']['name']}_{cfg['project']['version']}-outputs")
    pub=json.loads((root/'data/published/measurements.json').read_text(encoding='utf-8'))
    p=json.loads((root/'config/protocol.json').read_text(encoding='utf-8'))
    t=pub['Toscani_2026'];h=pub['Huang_2026']
    backend={'schema':'SST-BACKEND-MANIFEST-2','python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'REFERENCE'},'cpp':{'actual_backend':None,'precision':'float64','authority':'NOT_EXECUTED'}}
    def rec(gid,status,reason,metrics=None,**extra):
        ledger.record(gid,status,reason=reason,metrics=metrics or {},**extra)
    files=[root/'docs/2606.04997v2.pdf',root/'docs/2606.08870v2.pdf',root/'docs/SST28_MATHEMATICAL_EXTRACT.md',root/'data/published/measurements.json',root/'config/protocol.json']
    present=all(x.is_file() for x in files)
    rec('G0','PASS' if present else 'FAIL','Framework protocol verified upstream; source files verified locally.',
        {'source_count':len(files),'present':present,'hashes':{x.name:sha256_file(x) if x.exists() else None for x in files},'framework_version':cfg['project']['framework_version']})
    c=crystal_reconstruction(pub)
    err=abs(c['fractional_offset']-h['fractional_intercrystal_shift'])
    ok=err<0.1e-13 and abs(c['offset_Hz']-560)<10
    rec('G1','PASS' if ok else 'FAIL','Huang published two-crystal shift algebra; stability is not systematic accuracy.',
        {**c,'offset_fractional_residual':err,'instability_coeff_ratio':t['instability_1s']/h['instability_1s']})
    common=0.91
    cancel=common/common-1
    rec('G2','PASS' if cancel==0. else 'FAIL','Universal factor cancellation identity, not SST empirical support.',
        {'common_factor':common,'calculated_differential_shift':cancel,'SST_empirical_validation':False})
    x=np.asarray([0.,.25,.5,1.,2.,3.,8.],dtype=np.float64)
    smooth=sst28_ratio(x);omega=sst28_omega_scaled(x);thin=float(plateau_s([1.],1)[0])
    discrepancy=abs(thin-.9603)
    gate_status='FAIL' if discrepancy>p['kinematic_tolerance'] else 'PASS'
    rec('G3',gate_status,'SST-28 Eq. 23/24 disagree under printed kappa=2*pi*rc*vchar; omega(2rc)=0 does not imply S(2rc)=1.',
        {'smooth_S_rc':float(smooth[3]),'smooth_S_2rc':float(smooth[4]),'omega_scaled_2rc':float(omega[4]),'plateau_S_n1_rc_formula':thin,'printed_plateau_S_n1_rc':0.9603,'plateau_mismatch':discrepancy,'tol':p['kinematic_tolerance']})
    rec('G4','UNRESOLVED','Two crystals do not identify unknown SST clock susceptibility separately from local crystal/temperature shifts.',
        {'crystal_difference_Hz':c['offset_Hz'],'fractional_shift':c['fractional_offset'],'environment_parameters_not_identified':True,'source_evidence':'experimental_summary'})
    # Framework v1.0.7 owns strict native build provenance; no standalone executable can qualify this gate.
    try:
        from sst_falsifier.backends.cpp_pybind import load
        mod,br=load(root,force_build=False,require=True,verbose=False)
        if not hasattr(mod,'a061_swirl_clock'):
            rec('G5','FAIL','Native build exists but lacks A061 scientific kernel.',{'build':br.to_dict()},requested_backend='cpp-pybind',actual_backend=br.actual_backend,authority='CERTIFICATION')
        else:
            q=np.linspace(0,8,257,dtype=np.float64)
            values=np.asarray(mod.a061_swirl_clock(q),dtype=np.float64)
            ref=sst28_ratio(q)
            maxerr=float(np.max(np.abs(values-ref)))
            tolerance=float(p['backend_relative_tolerance'])
            status='PASS' if np.isfinite(values).all() and maxerr<=tolerance else 'FAIL'
            rec('G5',status,'Strict native pybind11 FP64 profile parity via frozen framework C++ build system.',
                {'max_abs_error':maxerr,'tolerance':tolerance,'n_points':len(q),'fingerprint':br.fingerprint_sha256,'native_source_sha256':sha256_file(root/'native/cpp/native.cpp')},
                requested_backend='cpp-pybind',actual_backend=br.actual_backend,authority='CERTIFICATION')
            backend['cpp']={'actual_backend':br.actual_backend,'precision':'float64','authority':'CERTIFICATION','build_fingerprint':br.fingerprint_sha256,'max_abs_error':maxerr}
    except Exception as exc:
        rec('G5','UNRESOLVED','Strict C++17 pybind backend unavailable; no Python fallback can certify C++.',
            {'reason':type(exc).__name__+': '+str(exc)[:900],'needed':'pybind11,compiler,C++17; run BUILD_NATIVE'},requested_backend='cpp-pybind',actual_backend='unavailable',authority='NOT_CERTIFIED')
    for gid in ('G6','G7'):
        rec(gid,'NOT_APPLICABLE','Disabled in CPU profile; optional SYCL/multilibrary lanes not promoted to precision certification.')
    rec('G8','UNRESOLVED','No independently derived SST constitutive map (Th/Yb or crystal-specific), hence no empirical Swirl Clock closure.')
    # G9 recorded DEFERRED by framework after pipeline completes.
    e=oscillator_feedback(seed=p['holdout_seed']); valid=bool(np.isfinite(e).all())
    if valid:
        freq=np.linspace(.001,.45,256)
        power=max_sinusoid_periodogram(np.arange(len(e),dtype=float),e,freq)
        rec('G10','PASS','Instrument-only delayed feedback generates a structured spectrum without SST; synthetic control.',
            {'signal_std':float(np.std(e)),'max_power':float(np.nanmax(power)),'delay_cycles':2,'gain':.38,'evidence_class':'synthetic_control'})
    else:rec('G10','FAIL','Nonfinite instrumental control response.')
    raw=root/'data/raw/center_beat_frequencies.csv'
    if mode in ('FULL','CERTIFY') and raw.is_file():
        try:
            time,beat_khz=load_two_col_csv(raw)
            result=monte_carlo_search(time,1000*beat_khz/t['frequency_Hz_approx'],seed=p['holdout_seed'],n_mc=p['monte_carlo'],n_freq=p['frequency_grid_count'],alpha=p['global_false_positive_rate'])
            write_json(out/'A061_EXPLORATORY_TIME_SERIES.json',{'data_sha256':sha256_file(raw),'result':result,'claim':'METHOD_ONLY_NO_SST_EVIDENCE'})
            rec('G11','PASS','Raw source periodogram computed with global trials bootstrap; provisional until clock-servo/noise model validated.',
                {**result,'raw_sha256':sha256_file(raw),'SST_empirical_validation':False},actual_backend='python-numpy-fp64',authority='EXPLORATORY')
        except Exception as exc:rec('G11','FAIL','Raw source present but invalid format or computation.',{'error':type(exc).__name__+': '+str(exc)})
    else:
        rec('G11','UNRESOLVED','Raw Toscani cadence required and only evaluated in FULL/CERTIFY; summary statistics cannot replace it.',
            {'mode':mode,'raw_exists':raw.exists(),'fetch_command':'run_all.cmd FETCH'})
    predicted=root/'data/raw/sst_differential_prediction.json'
    rec('G12','UNRESOLVED','SST species-resolved differential transfer coefficient not independently precommitted; local payload cannot be assumed predictive.',
        {'unsealed_candidate_sha256':sha256_file(predicted) if predicted.is_file() else None})
    rec('G13','UNRESOLVED','Two independent clock experiments do not establish a synchronous shared-phase spectral replication.',
        {'toscani_lab':True,'huang_lab':True,'synchronous_time_base':False,'independence_units':2})
    syn=[]
    for f in sorted((root/'data/synthetic').glob('anon*.csv')):
        try:
            tt,yy=load_two_col_csv(f)
            rs=monte_carlo_search(tt,yy,n_mc=64,n_freq=120,seed=p['holdout_seed'])
            syn.append({'anonymous_id':f.stem,'flagged':rs['global_peak_above_threshold'],'global_threshold':rs['global_95pct_threshold']})
        except Exception as ex:syn.append({'anonymous_id':f.stem,'error':type(ex).__name__+': '+str(ex)})
    write_json(out/'A061_ANONYMOUS_SYNTHETIC_CONTROLS.json',{'evidence_class':'synthetic_control','no_physical_inference':True,'cases':syn})
    from sst_falsifier.report import latex_escape
    (out/'report').mkdir(parents=True,exist_ok=True)
    rows=[r'\begin{longtable}{p{.10\linewidth}p{.20\linewidth}p{.60\linewidth}}',r'\toprule',r'Gate & Status & Meaning \\',r'\midrule',r'\endhead']
    for g in ledger.records:
        rows.append(f"{latex_escape(g.gate_id)} & {latex_escape(g.status)} & {latex_escape(g.reason[:125])} \\\\")
    rows += [r'G9 & DEFERRED & Separate reveal-only phase; all scientific conclusions remain blind. \\',r'\bottomrule',r'\end{longtable}']
    (out/'report/A061_GATES_SUMMARY.tex').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    return backend
