from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np


@dataclass(frozen=True)
class TopologyReference:
    knot_id: str
    source: str
    source_url: str | None = None
    snapshot_id: str | None = None
    crossings: int | None = None
    components: int | None = None
    dt: tuple[int, ...] | None = None
    gauss: tuple[int, ...] | None = None
    pd: tuple[tuple[int, int, int, int], ...] | None = None
    braid_strands: int | None = None
    braid_word: tuple[int, ...] | None = None
    determinant: int | None = None
    signature: int | None = None
    hyperbolic: bool | None = None
    hyperbolic_volume: float | None = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass
class GeometryAsset:
    components: List[np.ndarray]
    source_path: str | None = None
    source_family: str = 'unknown'
    source_format: str = 'unknown'
    source_sha256: str | None = None
    provider_id: str | None = None
    provider_name: str | None = None
    provider_class: str | None = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def n_components(self) -> int:
        return len(self.components)

    @property
    def is_knot(self) -> bool:
        return self.n_components == 1

    @property
    def points(self) -> np.ndarray:
        if not self.is_knot:
            raise ValueError('asset has multiple components; use .components')
        return self.components[0]


@dataclass
class CertificationResult:
    status: str  # CERTIFIED | MISMATCH | UNVERIFIED | NOT_REGISTERED | ERROR
    expected_topology: str | None
    provider: str
    observed: Dict[str, Any] = field(default_factory=dict)
    reference: Dict[str, Any] = field(default_factory=dict)
    checks: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == 'CERTIFIED'

    def to_dict(self):
        return asdict(self) | {'pass': self.passed}


@dataclass
class KnotRecord:
    topology_expected: str | None
    topology_reference: Dict[str, Any] | None
    topology_certification: Dict[str, Any]
    geometry: Dict[str, Any]
    qualification: Dict[str, Any] | None = None
    convergence: Any = None
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)
