from __future__ import annotations
from pathlib import Path
import csv, hashlib, json, math
import numpy as np

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def _read_csv(path: Path) -> list[dict]:
    with Path(path).open("r",newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def compute_circulation_from_loop(path: Path) -> dict:
    rows=_read_csv(path)
    if len(rows)<8:
        raise ValueError("Need at least 8 loop samples.")
    xyz=np.array([[float(r[k]) for k in ("x_m","y_m","z_m")] for r in rows],float)
    vel=np.array([[float(r[k]) for k in ("vx_m_s","vy_m_s","vz_m_s")] for r in rows],float)

    # Closed-loop midpoint/trapezoid line integral:
    # Gamma = integral v.dl ~= sum 0.5*(v_i+v_{i+1}).(x_{i+1}-x_i)
    xyz2=np.vstack([xyz,xyz[0]])
    vel2=np.vstack([vel,vel[0]])
    dl=np.diff(xyz2,axis=0)
    vmid=0.5*(vel2[:-1]+vel2[1:])
    terms=np.einsum("ij,ij->i",vmid,dl)
    gamma=float(np.sum(terms))

    # Discretization diagnostic using every second point when possible.
    coarse=None
    if len(xyz)>=16:
        idx=np.arange(0,len(xyz),2)
        xc=xyz[idx]; vc=vel[idx]
        xc2=np.vstack([xc,xc[0]])
        vc2=np.vstack([vc,vc[0]])
        coarse=float(np.sum(np.einsum(
            "ij,ij->i",
            0.5*(vc2[:-1]+vc2[1:]),
            np.diff(xc2,axis=0)
        )))
    rel_conv=None
    if coarse is not None and gamma!=0:
        rel_conv=abs(coarse-gamma)/abs(gamma)

    return {
        "Gamma_m2_s":gamma,
        "Gamma_abs_m2_s":abs(gamma),
        "orientation_sign":0 if gamma==0 else (1 if gamma>0 else -1),
        "n_loop_samples":len(rows),
        "coarse_every2_Gamma_m2_s":coarse,
        "coarse_fine_relative_difference":rel_conv,
        "input_sha256":sha256_file(path),
        "quadrature":"closed-loop trapezoid v.dl",
    }

def prepare_fluid_measurement(
    loop_csv: Path,
    provenance_json: Path,
    output_json: Path,
) -> dict:
    prov=json.loads(Path(provenance_json).read_text(encoding="utf-8"))
    calc=compute_circulation_from_loop(loop_csv)

    required_flags=(
        "depends_on_h","depends_on_hbar","depends_on_compton_radius",
        "depends_on_electron_mass","depends_on_alpha"
    )
    missing=[k for k in required_flags if k not in prov]
    if missing:
        raise ValueError(f"Missing provenance flags: {missing}")

    clean=(
        prov.get("status")=="INDEPENDENT_MEASURED"
        and not any(bool(prov[k]) for k in required_flags)
    )
    out={
        "format":"SST-GF-CIRCULATION-MEASUREMENT-2.0",
        "measurement_id":prov.get("measurement_id",""),
        "status":prov.get("status","UNDECLARED"),
        "method":prov.get("method","loop integral from raw velocity field"),
        "source":prov.get("source",""),
        "Gamma_m2_s":calc["Gamma_abs_m2_s"],
        "signed_Gamma_m2_s":calc["Gamma_m2_s"],
        "sigma_Gamma_m2_s":prov.get("sigma_Gamma_m2_s"),
        "depends_on_h":bool(prov["depends_on_h"]),
        "depends_on_hbar":bool(prov["depends_on_hbar"]),
        "depends_on_compton_radius":bool(prov["depends_on_compton_radius"]),
        "depends_on_electron_mass":bool(prov["depends_on_electron_mass"]),
        "depends_on_alpha":bool(prov["depends_on_alpha"]),
        "clean_for_specific_action":clean,
        "raw_loop_sha256":calc["input_sha256"],
        "provenance_sha256":sha256_file(provenance_json),
        "circulation_numerics":calc,
    }
    output_json.parent.mkdir(parents=True,exist_ok=True)
    output_json.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
    return out
