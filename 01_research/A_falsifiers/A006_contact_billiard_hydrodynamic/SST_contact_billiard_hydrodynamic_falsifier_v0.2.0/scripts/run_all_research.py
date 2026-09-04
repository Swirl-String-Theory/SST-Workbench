from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

import numpy as np

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from sstcbhf.constants import R_C
from sstcbhf.io import load_gilbert_curve, load_gilbert_database, write_xyz


COMPLETED_RETURN_CODES = {0, 2}  # 2 means a scientific gate failed; that is a valid falsification result.


@dataclass(frozen=True)
class Preset:
    name: str
    source_samples: int
    geometry_samples: int
    convergence_resolutions: tuple[int, ...]
    hydro_samples_main: int
    hydro_resolution_ladder: tuple[int, ...]
    core_ratios_main: tuple[float, ...]
    core_ratios_sensitivity: tuple[float, ...]
    exclusion_fractions: tuple[float, ...]
    local_bands: tuple[int, ...]
    jitter_amplitudes_over_diameter: tuple[float, ...]


PRESETS: dict[str, Preset] = {
    "quick": Preset(
        "quick", 4096, 256, (128, 192, 256), 64, (48, 64),
        (0.10, 0.20, 0.35, 0.50, 0.75, 1.00), (0.20, 0.50, 1.00),
        (0.02, 0.03, 0.04), (2, 3, 4), (1e-4,),
    ),
    "full": Preset(
        "full", 8192, 512, (128, 192, 256, 384, 512, 768), 96, (64, 96, 128),
        (0.075, 0.10, 0.15, 0.20, 0.35, 0.50, 0.75, 1.00, 1.25),
        (0.20, 0.50, 1.00), (0.015, 0.02, 0.025, 0.03, 0.04, 0.05),
        (1, 2, 3, 4, 6), (3e-5, 1e-4, 3e-4),
    ),
    "max": Preset(
        "max", 16384, 768, (128, 192, 256, 384, 512, 768, 1024, 1536), 128,
        (64, 96, 128, 160),
        (0.05, 0.075, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.65, 0.80, 1.00, 1.25, 1.50),
        (0.10, 0.20, 0.35, 0.50, 0.75, 1.00),
        (0.0125, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.05, 0.06),
        (1, 2, 3, 4, 5, 6, 8),
        (1e-5, 3e-5, 1e-4, 3e-4, 1e-3),
    ),
    "extreme": Preset(
        "extreme", 32768, 1024, (192, 256, 384, 512, 768, 1024, 1536, 2048, 3072), 192,
        (64, 96, 128, 160, 192, 224),
        (0.03, 0.04, 0.05, 0.075, 0.10, 0.125, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50,
         0.65, 0.80, 1.00, 1.25, 1.50, 2.00),
        (0.075, 0.10, 0.15, 0.20, 0.35, 0.50, 0.75, 1.00, 1.50),
        (0.01, 0.0125, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.05, 0.06, 0.075),
        (0, 1, 2, 3, 4, 5, 6, 8, 10, 12),
        (3e-6, 1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3),
    ),
}


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _json_safe(value):
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, Path):
        return str(value)
    return value


def json_write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")


def csv_write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def rigid_transform(points: np.ndarray) -> np.ndarray:
    ax, ay, az = np.deg2rad([31.0, -17.0, 23.0])
    rx = np.array([[1, 0, 0], [0, np.cos(ax), -np.sin(ax)], [0, np.sin(ax), np.cos(ax)]])
    ry = np.array([[np.cos(ay), 0, np.sin(ay)], [0, 1, 0], [-np.sin(ay), 0, np.cos(ay)]])
    rz = np.array([[np.cos(az), -np.sin(az), 0], [np.sin(az), np.cos(az), 0], [0, 0, 1]])
    rotation = rz @ ry @ rx
    return points @ rotation.T + np.array([0.37, -0.21, 0.13])


