from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Any, Iterable
import numpy as np

from .ideal_ab import parse_ideal_ab, sample_ideal_ab
from .geometry import resample_closed
from .physics import compute_blind

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "ideal_3_1_1.txt"


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=False), encoding="utf-8")


def write_csv(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key); fields.append(key)
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def prepare_centerline(*, data_path: str | Path = DEFAULT_DATA, knot_id: str = "3:1:1",
                       n: int = 128, oversample: int = 16) -> tuple[np.ndarray, dict[str, Any]]:
    model = parse_ideal_ab(data_path, knot_id=knot_id)
    n_hi = max(int(n) * int(oversample), 4096)
    raw = sample_ideal_ab(model, n_hi)
    center = resample_closed(raw, int(n))
    meta = {
        "data_path": str(data_path),
        "knot_id": model.knot_id,
        "conway": model.conway,
        "L_metadata": model.L,
        "D_metadata": model.D,
        "harmonic_count": int(len(model.harmonics)),
        "max_harmonic": int(np.max(model.harmonics)),
        "n": int(n),
        "oversample": int(oversample),
    }
    return center, meta


def run_blind_case(*, data_path: str | Path = DEFAULT_DATA, knot_id: str = "3:1:1", n: int = 128,
                   oversample: int = 16, offset_over_D: float = 0.5, eps_over_D: float = 0.05,
                   gamma_plus: float = 1.0, gamma_minus: float = -1.0, phase: float = 0.0,
                   force_python: bool = False, skip_build: bool = False,
                   force_build: bool = False, build_verbose: bool = False) -> dict[str, Any]:
    center, meta = prepare_centerline(data_path=data_path, knot_id=knot_id, n=n, oversample=oversample)
    blind = compute_blind(center, D=float(meta["D_metadata"]), offset_over_D=offset_over_D,
                          eps_over_D=eps_over_D, gamma_plus=gamma_plus, gamma_minus=gamma_minus, phase=phase,
                          force_python=force_python, skip_build=skip_build,
                          force_build=force_build, build_verbose=build_verbose)
    return {
        "protocol": "BLIND_HYDRODYNAMICS_NO_ALPHA_INPUT",
        "geometry": meta,
        "observables": blind.to_dict(),
    }


def run_grid(*, n_values=(64, 96, 128, 192), offsets=(0.10,0.20,0.30,0.40,0.50),
             eps_values=(0.025,0.05,0.10,0.20), data_path: str | Path = DEFAULT_DATA,
             knot_id: str = "3:1:1", force_python: bool = False,
             skip_build: bool = False, force_build: bool = False,
             build_verbose: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    first = True
    for n in n_values:
        center, meta = prepare_centerline(data_path=data_path, knot_id=knot_id, n=int(n))
        for off in offsets:
            for eps in eps_values:
                r = compute_blind(center, D=float(meta["D_metadata"]), offset_over_D=float(off),
                                  eps_over_D=float(eps), force_python=force_python,
                                  skip_build=(skip_build or not first),
                                  force_build=(force_build and first), build_verbose=(build_verbose and first))
                first = False
                row = {"knot_id": knot_id, "L_metadata": meta["L_metadata"], **r.to_dict()}
                rows.append(row)
    return rows
