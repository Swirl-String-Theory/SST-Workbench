from __future__ import annotations
from collections import defaultdict, Counter
from statistics import median
from math import isfinite

from .classify import evidence_class, contributes_to_scope

RESOLVED_STATUSES = {"RESOLVED"}
HARD_LITERATURE_GATES = (
    "G1_isotopy_safe_sampling",
    "G2_writhe_quadratic_convergence",
    "G3_signed_frenet_chirality_completeness",
)


def _num(x):
    try:
        y = float(x)
        return y if isfinite(y) else None
    except (TypeError, ValueError):
        return None


def admission_record(bundle: dict, campaign_passed: set[str] | None = None) -> dict:
    topo = bundle.get("topology_id")
    if bundle.get("status") != "LOADED":
        return {
            "topology_id": topo,
            "admission_status": "ERROR_MISSING_E010_ARTIFACTS",
            "admitted": False,
            "missing": bundle.get("missing", []),
        }
    gate = bundle.get("gate", {}) or {}
    summary = bundle.get("summary", {}) or {}
    metrics = bundle.get("metrics", {}) or {}
    failures = Counter()
    failed_carriers = []
    passed_carriers = []
    for row in metrics.get("carriers", []):
        if row.get("literature_hard_gate_pass") is True:
            passed_carriers.append(row.get("carrier_id"))
        elif row.get("literature_hard_gate_pass") is False:
            cid = row.get("carrier_id")
            failed_carriers.append(cid)
            for g in HARD_LITERATURE_GATES:
                if str((row.get("literature_gate_status") or {}).get(g, "")).upper() == "FAIL":
                    failures[g] += 1

    identity_ok = gate.get("identity_database_pass") is True
    admitted = identity_ok and bool(passed_carriers)
    aggregate_green = (
        gate.get("pass") is True
        and gate.get("geometry_qualification_pass") is True
        and summary.get("qualification_gate_pass") is True
        and summary.get("literature_hard_gate_pass") is True
    )
    if not identity_ok:
        status = "EXCLUDED_BY_E010_IDENTITY_GATE"
    elif not passed_carriers:
        status = "EXCLUDED_NO_LITERATURE_ADMITTED_CARRIER"
    elif aggregate_green:
        status = "ADMITTED_ALL_E010_CARRIERS_PASS"
    else:
        status = "ADMITTED_WITH_CARRIER_EXCLUSIONS"

    return {
        "topology_id": topo,
        "admission_status": status,
        "admitted": admitted,
        "campaign_index_passed": True if campaign_passed is None else topo in campaign_passed,
        "e010_aggregate_topology_gate_pass": gate.get("pass") is True,
        "geometry_qualification_pass_aggregate": gate.get("geometry_qualification_pass") is True,
        "identity_database_pass": identity_ok,
        "qualification_gate_pass_aggregate": summary.get("qualification_gate_pass") is True,
        "literature_hard_gate_pass_aggregate": summary.get("literature_hard_gate_pass") is True,
        "discovered_carriers": summary.get("discovered_carriers"),
        "qualified_carriers": summary.get("qualified_carriers"),
        "literature_admitted_carrier_count": len(passed_carriers),
        "literature_admitted_carrier_ids": passed_carriers,
        "literature_excluded_carrier_count": len(failed_carriers),
        "literature_excluded_carrier_ids": failed_carriers,
        "literature_gate_failure_counts": dict(failures),
        "policy_note": "E011 admission is carrier-level: a topology may remain usable when some E010 carriers fail literature gates, provided identity passes and at least one carrier passes all hard literature gates.",
    }


def join_carriers(bundle: dict) -> list[dict]:
    metrics_by = {r.get("carrier_id"): r for r in bundle["metrics"].get("carriers", [])}
    indep_entries = bundle["independence"].get("entries", [])
    rows: list[dict] = []
    for e in indep_entries:
        cid = e.get("carrier_id")
        m = metrics_by.get(cid, {})
        row = dict(e)
        row["analysis_evidence_class"] = evidence_class(e)
        row["finest_resolution"] = m.get("finest_resolution")
        row["overall_convergence"] = m.get("overall_convergence")
        row["observable_status"] = m.get("observable_status", {})
        row["finest_metrics"] = m.get("finest_metrics", {})
        row["reference_observables"] = m.get("reference_observables", {})
        row["scale_context"] = m.get("scale_context", {})
        row["literature_hard_gate_pass"] = m.get("literature_hard_gate_pass")
        row["literature_gate_status"] = m.get("literature_gate_status", {})
        rows.append(row)
    known = {r.get("carrier_id") for r in rows}
    for cid, m in metrics_by.items():
        if cid in known:
            continue
        rows.append({
            "carrier_id": cid,
            "catalog_id": m.get("catalog_id"),
            "source_family": m.get("source_family"),
            "analysis_evidence_class": "UNCLASSIFIED",
            "finest_resolution": m.get("finest_resolution"),
            "overall_convergence": m.get("overall_convergence"),
            "observable_status": m.get("observable_status", {}),
            "finest_metrics": m.get("finest_metrics", {}),
            "reference_observables": m.get("reference_observables", {}),
            "scale_context": m.get("scale_context", {}),
            "literature_hard_gate_pass": m.get("literature_hard_gate_pass"),
            "literature_gate_status": m.get("literature_gate_status", {}),
            "ledger_missing": True,
        })
    return rows


