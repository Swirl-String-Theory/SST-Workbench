from __future__ import annotations
import math
import numpy as np
from scipy.optimize import linear_sum_assignment


def station_phase(curve):
    c=np.asarray(curve,float)
    seg=np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1)
    total=float(np.sum(seg))
    if not np.isfinite(total) or total<=0: raise ValueError('degenerate curve length')
    s=np.concatenate(([0.0],np.cumsum(seg[:-1])))
    return 2*np.pi*s/total


def tangents(curve):
    c=np.asarray(curve,float)
    t=np.roll(c,-1,axis=0)-np.roll(c,1,axis=0)
    n=np.linalg.norm(t,axis=1)
    return t/np.maximum(n[:,None],1e-15)


def _rotate_axis(v,axis,angle):
    axis=np.asarray(axis,float); axis=axis/max(np.linalg.norm(axis),1e-15)
    v=np.asarray(v,float); c=math.cos(float(angle)); s=math.sin(float(angle))
    return v*c + np.cross(axis,v)*s + axis*np.dot(axis,v)*(1-c)


def _transport(v,t0,t1):
    t0=np.asarray(t0,float); t1=np.asarray(t1,float)
    cr=np.cross(t0,t1); ss=float(np.linalg.norm(cr)); cc=float(np.clip(np.dot(t0,t1),-1,1))
    if ss<1e-12:
        if cc>0: return np.asarray(v,float).copy()
        raise ValueError('near-antiparallel consecutive tangents: Bishop transport undefined')
    a=cr/ss
    # Minimal Rodrigues rotation carrying t0 to t1, with cos=cc and sin=ss.
    z=np.asarray(v,float)
    return z*cc + np.cross(a,z)*ss + a*np.dot(a,z)*(1-cc)


def periodic_bishop_frame(curve):
    """Deterministic periodic parallel-transport frame with distributed holonomy correction.

    A constant initial normal-plane gauge rotation leaves the summed normal/binormal signed
    powers invariant.  Distributing the closed-loop holonomy makes the frame periodic and
    avoids Frenet sign flips near low-curvature points.
    """
    c=np.asarray(curve,float); t=tangents(c); th=station_phase(c); npts=len(c)
    axes=np.eye(3); dots=np.abs(axes@t[0]); q=axes[int(np.argmin(dots))].copy()
    q-=t[0]*np.dot(t[0],q); q/=max(np.linalg.norm(q),1e-15)
    raw=np.zeros_like(c); raw[0]=q
    for i in range(npts-1):
        z=_transport(raw[i],t[i],t[i+1]); z-=t[i+1]*np.dot(t[i+1],z)
        raw[i+1]=z/max(np.linalg.norm(z),1e-15)
    end=_transport(raw[-1],t[-1],t[0]); end-=t[0]*np.dot(t[0],end); end/=max(np.linalg.norm(end),1e-15)
    hol=math.atan2(float(np.dot(t[0],np.cross(raw[0],end))),float(np.dot(raw[0],end)))
    n=np.zeros_like(raw)
    for i in range(npts):
        z=_rotate_axis(raw[i],t[i],-hol*float(th[i])/(2*math.pi)); z-=t[i]*np.dot(t[i],z)
        n[i]=z/max(np.linalg.norm(z),1e-15)
    b=np.cross(t,n); b/=np.maximum(np.linalg.norm(b,axis=1)[:,None],1e-15)
    n=np.cross(b,t); n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15)
    closure=_rotate_axis(end,t[0],-hol)
    return t,n,b,{'holonomy_rad':float(hol),'closure_error':float(np.linalg.norm(closure-raw[0]))}

