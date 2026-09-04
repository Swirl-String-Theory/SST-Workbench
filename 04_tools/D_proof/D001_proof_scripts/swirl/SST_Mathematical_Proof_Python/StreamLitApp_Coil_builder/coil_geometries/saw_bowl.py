# coil_geometries/saw_bowl.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import numpy as np

from .base import CoilModel, CoilParameter, MU_0


def r_profile(s: np.ndarray, Rb: float, Rt: float, profile: str, power: float = 2.2) -> np.ndarray:
    if profile == 'Exponential':
        return Rb + (Rt - Rb) * (s**power)
    elif profile == 'Inverse Exp':
        return Rt - (Rt - Rb) * (s**power)
    else:  # Linear
        return Rb + (Rt - Rb) * s


def generate_bowl_geometry(
        S: int,
        step_fwd: int,
        step_bwd: int,
        n_pairs: int,
        Rb: float,
        Rt: float,
        Hc: float,
        profile: str = 'Exponential',
        mode: str = 'Curved',
        angle_offset: float = 0.0,
        samples_per_seg: int = 8,
) -> np.ndarray:
    """
    Saw-bowl winding logic: multi-layer 'diabolo' bowl coil.

    This is essentially your original generate_bowl_geometry(), but
    packaged as a reusable function.
    """
    idx = 1
    seq = [idx]
    for k in range(2 * n_pairs):
        if k % 2 == 0:
            idx = (idx + step_fwd - 1) % S + 1
        else:
            idx = (idx + step_bwd - 1) % S + 1
        seq.append(idx)
    seq = np.array(seq, dtype=int)

    slot_angles_base = np.linspace(0, 2*np.pi, S, endpoint=False) - np.pi/2.0
    N_segs = len(seq) - 1

    if mode == 'Curved':
        s_nodes = np.linspace(0, 1, N_segs + 1)
        r_nodes = r_profile(s_nodes, Rb, Rt, profile)
        z_nodes = s_nodes

        xs, ys, zs = [], [], []

        for k in range(N_segs):
            i0, i1 = seq[k]-1, seq[k+1]-1
            a0 = slot_angles_base[i0] + angle_offset
            a1 = slot_angles_base[i1] + angle_offset

            da = (a1 - a0 + np.pi) % (2*np.pi) - np.pi

            t = np.linspace(0, 1, samples_per_seg, endpoint=False)
            a_line = a0 + t * da
            r_line = np.linspace(r_nodes[k], r_nodes[k+1], samples_per_seg, endpoint=False)
            z_line = np.linspace(z_nodes[k], z_nodes[k+1], samples_per_seg, endpoint=False)

            xs.append(r_line * np.cos(a_line))
            ys.append(r_line * np.sin(a_line))
            zs.append(z_line)

        a_end = slot_angles_base[seq[-1]-1] + angle_offset
        xs.append([r_nodes[-1] * np.cos(a_end)])
        ys.append([r_nodes[-1] * np.sin(a_end)])
        zs.append([z_nodes[-1]])

        X = np.concatenate(xs)
        Y = np.concatenate(ys)
        Z = np.concatenate(zs) * Hc

    else:  # Straight
        s_nodes = np.linspace(0, 1, N_segs + 1)
        r_nodes = r_profile(s_nodes, Rb, Rt, profile)
        z_nodes = s_nodes * Hc
        angles = slot_angles_base[seq-1] + angle_offset
        X = r_nodes * np.cos(angles)
        Y = r_nodes * np.sin(angles)
        Z = z_nodes

    return np.stack([X, Y, Z], axis=-1)


@dataclass
class SawBowlCoil(CoilModel):
    """
    Saw-bowl / diabolo coil (3-phase bowl geometry).
    """
    name: str = "Saw-Bowl (3-phase Diabolo)"
    parameters: Dict[str, CoilParameter] = field(default_factory=lambda: {
        "Rb": CoilParameter(
            name="Rb", label="Base radius Rb [m]",
            default=1.5, min_value=0.1, max_value=3.0, step=0.1
        ),
        "Rt": CoilParameter(
            name="Rt", label="Top radius Rt [m]",
            default=1.5, min_value=0.1, max_value=3.0, step=0.1
        ),
        "Hc": CoilParameter(
            name="Hc", label="Height Hc [m]",
            default=0.1, min_value=0.02, max_value=1.0, step=0.02
        ),
        "layers": CoilParameter(
            name="layers", label="Winding layers (pairs)",
            default=80, min_value=2, max_value=200, step=2, is_int=True
        ),
    })

    def build_polylines(
            self,
            params: Dict[str, float],
            points_per_turn: int = 1000,
    ) -> List[np.ndarray]:
        Rb = params["Rb"]
        Rt = params["Rt"]
        Hc = params["Hc"]
        layers = int(params["layers"])

        S_DEFAULT = 40
        STEP_FWD = 11
        STEP_BWD = -9
        offsets = [0.0, 2*np.pi/3, 4*np.pi/3]

        polylines: List[np.ndarray] = []
        for angle_offset in offsets:
            poly = generate_bowl_geometry(
                S=S_DEFAULT,
                step_fwd=STEP_FWD,
                step_bwd=STEP_BWD,
                n_pairs=layers,
                Rb=Rb,
                Rt=Rt,
                Hc=Hc,
                profile='Exponential',
                mode='Curved',
                angle_offset=angle_offset,
                samples_per_seg=8,
            )
            polylines.append(poly)

        return polylines

    def estimate_inductance(
            self,
            params: Dict[str, float],
            polylines: List[np.ndarray],
    ) -> float:
        """
        Orde van grootte: model als drie solenoïde-achtige spoelen
        met effectieve radius ~ (Rb+Rt)/2 en lengte ~ Hc.
        """
        Rb = params["Rb"]
        Rt = params["Rt"]
        Hc = params["Hc"]
        layers = float(params["layers"])

        R_eff = 0.5 * (Rb + Rt)
        A = np.pi * R_eff**2
        L_len = max(Hc, 1e-3)
        # effectieve "turns" per fase ~ layers
        N_eff_phase = layers
        L_phase = MU_0 * N_eff_phase**2 * A / L_len
        return float(3.0 * L_phase)