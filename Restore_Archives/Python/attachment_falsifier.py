#!/usr/bin/env python3
# Attachment-Lemma falsifier: compute chi = SL(K,U_phys) - SL(K,U_tor) for several
# HONEST framing definitions. No target injected; chi is whatever the section gives.
# Decision: a candidate "works" only if chi = +-1 UNIFORMLY in (p,q) AND is forced by
# physics (single-valuedness), not chosen.
import numpy as np

def gauss_linking(A, B):
    Am=0.5*(A+np.roll(A,-1,0)); dA=np.roll(A,-1,0)-A
    Bm=0.5*(B+np.roll(B,-1,0)); dB=np.roll(B,-1,0)-B
    s=0.0
    for i in range(len(Am)):
        r=Am[i]-Bm; rn=np.linalg.norm(r,axis=1); rn[rn<1e-12]=1e-12
        cr=np.cross(np.broadcast_to(dA[i],dB.shape),dB)
        s+=np.sum(np.einsum('ij,ij->i',r,cr)/rn**3)
    return s/(4*np.pi)

def torus_knot(p,q,R=2.0,a=0.7,n=3000):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    rho=R+a*np.cos(q*t)
    K=np.stack([rho*np.cos(p*t),rho*np.sin(p*t),a*np.sin(q*t)],1)
    U_tor=np.stack([np.cos(q*t)*np.cos(p*t),np.cos(q*t)*np.sin(p*t),np.sin(q*t)],1)
    Tt=np.gradient(K,axis=0); Tt/=np.linalg.norm(Tt,axis=1,keepdims=True)
    return t,K,U_tor,Tt

def perp(U,T):
    Up=U-np.sum(U*T,1,keepdims=True)*T
    return Up/np.linalg.norm(Up,axis=1,keepdims=True)

def rot(v,axis,ang):
    a=axis/np.linalg.norm(axis,axis=1,keepdims=True)
    c=np.cos(ang)[:,None]; s=np.sin(ang)[:,None]
    return v*c+np.cross(a,v)*s+a*np.sum(a*v,1,keepdims=True)*(1-c)

def bishop_closed(K,T):
    # genuine zero-twist (parallel-transport) frame, then distribute closure holonomy:
    n=len(K); U=np.zeros_like(K)
    ax=np.eye(3); U[0]=perp(ax[np.argmin(np.abs(ax@T[0]))][None],T[0:1])[0]
    for i in range(1,n):
        a=np.cross(T[i-1],T[i]); na=np.linalg.norm(a)
        if na<1e-12: U[i]=U[i-1]-np.dot(U[i-1],T[i])*T[i]
        else:
            ang=np.arctan2(na,np.dot(T[i-1],T[i]))
            U[i]=rot(U[i-1][None],a[None]/na,np.array([ang]))[0]
        U[i]=perp(U[i][None],T[i:i+1])[0]
    # closure holonomy distributed back (Bishop frame is the parameter-free zero-twist frame)
    hol=np.arctan2(np.dot(np.cross(U[-1],U[0]),T[0]),np.dot(U[-1],U[0]))
    tt=np.arange(n)/n
    return perp((rot(U,T,hol*tt)),T)

print("Attachment-Lemma falsifier  (chi = SL(U) - pq;  lepton target = +-1)\n")
print(f"{'T(p,q)':>7} {'pq':>4} | {'U_tor':>6} {'A:loop/1':>9} {'B1:toroid/p':>12}"
      f" {'B2:poloid/q':>12} {'PT:Bishop':>10} {'Hopf:p-q':>9}")
hdr_note=True
rows=[]
for (p,q) in [(2,3),(2,5),(2,7),(2,9),(3,2),(3,4)]:
    t,K,U_tor,T=torus_knot(p,q); eps=0.03; pq=p*q
    Ut=perp(U_tor,T)
    def chi(U): return gauss_linking(K,K+eps*U)-pq
    c_tor   = chi(Ut)                                   # reference (0)
    c_loop  = chi(rot(Ut,T, 1.0*t))                     # A: one net turn per CLOSED circuit
    c_phi   = chi(rot(Ut,T, p*t))                       # B1: lock to toroidal angle (through-hole), p turns
    c_psi   = chi(rot(Ut,T, q*t))                       # B2: lock to poloidal angle (around-tube), q turns
    c_bish  = gauss_linking(K,K+eps*bishop_closed(K,T))-pq   # parameter-free zero-twist
    c_hopf  = chi(rot(Ut,T, (p-q)*t))                   # Hopf-type combination p-q
    rows.append((p,q,pq,c_tor,c_loop,c_phi,c_psi,c_bish,c_hopf))
    print(f"  T({p},{q}) {pq:>4} | {c_tor:>6.2f} {c_loop:>9.2f} {c_phi:>12.2f}"
          f" {c_psi:>12.2f} {c_bish:>10.2f} {c_hopf:>9.2f}")

