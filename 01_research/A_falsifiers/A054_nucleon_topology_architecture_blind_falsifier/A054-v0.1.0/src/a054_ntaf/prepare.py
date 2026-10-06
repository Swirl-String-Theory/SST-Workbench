from __future__ import annotations
from pathlib import Path
import json,secrets,hashlib,random,itertools
from .geometry import (
    unlinked_three_rings,torus_link_3_3,borromean_braid,
    save_components_npz,geometry_sha256,pairwise_link_matrix
)
from .pklsa import write_upstream_plan,audit_required_topologies,materialize_anchor_geometry
from .composite import loose_components,decorate_skeleton,CompositeConstructionError
from .seal import sha256_file

SEMANTIC={
 "C0":{"role":"common_null","architecture":"unlinked","components":["0_1","0_1","0_1"]},
 "P_A":{"role":"proton_hypothesis","architecture":"unlinked","components":["5_2","5_2","6_1"]},
 "P_B":{"role":"proton_hypothesis","architecture":"triple_gear_T3_3","components":["0_1","0_1","0_1"]},
 "P_C":{"role":"proton_hypothesis","architecture":"triple_gear_T3_3_decorated","components":["5_2","5_2","6_1"]},
 "N_A":{"role":"neutron_hypothesis","architecture":"unlinked","components":["5_2","6_1","6_1"]},
 "N_B":{"role":"neutron_hypothesis","architecture":"borromean_skeleton","components":["0_1","0_1","0_1"]},
 "N_C":{"role":"neutron_hypothesis","architecture":"borromean_skeleton_decorated","components":["5_2","6_1","6_1"]},
}

def _anon(salt,label):
    return "CAND_"+hashlib.sha256((salt+"|"+label).encode()).hexdigest()[:16]

def _anchor_public_private_meta(a):
    return {k:a.get(k) for k in (
        "provider_group","static_seed_id","carrier_id","source_family",
        "static_ready","static_status","source_locator")}

