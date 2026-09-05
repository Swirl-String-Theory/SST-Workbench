"""
Machine-readable scientific conclusion ledger for
SST chiral Kelvin falsification v0.1.3.1.

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
    {
        "id": "C3.1",
        "introduced_in": "0.1.3",
        "status": "NUMERICALLY_VERIFIED",
        "previous_status": "HEURISTIC",
        "title": "Core-resolution threshold reached",
        "conclusion": (
            "For core_factor=1, the N=256,320,384 campaign places "
            "both ring and frozen trefoil inside the adopted "
            "eta_a <= 0.5 core-resolution regime."
        ),
    },
    {
        "id": "C3.2",
        "introduced_in": "0.1.3",
        "status": "NUMERICALLY_VERIFIED",
        "previous_status": "PLANNED_TEST",
        "title": "Resolved-grid numerical mode tracking established",
        "conclusion": (
            "Trefoil numerically-trackable fractions reach about "
            "88.27 percent for N=256->320 and 95.35 percent for "
            "N=320->384."
        ),
    },
    {
        "id": "C3.3",
        "introduced_in": "0.1.3",
        "status": "NUMERICALLY_VERIFIED",
        "previous_status": "PLANNED_TEST",
        "title": "Multiple three-resolution mode chains converge",
        "conclusion": (
            "Multiple frozen-trefoil branches can be followed through "
            "N=256->320->384 with high overlap, stable Fourier identity, "
            "stable circularity and decreasing frequency drift."
        ),
    },
    {
        "id": "C3.4",
        "introduced_in": "0.1.3",
        "status": "NUMERICALLY_VERIFIED",
        "title": "Frozen geometry remains non-physical",
        "conclusion": (
            "Numerical convergence of a frozen-trefoil eigenbranch "
            "does not establish a physical SST normal mode. A true "
            "relative equilibrium and co-moving operator remain required."
        ),
    },
    {
        "id": "C3.5",
        "introduced_in": "0.1.3.1",
        "status": "NUMERICALLY_VERIFIED",
        "title": "Previous spectral failure was predominantly resolution driven",
        "conclusion": (
            "The transition from poor low-resolution tracking to "
            "greater than 88 percent and then 95 percent tracking "
            "on the resolved ladder strongly supports finite "
            "discretization/resolution as the dominant earlier bottleneck."
        ),
    },
    {
        "id": "C3.6",
        "introduced_in": "0.1.3.1",
        "status": "NUMERICALLY_VERIFIED",
        "title": "PPW predicts spectral convergence quality",
        "conclusion": (
            "The resolved campaign supports PPW as an independent "
            "wavelength-resolution diagnostic. Branches satisfying "
            "the adopted PPW >= 12 criterion show substantially "
            "improved spectral stability."
        ),
    },
    {
        "id": "C3.7",
        "introduced_in": "0.1.3.1",
        "status": "DIAGNOSTIC",
        "title": "Circularity is a stable candidate mode observable",
        "conclusion": (
            "Circularity remains stable across many resolved tracked "
            "branches. This establishes it as a robust numerical "
            "diagnostic, not yet as a physical SST quantum number."
        ),
    },
    {
        "id": "C3.8",
        "introduced_in": "0.1.3.1",
        "status": "OPEN",
        "title": "Physical Kelvin spectrum requires relative equilibrium",
        "conclusion": (
            "The next physics gate is an ideal-trefoil relative "
            "equilibrium with co-moving linearization and removal "
            "of rigid and tangential gauge directions."
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
        "release": "0.1.3.1",
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
