#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SST chi-phase package v13B.0
Unified Track A/B alpha_ring benchmark pipeline.

Purpose
-------
This package consolidates the Track A Euler/Biot-Savart ring-energy result
and the Track B GP/NLSE core-envelope result into one benchmark table.
It is a synthesis/audit package, not a new physical derivation.

Track A answers: what alpha_ring follows from incompressible Euler/Biot-Savart
vorticity energy for selected swirl profiles?

Track B answers: what alpha_ring follows from the GP/NLSE core-envelope energy
with algebraic tail correction?

Status: Strong Research Track synthesis; not locked CANON.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from typing import Dict, Iterable, List, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
A0_STAR = (math.sqrt(385.0) - 13.0) / 4.0
NLS_ALPHA_LEGACY = 1.61
NLS_BETA_LEGACY = 0.61
RANKINE_ALPHA = 7.0 / 4.0


def beta_from_q(alpha: float, q: float) -> float:
    return alpha - 1.0 + q


def chi_speed_ratio_smooth(a0: float) -> float:
    return math.sqrt((2.0*a0*a0 + 13.0*a0 + 78.0)/105.0)


@dataclass(frozen=True)
class BenchmarkRow:
    track: str
    model: str
    alpha_ring: float
    beta_ring_q0: float
    beta_ring_qminus_half: float
    alpha_sigma: Optional[float]
    source: str
    mechanism: str
    expected_or_target: Optional[float]
    delta_expected_or_target: Optional[float]
    delta_legacy_nls_alpha: float
    delta_phi: float
    chi_speed_ratio: Optional[float]
    status: str
    note: str


def _row(
    *,
    track: str,
    model: str,
    alpha: float,
    source: str,
    mechanism: str,
    expected: Optional[float] = None,
    sigma: Optional[float] = None,
    chi: Optional[float] = None,
    status: str,
    note: str,
) -> BenchmarkRow:
    return BenchmarkRow(
        track=track,
        model=model,
        alpha_ring=alpha,
        beta_ring_q0=beta_from_q(alpha, 0.0),
        beta_ring_qminus_half=beta_from_q(alpha, -0.5),
        alpha_sigma=sigma,
        source=source,
        mechanism=mechanism,
        expected_or_target=expected,
        delta_expected_or_target=None if expected is None else alpha - expected,
        delta_legacy_nls_alpha=alpha - NLS_ALPHA_LEGACY,
        delta_phi=alpha - PHI,
        chi_speed_ratio=chi,
        status=status,
        note=note,
    )


def unified_reference_rows() -> List[BenchmarkRow]:
    """Return the v13B.0 unified benchmark table.

    Track A values are the v10A.0 low-resolution Biot-Savart intercepts.
    Track B values are the v12B.0 analytic-tail-corrected GP/NLSE estimates.
    This function deliberately preserves the provenance rather than retuning.
    """
    rows: List[BenchmarkRow] = []
    rows.append(_row(
        track="A",
        model="rankine_solid",
        alpha=1.74039741439,
        expected=RANKINE_ALPHA,
        source="v10A.0 Biot-Savart intercept, nr=8, ntheta=24",
        mechanism="Euler/Biot-Savart incompressible vorticity energy",
        status="benchmark prototype",
        note="Approaches classical 7/4 with resolution; validates Track A extraction direction.",
    ))
    rows.append(_row(
        track="A",
        model="smooth_a0star_chi_closure",
        alpha=1.50471814494,
        source="v10A.0 Biot-Savart intercept",
        mechanism="Euler/Biot-Savart smooth matched profile at v6 a0*",
        chi=1.0,
        status="negative selector test",
        note="The chi-closure root does not reproduce the NLS ring constant in Track A.",
    ))
    rows.append(_row(
        track="A",
        model="smooth_phi",
        alpha=1.50814979471,
        source="v10A.0 Biot-Savart intercept",
        mechanism="Euler/Biot-Savart smooth matched profile at phi",
        chi=chi_speed_ratio_smooth(PHI),
        status="negative selector test",
        note="Golden-ratio profile does not reproduce the NLS ring constant in Track A.",
    ))
    rows.append(_row(
        track="A",
        model="smooth_a0_2",
        alpha=1.47071103766,
        source="v10A.0 Biot-Savart intercept",
        mechanism="Euler/Biot-Savart simple matched polynomial f=2x-x^3",
        chi=chi_speed_ratio_smooth(2.0),
        status="negative selector test",
        note="Simple admissible polynomial is farther from NLS alpha_ring.",
    ))
    rows.append(_row(
        track="A",
        model="smooth_grad_min_a0_7_4",
        alpha=1.49579554890,
        source="v10A.0 Biot-Savart intercept",
        mechanism="Euler/Biot-Savart smooth profile at v6 gradient minimum",
        chi=chi_speed_ratio_smooth(7.0/4.0),
        status="negative selector test",
        note="Gradient-minimum shape does not reproduce NLS alpha_ring in Track A.",
    ))
    rows.append(_row(
        track="B",
        model="GP_NLSE_R_15_5_corrected",
        alpha=1.6183172,
        expected=NLS_ALPHA_LEGACY,
        source="v10B.1 corrected GP/NLSE at R/xi=15.5",
        mechanism="GP/NLSE core-envelope energy with coefficient 1/2",
        sigma=None,
        status="positive finite-radius test",
        note="Finite-R result already lies close to legacy NLS and phi.",
    ))
    rows.append(_row(
        track="B",
        model="GP_NLSE_infinity_tail_corrected",
        alpha=1.619350923,
        expected=NLS_ALPHA_LEGACY,
        source="v12B.0 analytic 4-term tail correction, R>=12",
        mechanism="GP/NLSE core-envelope energy plus algebraic tail extraction",
        sigma=2.171e-7,
        status="principal Track B result",
        note="Best current Track B estimate; still conditional on SST-internal proof of A=B=C.",
    ))
    rows.append(_row(
        track="target",
        model="legacy_NLS_note",
        alpha=NLS_ALPHA_LEGACY,
        expected=NLS_ALPHA_LEGACY,
        source="legacy notebook pages 49-51",
        mechanism="historical NLS ring constant target",
        status="external target",
        note="Target comparison only; not itself a derivation.",
    ))
    rows.append(_row(
        track="reference",
        model="golden_ratio_phi",
        alpha=PHI,
        expected=PHI,
        source="numeric reference",
        mechanism="dimensionless comparison constant",
        status="numerical proximity only",
        note="No canon structural derivation of phi in this sector yet.",
    ))
    rows.append(_row(
        track="reference",
        model="rankine_classical_7_4",
        alpha=RANKINE_ALPHA,
        expected=RANKINE_ALPHA,
        source="classical vortex-ring benchmark",
        mechanism="solid-core / Rankine benchmark",
        status="benchmark target",
        note="Used to audit Track A Biot-Savart extraction.",
    ))
    return rows


