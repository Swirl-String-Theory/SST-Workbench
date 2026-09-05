from __future__ import annotations

from typing import Any


def _cluster_q(entries: list[dict[str, Any]], tol: float) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    for e in sorted(entries, key=lambda x: float(x["q"])):
        if not groups:
            groups.append([e])
            continue
        mean = sum(float(x["q"]) for x in groups[-1]) / len(groups[-1])
        if abs(float(e["q"]) - mean) <= tol:
            groups[-1].append(e)
        else:
            groups.append([e])
    return groups


def evaluate_fourier_convergence(
    case_results: list[dict[str, Any]],
    *,
    q_cluster_tol: float = 0.015,
    q_gate_tol: float = 0.010,
) -> list[dict[str, Any]]:
    """Cluster only same Fourier-sector / same |m| candidates across numerical ladders."""
    buckets: dict[tuple[str, int, int], list[dict[str, Any]]] = {}
    for case in case_results:
        for cand in case["result"]["candidates"]:
            key = (str(cand["kind"]), int(cand["sector"]), int(cand["dominant_abs_m"]))
            buckets.setdefault(key, []).append({
                "axis": case["axis"],
                "case": case["case"],
                "value": case["value"],
                **cand,
            })

    out: list[dict[str, Any]] = []
    for (kind, sector, abs_m), entries in buckets.items():
        for group in _cluster_q(entries, q_cluster_tol):
            qs = [float(e["q"]) for e in group]
            by_axis: dict[str, list[dict[str, Any]]] = {}
            for e in group:
                by_axis.setdefault(str(e["axis"]), []).append(e)

            def one(axis: str, value: Any):
                return next((e for e in by_axis.get(axis, []) if e["value"] == value), None)

            r64, r96, r128 = one("resolution", 64), one("resolution", 96), one("resolution", 128)
            s2, s3 = one("image_shell", 2), one("image_shell", 3)
            fd = by_axis.get("fd_eps", [])

            gate_res_hi = bool(r96 and r128 and abs(float(r96["q"]) - float(r128["q"])) <= q_gate_tol)
            gate_res_triplet = bool(
                r64 and r96 and r128
                and max(float(r64["q"]), float(r96["q"]), float(r128["q"]))
                - min(float(r64["q"]), float(r96["q"]), float(r128["q"])) <= q_cluster_tol
            )
            gate_shell = bool(s2 and s3 and abs(float(s2["q"]) - float(s3["q"])) <= q_gate_tol)
            fd_q = [float(e["q"]) for e in fd]
            gate_fd = bool(len(fd) >= 3 and max(fd_q) - min(fd_q) <= q_gate_tol)
            case_ids = [(str(e["axis"]), str(e["case"])) for e in group]
            gate_unique = len(case_ids) == len(set(case_ids))
            promoted = bool(gate_res_hi and gate_res_triplet and gate_shell and gate_fd and gate_unique)

            out.append({
                "kind": kind + "_cluster",
                "sector": sector,
                "dominant_abs_m": abs_m,
                "q_mean": sum(qs) / len(qs),
                "q_min": min(qs),
                "q_max": max(qs),
                "n_entries": len(group),
                "gate_resolution_N96_N128": gate_res_hi,
                "gate_resolution_N64_N96_N128": gate_res_triplet,
                "gate_image_shell_2_3": gate_shell,
                "gate_fd_at_least_3": gate_fd,
                "gate_unique_candidate_per_case": gate_unique,
                "promote_converged_candidate": promoted,
                "entries": group,
            })
    return sorted(out, key=lambda x: (x["q_mean"], x["dominant_abs_m"], x["kind"]))
