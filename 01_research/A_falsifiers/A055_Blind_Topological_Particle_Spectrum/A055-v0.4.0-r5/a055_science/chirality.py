from __future__ import annotations
import math
import numpy as np
from scipy.optimize import linear_sum_assignment
from .traveling import periodic_bishop_frame,station_phase,signed_harmonic_powers_series,reconstruct_field,eigenvalue_multiset_relative_error


def component_signed_spectrum(field,components,harmonics=(1,2,3)):
    field=np.asarray(field,complex); sizes=[len(c) for c in components]
    if field.shape!=(sum(sizes),3): raise ValueError(f'field shape {field.shape} incompatible with components')
    kmax=max(int(k) for k in harmonics); out=[]; off=0; global_total=0.0
    for ci,(c,npts) in enumerate(zip(components,sizes)):
        part=field[off:off+npts]; off+=npts
        _t,n,b,meta=periodic_bishop_frame(c); th=station_phase(c)
        an=np.einsum('ij,ij->i',part,n); ab=np.einsum('ij,ij->i',part,b)
        total=float(np.sum(np.abs(an)**2+np.abs(ab)**2)); global_total+=total
        p=signed_harmonic_powers_series(th,an,ab,kmax)
        rows={}
        for k in harmonics:
            pp,pm=p[int(k)-1]; den=max(pp+pm,1e-30)
            rows[int(k)]={'power_plus':float(pp),'power_minus':float(pm),'raw_purity':float((pp-pm)/den),
                          'component_transverse_power':total,'frame_closure_error':float(meta['closure_error'])}
        out.append({'component_index':ci,'harmonics':rows,'total_transverse_power':total})
    return out,float(global_total)


def circulation_relative_spectrum(field,components,gammas,harmonics=(1,2,3)):
    gam=np.asarray(gammas,float)
    if len(gam)!=len(components): raise ValueError('gamma/component mismatch')
    comp,total=component_signed_spectrum(field,components,harmonics)
    rows={}
    for k in harmonics:
        denom=0.0; num=0.0; raw_num=0.0; detail=[]
        for c,g in zip(comp,gam):
            r=c['harmonics'][int(k)]; pp=float(r['power_plus']); pm=float(r['power_minus'])
            denom+=pp+pm; raw_num+=pp-pm; num+=(1.0 if g>=0 else -1.0)*(pp-pm)
            detail.append({'component_index':c['component_index'],'gamma_sign':1 if g>=0 else -1,'power_plus':pp,'power_minus':pm})
        den=max(denom,1e-30)
        rows[int(k)]={'circulation_relative_purity':float(num/den),'raw_purity':float(raw_num/den),
                      'harmonic_participation':float(den/max(total,1e-30)),'power_pair':float(den),
                      'total_transverse_power':float(total),'components':detail}
    return rows


def _kelvin_fraction(coeff,families):
    if families is None: return 1.0
    fam=list(families); idx=[i for i,x in enumerate(fam) if x=='kelvin']; den=max(float(np.sum(np.abs(coeff)**2)),1e-30)
    return float(np.sum(np.abs(coeff[idx])**2)/den) if idx else 0.0


def analyze_circulation_relative_modes(vals,vecs,basis,components,gammas,*,families=None,harmonics=(1,2,3),relative_imag_floor=1e-7,
        min_kelvin_basis_fraction=.5,min_harmonic_participation=.5,min_circulation_relative_purity=.6,max_re_over_im=1.0):
    vals=np.asarray(vals,complex); vecs=np.asarray(vecs,complex); scale=max(float(np.max(np.abs(vals))),1e-30)
    modes=[]
    for j,z in enumerate(vals):
        if float(z.imag)<=float(relative_imag_floor)*scale: continue
        coeff=np.asarray(vecs[:,j],complex); kfrac=_kelvin_fraction(coeff,families); q=abs(float(z.real))/max(abs(float(z.imag)),1e-30)
        field=reconstruct_field(coeff,basis); hs=circulation_relative_spectrum(field,components,gammas,harmonics)
        k=max(hs,key=lambda kk:(hs[kk]['harmonic_participation'],abs(hs[kk]['circulation_relative_purity']),-kk)); h=hs[k]
        xi=float(h['circulation_relative_purity']); eta=float(h['harmonic_participation'])
        ok=bool(kfrac>=min_kelvin_basis_fraction and eta>=min_harmonic_participation and abs(xi)>=min_circulation_relative_purity and q<=max_re_over_im)
        modes.append({'eigen_index':int(j),'lambda_re':float(z.real),'omega_positive':float(z.imag),'quality_re_over_im':float(q),
                      'kelvin_basis_fraction':float(kfrac),'dominant_harmonic':int(k),'circulation_relative_purity':xi,
                      'raw_purity':float(h['raw_purity']),'harmonic_participation':eta,'direction':0 if not ok else (1 if xi>0 else -1),
                      'qualifies':ok,'harmonics':{str(kk):vv for kk,vv in hs.items()}})
    qual=[m for m in modes if m['qualifies']]; np_=sum(m['direction']>0 for m in qual); nm=sum(m['direction']<0 for m in qual); n=len(qual)
    bias=0.0 if n==0 else float((np_-nm)/n)
    weighted=None
    if qual:
        w=np.asarray([m['harmonic_participation']*m['kelvin_basis_fraction'] for m in qual],float)
        x=np.asarray([m['circulation_relative_purity'] for m in qual],float)
        weighted=float(np.sum(w*x)/max(np.sum(w),1e-30))
    return {'schema':'A055-CIRCULATION-RELATIVE-MODES-1','positive_frequency_mode_count':len(modes),'modes':modes,
            'qualified_mode_count':n,'positive_direction_count':np_,'negative_direction_count':nm,'sector_vote_bias':bias,'weighted_purity_bias':weighted}


