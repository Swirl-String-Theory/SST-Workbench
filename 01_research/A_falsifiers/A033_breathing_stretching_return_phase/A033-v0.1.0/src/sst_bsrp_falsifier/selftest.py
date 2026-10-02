import tempfile,json
from pathlib import Path
import numpy as np
from .geometry import synthetic_ring,synthetic_trefoil,resample_closed,normalize,perturb,radius_gyration
from .solver import velocity_python,velocity,velocity_variable_core_python,segment_lengths,segment_cores,stretch_rate_python,stretch_rate,HAVE_NATIVE,backend_name
from .constants import GAMMA_CANON
from .observables import breathing_harmonic_phase,packet_track

def main():
    x,_=normalize(resample_closed(synthetic_trefoil(120),64));
    up=velocity_python(x,1.0,.06); un=velocity(x,1.0,.06,require_native=False)
    rel=float(np.linalg.norm(up-un)/max(np.linalg.norm(up),1e-30)); sp=stretch_rate_python(x,up); sn=stretch_rate(x,un); srel=float(np.linalg.norm(sp-sn)/max(np.linalg.norm(sp),1e-30))
    # uniform dilation must move Rg by the same fractional amount before dynamics
    y=perturb(x,.01,1,0,1,0,.08); dil=radius_gyration(y)/radius_gyration(x)-1
    ref=segment_lengths(x); x2=x.copy(); x2[1]=x2[0]+1.2*(x2[1]-x2[0]); cores=segment_cores(x2,ref,.06,-.5); ell=segment_lengths(x2); vol_rel=float(np.max(np.abs((cores*cores*ell)/(.06*.06*ref)-1)))
    ufix=velocity_python(x,1.0,.06); uvar0=velocity_variable_core_python(x,1.0,np.full(len(x),.06)); fixed_rel=float(np.linalg.norm(ufix-uvar0)/max(np.linalg.norm(ufix),1e-30))
    tt=np.linspace(0,10,201); ww=2.3; dd=.4; qq=.02*np.cos(ww*tt-dd); hf=breathing_harmonic_phase(tt,qq,3.2,161); phase_expected=float(np.angle(np.exp(1j*(ww*3.2-dd)))); phase_err=float(abs(np.angle(np.exp(1j*(float(hf.get('phase_rad',0))-phase_expected)))))
    N=64; M=100; ti=np.linspace(0,1,M); jj=np.arange(N); templ=np.exp(-.5*(np.angle(np.exp(1j*(2*np.pi*jj/N)))/.35)**2); SS=np.asarray([np.roll(templ,int(round(z*N))) for z in np.linspace(0,1.25,M)]); pt=packet_track(SS,ti,.1)
    out={'backend':backend_name(),'native_available':HAVE_NATIVE,'velocity_relative_error':rel,'stretch_relative_error':srel,'fixed_vs_variable_core0_relative_error':fixed_rel,'material_tube_volume_invariant_max_relative_error':vol_rel,'breathing_initial_fraction':dil,'harmonic_phase_error_rad':phase_err,'synthetic_packet_return_available':bool(pt.get('available',False)),'synthetic_packet_tau_return':float(pt.get('tau_return',np.nan)),'gamma_canon_m2_s':GAMMA_CANON,'pass':bool((not HAVE_NATIVE or (rel<1e-11 and srel<1e-11)) and fixed_rel<1e-12 and vol_rel<1e-12 and abs(dil-.01)<2e-4 and hf.get('available',False) and phase_err<.03 and pt.get('available',False) and abs(float(pt.get('tau_return',0))-.81)<.05)}
    print(json.dumps(out,indent=2,sort_keys=True));
    if not out['pass']: raise SystemExit(2)
if __name__=='__main__': main()
