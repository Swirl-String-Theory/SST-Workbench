from __future__ import annotations
import argparse
import json
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from sklsa.selection import load_selection, selected_ids
from sklsa.parent import normalize_workbench_root, locate_e010_output, validate_e010_release, extract_e010_subset
from sklsa.loaders import load_topology_bundle
from sklsa.analysis import (
    admission_record, join_carriers, build_availability, representative_rows,
    mirror_fallback_representative, consensus_rows, pairwise_rows, summarize_topology,
)
from sklsa.output import write_json, write_jsonl, write_csv


def main() -> int:
    ap = argparse.ArgumentParser(description="E011 SKLSA v0.2.0 — selected E010-v0.3.1 literature-gated carrier atlas")
    ap.add_argument("--workbench-root", default=r"C:\workspace\projects\SST-Workbench")
    ap.add_argument("--e010-output", help="E010-v0.3.1 output directory or output ZIP")
    ap.add_argument("--mode", choices=["poc", "core", "selected"], default="selected")
    ap.add_argument("--include-sentinels", action="store_true")
    ap.add_argument("--include-controls", action="store_true")
    ap.add_argument("--output-root")
    args = ap.parse_args()

    root = Path(args.workbench_root).absolute() if args.e010_output else normalize_workbench_root(args.workbench_root)
    selection = load_selection(HERE / "configs" / "selected_topologies.json")
    parent_contract = json.loads((HERE / "configs" / "parent_e010.json").read_text(encoding="utf-8"))
    metric_cfg = json.loads((HERE / "configs" / "metrics.json").read_text(encoding="utf-8"))

    if args.mode == "poc":
        wanted = list(selection["poc"])
    elif args.mode == "core":
        wanted = list(selection["core_knots"])
    else:
        wanted = selected_ids(selection, include_controls=args.include_controls, include_sentinels=args.include_sentinels)
    wanted = list(dict.fromkeys(wanted))

    located = locate_e010_output(root, args.e010_output)
    tmp = None
    parent_input = {"input_kind": "directory", "input_path": str(located)}
    if located.is_file():
        tmp = tempfile.TemporaryDirectory(prefix="e011_e010_subset_")
        e010, zip_meta = extract_e010_subset(located, wanted, Path(tmp.name))
        parent_input.update(zip_meta)
    else:
        e010 = located

    parent_check = validate_e010_release(e010, parent_contract)
    release = parent_check["release"]
    parent_warnings = parent_check["warnings"]
    campaign = json.loads((e010 / "CAMPAIGN_INDEX.json").read_text(encoding="utf-8"))
    campaign_passed = set(campaign.get("passed", []))

    out = Path(args.output_root) if args.output_root else HERE / "E011_SKLSA_Selected_Qualified_Carrier_Analysis_v0.2.0-outputs"
    out.mkdir(parents=True, exist_ok=True)

    family_order = metric_cfg["source_family_order"]
    metric_names = metric_cfg["metrics"]
    all_carriers, all_admitted_carriers, all_availability, all_reps, all_consensus, all_pairs = [], [], [], [], [], []
    topology_summaries, admission_rows, operational_errors = [], [], []

    for topology_id in wanted:
        bundle = load_topology_bundle(e010, topology_id)
        admission = admission_record(bundle, campaign_passed)
        admission_rows.append(admission)
        if bundle.get("status") != "LOADED":
            operational_errors.append({"topology_id": topology_id, "error": bundle.get("status"), "missing": bundle.get("missing", [])})
            topology_summaries.append({"topology_id": topology_id, "status": bundle.get("status"), "admitted": False})
            continue

        carriers = join_carriers(bundle)
        for r in carriers:
            r["topology_id"] = topology_id
        availability = build_availability(bundle, family_order, carriers)

        # Always write E010-derived diagnostics, even when the topology is excluded.
        topo_dir = out / "topologies" / topology_id
        write_json(topo_dir / "E010_ADMISSION.json", admission)
        write_json(topo_dir / "CARRIER_AVAILABILITY.json", availability)
        write_json(topo_dir / "E010_CARRIERS.json", carriers)

        admitted_carriers = [c for c in carriers if c.get("literature_hard_gate_pass") is True]
        write_json(topo_dir / "ADMITTED_CARRIERS.json", admitted_carriers)

        strict, extended, mirror_fallback, consensus, pairs = [], [], [], [], []
        if admission.get("admitted"):
            strict = representative_rows(admitted_carriers, "strict_upstream")
            extended = representative_rows(admitted_carriers, "extended_qualified")
            if not extended:
                mirror_fallback = mirror_fallback_representative(admitted_carriers)
            for r in strict + extended + mirror_fallback:
                r["topology_id"] = topology_id
            consensus = consensus_rows(topology_id, strict, metric_names, "strict_upstream")
            consensus += consensus_rows(topology_id, extended, metric_names, "extended_qualified")
            pairs = pairwise_rows(topology_id, strict, metric_names, "strict_upstream")
            pairs += pairwise_rows(topology_id, extended, metric_names, "extended_qualified")
            write_json(topo_dir / "PROVIDER_REPRESENTATIVES.json", {"strict_upstream": strict, "extended_qualified": extended, "mirror_fallback_provenance_only": mirror_fallback})
            write_json(topo_dir / "METRIC_CONSENSUS.json", consensus)
            write_json(topo_dir / "PAIRWISE_METRIC_DELTAS.json", pairs)

        topo_summary = summarize_topology(bundle, admission, carriers, strict, extended, mirror_fallback)
        write_json(topo_dir / "SUMMARY.json", topo_summary)

        all_carriers.extend(carriers)
        all_admitted_carriers.extend(admitted_carriers)
        all_availability.extend(availability)
        all_reps.extend(strict + extended + mirror_fallback)
        all_consensus.extend(consensus)
        all_pairs.extend(pairs)
        topology_summaries.append(topo_summary)

    write_json(out / "PARENT_RELEASE.json", release)
    write_json(out / "PARENT_INPUT.json", parent_input)
    write_json(out / "PARENT_WARNINGS.json", parent_warnings)
    write_json(out / "SELECTION.json", {"mode": args.mode, "topology_ids": wanted, "include_sentinels": args.include_sentinels, "include_controls": args.include_controls})
    write_json(out / "E010_ADMISSION_MATRIX.json", admission_rows)
    write_json(out / "TOPOLOGY_SUMMARIES.json", topology_summaries)
    write_json(out / "OPERATIONAL_ERRORS.json", operational_errors)
    write_jsonl(out / "E010_CARRIERS.jsonl", all_carriers)
    write_jsonl(out / "ADMITTED_CARRIERS.jsonl", all_admitted_carriers)
    write_jsonl(out / "PROVIDER_REPRESENTATIVES.jsonl", all_reps)
    write_csv(out / "CARRIER_AVAILABILITY.csv", all_availability)
    write_csv(out / "METRIC_CONSENSUS.csv", all_consensus)
    write_csv(out / "PAIRWISE_METRIC_DELTAS.csv", all_pairs)
    write_csv(out / "E010_ADMISSION_MATRIX.csv", admission_rows)

    admitted = [r for r in admission_rows if r.get("admitted")]
    excluded = [r for r in admission_rows if not r.get("admitted") and not str(r.get("admission_status", "")).startswith("ERROR_")]
    gate_failure_counts = Counter()
    for r in excluded:
        gate_failure_counts.update(r.get("literature_gate_failure_counts", {}))

    execution_gate = "PASS" if not operational_errors and len(admission_rows) == len(wanted) else "FAIL_CLOSED"
    atlas_status = "COMPLETE" if len(admitted) == len(wanted) else "PARTIAL_CARRIER_ADMISSION"
    summary = {
        "schema": "E011-SKLSA-SELECTED-LITERATURE-GATED-CARRIER-ATLAS-1",
        "e011_version": "0.2.0",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "workbench_root": str(root),
        "e010_input_kind": parent_input.get("input_kind"),
        "e010_input": parent_input.get("input_path"),
        "e010_input_sha256": parent_input.get("input_sha256"),
        "e010_release_version": release.get("e010_version"),
        "e010_full_campaign_gate_pass": release.get("full_campaign_gate_pass"),
        "e010_publication_ready_geometry_layer": release.get("publication_ready_geometry_layer"),
        "e010_failed_topology_count": release.get("failed_topology_count"),
        "mode": args.mode,
        "selected_topology_count": len(wanted),
        "admitted_topology_count": len(admitted),
        "excluded_by_e010_gate_count": len(excluded),
        "operational_error_count": len(operational_errors),
        "admitted_topology_ids": [r["topology_id"] for r in admitted],
        "excluded_topology_ids": [r["topology_id"] for r in excluded],
        "literature_gate_failure_counts_across_excluded_carriers": dict(gate_failure_counts),
        "carrier_rows_from_selected_topologies": len(all_carriers),
        "literature_admitted_carrier_rows": len(all_admitted_carriers),
        "literature_excluded_carrier_rows": len(all_carriers) - len(all_admitted_carriers),
        "mirror_carrier_rows_all_selected": sum(1 for r in all_carriers if r.get("analysis_evidence_class") == "MIRROR"),
        "mirror_carrier_rows_admitted": sum(1 for r in all_admitted_carriers if r.get("analysis_evidence_class") == "MIRROR"),
        "strict_upstream_representative_rows": sum(1 for r in all_reps if r.get("representative_scope") == "strict_upstream"),
        "extended_representative_rows": sum(1 for r in all_reps if r.get("representative_scope") == "extended_qualified"),
        "mirror_fallback_representative_rows": sum(1 for r in all_reps if r.get("representative_scope") == "mirror_fallback_provenance_only"),
        "mirror_fallback_topology_count": sum(1 for r in topology_summaries if r.get("mirror_fallback_representative_count", 0) > 0),
        "strict_cross_provider_topology_count": sum(1 for r in topology_summaries if r.get("strict_cross_provider_comparison_possible")),
        "extended_cross_provider_topology_count": sum(1 for r in topology_summaries if r.get("extended_cross_provider_comparison_possible")),
        "execution_gate": execution_gate,
        "atlas_status": atlas_status,
        "scientific_boundary": "E011 v0.2.0 performs carrier-level selection inside the requested E010-v0.3.1 topologies. Carriers failing any hard literature gate remain visible as exclusions but never enter representatives or consensus. Aggregate E010 topology failure is preserved as context and is not silently reinterpreted as carrier failure.",
    }
    write_json(out / "RUN_SUMMARY.json", summary)
    print(json.dumps(summary, indent=2))
    if tmp is not None:
        tmp.cleanup()
    return 0 if execution_gate == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
