#!/usr/bin/env python3
"""Rebuild registry from source snapshots; no external services or packages except PyMuPDF for PDF pages.
A raw extraction is NOT a scientific endorsement. v0.1.0 = seeded mathematical evidence register.
"""
from __future__ import annotations
import re, json, csv, hashlib, math
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'sources'
RES = ROOT / 'results'
RES.mkdir(exist_ok=True)
SOURCES = [
('SUM-SST','SST-00-90-summaries.md','secondary','May 2026; exported AI summaries; not manuscripts'),
('SUM-VAM','VAM-01-15-summaries.pdf','secondary','May 2026; exported AI summaries; not manuscripts'),
('SRC-VAM5','VAM-5-OnAVortexBasedLagrangianUnificationGravityElectromagnetism.pdf','primary','Original manuscript, historical'),
('SRC-SST17','SST-17_Photon_as_a_Torsion_Wave.pdf','primary','Original manuscript'),
('SRC-SST33T','SST-33_Heat_Transport.pdf','primary','Original manuscript'),
('SRC-SST33C','SST-33_HEAT_Compare.pdf','primary','Original manuscript'),
('SRC-SST35','SST-35_resonance_overlap_sst_methods.pdf','primary','Original manuscript'),
('SRC-SST36','SST-36_Wave-Particle_Duality.pdf','primary','Original manuscript'),
('SRC-KELVIN-A','Kelvin_Mode_Suppression_in_Atomic_Orbitals_A_Vortex-Filament_Gap-DH.pdf','primary','New paper, Kelvin gap, 10 pages'),
('SRC-KELVIN-B','Thermo_Suppression_of_Kelvin_Mode_Thermodynamics.pdf','primary','New paper, Kelvin gap, 8 pages'),
('SRC-DUAL','Hydrodynamic_Dual-Vacuum_Unification.pdf','primary','New paper, two interacting sectors, 5 pages'),
]

