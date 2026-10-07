from __future__ import annotations
from pathlib import Path
import json,secrets,hashlib,random,itertools
from .geometry import (
    unlinked_three_rings,torus_link_3_3,borromean_braid,
    save_components_npz,geometry_sha256,pairwise_link_matrix
)
from .pklsa import write_upstream_plan,audit_required_topologies,materialize_anchor_geometry
from .composite import loose_components,decorate_skeleton
from .seal import sha256_file

ARCHITECTURES={
    'U':{'architecture':'unlinked'},
    'G':{'architecture':'triple_gear_T3_3'},
    'B':{'architecture':'borromean_skeleton'},
}

# bit 0 -> 5_2, bit 1 -> 6_1. All 2^3 assignments are preregistered.
TWIST_ASSIGNMENTS=[f'{i:03b}' for i in range(8)]


def _component_labels(bits:str):
    return ['6_1' if b=='1' else '5_2' for b in bits]


def _composition_class(bits:str):
    n61=bits.count('1'); n52=3-n61
    if n61==1: hist='uud_like_5_2x2_6_1x1'
    elif n61==2: hist='udd_like_5_2x1_6_1x2'
    else: hist='homogeneous_twist_control'
    return {'n_5_2':n52,'n_6_1':n61,'historical_composition_class':hist}


def _anon(salt,label):
    return 'CAND_'+hashlib.sha256((salt+'|'+label).encode()).hexdigest()[:16]


def _anchor_public_private_meta(a):
    return {k:a.get(k) for k in (
        'provider_group','static_seed_id','carrier_id','source_family',
        'static_ready','static_status','source_locator')}


def _skeletons(n):
    return {
        'U':unlinked_three_rings(n),
        'G':torus_link_3_3(n),
        'B':borromean_braid(n),
    }


def _build_factor_geometry(code,bits,k52,k61,skeletons,n):
    knots=[k61 if b=='1' else k52 for b in bits]
    if code=='U':
        return loose_components(knots,n=n),{'class':'pklsa_loose_components','twist_bits':bits}
    return decorate_skeleton(skeletons[code],knots,n=n)


