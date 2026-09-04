from __future__ import annotations

import numpy as np

from .fourier import sample_component
from .qm_energy import tube_repulsion_energy
from .spectral import (
    active_mode_max_link,
    analytic_link_length_bending,
    nonlinear_geometry_recommended_samples,
    spectral_tail_audit,
)
from .native_ext import BackendOptions
from .native_ext.core import link_velocity_batch_arc_exclusion, neumann_coupling_matrices_arc_exclusion
from .biot_savart import sign_matrix, fit_normal_rigid_motion


def _samples(link, n: int):
    return [sample_component(component, int(n)) for component in link.components]


def _richardson(values: list[float], ns: list[int]) -> dict:
    if len(values) < 3:
        return {"order_estimate": None, "continuum_estimate": None}
    v0, v1, v2 = map(float, values[-3:])
    n0, n1, n2 = map(float, ns[-3:])
    r1=n1/n0; r2=n2/n1
    if abs(r1-r2)>1e-12 or r1<=1.0:
        return {"order_estimate": None, "continuum_estimate": None}
    d01=v0-v1; d12=v1-v2
    if abs(d12)<1e-15 or d01*d12<=0:
        return {"order_estimate": None, "continuum_estimate": None}
    p=float(np.log(abs(d01/d12))/np.log(r1))
    if not np.isfinite(p) or p<=0:
        return {"order_estimate": None, "continuum_estimate": None}
    denom=r1**p-1.0
    est=float(v2+(v2-v1)/denom) if abs(denom)>1e-15 else None
    return {"order_estimate": p, "continuum_estimate": est}


def _strict_increasing(ns):
    ns=[int(x) for x in ns]
    if len(ns)<2 or sorted(ns)!=ns or len(set(ns))!=len(ns):
        raise ValueError("sample ladder must be strictly increasing with at least two entries")
    return ns


