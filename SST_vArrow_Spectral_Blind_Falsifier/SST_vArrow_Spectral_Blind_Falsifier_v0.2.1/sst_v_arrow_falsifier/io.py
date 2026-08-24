from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

REQUIRED_MANIFEST = {"sample_id", "input_type", "path"}


def load_manifest(campaign_dir: str | Path) -> pd.DataFrame:
    campaign_dir = Path(campaign_dir)
    path = campaign_dir / "manifest.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing campaign manifest: {path}")
    df = pd.read_csv(path)
    missing = REQUIRED_MANIFEST - set(df.columns)
    if missing:
        raise ValueError(f"manifest.csv missing columns: {sorted(missing)}")
    for col, default in {
        "family_id": "",
        "topology": "BLINDED",
        "resolution_n": np.nan,
        "core_radius_m": np.nan,
    }.items():
        if col not in df.columns:
            df[col] = default
    return df


def resolve_input(campaign_dir: Path, p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else campaign_dir / path


def load_spectrum_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    aliases = {
        "k": "k_rad_m",
        "omega": "omega_rad_s",
        "amplitude": "power",
        "weight": "power",
    }
    for a, b in aliases.items():
        if a in df.columns and b not in df.columns:
            df[b] = df[a]
    req = {"k_rad_m", "omega_rad_s"}
    if not req.issubset(df.columns):
        raise ValueError(f"Spectrum {path} requires columns {sorted(req)}")
    if "power" not in df.columns:
        df["power"] = 1.0
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=["k_rad_m", "omega_rad_s", "power"])
    df = df[(df.k_rad_m != 0) & (df.omega_rad_s > 0) & (df.power > 0)].copy()
    df["abs_k_rad_m"] = np.abs(df.k_rad_m.to_numpy(float))
    return df


def load_trajectory_csv(path: Path):
    df = pd.read_csv(path)
    req = {"time_s", "point_id", "x_m", "y_m", "z_m"}
    if not req.issubset(df.columns):
        raise ValueError(f"Trajectory {path} requires columns {sorted(req)}")
    times = np.sort(df.time_s.unique())
    point_ids = np.sort(df.point_id.unique())
    if len(times) < 16:
        raise ValueError("Dynamic falsification requires at least 16 time frames; static centerlines cannot determine a propagation speed.")
    xyz = np.empty((len(times), len(point_ids), 3), float)
    pmap = {p:i for i,p in enumerate(point_ids)}
    tmap = {t:i for i,t in enumerate(times)}
    counts = np.zeros((len(times), len(point_ids)), int)
    for r in df.itertuples(index=False):
        ti, pi = tmap[r.time_s], pmap[r.point_id]
        xyz[ti, pi] = (r.x_m, r.y_m, r.z_m)
        counts[ti, pi] += 1
    if not np.all(counts == 1):
        raise ValueError("Each (time_s, point_id) must occur exactly once.")
    return times.astype(float), xyz


def load_trajectory_npz(path: Path):
    d = np.load(path)
    if "xyz" not in d or "time_s" not in d:
        raise ValueError("NPZ trajectory requires arrays 'xyz' [T,N,3] and 'time_s' [T].")
    xyz = np.asarray(d["xyz"], float)
    t = np.asarray(d["time_s"], float)
    if xyz.ndim != 3 or xyz.shape[2] != 3 or xyz.shape[0] != len(t):
        raise ValueError("Invalid trajectory shapes.")
    if len(t) < 16:
        raise ValueError("Dynamic falsification requires at least 16 time frames.")
    return t, xyz


def load_spectrum_npz(path: Path) -> pd.DataFrame:
    d = np.load(path)
    if "k_rad_m" not in d or "omega_rad_s" not in d:
        raise ValueError("Spectrum NPZ requires arrays 'k_rad_m' and 'omega_rad_s'.")
    k = np.asarray(d["k_rad_m"], float).ravel()
    w = np.asarray(d["omega_rad_s"], float).ravel()
    if len(k) != len(w):
        raise ValueError("Spectrum NPZ k_rad_m and omega_rad_s lengths differ.")
    power = np.asarray(d["power"], float).ravel() if "power" in d else np.ones_like(k)
    if len(power) != len(k):
        raise ValueError("Spectrum NPZ power length differs from k_rad_m.")
    df = pd.DataFrame({"k_rad_m": k, "omega_rad_s": w, "power": power})
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    df = df[(df.k_rad_m != 0) & (df.omega_rad_s > 0) & (df.power > 0)].copy()
    df["abs_k_rad_m"] = np.abs(df.k_rad_m.to_numpy(float))
    return df
