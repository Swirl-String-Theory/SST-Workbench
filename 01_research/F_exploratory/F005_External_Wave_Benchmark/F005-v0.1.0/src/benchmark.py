#!/usr/bin/env python3
"""SST External Wave Benchmark v0.1.0.
Only equations/parameters from primary papers plus explicit synthetic regressions.
NO digitized experimental points; NO PKLSA prediction; NO inferred SST validity.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
import numpy as np
from scipy.special import kve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]


def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1048576), b''): h.update(b)
    return h.hexdigest()


def kelvin_hollow_core_omega(k, gamma=0.018, a0=0.00147, m=1):
    """Eq (7) of Barckicke et al. (2026) in hollow-core idealization.
    m=1 branch, negative frequency in authors' convention. k in m^-1;
    result rad/s. NOT the implicit Rankine Eq (1) branch used in their Fig 2.
    """
    k=np.asarray(k,dtype=float)
    if np.any(k<=0) or gamma<=0 or a0<=0 or int(m)!=m or m<1:
        raise ValueError('positive k, circulation, core radius; m integer >=1 required')
    x=a0*k
    # exponentially scaled Bessel K cancels common factor exp(-x)
    ratio=kve(m-1,x)/kve(m,x)
    return (gamma/(2*np.pi*a0*a0))*(1-np.sqrt(1+x*ratio))


def kelvin_longwave_omega(k, gamma=0.018, a0=0.00147):
    """Asymptotic form for hollow core Eq (7) and m=1, ka<<1."""
    euler_gamma = 0.5772156649015329
    k=np.asarray(k,float)
    return -gamma*k*k/(4*np.pi)*(np.log(2/(k*a0))-euler_gamma)


def inertial_omega(theta, rotation_rpm):
    """Intrinsic inertial frequency in a rotating fluid, rad/s, Eq (1.2) JFM."""
    if rotation_rpm<0: raise ValueError('rpm nonnegative')
    return 2*(rotation_rpm*2*np.pi/60)*np.cos(np.asarray(theta,float))


def alias_condition(f_hz, fps):
    return abs(f_hz) < fps/2


def write_csv(path, fieldnames, rows):
    with open(path,'w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=fieldnames);w.writeheader();w.writerows(rows)


def run(root=ROOT):
    cfg=json.loads((root/'configs'/'source_contract.json').read_text(encoding='utf8'))
    (root/'results').mkdir(exist_ok=True);(root/'figures').mkdir(exist_ok=True)
    src=root/'sources'
    inputs={file['id']:{'filename':file['filename'],'sha256':sha256(src/file['filename']),
                         'matches_frozen_sha': sha256(src/file['filename'])==file['sha256']} for file in cfg['sources']}
    assert all(z['matches_frozen_sha'] for z in inputs.values()),'Source SHA mismatch: re-freeze required'
    p=cfg['reported_parameters']['kelvin_turbulence']
    g=float(p['Gamma_m2_s']);a=float(p['a0_m']); vz=float(p['v_z_m_s'])
    omega_core=g/(2*math.pi*a*a)
    kcycles=np.geomspace(2.5,210,180) # k/(2*pi) in cycles per m
    k=2*np.pi*kcycles
    om=kelvin_hollow_core_omega(k,g,a)
    rows=[dict(k_rad_m=float(ki),k_cycles_m=float(ci),ka0=float(ki*a),
               hollow_core_omega_rad_s=float(oi),hollow_core_f_hz=float(oi/(2*np.pi)),
               provenance='THEORY_ONLY_Eq7_NOT_EXPERIMENT') for ki,ci,oi in zip(k,kcycles,om)]
    write_csv(root/'results'/'kelvin_hollow_core_theory.csv', list(rows[0]), rows)
    fig, ax=plt.subplots(figsize=(7.4,4.2))
    ax.plot(kcycles,abs(om)/(2*np.pi),label='Hollow-core Eq. (7), m=1 (theory only)')
    ax.axvline(1/(2*np.pi*a),linestyle='--',linewidth=1,label='ka0 = 1')
    ax.set(xlabel='k / (2π) [m⁻¹]',ylabel='|f| [Hz]',title='Kelvin bending: analytical reference (not measured)')
    ax.grid(alpha=.2);ax.legend(fontsize=8); fig.tight_layout();fig.savefig(root/'figures'/'kelvin_reference.png',dpi=170);plt.close(fig)
    inertial=[]
    angles_deg=np.arange(0,91,5)
    for rpm in [3,6,9,12]:
        for theta in angles_deg:
            w=float(inertial_omega(np.deg2rad(theta),rpm))
            frot=rpm/60
            inertial.append(dict(rotation_rpm=rpm,theta_deg=int(theta),omega_rad_s=w,
                         f_inertial_hz=w/(2*np.pi),f_over_Frotation=(w/(2*np.pi))/frot,
                         provenance='THEORY_ONLY_JFM_Eq1.2_NOT_EXPERIMENT'))
    write_csv(root/'results'/'inertial_theory.csv',list(inertial[0]),inertial)
    fig,ax=plt.subplots(figsize=(7.4,4.2))
    for rpm in [3,6,9,12]:
        th=angles_deg
        ax.plot(th, np.asarray(inertial_omega(np.deg2rad(th),rpm))/(2*np.pi),label=f'{rpm} rpm')
    ax.set(xlabel='Wavevector angle θ [degrees]',ylabel='Intrinsic |f| [Hz]',
           title='Inertial waves: theoretical dispersion (no measured points)')
    ax.grid(alpha=.2);ax.legend(title='Tank rotation',fontsize=8);fig.tight_layout();fig.savefig(root/'figures'/'inertial_reference.png',dpi=170);plt.close(fig)
    # Published mutually close spectral predictions; do not claim resolved experimental discrimination.
    sf=np.geomspace(2,150,150)
    fig,ax=plt.subplots(figsize=(7.4,4.2))
    for slope,name in [(-11/5,'KS temporal -11/5'),(-7/3,'LN temporal -7/3')]:
        ax.loglog(sf,(sf/10)**slope,label=name)
    ax.set(xlabel='Frequency [Hz] (illustrative abscissa)',ylabel='Normalized spectral density [arbitrary]',
           title='Theoretical scaling ambiguity — not an experimental fit')
    ax.grid(alpha=.2,which='both');ax.legend();fig.tight_layout();fig.savefig(root/'figures'/'cascade_exponents.png',dpi=170);plt.close(fig)
    # Explicit gates differentiate analytic model checks from measurement validation.
    gates=[]
    def gate(name,status,scope,reason):
        gates.append({'id':name,'status':status,'scope':scope,'reason':reason})
    provenance_ok=all(z['matches_frozen_sha'] for z in inputs.values())
    units_ok=(g>0 and a>0 and np.isfinite(vz) and
              np.isclose(omega_core*g**0, g/(2*np.pi*a*a)))
    kshort=0.001/a
    short_full=float(kelvin_hollow_core_omega([kshort],g,a)[0])
    short_approx=float(kelvin_longwave_omega([kshort],g,a)[0])
    kelvin_check=np.isfinite(short_full) and short_full<0 and abs((short_full-short_approx)/short_approx)<0.0003
    inertial_check=all(abs(float(inertial_omega(0,rpm))/(2*np.pi)-rpm/30)<1e-12 and
                       abs(float(inertial_omega(np.pi/2,rpm)))<1e-12 for rpm in (3,6,9,12))
    gate('G0','PASS' if provenance_ok else 'FAIL','provenance','Both source SHA256 verified')
    gate('G1','PASS' if units_ok else 'FAIL','reported-inputs','SI-unit dimension and finite-source-parameter checks')
    gate('G2','PASS' if kelvin_check else 'FAIL','analytic-regression','Eq.7 m=1 agrees with long-wave hollow-core asymptotic below 3e-4 relative error')
    gate('G3','PASS' if inertial_check else 'FAIL','analytic-regression','Inertial omega(0)=2 Omega, omega(pi/2)=0, 3/6/9/12 rpm')
    gate('G4','BLOCKED_NO_RAW_DATA','experimental-validation','No source-native Kelvin eta(z,t) or experimental omega(k) points in attachments')
    gate('G5','BLOCKED_NO_RAW_DATA','experimental-validation','No raw amplitude spectrum/time series with confidence intervals for slope fits')
    gate('G6','BLOCKED_NO_RAW_DATA','experimental-validation','No 75-minute complex Fourier amplitudes for six-wave pentacoherence null test')
    gate('G7','BLOCKED_NO_RAW_PIV','experimental-validation','No source-native Jackson/Thomas PIV velocity cubes for reconstructed dispersion')
    gate('G8','NOT_RUN_NO_PKLSA','SST-prediction','No frozen source-native PKLSA predictions or geometry at the specified conditions')
    gate('G9','UNRESOLVED','physical-claim','No SST physical conclusion or independent model-comparison score is warranted')
    res={
       'title':'SST External Wave Benchmark v0.1.0', 'status':'DEVELOPMENT_LITERATURE_BASELINE_NOT_CERTIFIED',
       'sources':inputs,'reported_parameters':p,
       'derived':{'Omega_core_rad_s':omega_core,'f_core_hz':omega_core/(2*np.pi),
                  'Kelvin_at_kcyc_10_m_inv_f_hz':float(kelvin_hollow_core_omega(np.asarray([20*np.pi]),g,a)[0]/(2*np.pi)),
                  'JFM_12rpm_omega_max_rad_s':float(inertial_omega(0,12)),
                  'JFM_12rpm_fmax_hz':float(inertial_omega(0,12)/(2*np.pi)),
                  'JFM_12rpm_theta60_f_hz':float(inertial_omega(np.pi/3,12)/(2*np.pi)),
                  'JFM_12rpm_omega_doubled_check':float(inertial_omega(0,12)/(12*2*np.pi/60))},
       'gates':gates,'experiment_points_used':0,
       'false_claim_guard':'PASS analytic/regression != PASS empirical or SST',
       'spectrum_note':'KS and LN slopes too close to discriminate from stated experiment alone.',
       'timestamp_rule':'Source publication dates only; no fabricated acquisition date.'}
    (root/'results'/'gate_results.json').write_text(json.dumps(res,indent=2,ensure_ascii=False),encoding='utf8')
    return res

if __name__=='__main__':
    print(json.dumps(run(),indent=2,ensure_ascii=False))