def prepare(output_dir:Path,workbench:Path|None=None,n=144):
    output_dir.mkdir(parents=True,exist_ok=True)
    pub=output_dir/"blind_inputs"; priv=output_dir/"_private"
    pub.mkdir(exist_ok=True); priv.mkdir(exist_ok=True)
    salt=secrets.token_hex(32)
    write_upstream_plan(workbench,output_dir/"UPSTREAM_PLAN.json")

    # case_key -> components. Only case_key/private map know semantics.
    geometries={
        "C0":unlinked_three_rings(n),
        "P_B":torus_link_3_3(n),
        "N_B":borromean_braid(n),
    }
    case_info={
        "C0":{"semantic_id":"C0","provider_stratum":None,"construction_certificate":{"class":"analytic_unlinked_control"}},
        "P_B":{"semantic_id":"P_B","provider_stratum":None,"construction_certificate":{"class":"analytic_T3_3_proxy"}},
        "N_B":{"semantic_id":"N_B","provider_stratum":None,"construction_certificate":{"class":"analytic_closed_braid_control"}},
    }
    unavailable={}; provider_meta={}; all_anchor_loads_ok=False; expected_strata=[]

    if workbench and workbench.exists():
        try:
            aud=audit_required_topologies(workbench)
            loaded={"5_2":[],"6_1":[]}
            for top in ("5_2","6_1"):
                provider_meta[top]=[]
                anchors=sorted(aud[top]["anchors"],key=lambda x:(x.get("provider_group",""),x.get("static_seed_id","")))
                for a in anchors:
                    provider_meta[top].append(_anchor_public_private_meta(a))
                    try:
                        curve=materialize_anchor_geometry(a,workbench,n)
                        loaded[top].append({"provider_group":a.get("provider_group"),"seed_id":a.get("static_seed_id"),"curve":curve})
                    except Exception as e:
                        unavailable[f"anchor:{top}:{a.get('static_seed_id')}"]=str(e)
            all_anchor_loads_ok=(len(loaded["5_2"])==len(aud["5_2"]["anchors"]) and
                                 len(loaded["6_1"])==len(aud["6_1"]["anchors"]) and
                                 len(loaded["5_2"])>0 and len(loaded["6_1"])>0)

            # Every provider anchor participates: use the Cartesian provider-anchor envelope.
            for idx,(a52,a61) in enumerate(itertools.product(loaded["5_2"],loaded["6_1"])):
                stratum=f"S{idx:02d}"
                expected_strata.append(stratum)
                pmeta={
                    "stratum_id":stratum,
                    "5_2":{"provider_group":a52["provider_group"],"static_seed_id":a52["seed_id"]},
                    "6_1":{"provider_group":a61["provider_group"],"static_seed_id":a61["seed_id"]},
                }
                k52,k61=a52["curve"],a61["curve"]
                cases={
                    "P_A":lambda: (loose_components([k52,k52,k61],n=n),{"class":"pklsa_loose_components"}),
                    "N_A":lambda: (loose_components([k52,k61,k61],n=n),{"class":"pklsa_loose_components"}),
                    "P_C":lambda: decorate_skeleton(geometries["P_B"],[k52,k52,k61],n=n),
                    "N_C":lambda: decorate_skeleton(geometries["N_B"],[k52,k61,k61],n=n),
                }
                for base,builder in cases.items():
                    key=f"{base}@@{stratum}"
                    try:
                        comps,cert=builder()
                        geometries[key]=comps
                        case_info[key]={"semantic_id":base,"provider_stratum":pmeta,"construction_certificate":cert}
                    except Exception as e:
                        unavailable[f"case:{key}"]=f"{type(e).__name__}: {e}"
        except Exception as e:
            unavailable["PKLSA_AUDIT_OR_LOAD"]=f"{type(e).__name__}: {e}"
    else:
        unavailable["WORKBENCH"]="Workbench unavailable; source-native PKLSA strata not prepared"

    # Full tournament requires the three common controls plus P_A/P_C/N_A/N_C for every
    # preregistered provider-anchor stratum, and every E011 anchor must have loaded.
    expected_keys={"C0","P_B","N_B"} if expected_strata else set(SEMANTIC)
    for s in expected_strata:
        expected_keys.update({f"P_A@@{s}",f"P_C@@{s}",f"N_A@@{s}",f"N_C@@{s}"})
    scientific_ready=bool(expected_strata) and all_anchor_loads_ok and expected_keys.issubset(geometries)

    labels=list(geometries); random.SystemRandom().shuffle(labels)
    mapping={}; manifest=[]
    for key in labels:
        comps=geometries[key]; aid=_anon(salt,key); path=pub/f"{aid}.npz"
        save_components_npz(path,comps)
        L=pairwise_link_matrix(comps); ci=case_info[key]; base=ci["semantic_id"]
        mapping[aid]={
            "case_key":key,"semantic_id":base,**SEMANTIC[base],
            "provider_stratum":ci.get("provider_stratum"),
            "construction_certificate":ci.get("construction_certificate"),
            "geometry_sha256":geometry_sha256(comps),
            "private_pairwise_link_matrix":L.tolist(),
        }
        manifest.append({
            "anonymous_id":aid,"file":path.name,"sha256":sha256_file(path),
            "geometry_sha256":geometry_sha256(comps),"component_count":len(comps)
        })

    private={
        "salt":salt,"mapping":mapping,"unavailable":unavailable,"provider_meta":provider_meta,
        "semantic_preregistration":SEMANTIC,"expected_provider_strata":expected_strata,
        "all_anchor_loads_ok":all_anchor_loads_ok,"expected_case_count":len(expected_keys),
    }
    pp=priv/"PRIVATE_MAPPING.json"
    pp.write_text(json.dumps(private,indent=2),encoding="utf-8")
    public={
        "schema":"A054-BLIND-MANIFEST-1.0","scientific_ready":scientific_ready,
        "candidate_count":len(manifest),"candidates":manifest,
        "private_mapping_sha256":sha256_file(pp),"semantic_identity_fields_excluded":True,
        "circulation_sectors":[f"Q{i}" for i in range(8)],
    }
    (output_dir/"BLIND_MANIFEST.json").write_text(json.dumps(public,indent=2),encoding="utf-8")
    status={
        "status":"PREPARED_FULL" if scientific_ready else "PREPARED_PARTIAL_FAIL_CLOSED",
        "candidate_count":len(manifest),"expected_case_count_private":len(expected_keys),
        "unavailable_count":len(unavailable),
        "note":"Partial controls/strata are not a production nucleon tournament when scientific_ready=false.",
    }
    (output_dir/"PREPARE_STATUS.json").write_text(json.dumps(status,indent=2),encoding="utf-8")
    return status
