"""
Machine-readable scientific conclusion ledger for
SST chiral Kelvin falsification v0.1.3.

CHANGELOG.md answers:
    What changed in the software?

CONCLUSIONS.md / this module answer:
    What changed in the scientific interpretation?

The machine-readable ledger does NOT automatically rewrite
CONCLUSIONS.md.  Scientific prose remains human-controlled.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .core import write_json


CONCLUSIONS: list[dict[str, Any]] = [
    {
        "id": "C0.1",
        "introduced_in": "0.1.0",
        "status": "NUMERICALLY_VERIFIED",
        "title": "Analytic Jacobian implementation",
        "conclusion": (
            "The analytic Frechet/Jacobian action agrees with "
            "finite-difference differentiation at approximately "
            "1e-10 relative error in the validated baseline."
        ),
    },
    {
        "id": "C0.2",
        "introduced_in": "0.1.0",
        "status": "NUMERICALLY_VERIFIED",
        "title": "Python/native parity",
        "conclusion": (
            "The validated Python and C++/pybind implementations "
            "agree to approximately machine precision for the "
            "baseline observables."
        ),
    },
    {
        "id": "C0.3",
        "introduced_in": "0.1.0",
        "status": "NUMERICALLY_VERIFIED",
        "title": "Circulation reversal symmetry",
        "conclusion": (
            "The implemented frozen-geometry dynamical operator "
            "respects the expected circulation-reversal symmetry."
        ),
    },
    {
        "id": "C0.4",
        "introduced_in": "0.1.0",
        "status": "DERIVED_NEGATIVE",
        "title": "Four-state scalar energy degeneracy",
        "conclusion": (
            "Within the isotropic finite-core Euler/Biot-Savart "
            "model, scalar kinetic energy cannot split the four "
            "(handedness, circulation) states."
        ),
    },
    {
        "id": "C1.2",
        "introduced_in": "0.1.1",
        "status": "NUMERICALLY_VERIFIED",
        "title": "Scalar energy converges faster than spectrum",
        "conclusion": (
            "Scalar-energy convergence is not a sufficient proxy "
            "for eigenspectral convergence."
        ),
    },
    {
        "id": "C1.3",
        "introduced_in": "0.1.1",
        "status": "DERIVED_NEGATIVE",
        "title": "Low-resolution trefoil spectrum is not converged",
        "conclusion": (
            "The frozen trefoil spectrum at the tested low "
            "resolutions cannot be promoted to a converged "
            "physical SST spectrum."
        ),
    },
    {
        "id": "C1.4",
        "introduced_in": "0.1.1",
        "status": "DIAGNOSTIC",
        "title": "Circularity remains useful",
        "conclusion": (
            "Circularity behaves coherently as a mode diagnostic, "
            "but circularity convergence alone does not establish "
            "frequency convergence."
        ),
    },
    {
        "id": "C2.1",
        "introduced_in": "0.1.2.1",
        "status": "NUMERICALLY_VERIFIED",
        "title": "Matcher self-consistency",
        "conclusion": (
            "The v0.1.2 matcher self-test gives essentially unity "
            "subspace overlap and Fourier-fingerprint similarity."
        ),
    },
    {
        "id": "C2.2",
        "introduced_in": "0.1.2.1",
        "status": "REFINED",
        "title": "Near-degenerate rotation is not the sole bottleneck",
        "supersedes": "v0.1.1 working hypothesis",
        "conclusion": (
            "Near-degenerate eigenspace rotation explains only "
            "part of the observed convergence failure. "
            "Spatial/core and wavelength resolution increasingly "
            "appear to dominate the remaining frequency drift."
        ),
    },
    {
        "id": "C2.3",
        "introduced_in": "0.1.2.1",
        "status": "NUMERICALLY_VERIFIED",
        "title": "N <= 96 is not core resolved",
        "conclusion": (
            "None of the tested N <= 96 grids satisfy the adopted "
            "eta_a <= 0.5 core-resolution gate."
        ),
    },
    {
        "id": "C2.4",
        "introduced_in": "0.1.2.1",
        "status": "HEURISTIC",
        "title": "First core-resolved regime is approximately N=256",
        "conclusion": (
            "Observed eta_a scaling indicates that N around 256 "
            "is an appropriate first core-resolved campaign target."
        ),
    },
    {
        "id": "C2.5",
        "introduced_in": "0.1.2.1",
        "status": "DIAGNOSTIC",
        "title": "Wavelength resolution is an independent gate",
        "conclusion": (
            "Mode frequency convergence requires a wavelength "
            "sampling criterion in addition to core resolution."
        ),
    },
    {
        "id": "C2.6",
        "introduced_in": "0.1.2.1",
        "status": "DIAGNOSTIC",
        "title": "Circularity often converges faster than frequency",
        "conclusion": (
            "Several matched branches preserve overlap, Fourier "
            "identity, and circularity while omega remains "
            "substantially resolution dependent."
        ),
    },
    {
        "id": "C2.7",
        "introduced_in": "0.1.2.1",
        "status": "DIAGNOSTIC",
        "title": "Conditioning is not the main high-C drift source",
        "conclusion": (
            "Many high-circularity modes have eigenvalue condition "
            "numbers near unity, so strong non-normal sensitivity "
            "does not explain their dominant frequency drift."
        ),
    },
    {
        "id": "C2.8",
        "introduced_in": "0.1.2.1",
        "status": "NUMERICALLY_VERIFIED",
        "title": "Fixed m_max=24 fingerprint ceiling is inadequate",
        "conclusion": (
            "The m=24 cap aliases multiple high-frequency branches "
            "and must be replaced by a resolution-dependent "
            "Nyquist-safe range."
        ),
    },
]


def build_conclusions_summary(
    *,
    implementation_ok: bool,
    numerical_tracking_ready: bool,
    physical_interpretation_ready: bool,
) -> dict[str, Any]:

    by_status: dict[str, int] = {}

    for conclusion in CONCLUSIONS:
        status = str(
            conclusion["status"]
        )

        by_status[status] = (
            by_status.get(status, 0)
            + 1
        )

    return {
        "release": "0.1.3",
        "ledger_type": "scientific_conclusions",
        "implementation_ok":
            bool(implementation_ok),
        "numerical_tracking_ready":
            bool(numerical_tracking_ready),
        "physical_interpretation_ready":
            bool(physical_interpretation_ready),
        "conclusion_count":
            len(CONCLUSIONS),
        "status_counts":
            by_status,
        "conclusions":
            CONCLUSIONS,
        "rule": (
            "Machine-readable conclusion states do not "
            "automatically rewrite CONCLUSIONS.md."
        ),
    }


def write_conclusions_summary(
    path: str | Path,
    *,
    implementation_ok: bool,
    numerical_tracking_ready: bool,
    physical_interpretation_ready: bool,
) -> dict[str, Any]:

    summary = build_conclusions_summary(
        implementation_ok=
            implementation_ok,
        numerical_tracking_ready=
            numerical_tracking_ready,
        physical_interpretation_ready=
            physical_interpretation_ready,
    )

    write_json(
        path,
        summary,
    )

    return summary
