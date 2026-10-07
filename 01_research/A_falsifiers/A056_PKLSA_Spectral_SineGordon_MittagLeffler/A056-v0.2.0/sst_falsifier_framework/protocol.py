from __future__ import annotations
from dataclasses import dataclass

FRAMEWORK_GATE_ORDER=(
    "G0_PROVENANCE",
    "G1_ADMISSIBILITY",
    "G2_DISCOVERY",
    "G3_CONFIRMATION",
    "G4_NUMERICAL_CERTIFICATION",
    "G5_CROSS_SOURCE_REPLICATION",
    "G6_MECHANISM_PHYSICS",
)

@dataclass(frozen=True)
class FrameworkContract:
    catalog_id: str
    falsifier_name: str
    version: str
    independence_unit: str
    cpu_authority: str = "CPU reference"
    gpu_role: str = "screening only"
    reveal_stage: str = "after frozen BLIND archive"

    def validate(self):
        if not self.catalog_id or not self.version.startswith('v'):
            raise ValueError('invalid framework contract')
        if not self.independence_unit:
            raise ValueError('independence_unit required')
        return True
