from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import csv, hashlib, json
import numpy as np

EXPECTED_FAMILY = "knot_3.1"
EXPECTED_CANONICAL_ID = "3_1"
EXPECTED_FAMILY_INDEX = 14
EXPECTED_VARIANTS = 48
EXPECTED_POINTS = 512
EXPECTED_BUNDLE_SHA256 = "ffc31331fccaf10a3171e4ccbf3ec0043e56ff681f85cc8b8149932193d736d1"
EXPECTED_CONSTRUCTION = "PTSA-v1.0.0-exact-shape-up-to-global-similarity-normalization"

@dataclass(frozen=True)
class PKLSACandidate:
    candidate_id: str
    family: str
    canonical_id: str
    family_index: int
    variant_index: int
    component_count: int
    points_per_component: int
    construction_method: str
    source_record: str
    legacy_ptsa_id: str | None
    parameters: dict

    @classmethod
    def from_row(cls,row:dict):
        params=row.get("parameters")
        if params is None:
            raw=row.get("parameters_json") or "{}"
            params=json.loads(raw) if isinstance(raw,str) else dict(raw)
        return cls(
            candidate_id=str(row["candidate_id"]), family=str(row["family"]),
            canonical_id=str(row["canonical_id"]), family_index=int(row["family_index"]),
            variant_index=int(row["variant_index"]), component_count=int(row["component_count"]),
            points_per_component=int(row["points_per_component"]),
            construction_method=str(row["construction_method"]), source_record=str(row["source_record"]),
            legacy_ptsa_id=(str(row["legacy_ptsa_id"]) if row.get("legacy_ptsa_id") not in (None,"") else None),
            parameters=params,
        )


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""): h.update(block)
    return h.hexdigest()


def _rows_from_jsonl(path:Path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip(): yield json.loads(line)


def _rows_from_csv(path:Path):
    with path.open(newline="",encoding="utf-8-sig") as f:
        yield from csv.DictReader(f)


def load_manifest_rows(root:Path):
    root=Path(root)
    p_jsonl=root/"manifests"/"CANDIDATES_FULL.jsonl"
    p_csv=root/"manifests"/"CANDIDATES_FULL.csv"
    if p_jsonl.exists(): return list(_rows_from_jsonl(p_jsonl))
    if p_csv.exists(): return list(_rows_from_csv(p_csv))
    raise FileNotFoundError(f"PKLSA manifest missing: expected {p_jsonl} or {p_csv}")


def trefoil_candidates(root:Path, require_full_census:bool=True):
    rows=[PKLSACandidate.from_row(r) for r in load_manifest_rows(root) if str(r.get("family"))==EXPECTED_FAMILY]
    rows.sort(key=lambda r:r.variant_index)
    if require_full_census:
        if len(rows)!=EXPECTED_VARIANTS: raise RuntimeError(f"expected {EXPECTED_VARIANTS} trefoil candidates, found {len(rows)}")
        if [r.variant_index for r in rows] != list(range(EXPECTED_VARIANTS)): raise RuntimeError("trefoil variant indices are not exactly 0..47")
    for r in rows:
        if r.canonical_id!=EXPECTED_CANONICAL_ID or r.family_index!=EXPECTED_FAMILY_INDEX: raise RuntimeError("PKLSA trefoil identity mismatch")
        if r.component_count!=1 or r.points_per_component!=EXPECTED_POINTS: raise RuntimeError("PKLSA trefoil shape contract mismatch")
        if r.construction_method!=EXPECTED_CONSTRUCTION: raise RuntimeError("unexpected PKLSA trefoil construction_method")
    return rows


def bundle_path(root:Path)->Path:
    return Path(root)/"families"/"14_knot_3p1.npz"


def verify_trefoil_bundle(root:Path, strict_hash:bool=True):
    p=bundle_path(root)
    if not p.exists(): raise FileNotFoundError(f"PKLSA trefoil bundle missing: {p}")
    digest=sha256_file(p)
    if strict_hash and digest!=EXPECTED_BUNDLE_SHA256:
        raise RuntimeError(f"PKLSA bundle SHA256 mismatch: got {digest}, expected {EXPECTED_BUNDLE_SHA256}")
    z=np.load(p,allow_pickle=False)
    if "points" not in z: raise RuntimeError("PKLSA trefoil bundle has no 'points' array")
    shape=tuple(int(x) for x in z["points"].shape)
    # Signed atlas contract for 3_1 is expected to be 48 x 1 x 512 x 3.
    if shape != (EXPECTED_VARIANTS,1,EXPECTED_POINTS,3):
        raise RuntimeError(f"unexpected PKLSA trefoil points shape {shape}")
    if not np.isfinite(z["points"]).all(): raise RuntimeError("non-finite PKLSA coordinates")
    return {"path":str(p),"sha256":digest,"shape":list(shape)}


def load_centerline(root:Path, candidate:PKLSACandidate):
    p=bundle_path(root)
    z=np.load(p,allow_pickle=False)
    pts=np.asarray(z["points"][candidate.variant_index],float)
    if pts.shape!=(1,EXPECTED_POINTS,3): raise RuntimeError(f"candidate component shape mismatch: {pts.shape}")
    return pts[0].copy()


def closed_arclength_resample(points, n:int):
    P=np.asarray(points,float)
    if P.ndim!=2 or P.shape[1]!=3 or len(P)<8: raise ValueError("expected centerline shape (M,3), M>=8")
    Q=np.vstack([P,P[0]])
    seg=np.linalg.norm(np.diff(Q,axis=0),axis=1)
    if not np.isfinite(seg).all() or np.any(seg<=0): raise ValueError("degenerate/non-finite centerline segments")
    s=np.concatenate([[0.0],np.cumsum(seg)])
    targets=np.linspace(0.0,s[-1],int(n),endpoint=False)
    return np.column_stack([np.interp(targets,s,Q[:,j]) for j in range(3)])


def canonicalize_centerline(points,n:int,target_rms_radius:float):
    P=closed_arclength_resample(points,n)
    centroid=P.mean(axis=0); P=P-centroid
    rms=float(np.sqrt(np.mean(np.sum(P*P,axis=1))))
    if not np.isfinite(rms) or rms<=0: raise ValueError("invalid centerline RMS radius")
    scale=float(target_rms_radius)/rms
    P=P*scale
    raw=np.ascontiguousarray(np.asarray(points,dtype=np.float64))
    canon=np.ascontiguousarray(P,dtype=np.float64)
    return P,{
        "raw_coordinate_sha256":hashlib.sha256(raw.tobytes()).hexdigest(),
        "canonical_coordinate_sha256":hashlib.sha256(canon.tobytes()).hexdigest(),
        "input_points":int(len(raw)),"resampled_points":int(len(P)),
        "input_centroid":[float(x) for x in centroid],"input_rms_radius":rms,
        "scale_to_target":scale,"target_rms_radius":float(target_rms_radius),
        "transform":"closed-arclength resample -> centroid removal -> uniform RMS-radius scale; no rotation or reflection",
    }


def select_variants(rows,selection):
    if selection in (None,"all"): return list(rows)
    wanted={int(x) for x in selection}
    got=[r for r in rows if r.variant_index in wanted]
    missing=wanted-{r.variant_index for r in got}
    if missing: raise ValueError(f"requested PKLSA variants missing: {sorted(missing)}")
    return got
