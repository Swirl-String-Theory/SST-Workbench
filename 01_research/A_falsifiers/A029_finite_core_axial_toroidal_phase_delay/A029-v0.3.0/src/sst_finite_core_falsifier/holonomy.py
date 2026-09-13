"""Closed-loop wavenumber with holonomy represented exactly once."""

from __future__ import annotations

import math
from typing import Any

TWOPI = 2.0 * math.pi


def k_ref(n: int, L_hat: float) -> float:
    return TWOPI * float(n) / max(float(L_hat), 1e-14)


def k_closed(n: int, m: int, theta_B: float, L_hat: float) -> float:
    return (TWOPI * float(n) - float(m) * float(theta_B)) / max(float(L_hat), 1e-14)


def holonomy_record(n: int, m: int, theta_B: float, L_hat: float) -> dict[str, Any]:
    kr = k_ref(n, L_hat)
    kc = k_closed(n, m, theta_B, L_hat)
    return {
        "k_hat": kc,
        "k_ref": kr,
        "k_closed": kc,
        "L_hat": float(L_hat),
        "kL": kc * float(L_hat),
        "m": int(m),
        "n": int(n),
        "theta_B": float(theta_B),
        "holonomy_representation": "embedded_in_k",
        "phi_holonomy_explicit": 0.0,
    }


def forbid_double_counted_holonomy(record: dict[str, Any]) -> None:
    if record.get("holonomy_representation") == "embedded_in_k" and abs(float(record.get("phi_holonomy_explicit") or 0.0)) > 1e-12:
        raise ValueError("holonomy is already embedded in k; explicit m*theta_B is forbidden")