def prepare(output_dir:Path,workbench:Path|None=None,n=144):
    output_dir.mkdir(parents=True,exist_ok=True)
    pub=output_dir/'blind_inputs'; priv=output_dir/'_private'
    pub.mkdir(exist_ok=True); priv.mkdir(exist_ok=True)
    salt=secrets.token_hex(32)
    write_upstream_plan(workbench,output_dir/'UPSTREAM_PLAN.json')

    skeletons=_skeletons(n)
    geometries={f'CTRL@@{code}':geom for code,geom in skeletons.items()}
    case_info={
        f'CTRL@@{code}':{
            'semantic_kind':'unknot_control','architecture_code':code,
            'twist_bits':None,'provider_stratum':None,
            'construction_certificate':{'class':f'analytic_{ARCHITECTURES[code]["architecture"]}_unknot_control'},
        } for code in ARCHITECTURES
    }
    unavailable={}; provider_meta={}; all_anchor_loads_ok=False; expected_strata=[]

    if workbench and workbench.exists():
        try:
            aud=audit_required_topologies(workbench)
            loaded={'5_2':[],'6_1':[]}
            for top in ('5_2','6_1'):
                provider_meta[top]=[]
                anchors=sorted(aud[top]['anchors'],key=lambda x:(x.get('provider_group',''),x.get('static_seed_id','')))
                for a in anchors:
                    provider_meta[top].append(_anchor_public_private_meta(a))
                    try:
                        curve=materialize_anchor_geometry(a,workbench,n)
                        loaded[top].append({'provider_group':a.get('provider_group'),'seed_id':a.get('static_seed_id'),'curve':curve})
                    except Exception as e:
                        unavailable[f'anchor:{top}:{a.get("static_seed_id")}']=str(e)
            all_anchor_loads_ok=(len(loaded['5_2'])==len(aud['5_2']['anchors']) and
                                 len(loaded['6_1'])==len(aud['6_1']['anchors']) and
                                 len(loaded['5_2'])>0 and len(loaded['6_1'])>0)

            # Preserve the v0.1.0 provider-envelope policy: every independent provider-anchor pair participates.
            for idx,(a52,a61) in enumerate(itertools.product(loaded['5_2'],loaded['6_1'])):
                stratum=f'S{idx:02d}'; expected_strata.append(stratum)
                pmeta={
                    'stratum_id':stratum,
                    '5_2':{'provider_group':a52['provider_group'],'static_seed_id':a52['seed_id']},
                    '6_1':{'provider_group':a61['provider_group'],'static_seed_id':a61['seed_id']},
                }
                for code,bits in itertools.product(ARCHITECTURES,TWIST_ASSIGNMENTS):
                    key=f'F@@{code}@@{bits}@@{stratum}'
                    try:
                        comps,cert=_build_factor_geometry(code,bits,a52['curve'],a61['curve'],skeletons,n)
                        geometries[key]=comps
                        case_info[key]={
                            'semantic_kind':'factor_cell','architecture_code':code,'twist_bits':bits,
                            'provider_stratum':pmeta,'construction_certificate':cert,
                        }
                    except Exception as e:
                        unavailable[f'case:{key}']=f'{type(e).__name__}: {e}'
        except Exception as e:
            unavailable['PKLSA_AUDIT_OR_LOAD']=f'{type(e).__name__}: {e}'
    else:
        unavailable['WORKBENCH']='Workbench unavailable; source-native PKLSA factor cells not prepared'

    expected_keys={f'CTRL@@{c}' for c in ARCHITECTURES}
    for st in expected_strata:
        expected_keys.update(f'F@@{c}@@{bits}@@{st}' for c in ARCHITECTURES for bits in TWIST_ASSIGNMENTS)
    scientific_ready=bool(expected_strata) and all_anchor_loads_ok and expected_keys.issubset(geometries)

    labels=list(geometries); random.SystemRandom().shuffle(labels)
    mapping={}; manifest=[]
    for key in labels:
        comps=geometries[key]; aid=_anon(salt,key); path=pub/f'{aid}.npz'
        save_components_npz(path,comps)
        ci=case_info[key]; code=ci['architecture_code']; bits=ci['twist_bits']
        private_sem={
            'case_key':key,'semantic_kind':ci['semantic_kind'],
            'architecture_code':code,**ARCHITECTURES[code],
            'twist_bits':bits,
            'components':['0_1','0_1','0_1'] if bits is None else _component_labels(bits),
            'provider_stratum':ci.get('provider_stratum'),
            'construction_certificate':ci.get('construction_certificate'),
            'geometry_sha256':geometry_sha256(comps),
            'private_pairwise_link_matrix':pairwise_link_matrix(comps).tolist(),
        }
        if bits is not None: private_sem.update(_composition_class(bits))
        mapping[aid]=private_sem
        manifest.append({
            'anonymous_id':aid,'file':path.name,'sha256':sha256_file(path),
            'geometry_sha256':geometry_sha256(comps),'component_count':len(comps)
        })

    private={
        'schema':'A054-PRIVATE-MAPPING-1.1','salt':salt,'mapping':mapping,'unavailable':unavailable,
        'provider_meta':provider_meta,'expected_provider_strata':expected_strata,
        'all_anchor_loads_ok':all_anchor_loads_ok,'expected_case_count':len(expected_keys),
        'factor_preregistration':{
            'architecture_codes':list(ARCHITECTURES),
            'twist_assignment_bits':TWIST_ASSIGNMENTS,
            'bit_convention':'0=5_2, 1=6_1',
            'polarity_sectors':{
                'Q0':'+++ unit','Q1':'-++ unit','Q2':'+-+ unit','Q3':'++- unit',
                'Q4':'+++ fixed-total','Q5':'-++ fixed-total','Q6':'+-+ fixed-total','Q7':'++- fixed-total',
            },
            'discovery_to_preregistration_note':'v0.1.0 observed a strong 2+1 polarity effect; v0.1.1 tests it prospectively across the complete binary twist-assignment cube and all skeletons.',
        },
    }
    pp=priv/'PRIVATE_MAPPING.json'; pp.write_text(json.dumps(private,indent=2),encoding='utf-8')
    public={
        'schema':'A054-BLIND-MANIFEST-1.1','scientific_ready':scientific_ready,
        'candidate_count':len(manifest),'candidates':manifest,
        'private_mapping_sha256':sha256_file(pp),'semantic_identity_fields_excluded':True,
        'circulation_sectors':[f'Q{i}' for i in range(8)],
        'anonymous_factor_counts':{'geometry_factor_levels':3,'binary_component_assignments':8,'polarity_sectors':8},
    }
    (output_dir/'BLIND_MANIFEST.json').write_text(json.dumps(public,indent=2),encoding='utf-8')
    status={
        'status':'PREPARED_FULL' if scientific_ready else 'PREPARED_PARTIAL_FAIL_CLOSED',
        'candidate_count':len(manifest),'expected_case_count_private':len(expected_keys),
        'unavailable_count':len(unavailable),
        'note':'A production v0.1.1 tournament requires every preregistered provider stratum and all 3 x 8 factor cells; partial controls are diagnostic only.',
    }
    (output_dir/'PREPARE_STATUS.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    return status
