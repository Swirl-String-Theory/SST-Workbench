"""Blind hydrodynamic phase observables.

IMPORTANT: this module contains no fine-structure-constant value. It may be run and
archived before any alpha benchmark is evaluated.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
from typing import Any
import numpy as np

from .backend import load_backend
from .geometry import make_counter_channels, polygon_length, resample_closed
from .holonomy import cross_section_omega, director_holonomy, clocked_phases


@dataclass
class BlindResult:
    n: int
    D: float
    offset_over_D: float
    eps_over_D: float
    gamma_plus: float
    gamma_minus: float
    backend: str
    centerline_length: float
    plus_length: float
    minus_length: float
    H_pp: float
    H_mm: float
    H_pm: float
    E_self_sum: float
    E_cross: float
    E_pair: float
    G_energy: float
    delta_energy_rel: float
    omega_plus_mean_dimless: float
    omega_minus_mean_dimless: float
    omega_relative_mean_dimless: float
    mutual_speed_rms_dimless: float
    relative_velocity_director_turns_unwrapped: float
    relative_velocity_director_principal_turns: float
    relative_velocity_director_min_over_rms: float
    relative_velocity_director_max_step_rad: float
    circulation_clock_separation_turns: float
    circulation_clock_separation_principal_turns: float
    differential_rotor_clock_turns: float
    differential_rotor_clock_principal_turns: float
    countergear_slip_clock_turns: float
    countergear_slip_clock_principal_turns: float
    local_speed_clock_separation_turns: float
    local_speed_clock_separation_principal_turns: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_blind(centerline: np.ndarray, *, D: float,
                  offset_over_D: float = 0.5, eps_over_D: float = 0.05,
                  gamma_plus: float = 1.0, gamma_minus: float = -1.0, phase: float = 0.0,
                  force_python: bool = False, skip_build: bool = False,
                  force_build: bool = False, build_verbose: bool = False) -> BlindResult:
    p = np.ascontiguousarray(centerline, dtype=float)
    if D <= 0:
        raise ValueError("D must be > 0")
    if not (0 < offset_over_D <= 2.0):
        raise ValueError("offset_over_D must be in (0,2]")
    if eps_over_D <= 0:
        raise ValueError("eps_over_D must be > 0")
    offset = offset_over_D * D
    eps = eps_over_D * D
    plus, minus, tangent, normal = make_counter_channels(p, offset, phase=phase)

    # Energy remains as a legacy control observable from v0.1.
    plus_energy = resample_closed(plus, len(p))
    minus_energy = resample_closed(minus, len(p))
    backend, backend_name = load_backend(force_python=force_python, skip_build=skip_build,
                                         force_build=force_build, build_verbose=build_verbose)
    Hpp = float(backend.interaction_hamiltonian(plus_energy, plus_energy, gamma_plus, gamma_plus, eps))
    Hmm = float(backend.interaction_hamiltonian(minus_energy, minus_energy, gamma_minus, gamma_minus, eps))
    Hpm = float(backend.interaction_hamiltonian(plus_energy, minus_energy, gamma_plus, gamma_minus, eps))
    Eself = Hpp + Hmm
    Ecross = 2.0 * Hpm
    Epair = Eself + Ecross
    if abs(Eself) < 1e-30:
        raise ZeroDivisionError("Self-energy normalization vanished")
    G = Epair / Eself

    # Mutual induction, evaluated on the physical offset channels.
    u_plus = np.asarray(backend.induced_velocity(plus, minus, gamma_minus, eps), dtype=float)
    u_minus = np.asarray(backend.induced_velocity(minus, plus, gamma_plus, eps), dtype=float)
    r_plus = offset * normal
    r_minus = -offset * normal
    om_plus = cross_section_omega(r_plus, u_plus, tangent)
    om_minus = cross_section_omega(r_minus, u_minus, tangent)
    gscale = 0.5 * (abs(gamma_plus) + abs(gamma_minus))
    if gscale <= 0:
        raise ValueError("nonzero circulation scale required")
    omega_scale = gscale / (4.0 * math.pi * D * D)
    speed_scale = gscale / (4.0 * math.pi * D)
    rel_omega = 0.5 * (om_plus - om_minus)
    mutual_speed = np.sqrt(0.5 * (np.einsum("ij,ij->i", u_plus, u_plus)
                                  + np.einsum("ij,ij->i", u_minus, u_minus)))

    # Clock-free normal-bundle holonomy of the relative velocity director.
    q_rel = u_plus - u_minus
    hd = director_holonomy(q_rel, tangent)

    # Dynamic phase diagnostics with explicitly declared clocks.
    ph = clocked_phases(centerline=p, tangent=tangent, normal=normal,
                        u_plus=u_plus, u_minus=u_minus, offset=offset, D=D,
                        gamma_plus=gamma_plus, gamma_minus=gamma_minus)

    return BlindResult(
        n=len(p), D=float(D), offset_over_D=float(offset_over_D), eps_over_D=float(eps_over_D),
        gamma_plus=float(gamma_plus), gamma_minus=float(gamma_minus), backend=backend_name,
        centerline_length=polygon_length(p), plus_length=polygon_length(plus), minus_length=polygon_length(minus),
        H_pp=Hpp, H_mm=Hmm, H_pm=Hpm, E_self_sum=Eself, E_cross=Ecross, E_pair=Epair,
        G_energy=float(G), delta_energy_rel=float(G - 1.0),
        omega_plus_mean_dimless=float(np.mean(om_plus) / omega_scale),
        omega_minus_mean_dimless=float(np.mean(om_minus) / omega_scale),
        omega_relative_mean_dimless=float(np.mean(rel_omega) / omega_scale),
        mutual_speed_rms_dimless=float(np.sqrt(np.mean(mutual_speed**2)) / speed_scale),
        relative_velocity_director_turns_unwrapped=float(hd["turns_unwrapped"]),
        relative_velocity_director_principal_turns=float(hd["turns_principal"]),
        relative_velocity_director_min_over_rms=float(hd["min_over_rms"]),
        relative_velocity_director_max_step_rad=float(hd["max_step_angle_rad"]),
        circulation_clock_separation_turns=float(ph["circulation_clock_separation_turns"]),
        circulation_clock_separation_principal_turns=float(ph["circulation_clock_separation_principal_turns"]),
        differential_rotor_clock_turns=float(ph["differential_rotor_clock_turns"]),
        differential_rotor_clock_principal_turns=float(ph["differential_rotor_clock_principal_turns"]),
        countergear_slip_clock_turns=float(ph["countergear_slip_clock_turns"]),
        countergear_slip_clock_principal_turns=float(ph["countergear_slip_clock_principal_turns"]),
        local_speed_clock_separation_turns=float(ph["local_speed_clock_separation_turns"]),
        local_speed_clock_separation_principal_turns=float(ph["local_speed_clock_separation_principal_turns"]),
    )