def audit_link_continuum(link, cfg: dict, backend_options: BackendOptions) -> dict:
    diameter=float(link.diameter)
    active_mode=active_mode_max_link(link)
    recommended_geom=nonlinear_geometry_recommended_samples(active_mode, float(cfg.get("spectral_nonlinear_oversample",4.0)))

    # Derivative-sensitive geometry is cheap and is audited separately at high N with analytic Fourier derivatives.
    geom_ns=cfg.get("continuum_spectral_geometry_sample_ns")
    if geom_ns is None:
        base=max(1024, recommended_geom)
        geom_ns=[base, 2*base, 4*base]
    geom_ns=_strict_increasing(geom_ns)

    # Pairwise O(N^2) hydrodynamic/repulsion diagnostics have their own ladder.
    hydro_ns=cfg.get("continuum_sample_ns", cfg.get("continuum_hydrodynamic_sample_ns", [512,1024,2048]))
    hydro_ns=_strict_increasing(hydro_ns)

    epsilon=float(cfg.get("qm_epsilon_D",0.10))*diameter
    energy_arc=float(cfg.get("self_exclusion_energy_arc_D",0.20))*diameter
    velocity_arc=float(cfg.get("self_exclusion_velocity_arc_D",0.25))*diameter
    rep_soft=float(cfg.get("repulsion_softness_D",0.04))
    rep_margin=float(cfg.get("repulsion_margin",0.0))
    sectors=sign_matrix(len(link.components))

    geometry_rows=[]
    for n in geom_ns:
        length,bending=analytic_link_length_bending(link,n)
        geometry_rows.append({
            "sample_n": int(n),
            "length_over_D": float(length/max(diameter,1e-300)),
            "bending_times_D": float(bending*diameter),
            "derivative_method": "analytic_fourier",
        })

    geometry_convergence={}
    for name in ["length_over_D","bending_times_D"]:
        vals=[float(row[name]) for row in geometry_rows]
        rel=abs(vals[-1]-vals[-2])/max(abs(vals[-1]),1e-300)
        geometry_convergence[name]={
            "values": vals,
            "last_pair_relative_difference": float(rel),
            **_richardson(vals,geom_ns),
        }

    hydro_rows=[]
    for n in hydro_ns:
        samples=_samples(link,n)
        curves=[np.ascontiguousarray(s.r,dtype=float) for s in samples]
        repulsion=tube_repulsion_energy(curves,diameter,rep_soft,rep_margin)
        coupling,energy_backend=neumann_coupling_matrices_arc_exclusion(curves,[epsilon],energy_arc,backend_options)
        velocity_batches,velocity_backend=link_velocity_batch_arc_exclusion(curves,sectors,epsilon,velocity_arc,backend_options)
        if velocity_backend!=energy_backend:
            raise RuntimeError(f"mixed backend: {velocity_backend} vs {energy_backend}")
        coupling=np.asarray(coupling[0],dtype=float)
        sector_rows=[]
        for k,signs in enumerate(sectors):
            fits=fit_normal_rigid_motion(samples,[batch[k] for batch in velocity_batches])
            sector_rows.append({
                "signs":[int(x) for x in signs],
                "sign_string":"".join("+" if x>0 else "-" for x in signs),
                "neumann_energy_D":float(signs@coupling@signs)/max(diameter,1e-300),
                "relative_equilibrium_score":float(fits["relative_equilibrium_score"]),
            })
        hydro_rows.append({
            "sample_n":int(n),
            "tube_repulsion_dimensionless":float(repulsion),
            "coupling_matrix_over_D":coupling/max(diameter,1e-300),
            "sectors":sector_rows,
            "backend":energy_backend,
        })

    rep_vals=[float(x["tube_repulsion_dimensionless"]) for x in hydro_rows]
    rep_rel=abs(rep_vals[-1]-rep_vals[-2])/max(abs(rep_vals[-1]),1e-300)
    hydrodynamic_convergence={
        "tube_repulsion_dimensionless":{
            "values":rep_vals,
            "last_pair_relative_difference":float(rep_rel),
            **_richardson(rep_vals,hydro_ns),
        }
    }
    sector_convergence=[]
    for idx,signs in enumerate(sectors):
        energies=[float(row["sectors"][idx]["neumann_energy_D"]) for row in hydro_rows]
        residuals=[float(row["sectors"][idx]["relative_equilibrium_score"]) for row in hydro_rows]
        e_rel=abs(energies[-1]-energies[-2])/max(abs(energies[-1]),1e-300)
        r_rel=abs(residuals[-1]-residuals[-2])/max(abs(residuals[-1]),1e-300)
        sector_convergence.append({
            "signs":[int(x) for x in signs],
            "sign_string":"".join("+" if x>0 else "-" for x in signs),
            "neumann_energy_D_values":energies,
            "neumann_last_pair_relative_difference":float(e_rel),
            "relative_equilibrium_values":residuals,
            "relative_equilibrium_last_pair_relative_difference":float(r_rel),
            "neumann_richardson":_richardson(energies,hydro_ns),
            "equilibrium_richardson":_richardson(residuals,hydro_ns),
        })

    spectral=spectral_tail_audit(link,cfg)
    tol=float(cfg.get("continuum_relative_tolerance",0.05))
    geom_max=max(x["last_pair_relative_difference"] for x in geometry_convergence.values())
    hydro_max=max(
        [hydrodynamic_convergence["tube_repulsion_dimensionless"]["last_pair_relative_difference"]]
        +[x["neumann_last_pair_relative_difference"] for x in sector_convergence]
        +[x["relative_equilibrium_last_pair_relative_difference"] for x in sector_convergence]
    )
    geom_pass=bool(geom_max<=tol)
    hydro_pass=bool(hydro_max<=tol)
    numerical_pass=bool(geom_pass and hydro_pass)
    v040_ready=bool(numerical_pass and not spectral["spectral_tail_contaminated_risk"])

    return {
        "link_id":link.link_id,
        "diameter_D":diameter,
        "source_active_mode_max":int(active_mode),
        "recommended_nonlinear_geometry_sample_n":int(recommended_geom),
        "spectral_geometry_sample_ns":geom_ns,
        "hydrodynamic_sample_ns":hydro_ns,
        # Backward compatibility for older summary consumers: this now refers to the hydrodynamic ladder.
        "sample_ns":hydro_ns,
        "epsilon_D":epsilon/diameter,
        "self_exclusion_energy_arc_D":energy_arc/diameter,
        "self_exclusion_velocity_arc_D":velocity_arc/diameter,
        "spectral_geometry_rows":geometry_rows,
        "hydrodynamic_rows":hydro_rows,
        "term_convergence":geometry_convergence,
        "hydrodynamic_convergence":hydrodynamic_convergence,
        "sector_convergence":sector_convergence,
        "spectral_tail_audit":spectral,
        "geometry_max_last_pair_relative_difference":float(geom_max),
        "hydrodynamic_max_last_pair_relative_difference":float(hydro_max),
        "max_last_pair_relative_difference":float(max(geom_max,hydro_max)),
        "continuum_relative_tolerance":tol,
        "geometry_continuum_pass":geom_pass,
        "hydrodynamic_continuum_pass":hydro_pass,
        "continuum_pass":numerical_pass,
        "v040_numerical_spectral_ready":v040_ready,
        "status":(
            "[NUMERICAL] v0.3.4 separates analytic-Fourier derivative-sensitive geometry from O(N^2) "
            "hydrodynamic refinement. continuum_pass is N-convergence only; v040_numerical_spectral_ready also "
            "requires that the source-precision spectral-tail risk flag is clear."
        ),
    }