print("""
READOUT (chi must be +-1 UNIFORMLY to match the lepton fermion ladder pq+1):
  U_tor      : 0           (reference, by construction)
  A loop/1   : +1 for ALL (p,q)  <-- ONLY candidate that gives the lepton ladder pq+1.
               physical meaning: ONE net swirl-phase rotation per CLOSED circuit of the
               whole string. Topological (per-circuit), NOT advective -> survives the M5 veto.
  B1 toroid/p: = p   -> for leptons p=2 gives chi=+2 -> SL=pq+2 (EVEN) -> BOSON. RULED OUT.
               (this is the literal "through the central hole" lock; it does NOT give fermions)
  B2 poloid/q: = q   -> q-dependent -> ladder not 2q+1. RULED OUT.
  PT Bishop  : q-dependent (parameter-free geometry) -> not +-1. RULED OUT.
  Hopf p-q   : = p-q -> q-dependent. RULED OUT.

CONCLUSION: of all honest sections, EXACTLY ONE gives the lepton ladder: "one net phase
turn per closed circuit". It is not derived here -- it is a single-valuedness SELECTION
RULE -- but the falsifier has now (i) ruled out the toroidal through-hole lock (gives bosons),
the poloidal lock, the Hopf p-q lock, and the parameter-free Bishop framing; and (ii) shown
the surviving rule is exactly the spin-1/2 / Route-B "one self-rotation per circuit" object.
The open problem is razor-sharp: WHY one net turn per circuit (fermion) rather than p (boson).
""")

# --- clean re-display: chi RELATIVE to the measured torus framing (baseline = SL_tor) ---
print("="*78)
print("CLEAN TABLE: chi = SL(U) - SL(U_tor)  [relative winding; U_tor column must read 0]\n")
print(f"{'T(p,q)':>7} {'|pq|':>5} | {'U_tor':>6} {'A:loop/1':>9} {'B1:thru-hole/p':>14}"
      f" {'B2:tube/q':>10} {'Bishop':>8} {'Hopf:p-q':>9}   match pq+1?")
for (p,q) in [(2,3),(2,5),(2,7),(2,9),(3,2),(3,4)]:
    t,K,U_tor,T=torus_knot(p,q); eps=0.03
    Ut=perp(U_tor,T)
    SL=lambda U: gauss_linking(K,K+eps*U)
    base=SL(Ut)
    rel=lambda U: SL(U)-base
    a=rel(rot(Ut,T,1.0*t)); b1=rel(rot(Ut,T,p*t)); b2=rel(rot(Ut,T,q*t))
    bi=gauss_linking(K,K+eps*bishop_closed(K,T))-base; hp=rel(rot(Ut,T,(p-q)*t))
    flag = "A: YES (+1)" if abs(abs(a)-1)<0.05 else ""
    print(f"  T({p},{q}) {p*q:>5} | {0.0:>6.2f} {a:>9.2f} {b1:>14.2f}"
          f" {b2:>10.2f} {bi:>8.2f} {hp:>9.2f}   {flag}")
print("""
So, side by side:
  A  (one net turn per CLOSED circuit)  -> chi = +-1 for every (p,q).  *** lepton ladder pq+1 ***
  B1 (lock through the central hole, p) -> chi = p = 2 -> pq+2 EVEN -> boson. Omar's literal
                                            "through-the-hole" reading gives BOSONS, not leptons.
  B2 (lock around the tube, q)          -> chi = q -> q-dependent. no.
  Bishop (parameter-free geometry)      -> q-dependent. no.
  Hopf (p-q)                            -> p-q -> q-dependent. no.
""")
