from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any
import math


DEFAULT_GATE_SET = ("H2", "H3", "P3", "P4", "P5", "P6")


def _state(v: Any) -> str:
    if v is True:
        return "PASS"
    if v is False:
        return "FAIL"
    return "INELIGIBLE"


def _numeric_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def finite(vals):
        return [float(x) for x in vals if x is not None and math.isfinite(float(x))]
    h3 = finite([r.get("relative_equilibrium", {}).get("normal_nrmse") for r in rows])
    p5 = finite([r.get("energy_partition_high", {}).get("exterior_energy_fraction") for r in rows])
    p6 = finite([r.get("far_field", {}).get("velocity_decay_exponent") for r in rows])
    def stat(x):
        if not x: return None
        return {"min": min(x), "max": max(x), "range": max(x)-min(x), "mean": sum(x)/len(x), "n": len(x)}
    return {"H3_normal_nrmse": stat(h3), "P5_exterior_energy_fraction": stat(p5), "P6_velocity_decay_exponent": stat(p6)}


def evaluate_cross_source_consistency(samples: list[dict[str, Any]], errors: list[dict[str, Any]], cfg: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
    t = cfg["thresholds"]
    gate_set = tuple(cfg.get("cross_source", {}).get("gate_set", DEFAULT_GATE_SET))
    min_providers = int(t["cross_source_min_provider_groups"])
    min_topologies = int(t["cross_source_min_topologies"])
    min_agree = float(t["cross_source_min_agreement_fraction"])

    # Generated/derived carriers cannot close X0. E011 primary/anchor populations are upstream-only by contract.
    upstream = [s for s in samples if not bool(s.get("source_generated", False))]
    by_topology: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for s in upstream:
        by_topology[str(s["topology_group_id"])].append(s)

    comparisons = []
    qualified_topologies = 0
    all_pass = True
    for top_id in sorted(by_topology):
        rows = by_topology[top_id]
        by_provider: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in rows:
            by_provider[str(r["provider_group_id"])].append(r)
        if len(by_provider) < min_providers:
            continue
        qualified_topologies += 1
        gate_rows = []
        topology_pass = True
        for gid in gate_set:
            provider_votes: dict[str, str] = {}
            provider_details: dict[str, Any] = {}
            for provider, prows in sorted(by_provider.items()):
                states = [_state(r.get("sample_gate_pass", {}).get(gid)) for r in prows]
                c = Counter(states)
                # Multiple carrier variants from one provider are not independent votes.
                # If they disagree, the provider vote is explicitly inconsistent.
                vote = states[0] if len(c) == 1 else "INTERNAL_INCONSISTENCY"
                provider_votes[provider] = vote
                provider_details[provider] = {"states": dict(c), "n_carriers": len(states), "vote": vote}
            counts = Counter(provider_votes.values())
            n = len(provider_votes)
            agree = (max(counts.values()) / n) if n else 0.0
            gp = bool(n >= min_providers and agree >= min_agree and "INTERNAL_INCONSISTENCY" not in counts)
            topology_pass = topology_pass and gp
            gate_rows.append({
                "gate_id": gid,
                "provider_votes": provider_votes,
                "provider_details": provider_details,
                "state_counts": dict(counts),
                "agreement_fraction": float(agree),
                "pass": gp,
            })
        all_pass = all_pass and topology_pass
        comparisons.append({
            "topology_group_id": top_id,
            "n_upstream_carriers": len(rows),
            "n_provider_groups": len(by_provider),
            "n_source_families": len({str(r["source_family_group_id"]) for r in rows}),
            "topology_pass": topology_pass,
            "gate_comparisons": gate_rows,
            "numeric_dispersion_informational": _numeric_summary(rows),
        })

    metrics = {
        "gate_set": list(gate_set),
        "n_public_samples": len(samples),
        "n_upstream_samples": len(upstream),
        "n_generated_samples_excluded_from_closure": len(samples) - len(upstream),
        "n_qualified_cross_source_topologies": qualified_topologies,
        "minimum_provider_groups": min_providers,
        "minimum_topologies": min_topologies,
        "minimum_agreement_fraction": min_agree,
        "n_evaluation_errors": len(errors),
        "comparisons": comparisons,
    }
    if errors:
        return "FAIL", metrics, "One or more E011 STATIC_READY carrier evaluations failed, so cross-source consistency cannot be certified from the admitted panel."
    if qualified_topologies < min_topologies:
        return "UNRESOLVED", metrics, "Too few topologies contain the preregistered minimum number of distinct upstream E011 provider groups."
    if all_pass:
        return "PASS", metrics, "All eligible topology/provider comparisons meet the preregistered classification-agreement threshold; generated carriers did not count toward closure."
    return "FAIL", metrics, "At least one topology/gate classification is provider-dependent beyond the preregistered agreement threshold."
