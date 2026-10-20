"""One-time deterministic issuance of three synthetic source datasets."""
from __future__ import annotations
import pathlib,random
from .security import writejson,create_seal,create_global_commitment

def make(root):
    root=pathlib.Path(root)
    if list((root/'seals').glob('*.seal.json')):raise RuntimeError('already sealed; source data regeneration is prohibited')
    r=random.Random(20261014)
    cases=[]
    for name, g, rho in [
        ('potential_stagnation',[[.37,0,0],[0,-.37,0],[0,0,0]],1.2),
        ('rigid_rotation',[[0,-.28,0],[.28,0,0],[0,0,0]],0.95),
        ('simple_shear',[[0,.51,0],[0,0,0],[0,0,0]],1.7)]:
        for n in range(8):
            p=[r.uniform(-0.5,0.5),r.uniform(-0.5,0.5),r.uniform(-0.5,0.5)]
            cases.append(dict(name=name,gradient=g,rho=rho,c_star=3.7,point=p))
    writejson(root/'data'/'D01_EULER'/'cases.json',{'dataset_id':'D01_EULER','class':'synthetic_control','cases':cases,'provenance':'analytic steady linear flow; no PKLSA solver'})
    surfaces={
      'A':{'name':'A','kind':'toy_sheet','M':[1.0,1.2],'K':[[4.4,.25],[.25,5.6]],'b':[.29,.12],'lambda_bare':2.5},
      'B':{'name':'B','kind':'toy_sheet','M':[1.25,1.0],'K':[[5.1,-.12],[-.12,3.9]],'b':[.21,.20],'lambda_bare':1.65},
      'C':{'name':'C','kind':'decoupled','M':[1.0,1.0],'K':[[4.0,0.0],[0.0,4.0]],'b':[0.0,0.0],'lambda_bare':0.0}}
    graph={'theta':[.13,-.24,.52],'phi':[.02,-.01,.07], 'omega0':[1.8,1.6,1.9], 'clock_N':[.96,.99,.94],
      'edges':[{'i':0,'j':1,'vartheta':.23,'E':.19},{'i':1,'j':2,'vartheta':-.15,'E':-.07},{'i':0,'j':2,'vartheta':.04,'E':.11}]}
    writejson(root/'data'/'D02_CLOCK_LINK'/'single_surface.json',{'dataset_id':'D02_CLOCK_LINK','class':'synthetic_control','graph':graph,'surfaces':surfaces,'imaginary_frequencies':[0,.2,.6,1.0,2.0,4.0], 'provenance':'independent toy oscillator Hessians and explicit bare sheet stiffness; NOT derived from PKLSA'})
    distances=[.60,.85,1.10,1.50,2.0,2.8,4.0]
    conditions=[]
    for pair in [('A','B'),('A','C'),('B','B')]:
        for T in [.8,1.6]:
            for a in distances:
                conditions.append({'surface_1':pair[0],'surface_2':pair[1],'temperature_dimensionless':T,'distance':a})
    writejson(root/'data'/'D03_TWO_SURFACE'/'conditions.json',{'dataset_id':'D03_TWO_SURFACE','class':'synthetic_holdout','cases':conditions,'force_target_unavailable':True,'provenance':'predeclared two-surface geometry; no target force injected'})
    # The target lives outside all scientific kernels and is never loaded during BLIND.
    writejson(root/'private_reveal'/'targets.json',{
        'schema':'POST_SEAL_COMPARISON_ONLY','reference_exponent_ideal_em_T0':4.0,
        'reference_exponent_ideal_scalar_classical_T_gt_0':3.0,
        'reference_ideal_scalar_classical_pressure_coefficient_zeta3_over_8pi':0.04782832450341004,
        'reference_ideal_em_T0_pressure_coefficient_pi_squared_over_240':0.04112335167120566,
        'interpretation':'Exponent and coefficients are separate orthodox ideal-model comparators; neither is the toy sheet physical calibration.',
        'external_measurements_included':False})
    for ds in ['D01_EULER','D02_CLOCK_LINK','D03_TWO_SURFACE']:create_seal(root,ds)
    create_global_commitment(root)