def build_availability(bundle: dict, family_order: list[str], carriers: list[dict] | None = None) -> list[dict]:
    by = {str(r.get("source_family")): r for r in bundle["source_matrix"]}
    families = list(dict.fromkeys([*family_order, *by.keys()]))
    carriers = carriers or []
    gate_by_family: dict[str, Counter] = defaultdict(Counter)
    for c in carriers:
        fam = str(c.get("source_family"))
        if c.get("literature_hard_gate_pass") is True:
            gate_by_family[fam]["literature_pass"] += 1
        elif c.get("literature_hard_gate_pass") is False:
            gate_by_family[fam]["literature_fail"] += 1
    out = []
    for family in families:
        r = by.get(family, {})
        def iv(k):
            try: return int(r.get(k, 0) or 0)
            except (TypeError, ValueError): return 0
        discovered, qualified, errors = iv("discovered"), iv("qualified"), iv("errors")
        if errors:
            status = "ERROR"
        elif qualified:
            status = "QUALIFIED_BY_E010"
        elif discovered:
            status = "DISCOVERED_NOT_QUALIFIED"
        else:
            status = "ABSENT"
        out.append({
            "topology_id": bundle["topology_id"],
            "source_family": family,
            "catalog_ids": r.get("catalog_ids", ""),
            "discovered": discovered,
            "qualified": qualified,
            "errors": errors,
            "independence_groups": iv("independence_groups"),
            "provider_groups": iv("provider_groups"),
            "literature_gate_pass_carriers": gate_by_family[family]["literature_pass"],
            "literature_gate_fail_carriers": gate_by_family[family]["literature_fail"],
            "availability_status": status,
        })
    return out


def representative_rows(carriers: list[dict], scope: str) -> list[dict]:
    eligible = [r for r in carriers if r.get("literature_hard_gate_pass") is True and contributes_to_scope(r.get("analysis_evidence_class", ""), scope)]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for r in eligible:
        key = r.get("provider_group") or r.get("independence_group") or r.get("carrier_id")
        grouped[str(key)].append(r)

    reps = []
    for provider, rows in grouped.items():
        def score(r: dict):
            statuses = r.get("observable_status", {}) or {}
            n_resolved = sum(1 for v in statuses.values() if str(v).upper() == "RESOLVED")
            res = int(r.get("finest_resolution") or 0)
            fam_priority = {
                "gilbert_ideal": 0, "fremlin_fourier": 1, "knotinfo_3d": 2,
                "knotplot_relaxed": 3, "knotplot_ideal": 4, "ridgerunner": 5,
                "knotplot_qhp": 6, "ptsa": 7, "siaf": 8,
            }.get(r.get("source_family"), 50)
            return (-n_resolved, -res, fam_priority, str(r.get("carrier_id")))
        chosen = sorted(rows, key=score)[0]
        c = dict(chosen)
        c["representative_scope"] = scope
        c["representative_group"] = provider
        c["representative_reason"] = "deterministic provider representative among E010 literature-admitted carriers; not a physical seed ranking"
        reps.append(c)
    return sorted(reps, key=lambda r: (str(r.get("representative_group")), str(r.get("carrier_id"))))


def mirror_fallback_representative(carriers: list[dict]) -> list[dict]:
    """Return one literature-admitted mirror only when no non-mirror representative exists.

    This keeps a usable geometry seed for provenance/engineering purposes without promoting
    the mirror to independent evidence or allowing it into consensus statistics.
    """
    mirrors = [r for r in carriers if r.get("literature_hard_gate_pass") is True and r.get("analysis_evidence_class") == "MIRROR"]
    if not mirrors:
        return []
    def score(r: dict):
        statuses = r.get("observable_status", {}) or {}
        n_resolved = sum(1 for v in statuses.values() if str(v).upper() == "RESOLVED")
        res = int(r.get("finest_resolution") or 0)
        return (-n_resolved, -res, str(r.get("source_family")), str(r.get("carrier_id")))
    c = dict(sorted(mirrors, key=score)[0])
    c["representative_scope"] = "mirror_fallback_provenance_only"
    c["representative_group"] = c.get("provider_group") or c.get("independence_group") or c.get("carrier_id")
    c["representative_reason"] = "literature-admitted mirror fallback; usable geometry seed only; never independent evidence and never included in consensus"
    return [c]


def _mad(values: list[float], med: float) -> float:
    return median([abs(v - med) for v in values]) if values else float("nan")


