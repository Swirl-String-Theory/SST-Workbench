from __future__ import annotations
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any
import json

CONVERGENCE_STATES = ("UNRESOLVED", "COARSE", "CONVERGING", "RESOLVED", "REFERENCE_VALUE")

@dataclass
class Carrier:
    carrier_id: str
    topology_id: str
    source_family: str
    source_role: str
    representation: str
    source_path: str | None = None
    reference_id: str | None = None
    variant_id: str | None = None
    independence_group: str | None = None
    parent_source_family: str | None = None
    parent_carrier_id: str | None = None
    raw_sha256: str | None = None
    provider_group: str | None = None
    lineage_group: str | None = None
    method_group: str | None = None
    catalog_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

@dataclass
class QualificationConfig:
    resolution_ladder: list[int] = field(default_factory=lambda: [128,256,512,1024,2048])
    min_levels_for_resolution: int = 3
    resolved_rel_tol: float = 5e-3
    converging_rel_tol: float = 5e-2
    max_workers: int = 0
    normalize_length: float | None = 1.0
    spline_mode: str = "periodic_cubic"
    dcs_orthogonality_tol: float = 0.12
    nonlocal_exclusion_fraction: float = 0.02
    adaptive_stop: bool = True
    minimum_resolution_for_stop: int = 512
    expensive_metrics: bool = True
    copy_source_geometry: bool = False

    @classmethod
    def load(cls, path):
        d=json.loads(Path(path).read_text(encoding='utf-8'))
        return cls(**d)

    def to_dict(self): return asdict(self)
