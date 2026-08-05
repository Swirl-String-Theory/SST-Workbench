from __future__ import annotations

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


def plot_curve(points: np.ndarray, path: Path, orbit_points: np.ndarray | None = None) -> None:
    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection="3d")
    closed = np.vstack([points, points[0]])
    ax.plot(closed[:, 0], closed[:, 1], closed[:, 2], linewidth=1.2)
    if orbit_points is not None and len(orbit_points):
        op = np.vstack([orbit_points, orbit_points[0]])
        ax.plot(op[:, 0], op[:, 1], op[:, 2], marker="o", linewidth=1.0)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.set_box_aspect(np.ptp(points, axis=0) + 1e-12)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_contact_map(s: np.ndarray, a: np.ndarray, b: np.ndarray, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(s, a, s=6, label="branch a")
    ax.scatter(s, b, s=6, label="branch b")
    ax.set_xlabel("s/L")
    ax.set_ylabel("contact parameter")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend()
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_force_compatibility(s: np.ndarray, compatibility: np.ndarray, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(s, compatibility)
    ax.set_xlabel("s/L")
    ax.set_ylabel("compatibility residual")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_hydro_sweep(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    fig, ax = plt.subplots(figsize=(9, 5))
    interactions = sorted({str(row.get("interaction", "full")) for row in rows})
    for interaction in interactions:
        subset = sorted(
            (row for row in rows if str(row.get("interaction", "full")) == interaction),
            key=lambda row: row["core_ratio"],
        )
        x = [row["core_ratio"] for row in subset]
        ax.plot(x, [row["relative_equilibrium_residual"] for row in subset], marker="o", label=f"{interaction}: relative equilibrium")
        ax.plot(x, [row["fitted_shape_residual"] for row in subset], marker="s", label=f"{interaction}: force shape")
        if interaction == "full":
            ax.plot(x, [row["tension_cv"] for row in subset], marker="^", label="full: tension CV")
    ax.set_xlabel("a / thickness")
    ax.set_ylabel("dimensionless residual")
    ax.legend(fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)
