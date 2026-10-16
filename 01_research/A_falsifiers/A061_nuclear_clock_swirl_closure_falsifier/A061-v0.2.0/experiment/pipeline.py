"""A061 v0.2.0: scientific gates executed through the real v1.0.7 GateLedger.

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
from a061.canon_v020 import canon_factor,legacy_factor,action_phase,spectro_gap,lock_window,pinning_energy,pinning_stationary_minima,phase_jump_countermodel,common_ratio,C_SI,V_SWIRL,H_SI


def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    root=Path(root);out=root/(f"{cfg['project']['name']}_{cfg['project']['version']}-outputs")
    pub=json.loads((root/'data/published/measurements.json').read_text(encoding='utf-8'))
    p=json.loads((root/'config/protocol.json').read_text(encoding='utf-8'))
    t=pub['Toscani_2026'];h=pub['Huang_2026']
    backend={'schema':'SST-BACKEND-MANIFEST-2','python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'REFERENCE'},'cpp':{'actual_backend':None,'precision':'float64','authority':'NOT_EXECUTED'}}
    def rec(gid,status,reason,metrics=None,**extra):
        ledger.record(gid,status,reason=reason,metrics=metrics or {},**extra)
    files=[root/'docs/2606.04997v2.pdf',root/'docs/2606.08870v2.pdf',root/'docs/SST28_MATHEMATICAL_EXTRACT.md',root/'data/published/measurements.json',root/'config/protocol.json',root/'docs/CANON_v0.8.36_EXTRACT.md',root/'docs/Z6_BENCHMARK_SOURCE_NOTES.md',root/'docs/2511.16065v1.pdf',root/'docs/41563_2026_2516_MOESM1_ESM.pdf']
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
        if not hasattr(mod,'a061_swirl_clock') or not hasattr(mod,'a061_canon_clock'):
            rec('G5','FAIL','Native build exists but lacks A061 scientific kernel.',{'build':br.to_dict()},requested_backend='cpp-pybind',actual_backend=br.actual_backend,authority='CERTIFICATION')
        else:
            q=np.linspace(0,8,257,dtype=np.float64)
            values=np.asarray(mod.a061_swirl_clock(q),dtype=np.float64)
            ref=sst28_ratio(q)
            maxerr=float(np.max(np.abs(values-ref)))
            vc=np.linspace(-.99*C_SI,.99*C_SI,257,dtype=np.float64)
            cpp_canon=np.asarray(mod.a061_canon_clock(vc),dtype=np.float64)
            canonerr=float(np.max(np.abs(cpp_canon-canon_factor(vc))))
            tolerance=float(p['backend_relative_tolerance'])
            status='PASS' if np.isfinite(values).all() and maxerr<=tolerance and canonerr<=tolerance else 'FAIL'
            rec('G5',status,'Strict native pybind11 FP64 profile parity via frozen framework C++ build system.',
                {'max_abs_error':maxerr,'canonical_max_abs_error':canonerr,'tolerance':tolerance,'n_points':len(q),'fingerprint':br.fingerprint_sha256,'native_source_sha256':sha256_file(root/'native/cpp/native.cpp')},
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
    # New v0.2.0 canonical gates are independent mathematical/source qualifications.
    velocity=500000.0
    canonical=float(canon_factor(velocity)); historical=float(legacy_factor(velocity))
    z=float(canon_factor(0.0))
    low_approx=1-0.5*(velocity/C_SI)**2
    ok=(z==1. and 0<canonical<1 and 0<historical<1 and abs(canonical-low_approx)<5e-12 and abs(canonical-historical)>1e-4)
    rec('G14','PASS' if ok else 'FAIL','Canonical c-normalized reduction checked separately from historical SST28 normalization; no physical equivalence assumed.',
        {'speed_m_s':velocity,'canon':canonical,'sst28_legacy':historical,'small_speed_expansion':low_approx,'source':'SST_CANON-v0.8.36 eq94'})
    q=np.array([0.,.01,.1,1.,10.,1e5])
    rel,factor=action_phase(q,omega0=1.)
    err=float(np.max(np.abs(rel-factor)));large=float(factor[-1])
    rec('G15','PASS' if err<=1e-14 and factor[0]==1 and large<1.1e-5 and np.all(np.diff(factor)<0) else 'FAIL',
        'Mass-shell action-phase identity and limits, conditional on canonical action-phase assumptions.',
        {'max_error':err,'large_p_ratio':large,'zero_p':float(factor[0]),'evidence_class':'mathematical_control'})
    freq=h['nu_S1_Hz'];gap=float(spectro_gap(freq));back=gap/H_SI
    rec('G16','PASS' if abs(back-freq)/freq<1e-14 else 'FAIL',
        'E=h nu dimensional spectroscopy reconstruction; no SST species susceptibility supplied.',
        {'nu_Hz':freq,'transition_energy_J':gap,'roundtrip_rel_error':abs(back-freq)/freq,'status':'mathematical_control'})
    close=lock_window(100.3,100.,.5);far=lock_window(102.,100.,.5)
    rec('G17','PASS' if close and not far else 'FAIL',
        'Canonical Q.3 phase-locking interval, research-track driven-oscillator control; not an internal quantum gap.',
        {'inside_interval':close,'outside_interval':far,'coupling_in_angular_frequency_units_s_minus_1':.5})
    summaries=[];success=True
    for kval in p['zq_test_values']:
        minima=pinning_stationary_minima(kval)
        err_q=float(np.max(abs(pinning_energy(minima,kval,1.)))) if len(minima) else 0.0
        success=success and len(minima)==kval and err_q<1e-11
        summaries.append({'q':kval,'stable_minima':len(minima),'max_pinning_minimum_energy_abs_J':err_q})
    rec('G18','PASS' if success else 'FAIL',
        'Generic Z_q angular energy gives q minima by construction; NiPS3 q=6 cannot be imposed on a vortex knot.',
        {'models':summaries,'benchmark':'Cheon2025 and Gao2026 NiPS3','evidence_class':'mathematical_control'})
    time=np.linspace(0.,2.,2001);phi,apparent=phase_jump_countermodel(time,base_hz=10.,offset_hz=2.,transition_s=1.)
    before=float(np.median(apparent[100:800]));after=float(np.median(apparent[1200:1800]))
    fake=abs((after-before)-2.)<1e-10
    rec('G19','PASS' if fake else 'FAIL',
        'Synthetic phase branch switching produces 2 Hz observed change with S_t=1 throughout (adversarial negative control).',
        {'before_Hz':before,'after_Hz':after,'apparent_jump_Hz':after-before,'clock_factor_fixed':1.0,'evidence_class':'synthetic_control'})
    cancels=abs(common_ratio(3.,.9001)-3.)<1e-14
    nuisance=common_ratio(3.,.9001,1.+1e-11,1.)
    rec('G20','PASS' if cancels and abs(nuisance-3.)>1e-12 else 'FAIL',
        'Universal co-located clock factor cancels; a species-specific transfer needs an independently derived susceptibility.',
        {'reference_ratio':3.,'common_ratio':common_ratio(3.,.9001),'differential_nuisance_ratio':nuisance,'common_mode_cancel':cancels})
    rec('G21','UNRESOLVED',
        'Canon v0.8.36 gives a universal clock postulate and a conditional phase response, not a preregistered absolute Th/Yb differential coefficient with uncertainty.',
        {'source':'SST_CANON-v0.8.36','published_th_yb_transfer_from_canon':False,'retuning_forbidden':True})
    from sst_falsifier.report import latex_escape
    (out/'report').mkdir(parents=True,exist_ok=True)
    rows=[r'\begin{longtable}{p{.10\linewidth}p{.20\linewidth}p{.60\linewidth}}',r'\toprule',r'Gate & Status & Meaning \\',r'\midrule',r'\endhead']
    for g in ledger.records:
        rows.append(f"{latex_escape(g.gate_id)} & {latex_escape(g.status)} & {latex_escape(g.reason[:125])} \\\\")
    rows += [r'G9 & DEFERRED & Separate reveal-only phase; all scientific conclusions remain blind. \\',r'\bottomrule',r'\end{longtable}']
    (out/'report/A061_GATES_SUMMARY.tex').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    return backend