def sector_bias_qualified(summary,min_modes=3,min_abs_bias=.5):
    return bool(summary['qualified_mode_count']>=int(min_modes) and abs(float(summary['sector_vote_bias']))>=float(min_abs_bias))


def _rotate_rows(x,Q): return np.asarray(x)@np.asarray(Q).T

def transform_shift(field,components):
    sizes=[len(c) for c in components]; outc=[]; outf=[]; off=0
    for i,(c,n) in enumerate(zip(components,sizes)):
        sh=((i+1)*max(1,n//7))%n; outc.append(np.roll(np.asarray(c),sh,axis=0)); outf.append(np.roll(np.asarray(field)[off:off+n],sh,axis=0)); off+=n
    return np.vstack(outf),outc

def transform_rotate(field,components):
    a=.431; b=-.287; c=.613
    Rx=np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
    Ry=np.array([[math.cos(b),0,math.sin(b)],[0,1,0],[-math.sin(b),0,math.cos(b)]])
    Rz=np.array([[math.cos(c),-math.sin(c),0],[math.sin(c),math.cos(c),0],[0,0,1]])
    Q=Rz@Ry@Rx
    return _rotate_rows(field,Q),[_rotate_rows(x,Q) for x in components]
def transform_reverse_gauge(field,components,gammas):
    sizes=[len(c) for c in components]; outc=[]; outf=[]; off=0
    for c,n in zip(components,sizes): outc.append(np.asarray(c)[::-1].copy()); outf.append(np.asarray(field)[off:off+n][::-1].copy()); off+=n
    return np.vstack(outf),outc,-np.asarray(gammas,float)
def transform_permute(field,components,gammas,perm=(1,2,0)):
    sizes=[len(c) for c in components]; parts=[]; off=0
    for n in sizes: parts.append(np.asarray(field)[off:off+n]); off+=n
    return np.vstack([parts[i] for i in perm]),[np.asarray(components[i]) for i in perm],np.asarray(gammas,float)[list(perm)]


def metamorphic_errors(field,components,gammas,harmonic):
    k=int(harmonic); base=circulation_relative_spectrum(field,components,gammas,(k,))[k]['circulation_relative_purity']; vals={'canonical':float(base)}
    fs,cs=transform_shift(field,components); vals['cyclic_shift']=float(circulation_relative_spectrum(fs,cs,gammas,(k,))[k]['circulation_relative_purity'])
    fr,cr=transform_rotate(field,components); vals['rigid_rotation']=float(circulation_relative_spectrum(fr,cr,gammas,(k,))[k]['circulation_relative_purity'])
    fv,cv,gv=transform_reverse_gauge(field,components,gammas); vals['orientation_reverse_gamma_flip']=float(circulation_relative_spectrum(fv,cv,gv,(k,))[k]['circulation_relative_purity'])
    fp,cp,gp=transform_permute(field,components,gammas); vals['component_permutation']=float(circulation_relative_spectrum(fp,cp,gp,(k,))[k]['circulation_relative_purity'])
    errs={name:abs(v-base) for name,v in vals.items() if name!='canonical'}
    return {'values':vals,'errors':errs,'max_abs_error':float(max(errs.values()) if errs else 0.0)}


def analytic_covariance_selftest():
    n=128; th=2*np.pi*np.arange(n)/n
    comps=[]; fields=[]
    centers=[(-3.,0.,0.),(3.,0.,0.),(0.,3.,0.)]
    for i,ctr in enumerate(centers):
        c=np.c_[np.cos(th)+ctr[0],np.sin(th)+ctr[1],0.15*np.sin(2*th)+ctr[2]]; comps.append(c)
        _t,nv,b,_=periodic_bishop_frame(c); z=np.exp(1j*(i%2+1)*th); fields.append(z[:,None]*nv+0.3j*z[:,None]*b)
    field=np.vstack(fields); gam=np.array([1.,-1.,1.])
    h=circulation_relative_spectrum(field,comps,gam,(1,2,3)); k=max(h,key=lambda x:h[x]['harmonic_participation']); m=metamorphic_errors(field,comps,gam,k)
    return {'pass':bool(m['max_abs_error']<1e-10),'dominant_harmonic':int(k),**m}