def signed_harmonic_powers_series(theta, normal_amp, binormal_amp, kmax):
    """Return [(P(+k),P(-k))] for one complex transverse series.

    theta is the arclength phase.  Complex amplitudes are projected on a deterministic
    local normal/binormal frame before this function is called.
    """
    th=np.asarray(theta,float); an=np.asarray(normal_amp,complex); ab=np.asarray(binormal_amp,complex)
    if th.ndim!=1 or an.shape!=th.shape or ab.shape!=th.shape: raise ValueError('shape mismatch')
    norm=math.sqrt(max(len(th),1)); out=[]
    for k in range(1,int(kmax)+1):
        ep=np.exp(-1j*k*th); em=np.exp(+1j*k*th)
        np_=np.sum(an*ep)/norm; bp=np.sum(ab*ep)/norm
        nm=np.sum(an*em)/norm; bm=np.sum(ab*em)/norm
        out.append((float(abs(np_)**2+abs(bp)**2),float(abs(nm)**2+abs(bm)**2)))
    return np.asarray(out,float)


def field_signed_spectrum(field, components, harmonics=(1,2,3)):
    field=np.asarray(field,complex); sizes=[len(c) for c in components]
    if field.shape!=(sum(sizes),3): raise ValueError(f'field shape {field.shape} incompatible with components')
    kmax=max(int(k) for k in harmonics); powers=np.zeros((kmax,2),float); total=0.0; offset=0
    for c,npts in zip(components,sizes):
        part=field[offset:offset+npts]; offset+=npts
        _t,n,b,_frame=periodic_bishop_frame(c); th=station_phase(c)
        an=np.einsum('ij,ij->i',part,n); ab=np.einsum('ij,ij->i',part,b)
        total += float(np.sum(np.abs(an)**2+np.abs(ab)**2))
        powers += signed_harmonic_powers_series(th,an,ab,kmax)
    rows={}
    for k in harmonics:
        pp,pm=powers[int(k)-1]; den=max(pp+pm,1e-30)
        rows[int(k)]={
          'power_plus':float(pp),'power_minus':float(pm),
          'traveling_purity':float((pp-pm)/den),
          'harmonic_participation':float((pp+pm)/max(total,1e-30)),
          'total_transverse_power':float(total)}
    return rows


def reconstruct_field(coeffs,basis):
    v=np.asarray(coeffs,complex); B=np.asarray(basis,float)
    if B.ndim!=3 or len(v)!=B.shape[0]: raise ValueError('basis/eigenvector mismatch')
    return np.tensordot(v,B,axes=(0,0))


def eigenvalue_multiset_relative_error(recomputed,stored):
    a=np.asarray(recomputed,complex); b=np.asarray(stored,complex)
    if len(a)!=len(b): return math.inf
    scale=max(float(np.max(np.abs(b))) if len(b) else 0.0,1e-30)
    cost=np.abs(a[:,None]-b[None,:])/scale
    rr,cc=linear_sum_assignment(cost)
    return float(np.max(cost[rr,cc])) if len(rr) else 0.0


