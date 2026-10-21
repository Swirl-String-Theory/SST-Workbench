"""Additive, opt-in KnotPlot Native Census v0.1.2 reader for PKLSA E010 v0.3.1.
No default-provider override, no relaxation, no unit conversion, no silent promotion to independent evidence.
"""
from __future__ import annotations
from pathlib import Path
import hashlib, json, math
import numpy as np

DATASET_ID = "knotplot.native_census.v0.1.2"
DATASET_RELATIVE = Path("03_data/A_knots/04_knotplot/PKLSA_KnotPlot_Native_Census_v0.1.2")

class NativeCensusError(RuntimeError):
    pass

class KnotPlotNativeCensus:
    def __init__(self, workbench_root, *, verify_hash=True):
        root = Path(getattr(workbench_root, "root", workbench_root)).resolve()
        self.root = root / DATASET_RELATIVE
        self._registry_path = self.root / "registry.json"
        if not self._registry_path.is_file():
            raise NativeCensusError(f"Dataset not installed: {self._registry_path}")
        self.registry = json.loads(self._registry_path.read_text(encoding="utf-8"))
        if self.registry.get("dataset_id") != DATASET_ID:
            raise NativeCensusError("Dataset ID mismatch")
        self._records = {r["geometry_id"]: r for r in self.registry["objects"]}
        if len(self._records) != len(self.registry["objects"]):
            raise NativeCensusError("Duplicate geometry IDs in registry")
        self.verify_hash = verify_hash

    @classmethod
    def open(cls, workbench, **kwargs):
        return cls(workbench, **kwargs)

    def list_ids(self, kind=None):
        if kind is not None and kind not in ("knot", "link", "torus"):
            raise ValueError("kind must be knot, link or torus")
        return [r["geometry_id"] for r in self.registry["objects"] if kind is None or r["kind"] == kind]

    def describe(self, geometry_id):
        try: return dict(self._records[geometry_id])
        except KeyError: raise KeyError(f"Not in {DATASET_ID}: {geometry_id}") from None

    def _checked_file(self, record, key, sha_key):
        path = self.root / record[key]
        if path.resolve().parent != (self.root / "raw_native").resolve():
            raise NativeCensusError("Unsafe geometry path")
        data = path.read_bytes()
        if self.verify_hash and hashlib.sha256(data).hexdigest() != record[sha_key]:
            raise NativeCensusError(f"SHA-256 mismatch: {path}")
        return path

    def xyz_path(self, geometry_id):
        return self._checked_file(self.describe(geometry_id), "xyz_path", "sha256_xyz")

    def kpf_path(self, geometry_id):
        return self._checked_file(self.describe(geometry_id), "kpf_path", "sha256_kpf")

    def load(self, geometry_id):
        """Load as [numpy.ndarray(N_i,3), ...], native coordinates, order retained.
        Compatible with pklsa_builder.io_geometry.load_geometry(...), but keeps identity and hashes.
        """
        from pklsa_builder.io_geometry import load_geometry
        rec = self.describe(geometry_id)
        parts = load_geometry(self.xyz_path(geometry_id), representation="xyz")
        expected = rec["components"]
        if len(parts) != len(expected):
            raise NativeCensusError("Component count mismatch")
        n = 0
        for a, c in zip(parts, expected):
            if a.ndim != 2 or a.shape[1] != 3 or len(a) != c["n_beads"] or not np.isfinite(a).all():
                raise NativeCensusError("Vertex/component data mismatch")
            segment = np.roll(a, -1, axis=0) - a
            length = float(np.linalg.norm(segment,axis=1).sum())
            if not math.isclose(length, c["length_polygon_knotplot_units"], rel_tol=0, abs_tol=3e-4):
                raise NativeCensusError("Polygonal arclength mismatch")
            n += len(a)
        if n != rec["n_beads"]:
            raise NativeCensusError("Total bead count mismatch")
        return parts

    def provenance(self, geometry_id):
        r = self.describe(geometry_id)
        return {'dataset_id':DATASET_ID,'geometry_id':geometry_id,'source_sha256':r['sha256_kpf'],
            'xyz_sha256':r['sha256_xyz'],'provider_group':'knotplot',
            'independent_from_existing_knotplot_provider':False,
            'topology_catalogue_identity':'UNVERIFIED',
            'finite_core_convergence':'NOT_TESTED',
            'units':'KnotPlot native coordinates; not SI',
            'qualification':'GEOMETRY_PARITY_PASS_ONLY'}