def sha256(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for buf in iter(lambda:f.read(2**20),b''): h.update(buf)
 return h.hexdigest()

def write_json(name,x): (RES/name).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def write_jsonl(name,items): (RES/name).write_text(''.join(json.dumps(v,ensure_ascii=False)+'\n' for v in items),encoding='utf-8')
def write_csv(name,rows,fields):
 with (RES/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader();w.writerows(rows)

manifest=[]
for sid,fname,kind,remark in SOURCES:
 p=SRC/fname
 if not p.exists(): raise FileNotFoundError(f'Missing source snapshot: {p}')
 manifest.append(dict(source_id=sid,filename='sources/'+fname,kind=kind,notes=remark,sha256=sha256(p),bytes=p.stat().st_size))
write_json('source_manifest.json',{'version':'0.1.0','provenance_policy':'secondary summaries are discovery only; mathematical proof must be independently reconstructed','sources':manifest})

md=(SRC/'SST-00-90-summaries.md').read_text(encoding='utf-8')
lines=md.splitlines(keepends=True)
# Determine primary 'paper assessment' headers and multiline labels.
head_re=re.compile(r'^#\s+SST-(\d{2})\b(.*)$')
current=[];last_header='(unassigned; summary context)';headings={}
line_papers=[]
for i,line in enumerate(lines,1):
 m=head_re.match(line)
 if m:
  first=m.group(1);rest=m.group(2).split('—')[0]
  # Only paper numbers in the header identifier, not title/content.
  extras=re.findall(r'(?:(?:SST-)|(?<=[/& ,]))(\d{2})(?!\d)',rest)
  current=list(dict.fromkeys([first]+extras))
  last_header=line.strip()
  for p in current:headings.setdefault('SST-'+p,[]).append(dict(line=i,title=last_header))
 elif line.startswith('# you asked') or line.startswith('# claude response'):
  current=[];last_header='(non-paper discussion)'
 line_papers.append((list(current),last_header))

# Extract raw $$ blocks including untested/malformed spans: track line-based offsets exactly.
starts=[0]
for l in lines:starts.append(starts[-1]+len(l))
from bisect import bisect_right
formula_candidates=[]
for n,m in enumerate(re.finditer(r'\$\$(.*?)\$\$',md,flags=re.S),1):
 body=m.group(1).strip();a=bisect_right(starts,m.start());b=bisect_right(starts,m.end()-1)
 papers,context=line_papers[a-1]
 formula_candidates.append({'id':f'RAW-SST-{n:04d}','source_id':'SUM-SST','source_kind':'secondary_AI_summary',
  'source_line_start':a,'source_line_end':b,'paper_ids':['SST-'+p for p in papers],
  'heading':context,'latex_raw':body,'sha256_raw':hashlib.sha256(body.encode()).hexdigest(),
  'scientific_status':'NOT_REVIEWED','technical_status':'RAW_EXTRACTION','notes':'Mathematical correctness, units and assumptions NOT yet audited; original paper may differ.'})
write_jsonl('raw_formula_candidates.jsonl',formula_candidates)

# Inventory is comprehensive for 00..90 ID-space, but recognition is explicit.
mentioned=set(int(x) for x in re.findall(r'(?<![\w])SST-(\d{2})(?!\d)',md))
raw_counts=Counter(x for f in formula_candidates for x in f['paper_ids'])
papers=[]
for i in range(91):
 pid=f'SST-{i:02d}'
 papers.append({'paper_id':pid,'series':'SST','mentioned_in_secondary_summary':i in mentioned,
    'has_dedicated_assessment_heading':pid in headings,
    'assessment_heading_count':len(headings.get(pid,[])),
    'raw_formula_candidate_count':raw_counts[pid],
    'assessment_headings':' | '.join(h['title'][:95] for h in headings.get(pid,[])),
    'evidence_rating':'INDEX_ONLY_NOT_AUDITED'})
for i in range(1,16):
 pid=f'VAM-{i:02d}'
 papers.append({'paper_id':pid,'series':'VAM','mentioned_in_secondary_summary':True,
   'has_dedicated_assessment_heading':None,'assessment_heading_count':None,'raw_formula_candidate_count':0,
   'assessment_headings':'AI PDF summary volume (coverage not independently verified entry-by-entry)',
   'evidence_rating':'INDEX_ONLY_NOT_AUDITED'})
write_csv('paper_inventory.csv',papers,['paper_id','series','mentioned_in_secondary_summary','has_dedicated_assessment_heading','assessment_heading_count','raw_formula_candidate_count','assessment_headings','evidence_rating'])

# Curated formula-level audit: no automated extraction is quietly promoted to proof.
cur=[]
def claim(id,paper,src,loc,formula,status,scope,unit,note,test='NOT_TESTED',dependencies='',falsifier=''):
 cur.append({'claim_id':id,'paper_id':paper,'source_id':src,'source_locator':loc,'formula_latex':formula,
 'evidence_status':status,'scope_or_assumptions':scope,'dimension_status':unit,'audit_comment':note,
 'test_status':test,'dependencies':dependencies,'suggested_falsifier':falsifier,
 'review_level':'FORMULA_LEVEL_MANUAL_AUDIT_V0.1.0'})

claim('M001','SST-00','SUM-SST','SST-00 summary §3.3',r'\mathcal M_0=C_0(\sum_iV_i)\rho_{\!f}v_{\star}^2','INCONSISTENT_AS_MASS','C0 dimensionless and Vi volumes','FAIL_JOULES_NOT_KG','Correct dimensions are energy [J]; mass needs division by c^2 or dimensionful C0. Previous summary calls it dimensionally correct.','CHECKED_ALGEBRA','rho_f,v_star,V,C0','MASS_DIMENSIONS')
claim('M002','SST-83','SUM-SST','SST-83 summary §3.5',r'E_{\rm kin}=\frac23m_ec^2','IDENTITY_UNDER_ASSUMED_INPUTS','rho_core and spherical core formula introduced in summary','PASS_ENERGY','Identity under density/core definitions. Interpretation as harmonic virial confirmation is unsupported: harmonic virial has <T>=Etotal/2.','CHECKED_ALGEBRA','assumed rho_core, me, rc, v','VIRIAL_INDEPENDENCE')
claim('M003','SST-90','SUM-SST','SST-90 summary §3.1',r'M_K=(\rho_{\!f}v^2/2c^2)r_c^3\,\Pi_K\,\Xi_K\,S_t^{-2}','MATHEMATICAL_ANSATZ','dimensionless Pi,Xi,St; assumes clock factor','PASS_KG','Dimensionally consistent product; no derivation of factorization or coefficients demonstrated.','CHECKED_ALGEBRA','Pi,Xi,St','BLIND_FACTORISATION')
claim('M004','SST-83','SUM-SST','SST-83 summary §3.1',r'\Omega_C=m_ec^2/\hbar=\mathbf v_{\!\boldsymbol{\circlearrowleft}}/r_c','POSTULATED_CLOSURE','electron mass/frequency supplied externally','PASS_RAD_PER_S','Equality is numerically calibrated; not an independent electron-mass prediction.','CHECKED_ALGEBRA','me,rc,swirl_speed','BLIND_COMPTON_CLOSURE')
claim('M005','VAM-05','SRC-VAM5','pp. 11,14; Lagrangian and Hamiltonian',r'\mathbf P_{\mathbf v}=\partial\mathcal L/\partial\dot{\mathbf v}=\rho_{\!f}\mathbf v','INCONSISTENT','written L has no time derivative of velocity','FAIL_VARIATIONAL','Velocity conjugate momentum claimed without dot{v} dependence: zero, not rho v.','CHECKED_SYMBOLIC','VAM5_L','VARIATIONAL_VARIATION')
claim('M006','VAM-05','SRC-VAM5','pp. 38-43 master mass formula',r'M\propto \rho_{\rm core}v^2 V','INCONSISTENT_AS_MASS','dimensionless other factors','FAIL_JOULES_NOT_KG','Right hand side is energy, not mass. Fits not reproducible from printed formula.','CHECKED_ALGEBRA','rho_core,v,V','MASS_DIMENSIONS')
claim('M007','VAM-05','SRC-VAM5','pp. 31-32 Coulomb benchmark',r'\mathbf E_H(\mathbf x)=\kappa\int h(\mathbf x\prime)\frac{\mathbf x-\mathbf x\prime}{|\mathbf x-\mathbf x\prime|^3}\,d^3x\prime','MATHEMATICAL_CONSTRUCTION','postulated Coulomb kernel','COUPLING_UNDEFINED','Correct far-field kernel by construction; not derived from Euler or an electromagnetic action.','CHECKED_STRUCTURAL','helicity density h, coupling kappa','COULOMB_KERNEL_INDEPENDENCE')
claim('M008','SST-17','SRC-SST17','p. 2 eqs. (5)-(11)',r'\mathcal L_d=\frac12\rho_d|\dot{\mathbf q}|^2-\frac12 K|\nabla\times\mathbf q|^2','CONDITIONAL_MODEL','separate transverse elastic/director field, div q=0','PASS_IF_q_DISPLACEMENT','Produces transverse wave speed sqrt(K/rho_d) if q has displacement units. Does not follow from unmodified inviscid Euler.','CHECKED_VARIATION','rho_d,K,q','DIRECTOR_FROM_EULER')
claim('M009','SST-17','SRC-SST17','p. 2 eq. (4)',r'F=\kappa u_a T^a=\kappa u_a d\theta^a','CONDITIONAL_GEOMETRY','constant u_a and Weitzenbock gauge','COUPLING_DIMENSIONS_OPEN','dF=0 follows from d^2=0, but Maxwell dynamics and physical EM identification do not follow.','CHECKED_ALGEBRA','Cartan coframe torsion','EM_FROM_TORSION')
claim('M010','SST-17','SRC-SST17','p. 3 eq. (16)',r'V_{vac}\simeq\alpha_{vac}/2','UNRESOLVED','Verdet constant has dimensions rad/(T m)','UNSPECIFIED_ALPHA_UNITS','No independent constitutive derivation; alpha_vac requires units.','NOT_TESTED','CFJ coupling','VACUUM_ROTATION')
claim('M011','SST-33','SRC-SST33T','p. 4 eq. (7)',r'\mathcal K(\delta,\Gamma)=\Gamma/(4\delta^2+\Gamma^2)','MATHEMATICAL_CONSTRUCTION','gamma linewidth positive','PASS_SECONDS','Valid Lorentzian kernel; transport prefactors, linewidth definition and normalization are additional requirements.','CHECKED_ALGEBRA','delta,Gamma','MODE_TRANSPORT')
claim('M012','SST-33','SRC-SST33C','p. 4 eqs. (14)-(15)',r'\epsilon=(r-r_c)/r_c,\quad T_{swirl}=\Theta\epsilon','MATHEMATICAL_ANSATZ','Theta in K','PASS_IF_THETA_K','Geometric strain definition does not establish thermodynamic temperature.','CHECKED_ALGEBRA','r_c,Theta','TEMPERATURE_INDEPENDENCE')
claim('M013','SST-33','SRC-SST33C','p. 5 eqs. (20)-(25)',r'\Delta E=\frac12 K_{eff}(T_{swirl}/\Theta)^2','CONDITIONAL_MODEL','harmonic stiffness and strain-temperature relation imposed','PASS_IF_Keff_J','Energy quadratic in defined strain variable; linear physical heat capacity does not generally follow.','CHECKED_ALGEBRA','M012,Keff','THERMODYNAMIC_HEAT_CAPACITY')
claim('M014','SST-35','SRC-SST35','p. 1 eqs. (1)-(3)',r'Y(\omega_0)=\int S(\omega)\sum_n L_n(\omega)d\omega','MATHEMATICAL_CONSTRUCTION','spectra and resonance weights defined, normalizations fixed','CONDITIONAL','Gaussian times Lorentzian yields Voigt convolution, but original amplitudes need normalized convention.','CHECKED_NUMERIC','source spectrum,target lines','VOIGT_IDENTIFIABILITY')
claim('M015','SST-35','SRC-SST35','p. 2 Fisher information',r'I(\theta)=\sigma_\epsilon^{-2}\sum_k\nabla\mu_k\nabla\mu_k^T','ESTABLISHED_WITH_ASSUMPTIONS','independent Gaussian noise with known constant variance','PASS_STATISTICAL','Valid Fisher matrix under noise model; full rank requires experiment-dependent Jacobian test.','CHECKED_ALGEBRA','gaussian likelihood','FIM_RANK')
claim('M016','SST-36','SRC-SST36','pp. 1-2, transition R<->T',r'0_1\leftrightarrow3_1','INCOMPATIBLE_WITH_SMOOTH_EULER','smooth ideal Euler flow, embedded filament advected without reconnection','TOPOLOGICAL_NO_GO','Smooth Euler material transport cannot change knot type. Requires additional non-Euler dynamics.','CHECKED_THEOREM_ASSUMPTIONS','Kelvin/Helmholtz','KNOT_TYPE_PRESERVATION')
claim('M017','SST-36','SRC-SST36','p. 2 eq. (4)',r'E[K]=\epsilon_0 A L[K]+\beta L[K]+\alpha C[K]+\gamma H[K]','MATHEMATICAL_ANSATZ','geometry functionals need definitions and dimensionful couplings','COUPLINGS_OPEN','Well-formed as a functional if coefficients carry correct SI units; not proven to be physical energy.','CHECKED_ALGEBRA','filament geometry','ENERGY_CURVATURE_HELICITY')
claim('M018','SST-36','SRC-SST36','p. 3 eq. (15)',r'\Delta\lambda=\frac{h}{m_ec}(1-\cos\theta)','ESTABLISHED_KINEMATICS_ONLY','photon energy momentum and relativistic electron already supplied','PASS_METRES','Kinematic Compton formula correct; does not derive photon ontology or SST source dynamics.','CHECKED_ALGEBRA','QED kinematics','SST_COMPTON_INDEPENDENCE')
claim('M019','SST-36','SRC-SST36','p. 6, visibility',r'\mathcal V=e^{-\Gamma t}','MATHEMATICAL_CONSTRUCTION','Markov dephasing model','PASS_DIMENSIONLESS','A common phenomenological model, not evidence of topology-changing collapse.','CHECKED_ALGEBRA','dephasing rate','DECOHERENCE_BASELINES')
claim('M020','SST-29','SRC-KELVIN-A','p. 2 eq. (1)',r'\omega(k)\simeq\frac{\Gamma}{4\pi}k^2\left[\ln\frac1{|k|\xi}+C_0\right]','CONDITIONAL_KELVIN_DISPERSION','thin filament, weak bending, |k|xi <<1, core dependent C0','PASS_S_MINUS_1','Standard approximate small-wave Kelvin relation; not evidence for atomic-electron filaments.','CHECKED_ALGEBRA','Gamma,k,xi,C0','PKLSA_KELVIN_DISPERSION')
claim('M021','SST-29','SRC-KELVIN-A','p. 2 eq. (2)',r'k_m=2\pi m/L','ESTABLISHED_WITH_ASSUMPTIONS','periodic smooth filament loop, valid longitudinal modes','PASS_M_MINUS_1','Periodic mode quantization; real knotted loop modes can mix beyond this simple spectrum.','CHECKED_ALGEBRA','loop L','KNOT_MODES')
claim('M022','SST-29','SRC-KELVIN-A','p. 3 eqs. (6)-(9)',r'U=\Delta/(e^{\Delta/(k_BT)}-1)\sim\Delta e^{-\Delta/(k_BT)}','ESTABLISHED_WITH_ASSUMPTIONS','independent bosonic oscillator with postulated positive excitation gap','PASS_JOULES','Correct thermal excitation energy with zero-point excluded; DOES NOT prove existence or magnitude of Kelvin gap.','CHECKED_NUMERIC','gap and k_B T','THERMAL_GAP_MODEL')
claim('M023','SST-29','SRC-KELVIN-A','p. 5 eqs. (11)-(13)',r'\Delta_K/(k_BT_{eff})\gtrsim60\Rightarrow\Delta_K\gtrsim500\,{\rm eV}\ (T=10^5K)','CONDITIONAL_NUMERIC_BOUND','postulated gap ratio >=60, chosen T_eff=100000 K','PASS_NUMERIC','Numerical implication gives 517 eV. Threshold of 60 requires independently validated spectroscopy/noise budget.','CHECKED_NUMERIC','k_B, T_eff, threshold','GAP_REQUIRED_FROM_DATA')
claim('M024','SST-29','SRC-KELVIN-A','p. 8 eq. (22)',r'\omega_1=2.8\times10^{17}\,s^{-1}\quad\Rightarrow\quad\hbar\omega_1=29.5\,eV','NUMERICALLY_INCONSISTENT','hbar CODATA 1.054571817e-34','FAIL_NUMERIC','Given angular frequency corresponds to ~184.3 eV. Formula with stated Gamma, L, xi, C0=1 yields ~161.7 eV.','DETECTED_FAIL','hbar,eV conversion','KELVIN_FREQ_ENERGY_AUDIT')
claim('M025','SST-29','SRC-KELVIN-A','p. 3, gap dimensional estimate',r'\Delta_K\sim\Gamma^2/(4\pi\xi L)','DIMENSIONALLY_INCONSISTENT','no omitted factors with dimensions','FAIL_ENERGY','Gamma^2/(xi L) has m^2/s^2 (specific energy), not joules; needs a mass or inertia.','DETECTED_FAIL','Gamma,xi,L','KELVIN_GAP_DIMENSION')
claim('M026','SST-29','SRC-KELVIN-A','p. 3, tension estimate',r'T_f\sim\rho\Gamma^2/(4\pi\xi^2)','DIMENSIONALLY_INCONSISTENT_AS_TENSION','rho mass per volume','FAIL_LINE_TENSION','Units are pressure kg m^-1 s^-2, not force N or energy/length.','DETECTED_FAIL','rho,Gamma,xi','TENSION_UNITS')
claim('M027','SST-29','SRC-KELVIN-B','p. 4 eqs. (9)-(10)',r'\Delta_K>0\ \text{topological Kelvin gap}','HYPOTHESIS_UNTESTED','requires native Euler/PKLSA spectral gap and convergence','NOT_ESTABLISHED','A closed loop has discretized modes, but a universal gap of 0.5 keV is not established by kinematic quantization.','NOT_TESTED','mode spectrum','PKLSA_GAP_BLIND')
claim('M028','SST-29','SRC-KELVIN-B','p. 5 eqs. (19)-(20)',r'\delta\mathcal F/\delta\psi^*=0\Rightarrow -\hbar^2\nabla^2\psi/(2m_e)+V\psi=E\psi','CONDITIONAL_VARIATIONAL_IDENTITY','postulate Schrodinger energy functional and norm','PASS_UNDER_ANSATZ','Correct variation; does not derive Schrodinger from Euler because the functional was assumed.','CHECKED_VARIATION','postulated F','EULER_TO_SCHRODINGER')
claim('M029','SST-29','SRC-KELVIN-B','p. 4 eq. (8)',r'a_n\lesssim10^{-62}\,\mathrm{J\,K^{-2}}','UNVERIFIED_EMPIRICAL_BOUND','spectroscopy precision, temperature model and fitting relation must be supplied','PASS_UNITS_ONLY','Source provides bound without traceable independent data calculation; do not canonize as measured.','NOT_TESTED','experimental comparison','SPECTROSCOPY_BOUND')
claim('M030','SST-XX','SRC-DUAL','p. 3 eq. (3)',r'D\boldsymbol\omega/Dt=(\boldsymbol\omega\cdot\nabla)\mathbf v','ESTABLISHED_WITH_ASSUMPTIONS','smooth incompressible inviscid Euler, constant density, no external torque','PASS_S_MINUS_2','Correct vorticity-stretching identity; acceleration alone does not necessarily imply stretching.','CHECKED_ALGEBRA','Euler eq','ACCELERATION_VS_STRETCH')
claim('M031','SST-XX','SRC-DUAL','p. 3 eqs. (8)-(9)',r'Z_S=\rho_{\!f}v_s,\quad\kappa_{se}=4Z_S/Z_{bound}','MATHEMATICAL_ANSATZ','effective acoustic impedance; boundary model supplied','PASS_DIMENSIONLESS','Impedance numbers yield ~0.7657 Rayl and ratio ~3.06e-7 for Zbound=1e7; not a transfer rate.','CHECKED_NUMERIC','rho_f,v_s,Zbound','TRANSDUCTION_COUPLING')
claim('M032','SST-XX','SRC-DUAL','p. 4 eqs. (11)-(13)',r'\dot n_S=-(\Gamma_S+\gamma_d+\kappa_{se})n_S','DIMENSIONALLY_INCONSISTENT','Gamma and gamma are s^-1, kappa from impedance is dimensionless','FAIL_RATE_UNITS','Must introduce a distinct exchange rate k_SE [s^-1] and coupling efficiency epsilon_SE.','DETECTED_FAIL','M031','RATE_MODEL_UNITS')
claim('M033','SST-XX','SRC-DUAL','p. 4 eq. (13)',r'n_{EM}(t)={k_{SE}n_S(0)\over\lambda_{EM}-\lambda_S}\left(e^{-\lambda_St}-e^{-\lambda_{EM}t}\right)','CONDITIONAL_ODE_SOLUTION','lambda_S and lambda_EM are rates, zero initial nEM','PASS_IF_RATES','Mathematically correct solution after repair of rate units and inclusion initial nS.','CHECKED_NUMERIC','M032','RATE_ODE_SOLUTION')
claim('M034','SST-XX','SRC-DUAL','pp. 2-3 eqs. (2),(7)',r'\eta=c/v_s\simeq274,\quad\tau_S\sim(v_s/c)\tau_\gamma','MATHEMATICAL_SCALING_ANSATZ','two speeds, non-derived relation of delays','PASS_DIMENSIONLESS','Arithmetic tauS~0.11 ns for 30ns; manuscript statement that slower sector responds faster does not follow from speeds.','CHECKED_NUMERIC','c,v_s,tau_gamma','DELAY_MECHANISM')
claim('M035','SST-XX','SRC-DUAL','p. 3 eq. (10)',r'\nabla\times\mathbf E=-\partial_t\mathbf B-G\,\partial_t(\nabla\times\mathbf v)\,\hat{\mathbf n}','ILL_DEFINED_TENSOR_EXPRESSION','a vector multiplied by another vector with unspecified contraction','FAIL_VECTOR_STRUCTURE','Cannot add to Faraday vector equation without an explicit scalar contraction/tensor operator and consistent G units.','CHECKED_SYMBOLIC','director n,G','TORSION_FARADAY_OPERATOR')
claim('M036','SST-XX','SRC-DUAL','p. 2 eq. (6)',r'T_{SST}=\hbar a/(2\pi k_Bv_s)','MATHEMATICAL_FORMAL_ANALOGY','Unruh formula replaces c with v_s','PASS_KELVIN','Units correct; quantum thermal spectrum, detector response and fluctuation state not derived.','CHECKED_ALGEBRA','a,hbar,k_B,v_s','UNRUH_ANALOGUE')
claim('M037','SST-36','SRC-SST36','p. 5 eqs. (16)-(18)',r'V=|\langle e^{i\delta\phi}\rangle|','ESTABLISHED_WITH_ASSUMPTIONS','normalized two-path interference with equal path intensities','PASS_DIMENSIONLESS','Source writes visibility as complex average; physical visibility is magnitude. For unequal intensities requires contrast prefactor.','CHECKED_ALGEBRA','phase distribution','INTERFERENCE_VISIBILITY')
claim('M038','SST-35','SRC-SST35','p. 1 Voigt normalization',r'V(\Delta;\sigma,\Gamma)={\Re w[(\Delta+i\Gamma)/(\sigma\sqrt2)]\over\sigma\sqrt{2\pi}}','ESTABLISHED_WITH_ASSUMPTIONS','Gaussian sigma>0, Lorentz gamma HWHM>0, normalized line shapes','PASS_INV_RAD_S','Unit-area Voigt profile; source amplitude Bn Gamma^2 and unnormalized Gaussian require additional prefactors.','CHECKED_NUMERIC','Gaussian,Lorentzian','SPECTRAL_OVERLAP_NORMALIZATION')
claim('M039','SST-33','SRC-SST33T','p. 3 eqs. (2)-(4)',r'\partial_t N=-i[\Omega,N]-\Gamma\circ(N-N^{(0)})-\tfrac12\{V_x,\partial_x N\}','MATHEMATICAL_MODEL','density matrix mode dynamics, phenomenological damping','COUPLING_UNITS_OPEN','Damping conflicts with strictly conservative closed Euler sector unless coupling to bath/coarse-graining explicit.','NOT_TESTED','Gamma,bath,M','DISSIPATION_PROVENANCE')
claim('M040','VAM-05','SRC-VAM5','p. 41 fig. 10',r'T(2,3)\cong T(3,2)','ESTABLISHED_TOPOLOGY','unoriented torus-knot classes','PASS_TOPOLOGY','Swapping p,q yields equivalent torus knot rather than opposite-handed mirror.','CHECKED_THEOREM_ASSUMPTIONS','knot isotopy','MIRROR_TOPOLOGY')
claim('M041','SST-29','SRC-KELVIN-A','p. 8 Appendix A',r'\Gamma_{paper}=h/m_e\neq 2\pi r_c\mathbf v_{\!\boldsymbol{\circlearrowleft}}=\Gamma_{SST}',
 'CANON_INCONSISTENCY','paper explicitly substitutes h/me; current SST canon has Gamma=2*pi*rc*v_swirl','FAIL_PRIMITIVE_MISMATCH',
 'The prescribed circulation h/me is about 7.51e4 times the canonical SST filament circulation, so numerical mode energies cannot be ported without selecting an explicit circulation contract.',
 'CHECKED_NUMERIC','h,me,rc,swirl_speed','CIRCULATION_BLIND_CONTRACT')
write_jsonl('curated_claims.jsonl',cur)
write_csv('curated_claims.csv',cur,['claim_id','paper_id','source_id','source_locator','formula_latex','evidence_status','scope_or_assumptions','dimension_status','test_status','audit_comment','dependencies','suggested_falsifier','review_level'])

# Construct issue list with precise source locations and implications.
issue_status={'INCONSISTENT','INCONSISTENT_AS_MASS','NUMERICALLY_INCONSISTENT','DIMENSIONALLY_INCONSISTENT','DIMENSIONALLY_INCONSISTENT_AS_TENSION','DIMENSIONALLY_INCONSISTENT_AS_MASS','ILL_DEFINED_TENSOR_EXPRESSION','INCOMPATIBLE_WITH_SMOOTH_EULER'}
issues=[]
for c in cur:
 if c['evidence_status'] in issue_status or c['dimension_status'].startswith('FAIL'):
  issues.append({'claim_id':c['claim_id'],'source':c['source_id'],'location':c['source_locator'],
   'severity':'CRITICAL' if c['test_status']=='DETECTED_FAIL' or c['evidence_status']=='INCONSISTENT' else 'HIGH',
   'problem':c['audit_comment'],'needed_action':c['suggested_falsifier']})
write_csv('issues.csv',issues,['claim_id','source','location','severity','problem','needed_action'])

# A transparent numerical audit - these values are not measured SST observables.
pi=math.pi; hbar=1.054571817e-34; eV=1.602176634e-19; c=299792458.0
me=9.1093837139e-31; kb=1.380649e-23
rc=1.40897017e-15;rho_f=7.0e-7;vs=1.09384563e6
Gamma=2*pi*hbar/me; L=2*pi*5.29e-11; k1=2*pi/L; xi=1e-15
omega=Gamma/(4*pi)*k1*k1*(math.log(1/(k1*xi))+1.0)
gap_ratio=60*kb*1e5/eV
report={'version':'0.1.0','status':'DEVELOPMENT_NOT_PHYSICALLY_CERTIFIED',
'summary_index':{'sst_id_range':'00..90','sst_ids_mentioned':len(mentioned),'sst_ids_missing_in_mentions':[f'SST-{i:02d}' for i in sorted(set(range(91))-mentioned)],
    'sst_with_explicit_heading':len(headings),'vam_id_range':'01..15','raw_equations_from_AI_MD':len(formula_candidates),
    'curated_manually_audited_claims':len(cur),'issues_flagged':len(issues)},
'numerical_checks':{'kelvin_given_omega_rad_s':2.8e17,'kelvin_given_energy_eV':29.5,
   'calculated_energy_from_quoted_omega_eV':2.8e17*hbar/eV,
   'calculated_omega_from_stated_filament_parameters_rad_s':omega,
   'calculated_energy_from_filament_parameters_eV':omega*hbar/eV,
   'minimum_gap_eV_for_ratio60_at_1e5K':gap_ratio,
   'swirl_impedance_Rayl':rho_f*vs,'boundary_transduction_efficiency_for_1e7_Rayl':4*rho_f*vs/1e7,
   'gamma_kelvin_paper_m2_s':Gamma,'gamma_sst_canon_m2_s':2*pi*rc*vs,'gamma_ratio_paper_to_canon':Gamma/(2*pi*rc*vs),
   'swirl_frequency_rad_s':vs/rc,'swirl_energy_density_J_m3':rho_f*vs*vs/2,
   'test_that_kelvin_gap_is_real':'UNRESOLVED','native_pklsa_provider':'NOT_CONNECTED'},
'knowledge_limits':['Secondary summary ratings are not independent proofs.',
 'No exhaustive validation of all SST/VAM equations is claimed.',
 'Lack of original source for most SST 00..90 papers blocks manuscript-level verification.',
 'Paper-ID association for combined group headings is automatically assigned, not independently validated.',
 'Thermal gap is hypothesized; low-temperature Boltzmann factors do not imply it exists.']}
write_json('qualification_summary.json',report)
print(json.dumps(report['summary_index'],indent=2))