def analyze_eigensystem(vals,vecs,basis,components,*,families=None,harmonics=(1,2,3),relative_imag_floor=1e-7,
                        min_kelvin_basis_fraction=.50,min_harmonic_participation=.50,min_traveling_purity=.60,max_re_over_im=1.0,
                        max_pair_frequency_asymmetry=.25):
    vals=np.asarray(vals,complex); vecs=np.asarray(vecs,complex); scale=max(float(np.max(np.abs(vals))),1e-30)
    candidates=[]
    fam=list(families) if families is not None else None
    kelvin_idx=[i for i,x in enumerate(fam or []) if x=='kelvin']
    # Positive temporal frequency is the representative of each real-matrix conjugate pair.
    for j,z in enumerate(vals):
        if float(z.imag)<=float(relative_imag_floor)*scale: continue
        q=abs(float(z.real))/max(abs(float(z.imag)),1e-30)
        coeff=np.asarray(vecs[:,j],complex)
        den_coeff=max(float(np.sum(np.abs(coeff)**2)),1e-30)
        kelvin_fraction=1.0 if fam is None else float(np.sum(np.abs(coeff[kelvin_idx])**2)/den_coeff)
        field=reconstruct_field(coeff,basis)
        sig=field_signed_spectrum(field,components,harmonics)
        for k,r in sig.items():
            chi=float(r['traveling_purity']); eta=float(r['harmonic_participation'])
            qualifies=bool(kelvin_fraction>=min_kelvin_basis_fraction and eta>=min_harmonic_participation and abs(chi)>=min_traveling_purity and q<=max_re_over_im)
            direction=0 if not qualifies else (1 if chi>0 else -1)
            candidates.append({
              'eigen_index':int(j),'harmonic':int(k),'lambda_re':float(z.real),'omega_positive':float(z.imag),
              'quality_re_over_im':float(q),'kelvin_basis_fraction':float(kelvin_fraction),'traveling_purity':chi,'harmonic_participation':eta,
              'direction':int(direction),'qualifies':qualifies,
              'power_plus':r['power_plus'],'power_minus':r['power_minus']})
    pairs=[]
    for k in harmonics:
        pos=[r for r in candidates if r['harmonic']==int(k) and r['qualifies'] and r['direction']==1]
        neg=[r for r in candidates if r['harmonic']==int(k) and r['qualifies'] and r['direction']==-1]
        for a in pos:
            for b in neg:
                # Distinct positive-frequency eigenmodes only; conjugate partners were excluded above.
                if a['eigen_index']==b['eigen_index']: continue
                asym=abs(a['omega_positive']-b['omega_positive'])/max(.5*(a['omega_positive']+b['omega_positive']),1e-30)
                pairs.append({'harmonic':int(k),'positive_direction_eigen_index':a['eigen_index'],
                              'negative_direction_eigen_index':b['eigen_index'],
                              'omega_positive_direction':a['omega_positive'],'omega_negative_direction':b['omega_positive'],
                              'frequency_asymmetry':float(asym),'qualified':bool(asym<=max_pair_frequency_asymmetry)})
    pairs.sort(key=lambda r:(not r['qualified'],r['frequency_asymmetry'],r['harmonic']))
    return {
      'schema':'A055-SIGNED-TRAVEL-SPECTRUM-1',
      'positive_frequency_mode_count':len({r['eigen_index'] for r in candidates}),
      'traveling_candidates':candidates,'opposite_direction_pairs':pairs,
      'qualified_bidirectional_pair':bool(any(r['qualified'] for r in pairs)),
      'best_qualified_pair':next((r for r in pairs if r['qualified']),None),
      'interpretation_guard':'Positive temporal frequency removes automatic conjugate duplication; spatial direction is determined independently from signed arclength-Fourier power.'}


def analytic_selftest():
    n=96; th=2*np.pi*np.arange(n)/n
    # Use direct scalar series to test signed Fourier convention.
    zplus=np.exp(1j*2*th); zminus=np.exp(-1j*2*th); stand=np.cos(2*th).astype(complex)
    p=signed_harmonic_powers_series(th,zplus,np.zeros(n,complex),3)
    m=signed_harmonic_powers_series(th,zminus,np.zeros(n,complex),3)
    s=signed_harmonic_powers_series(th,stand,np.zeros(n,complex),3)
    chi_p=(p[1,0]-p[1,1])/max(p[1].sum(),1e-30)
    chi_m=(m[1,0]-m[1,1])/max(m[1].sum(),1e-30)
    chi_s=(s[1,0]-s[1,1])/max(s[1].sum(),1e-30)
    # Conjugation flips spatial chirality and temporal frequency, leaving omega*chi direction invariant.
    inv=(1.0*chi_p)==(-1.0*chi_m)
    ok=abs(chi_p-1)<1e-12 and abs(chi_m+1)<1e-12 and abs(chi_s)<1e-12 and inv
    return {'pass':bool(ok),'chi_plus':float(chi_p),'chi_minus':float(chi_m),'chi_standing':float(chi_s),
            'conjugate_direction_invariant':bool(inv)}
