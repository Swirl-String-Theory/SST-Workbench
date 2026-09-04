from __future__ import annotations
import math
import numpy as np
from sst6.blind import stable_seed
from .common import result


def _fit_ringdown(t,y,w0_guess,gamma_guess):
    best=None
    gs=np.linspace(max(0.02,gamma_guess*0.45),gamma_guess*1.65,41)
    ws=np.linspace(w0_guess*0.90,w0_guess*1.10,81)
    for g in gs:
        env=np.exp(-g*t)
        for w in ws:
            A=np.column_stack([env*np.sin(w*t),env*np.cos(w*t)])
            c=np.linalg.lstsq(A,y,rcond=None)[0]; r=y-A@c; s=float(r@r)
            if best is None or s<best[0]: best=(s,g,w,c)
    return best


def classical_null_calibration(campaign_hash,cfg):
    seed=stable_seed(campaign_hash,"H6CAL"); rng=np.random.default_rng(seed)
    w0=9.0+rng.uniform(0.5,2.0); gamma=0.18+rng.uniform(0.05,0.18); wd=math.sqrt(w0*w0-gamma*gamma)
    t=np.linspace(0,float(cfg.get("ringdown_duration",30.0)),int(cfg.get("ringdown_points",1800))); phase=rng.uniform(0,2*math.pi); y=np.exp(-gamma*t)*np.sin(wd*t+phase); y+=rng.normal(scale=float(cfg.get("noise_sigma",0.002)),size=len(t))
    fit=_fit_ringdown(t,y,w0,gamma); _,gfit,wdfit,_=fit; w0fit=math.sqrt(wdfit*wdfit+gfit*gfit); wpk_pred=math.sqrt(max(w0fit*w0fit-2*gfit*gfit,0.0))
    w=np.linspace(w0*0.82,w0*1.18,int(cfg.get("drive_points",500))); chi=1.0/(w0*w0-w*w-2j*gamma*w); amp=np.abs(chi); ph=np.unwrap(np.angle(chi)); wpk_meas=float(w[int(np.argmax(amp))])
    amp_pred=np.abs(1.0/(w0fit*w0fit-w*w-2j*gfit*w)); scale=float(np.dot(amp,amp_pred)/np.dot(amp_pred,amp_pred)); amp_rel=float(np.sqrt(np.mean((amp-scale*amp_pred)**2))/np.mean(amp)); ph_pred=np.unwrap(np.angle(1.0/(w0fit*w0fit-w*w-2j*gfit*w))); ph_rmse=float(np.sqrt(np.mean((ph-ph_pred)**2)))
    peak_rel=abs(wpk_meas-wpk_pred)/wpk_meas; ok=peak_rel<=float(cfg.get("peak_rel_max",0.01)) and amp_rel<=float(cfg.get("amp_rel_rmse_max",0.03)) and ph_rmse<=float(cfg.get("phase_rmse_max",0.08))
    return result(6,"H6_CLASSICAL_NULL_CALIBRATION","The analysis pipeline recovers the same damped-oscillator parameters from free ringdown and driven amplitude/phase response.","CALIBRATION","PASS" if ok else "FAIL",{
        "hidden":{"omega0":w0,"gamma":gamma,"omega_d":wd},"fit":{"omega0":w0fit,"gamma":gfit,"omega_d":wdfit},"omega_peak_pred":wpk_pred,"omega_peak_measured":wpk_meas,"peak_relative_error":peak_rel,"amplitude_relative_rmse":amp_rel,"phase_rmse_rad":ph_rmse
    },{"peak_rel_max":cfg.get("peak_rel_max",0.01),"amp_rel_rmse_max":cfg.get("amp_rel_rmse_max",0.03),"phase_rmse_max":cfg.get("phase_rmse_max",0.08)})


def nonlinear_mixing_calibration(campaign_hash,cfg):
    seed=stable_seed(campaign_hash,"H6MIX"); rng=np.random.default_rng(seed); f1=17.0; f2=29.0; fs=1024.0; T=4.0; t=np.arange(0,T,1/fs); amps=np.asarray(cfg.get("amplitudes",[0.05,0.08,0.12,0.18,0.27]),float)
    def fftamp(y,f):
        Y=np.fft.rfft(y); fr=np.fft.rfftfreq(len(y),1/fs); j=int(np.argmin(abs(fr-f))); return float(2*abs(Y[j])/len(y))
    intrinsic=[]; multiplicative=[]
    mod_amp=0.2
    for A in amps:
        x=A*np.sin(2*math.pi*f1*t)+A*np.sin(2*math.pi*f2*t); y=x+0.7*x*x; intrinsic.append(fftamp(y,f1+f2))
        z=(1+mod_amp*np.sin(2*math.pi*f2*t))*(A*np.sin(2*math.pi*f1*t)); multiplicative.append(fftamp(z,f1+f2))
    def slope(y): return float(np.polyfit(np.log(amps),np.log(np.maximum(y,1e-30)),1)[0])
    s_int=slope(np.asarray(intrinsic)); s_mul=slope(np.asarray(multiplicative)); ok=abs(s_int-2)<=float(cfg.get("intrinsic_slope_tol",0.15)) and abs(s_mul-1)<=float(cfg.get("multiplicative_slope_tol",0.15))
    return result(6,"H6_NONLINEAR_MIXING_CALIBRATION","Amplitude-scaling discriminates intrinsic quadratic mixing from multiplicative transfer-chain modulation in the calibration signals.","CALIBRATION","PASS" if ok else "FAIL",{"amplitudes":amps.tolist(),"intrinsic_sum_tone":intrinsic,"multiplicative_sum_tone":multiplicative,"intrinsic_log_slope":s_int,"multiplicative_log_slope":s_mul},{"intrinsic_expected":2.0,"multiplicative_expected":1.0,"intrinsic_slope_tol":cfg.get("intrinsic_slope_tol",0.15),"multiplicative_slope_tol":cfg.get("multiplicative_slope_tol",0.15)})
