from sklsa.static_ready import static_ready, build_seed_record, provider_anchors
from sklsa.agreement import provider_agreement_rows, topology_agreement_status

POLICY={
 "policy_version":"0.3.0",
 "static_ready":{"required_core_observables":["Wr","ACN","dcsd","kappa_rms"],"require_literature_hard_gate_pass":True,"exclude_evidence_classes":["MIRROR","UNCLASSIFIED"],"primary_evidence_classes":["UPSTREAM_INDEPENDENT"],"secondary_evidence_classes":["QUALIFIED_NONMIRROR","DERIVED_NUMERICAL"],"control_evidence_classes":["GENERATED_OR_CONTROL"]},
 "capabilities":{"writhe_ready":["Wr"],"ropelength_ready":["Rop"],"chirality_ready":["Wr"]},
 "provider_agreement":{"metrics":["Wr_abs","ACN","kappa_rms","dcsd"],"required_for_cross_provider_robust":["Wr_abs","ACN","kappa_rms","dcsd"],"bands":{"default":{"strong_max_relative_span":0.05,"acceptable_max_relative_span":0.15,"weak_max_relative_span":0.30},"dcsd":{"strong_max_relative_span":0.10,"acceptable_max_relative_span":0.30,"weak_max_relative_span":0.50}}}
}

def seed(cid,provider,wr=3.0,acn=5.0,dcsd=.07,k=.12,cls="UPSTREAM_INDEPENDENT",stage=None,role="independent_reference_geometry"):
 return {"carrier_id":cid,"topology_id":"3_1","provider_group":provider,"analysis_evidence_class":cls,"literature_hard_gate_pass":True,"literature_gate_status":{"G3_signed_frenet_chirality_completeness":"PASS"},"observable_status":{"Wr":"RESOLVED","ACN":"RESOLVED","dcsd":"RESOLVED","kappa_rms":"RESOLVED","Rop":"RESOLVED"},"finest_metrics":{"Wr":wr,"ACN":acn,"dcsd":dcsd,"kappa_rms":k,"Rop":16.4},"_stage":stage,"_role":role}

def record(s):
 sr={"geometry_sha256":"g"+s["carrier_id"],"carrier":{"carrier_id":s["carrier_id"],"source_role":s.pop("_role",None),"metadata":{"relaxation_stage":s.pop("_stage",None)},"source_path":"x"}}
 return build_seed_record(s,sr,POLICY)

def test_static_ready_core_and_mirror_guard():
 ok,reasons=static_ready(seed("A","p"),POLICY); assert ok and not reasons
 ok,reasons=static_ready(seed("M","p",cls="MIRROR"),POLICY); assert not ok and any("MIRROR" in x for x in reasons)

def test_provider_median_prevents_many_variants_from_extra_votes():
 a1=record(seed("A1","a",wr=3.0)); a2=record(seed("A2","a",wr=3.02)); a3=record(seed("A3","a",wr=2.98)); b=record(seed("B","b",wr=-3.03))
 rows=provider_agreement_rows("3_1",[a1,a2,a3,b],POLICY); by={r["metric"]:r for r in rows}
 assert by["Wr_abs"]["provider_count"]==2
 assert by["Wr_abs"]["seed_count"]==4
 assert by["Wr_abs"]["between_provider_relative_span"] < .02
 status,_=topology_agreement_status([a1,a2,a3,b],rows,POLICY); assert status=="CROSS_PROVIDER_ROBUST"

def test_provider_sensitive_is_not_seed_rejection():
 a=record(seed("A","a",wr=3.0)); b=record(seed("B","b",wr=1.0))
 rows=provider_agreement_rows("3_1",[a,b],POLICY); status,_=topology_agreement_status([a,b],rows,POLICY)
 assert status=="CROSS_PROVIDER_SENSITIVE" and a["static_ready"] and b["static_ready"]

def test_final_stage_anchor_beats_unspecified_trial_without_metric_optimization():
 trial=record(seed("T","knotplot",stage="UNSPECIFIED",role="historical_relaxation_state"))
 final=record(seed("F","knotplot",stage="FINAL",role="relaxed_reference_geometry"))
 anchors=provider_anchors([trial,final])
 assert anchors[0]["carrier_id"]=="F"