def prepare_variants(database: Path, out: Path, preset: Preset) -> dict[str, Path]:
    points, _ = load_gilbert_curve(database, "3:1:1", preset.source_samples, 0)
    diameter = 1.0
    variants: dict[str, np.ndarray] = {
        "baseline": points,
        "cyclic_shift": np.roll(points, len(points) // 7, axis=0),
        "reverse_orientation": points[::-1].copy(),
        "rigid_transform": rigid_transform(points),
        "scale_half": 0.5 * points,
        "scale_double": 2.0 * points,
    }
    rng = np.random.default_rng(31092026)
    for amplitude in preset.jitter_amplitudes_over_diameter:
        noise = rng.normal(size=points.shape)
        noise /= np.maximum(np.linalg.norm(noise, axis=1, keepdims=True), 1e-15)
        variants[f"jitter_{amplitude:.0e}"] = points + amplitude * diameter * noise
    paths: dict[str, Path] = {}
    for name, curve in variants.items():
        path = out / f"{name}.xyz"
        write_xyz(path, curve)
        paths[name] = path
    return paths


def audit_database(database: Path, out: Path) -> dict:
    records = load_gilbert_database(database)
    entries = []
    for record in records:
        entries.append({
            "id": record.record_id,
            "conway": record.conway,
            "reported_length": record.reported_length,
            "diameter": record.diameter,
            "components": record.component_count,
            "coefficient_counts": [len(c) for c in record.components],
            "highest_modes": [max(x[0] for x in c) for c in record.components],
        })
    trefoil = next((x for x in entries if x["id"] == "3:1:1"), None)
    payload = {
        "database": str(database.resolve()),
        "sha256": sha256_file(database),
        "size_bytes": database.stat().st_size,
        "record_count": len(records),
        "trefoil": trefoil,
        "entries": entries,
    }
    json_write(out, payload)
    return payload


def gate_statuses(summary: dict) -> dict[str, str]:
    return {gate.get("gate_id", gate.get("id")): gate["status"] for gate in summary.get("gates", []) if gate.get("gate_id", gate.get("id"))}


def extract_metrics(summary: dict) -> dict:
    geometry = summary.get("geometry", {})
    contact = summary.get("contact", {})
    billiard = summary.get("billiard", {})
    force = summary.get("geometric_force", {})
    hydro = summary.get("hydrodynamics", [])
    full = [x for x in hydro if x.get("interaction") == "full"]
    nonlocal_rows = [x for x in hydro if x.get("interaction") == "nonlocal"]

    def finite_min(rows, key):
        values = [float(x[key]) for x in rows if x.get(key) is not None and np.isfinite(float(x[key]))]
        return min(values) if values else None

    return {
        "scientific_verdict": summary.get("scientific_verdict"),
        "samples": summary.get("settings", {}).get("samples"),
        "hydro_samples": summary.get("settings", {}).get("hydro_samples"),
        "exclusion_fraction": summary.get("settings", {}).get("exclusion_fraction"),
        "local_band": summary.get("settings", {}).get("local_band"),
        "length": geometry.get("length"),
        "thickness_proxy": geometry.get("thickness_proxy"),
        "ropelength_diameter_proxy": geometry.get("ropelength_diameter_proxy"),
        "contact_completeness": contact.get("completeness_fraction"),
        "contact_inverse_rms": contact.get("inverse_residual_rms"),
        "contact_orthogonality_rms": contact.get("orthogonality_rms"),
        "billiard_closure": billiard.get("closure_residual"),
        "billiard_branch_a_closure": billiard.get("branch_a_closure_residual"),
        "billiard_branch_b_closure": billiard.get("branch_b_closure_residual"),
        "billiard_paired_hausdorff": billiard.get("paired_orbit_hausdorff"),
        "force_compatibility": force.get("compatibility_relative_l2"),
        "force_inverse_compatibility": force.get("inverse_compatibility_relative_l2"),
        "force_local_balance": force.get("local_balance_relative_l2"),
        "best_full_relative_equilibrium": finite_min(full, "relative_equilibrium_residual"),
        "best_full_shape_residual": finite_min(full, "fitted_shape_residual"),
        "best_nonlocal_shape_residual": finite_min(nonlocal_rows, "fitted_shape_residual"),
    }


def extract_convergence_metrics(payload: dict) -> dict:
    rows = payload.get("rows", [])
    if not rows:
        return {}
    last = rows[-1]
    return {
        "samples": last.get("samples"),
        "length": last.get("length"),
        "thickness_proxy": last.get("thickness_proxy"),
        "ropelength_diameter_proxy": last.get("ropelength_diameter_proxy"),
        "contact_completeness": last.get("contact_completeness"),
        "contact_inverse_rms": last.get("contact_inverse_rms"),
        "billiard_branch_a_closure": last.get("billiard_a_closure"),
        "billiard_branch_b_closure": last.get("billiard_b_closure"),
        "billiard_paired_hausdorff": last.get("billiard_paired_orbit_hausdorff"),
        "convergence_levels": len(rows),
    }


class Runner:
    def __init__(self, root: Path, resume: bool, plan_only: bool):
        self.root = root
        self.resume = resume
        self.plan_only = plan_only
        self.rows: list[dict] = []
        self.infrastructure_failures: list[dict] = []
        self.planned: list[dict] = []
        self.env = dict(os.environ)
        self.env.setdefault("MPLBACKEND", "Agg")
        self.env.setdefault("PYTHONHASHSEED", "0")

    def checkpoint(self, current_step: str | None = None) -> None:
        json_write(self.root / "progress.json", {
            "updated_utc": datetime.now(timezone.utc).isoformat(),
            "current_step": current_step,
            "completed_rows": self.rows,
            "infrastructure_failures": self.infrastructure_failures,
            "planned_so_far": self.planned,
        })

    def run(self, name: str, category: str, arguments: list[str], output_dir: Path | None = None) -> None:
        command = [sys.executable, "-m", "sstcbhf", *arguments]
        relative_output = str(output_dir.relative_to(self.root)) if output_dir else None
        self.planned.append({"name": name, "category": category, "command": command, "output": relative_output})
        if self.plan_only:
            return
        result_path = None
        if output_dir:
            result_path = output_dir / ("convergence.json" if category == "convergence" else "summary.json")
        if self.resume and result_path and result_path.exists():
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            metrics = extract_convergence_metrics(payload) if category == "convergence" else extract_metrics(payload)
            gates = {} if category == "convergence" else gate_statuses(payload)
            row = {"name": name, "category": category, "state": "RESUMED", "return_code": None, **metrics, **gates}
            self.rows.append(row)
            self.checkpoint()
            return
        self.checkpoint(current_step=name)
        log_dir = self.root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{name}.log"
        started = time.perf_counter()
        printable = subprocess.list2cmdline(command)
        print(f"\n[STEP {len(self.planned)}] START {name}", flush=True)
        print(printable, flush=True)
        with log_path.open("w", encoding="utf-8", errors="replace", buffering=1) as log_handle:
            log_handle.write(f"START_UTC={datetime.now(timezone.utc).isoformat()}\n")
            log_handle.write(f"COMMAND={printable}\n\n")
            log_handle.flush()
            proc = subprocess.Popen(
                command,
                cwd=PACKAGE_ROOT,
                env=self.env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                log_handle.write(line)
                log_handle.flush()
                print(f"[{name}] {line}", end="", flush=True)
            return_code = proc.wait()
            elapsed = time.perf_counter() - started
            log_handle.write(f"\nEND_UTC={datetime.now(timezone.utc).isoformat()}\n")
            log_handle.write(f"RETURN_CODE={return_code}\nELAPSED_S={elapsed:.6f}\n")
        print(f"[{name}] END rc={return_code} elapsed={elapsed / 60.0:.2f} min", flush=True)
        state = "COMPLETED" if return_code in COMPLETED_RETURN_CODES else "INFRASTRUCTURE_FAILURE"
        row = {"name": name, "category": category, "state": state, "return_code": return_code, "elapsed_s": elapsed, "log": str(log_path.relative_to(self.root))}
        if result_path and result_path.exists():
            try:
                payload = json.loads(result_path.read_text(encoding="utf-8"))
                if category == "convergence":
                    row.update(extract_convergence_metrics(payload))
                else:
                    row.update(extract_metrics(payload))
                    row.update(gate_statuses(payload))
            except Exception as exc:  # report malformed output instead of hiding it
                row["result_read_error"] = repr(exc)
                state = "INFRASTRUCTURE_FAILURE"
                row["state"] = state
        elif output_dir is not None:
            row["result_read_error"] = f"{result_path.name if result_path else 'result file'} missing"
            state = "INFRASTRUCTURE_FAILURE"
            row["state"] = state
        self.rows.append(row)
        if state == "INFRASTRUCTURE_FAILURE":
            self.infrastructure_failures.append(row)
        self.checkpoint()


def build_campaign(runner: Runner, database: Path, preset: Preset, variants: dict[str, Path], campaign_root: Path) -> None:
    common_db = ["--database", str(database), "--id", "3:1:1", "--source-samples", str(preset.source_samples)]

    runner.run(
        "contact_convergence", "convergence",
        ["convergence", *common_db, "--resolutions", *map(str, preset.convergence_resolutions), "--exclusion-fraction", "0.03", "--out", str(campaign_root / "geometry" / "contact_convergence")],
        campaign_root / "geometry" / "contact_convergence",
    )

    # Geometry-only falsification and parameter sensitivity.
    for fraction in preset.exclusion_fractions:
        name = f"exclusion_{fraction:.4f}".replace(".", "p")
        out = campaign_root / "geometry" / "exclusion_sweep" / name
        runner.run(name, "exclusion_sweep", ["analyze", *common_db, "--samples", str(preset.geometry_samples), "--hydro-samples", "32", "--skip-hydro", "--exclusion-fraction", str(fraction), "--out", str(out)], out)

    for name, path in variants.items():
        out = campaign_root / "geometry" / "invariance_and_noise" / name
        runner.run(f"variant_{name}", "invariance_noise", ["analyze", "--input", str(path), "--source-samples", str(preset.source_samples), "--samples", str(preset.geometry_samples), "--hydro-samples", "32", "--skip-hydro", "--exclusion-fraction", "0.03", "--out", str(out)], out)

    # Negative controls: they are expected to fail one or more gates.
    out = campaign_root / "controls" / "analytic_torus_trefoil"
    runner.run("control_torus_trefoil", "negative_control", ["demo", "--samples", str(min(preset.geometry_samples, 512)), "--hydro-samples", str(min(preset.hydro_samples_main, 96)), "--out", str(out)], out)
    for record_id, label in [("0:1:1", "unknot_circle"), ("4:1:1", "figure_eight")]:
        out = campaign_root / "controls" / label
        runner.run(f"control_{label}", "negative_control", ["analyze", "--database", str(database), "--id", record_id, "--source-samples", str(preset.source_samples), "--samples", str(min(preset.geometry_samples, 512)), "--hydro-samples", "32", "--skip-hydro", "--out", str(out)], out)

    # Highest-information baseline: all interaction partitions and dense finite-core sweep.
    main_out = campaign_root / "hydrodynamics" / "main_full_local_nonlocal"
    runner.run(
        "hydro_main", "hydrodynamics_main",
        ["analyze", *common_db, "--samples", str(preset.geometry_samples), "--hydro-samples", str(preset.hydro_samples_main),
         "--exclusion-fraction", "0.03", "--core-ratios", *map(str, preset.core_ratios_main),
         "--hydro-interactions", "full", "local", "nonlocal", "--local-band", "3",
         "--physical-thickness", repr(R_C), "--out", str(main_out)],
        main_out,
    )

    # Hydro discretization ladder with a smaller but representative core set.
    for hydro_n in preset.hydro_resolution_ladder:
        out = campaign_root / "hydrodynamics" / "resolution_sweep" / f"N{hydro_n}"
        runner.run(
            f"hydro_resolution_N{hydro_n}", "hydro_resolution",
            ["analyze", *common_db, "--samples", str(min(preset.geometry_samples, 768)), "--hydro-samples", str(hydro_n),
             "--core-ratios", *map(str, preset.core_ratios_sensitivity), "--hydro-interactions", "full", "nonlocal",
             "--local-band", "3", "--physical-thickness", repr(R_C), "--out", str(out)],
            out,
        )

    # Nonlocal index-split sensitivity. Full is retained as a same-run reference.
    for band in preset.local_bands:
        out = campaign_root / "hydrodynamics" / "local_band_sweep" / f"band_{band}"
        runner.run(
            f"local_band_{band}", "local_band_sweep",
            ["analyze", *common_db, "--samples", str(min(preset.geometry_samples, 512)), "--hydro-samples", str(min(preset.hydro_samples_main, 96)),
             "--core-ratios", *map(str, preset.core_ratios_sensitivity), "--hydro-interactions", "full", "nonlocal",
             "--local-band", str(band), "--physical-thickness", repr(R_C), "--out", str(out)],
            out,
        )

    # SI dimensional scaling guard. Shape metrics should remain invariant while SI force scales change.
    for factor in (0.5, 1.0, 2.0):
        out = campaign_root / "hydrodynamics" / "physical_scale_sweep" / f"rc_x_{factor:g}".replace(".", "p")
        runner.run(
            f"physical_scale_{factor:g}".replace(".", "p"), "physical_scale_sweep",
            ["analyze", *common_db, "--samples", str(min(preset.geometry_samples, 512)), "--hydro-samples", str(min(preset.hydro_samples_main, 96)),
             "--core-ratios", *map(str, preset.core_ratios_sensitivity), "--hydro-interactions", "full", "nonlocal",
             "--local-band", "3", "--physical-thickness", repr(factor * R_C), "--out", str(out)],
            out,
        )

    # Hydrodynamic orientation/rigid-motion invariance at representative core ratios.
    for variant_name in ("baseline", "reverse_orientation", "rigid_transform"):
        out = campaign_root / "hydrodynamics" / "hydro_invariance" / variant_name
        runner.run(
            f"hydro_invariance_{variant_name}", "hydro_invariance",
            ["analyze", "--input", str(variants[variant_name]), "--samples", str(min(preset.geometry_samples, 512)),
             "--hydro-samples", str(min(preset.hydro_samples_main, 96)), "--core-ratios", *map(str, preset.core_ratios_sensitivity),
             "--hydro-interactions", "full", "nonlocal", "--local-band", "3", "--physical-thickness", repr(R_C), "--out", str(out)],
            out,
        )


def create_archive(root: Path) -> Path:
    archive = root.with_suffix(".zip")
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=str(Path(root.name) / path.relative_to(root)))
    archive.with_suffix(archive.suffix + ".sha256").write_text(f"{sha256_file(archive)}  {archive.name}\n", encoding="ascii")
    return archive



def robustness_summary(rows: list[dict]) -> dict:
    numeric_keys = [
        "ropelength_diameter_proxy", "contact_inverse_rms", "contact_orthogonality_rms",
        "billiard_branch_a_closure", "billiard_branch_b_closure", "billiard_paired_hausdorff",
        "force_compatibility", "force_inverse_compatibility", "best_full_relative_equilibrium",
        "best_full_shape_residual", "best_nonlocal_shape_residual",
    ]
    result: dict[str, dict] = {}
    categories = sorted({str(row.get("category")) for row in rows})
    for category in categories:
        group = [row for row in rows if str(row.get("category")) == category]
        stats = {}
        for key in numeric_keys:
            values = []
            for row in group:
                value = row.get(key)
                if value is not None:
                    try:
                        number = float(value)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(number):
                        values.append(number)
            if values:
                mean = float(np.mean(values))
                stats[key] = {
                    "count": len(values),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "mean": mean,
                    "absolute_range": float(np.ptp(values)),
                    "relative_range_over_abs_mean": float(np.ptp(values) / max(abs(mean), 1e-30)),
                }
        gate_counts = {}
        for gate in [f"H{i}" for i in range(9)]:
            counts = {}
            for row in group:
                value = row.get(gate)
                if value:
                    counts[str(value)] = counts.get(str(value), 0) + 1
            if counts:
                gate_counts[gate] = counts
        result[category] = {"row_count": len(group), "metrics": stats, "gate_counts": gate_counts}
    return result

def write_report(root: Path, preset: Preset, audit: dict, runner: Runner, elapsed_s: float) -> None:
    csv_write(root / "research_index.csv", runner.rows)
    gate_rows = []
    for row in runner.rows:
        gate_rows.append({"name": row.get("name"), "category": row.get("category"), **{f"H{i}": row.get(f"H{i}") for i in range(9)}})
    csv_write(root / "gate_matrix.csv", gate_rows)

    verdict_counts: dict[str, int] = {}
    for row in runner.rows:
        verdict = row.get("scientific_verdict") or row.get("state") or "UNKNOWN"
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
    robustness = robustness_summary(runner.rows)
    json_write(root / "robustness_summary.json", robustness)
    manifest = {
        "schema": "sst.cbhf.run-all.v0.2",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "preset": asdict(preset),
        "database_audit": audit,
        "elapsed_s": elapsed_s,
        "planned_steps": runner.planned,
        "completed_rows": runner.rows,
        "infrastructure_failures": runner.infrastructure_failures,
        "verdict_counts": verdict_counts,
        "robustness_summary": robustness,
        "scientific_exit_policy": "Gate failures are valid research results; only infrastructure failures make RUN_ALL return non-zero.",
    }
    json_write(root / "run_manifest.json", manifest)
    lines = [
        f"# SST contact–billiard–hydrodynamic run-all report ({preset.name})",
        "",
        f"- Database SHA-256: `{audit['sha256']}`",
        f"- Database records: {audit['record_count']}",
        f"- Completed campaign rows: {len(runner.rows)}",
        f"- Infrastructure failures: {len(runner.infrastructure_failures)}",
        f"- Wall time: {elapsed_s / 3600.0:.3f} h",
        "",
        "## Verdict counts",
        "",
    ]
    lines += [f"- `{key}`: {value}" for key, value in sorted(verdict_counts.items())]
    lines += [
        "",
        "## Interpretation guard",
        "",
        "A scientific FAIL is not a software failure. It is the intended outcome when a geometry, contact, billiard, force-balance, or hydrodynamic gate rejects the hypothesis.",
        "The regularized filament calculation remains a finite-core proxy and is not a resolved three-dimensional Euler-core simulation.",
        "",
        "See `research_index.csv`, `gate_matrix.csv`, and each campaign's `summary.json` for quantitative evidence.",
    ]
    (root / "RESEARCH_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the complete SST contact-billiard-hydrodynamic falsification matrix.")
    parser.add_argument("--database", type=Path, default=Path("data/ideal_favorites.txt"))
    parser.add_argument("--preset", choices=sorted(PRESETS), default="max")
    parser.add_argument("--out-root", type=Path, default=Path("outputs/run_all"))
    parser.add_argument("--resume", action="store_true", help="reuse the newest run for this preset and skip completed outputs")
    parser.add_argument("--new-run", action="store_true", help="start a fresh timestamped run even when --resume is set")
    parser.add_argument("--force", action="store_true", help="delete an explicitly selected existing run directory")
    parser.add_argument("--run-id", help="fixed output folder name; default is UTC timestamp")
    parser.add_argument("--plan-only", action="store_true", help="write the campaign plan without executing numerical steps")
    parser.add_argument("--no-archive", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    package_root = PACKAGE_ROOT
    database = (package_root / args.database).resolve() if not args.database.is_absolute() else args.database.resolve()
    if not database.exists():
        print(f"ERROR: database not found: {database}", file=sys.stderr)
        return 1
    preset = PRESETS[args.preset]
    out_base = (package_root / args.out_root).resolve() if not args.out_root.is_absolute() else args.out_root.resolve()
    preset_base = out_base / preset.name
    existing_runs = sorted((p for p in preset_base.iterdir() if p.is_dir()), key=lambda p: p.name) if preset_base.exists() else []
    if args.run_id:
        root = preset_base / args.run_id
    elif args.resume and existing_runs and not args.new_run:
        root = existing_runs[-1]
    else:
        root = preset_base / utc_stamp()
    if root.exists() and args.force:
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    (out_base / "LATEST_RUN.txt").write_text(str(root) + "\n", encoding="utf-8")

    started = time.perf_counter()
    audit = audit_database(database, root / "database_audit.json")
    variants = prepare_variants(database, root / "input_variants", preset)
    runner = Runner(root, resume=args.resume, plan_only=args.plan_only)
    build_campaign(runner, database, preset, variants, root / "campaigns")
    json_write(root / "campaign_plan.json", {"preset": asdict(preset), "steps": runner.planned})

    if args.plan_only:
        print(f"PLAN_ONLY: {len(runner.planned)} steps")
        print(root)
        return 0

    elapsed = time.perf_counter() - started
    write_report(root, preset, audit, runner, elapsed)
    archive = None if args.no_archive else create_archive(root)
    print(f"Completed {len(runner.rows)} steps in {elapsed / 3600.0:.3f} h")
    print(f"Infrastructure failures: {len(runner.infrastructure_failures)}")
    print(f"Results: {root}")
    if archive:
        print(f"Archive: {archive}")
    return 1 if runner.infrastructure_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