def consensus_rows(topology_id: str, reps: list[dict], metric_names: list[str], scope: str) -> list[dict]:
    out = []
    for metric in metric_names:
        base_metric = "Wr" if metric == "Wr_abs" else metric
        vals, carriers = [], []
        for r in reps:
            status = str((r.get("observable_status") or {}).get(base_metric, "")).upper()
            value = _num((r.get("finest_metrics") or {}).get(base_metric))
            if status in RESOLVED_STATUSES and value is not None:
                vals.append(abs(value) if metric == "Wr_abs" else value)
                carriers.append(r.get("carrier_id"))
        if not vals:
            out.append({"topology_id": topology_id, "scope": scope, "metric": metric, "n": 0, "status": "NO_RESOLVED_VALUES"})
            continue
        med = median(vals)
        lo, hi = min(vals), max(vals)
        denom = max(abs(med), 1e-15)
        out.append({
            "topology_id": topology_id,
            "scope": scope,
            "metric": metric,
            "n": len(vals),
            "median": med,
            "mad": _mad(vals, med),
            "min": lo,
            "max": hi,
            "relative_span": (hi - lo) / denom,
            "carrier_ids": carriers,
            "status": "CROSS_PROVIDER" if len(vals) >= 2 else "SINGLE_PROVIDER_ONLY",
        })
    return out


def pairwise_rows(topology_id: str, reps: list[dict], metric_names: list[str], scope: str) -> list[dict]:
    out = []
    for i, a in enumerate(reps):
        for b in reps[i+1:]:
            for metric in metric_names:
                base_metric = "Wr" if metric == "Wr_abs" else metric
                sa = str((a.get("observable_status") or {}).get(base_metric, "")).upper()
                sb = str((b.get("observable_status") or {}).get(base_metric, "")).upper()
                va = _num((a.get("finest_metrics") or {}).get(base_metric))
                vb = _num((b.get("finest_metrics") or {}).get(base_metric))
                if sa not in RESOLVED_STATUSES or sb not in RESOLVED_STATUSES or va is None or vb is None:
                    continue
                if metric == "Wr_abs":
                    va, vb = abs(va), abs(vb)
                den = max(abs(va), abs(vb), 1e-15)
                out.append({
                    "topology_id": topology_id,
                    "scope": scope,
                    "metric": metric,
                    "carrier_a": a.get("carrier_id"),
                    "provider_a": a.get("provider_group"),
                    "family_a": a.get("source_family"),
                    "carrier_b": b.get("carrier_id"),
                    "provider_b": b.get("provider_group"),
                    "family_b": b.get("source_family"),
                    "value_a": va,
                    "value_b": vb,
                    "abs_delta": abs(va - vb),
                    "relative_delta": abs(va - vb) / den,
                })
    return out


def summarize_topology(bundle: dict, admission: dict, carriers: list[dict], strict_reps: list[dict], extended_reps: list[dict], mirror_fallback: list[dict]) -> dict:
    gate = bundle.get("gate", {})
    summary = bundle.get("summary", {})
    mirror_count = sum(1 for r in carriers if r.get("analysis_evidence_class") == "MIRROR")
    lit_pass = sum(1 for r in carriers if r.get("literature_hard_gate_pass") is True)
    lit_fail = sum(1 for r in carriers if r.get("literature_hard_gate_pass") is False)
    if not admission.get("admitted"):
        status = admission.get("admission_status")
    elif mirror_fallback and not extended_reps:
        status = "ADMITTED_MIRROR_FALLBACK_ONLY"
    else:
        status = admission.get("admission_status")
    return {
        "topology_id": bundle["topology_id"],
        "status": status,
        "admitted": admission.get("admitted"),
        "e010_aggregate_topology_gate_pass": gate.get("pass") is True,
        "geometry_qualification_pass_aggregate": gate.get("geometry_qualification_pass") is True,
        "identity_database_pass": gate.get("identity_database_pass") is True,
        "qualification_gate_pass_aggregate": summary.get("qualification_gate_pass") is True,
        "literature_hard_gate_pass_aggregate": summary.get("literature_hard_gate_pass") is True,
        "literature_gate_failure_counts": admission.get("literature_gate_failure_counts", {}),
        "carrier_count": len(carriers),
        "literature_admitted_carrier_count": lit_pass,
        "literature_failed_carrier_count": lit_fail,
        "mirror_carrier_count": mirror_count,
        "strict_upstream_representative_count": len(strict_reps),
        "extended_representative_count": len(extended_reps),
        "mirror_fallback_representative_count": len(mirror_fallback),
        "strict_cross_provider_comparison_possible": len({r.get("provider_group") for r in strict_reps}) >= 2,
        "extended_cross_provider_comparison_possible": len({r.get("provider_group") for r in extended_reps}) >= 2,
        "strict_upstream_independent_provider_count_e010": bundle.get("independence", {}).get("strict_upstream_independent_provider_count"),
    }