def summary_metrics(rows: Iterable[BenchmarkRow]) -> Dict[str, float | str]:
    rowmap = {r.model: r for r in rows}
    a_smooth = rowmap["smooth_a0star_chi_closure"].alpha_ring
    a_gp = rowmap["GP_NLSE_infinity_tail_corrected"].alpha_ring
    a_rankine = rowmap["rankine_solid"].alpha_ring
    out: Dict[str, float | str] = {
        "A_smooth_a0star_alpha": a_smooth,
        "B_GP_alpha_inf": a_gp,
        "TrackB_minus_legacy_NLS": a_gp - NLS_ALPHA_LEGACY,
        "TrackB_minus_phi": a_gp - PHI,
        "TrackB_minus_TrackA_smooth_a0star": a_gp - a_smooth,
        "TrackA_smooth_a0star_minus_legacy_NLS": a_smooth - NLS_ALPHA_LEGACY,
        "TrackA_rankine_error_vs_7_4": a_rankine - RANKINE_ALPHA,
        "core_result": "Track A smooth chi-closure and Track B GP/NLSE ring constant are distinct selectors.",
    }
    return out


def canon_gate_status(rows: Iterable[BenchmarkRow]) -> List[Dict[str, str]]:
    """Return checklist for what remains before locked-CANON status."""
    return [
        {
            "gate": "G1: notation firewall",
            "status": "pass",
            "criterion": "Use alpha_ring/beta_ring; reserve alpha_fs for fine-structure/shielding and alpha' for Regge slope.",
        },
        {
            "gate": "G2: Track A benchmark",
            "status": "partial pass",
            "criterion": "Rankine Biot-Savart benchmark points toward 7/4; higher-resolution v10A.1 still desirable.",
        },
        {
            "gate": "G3: Track B energy consistency",
            "status": "pass conditional",
            "criterion": "Corrected GP/NLSE energy coefficient 1/2 varies to the solved ODE.",
        },
        {
            "gate": "G4: Track B asymptotic extraction",
            "status": "pass conditional",
            "criterion": "Algebraic tail supports 1/R^2+1/R^4 extraction and alpha_ring^GP≈1.61935.",
        },
        {
            "gate": "G5: SST internal core-envelope equality",
            "status": "open",
            "criterion": "Need SST-internal proof that A_grad=B_phase=C_depletion, not an imposed GP convention.",
        },
        {
            "gate": "G6: phi structural selector",
            "status": "open",
            "criterion": "phi proximity remains numerical until derived from boundary/topology/eigenvalue selection.",
        },
    ]
