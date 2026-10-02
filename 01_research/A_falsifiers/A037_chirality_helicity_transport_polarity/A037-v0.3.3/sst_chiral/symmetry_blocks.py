"""Pure adapter around the parent CAMPAIGN selection-matrix rule."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np

from . import __version__

SCHEMA = "SST_MODAL_PHASE_CONTRACT-1.0"
EXPECTED_MATRIX = [[1, 0, 0], [0, 1, 1], [0, 1, 1]]
CHANNEL_LABELS = ("body_x", "body_y", "body_z")
PROTOCOL_R = [[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


class SymmetryBlockError(ValueError):
    """Integrity failure for ordered symmetry blocks."""


def coerce_selection_matrix(matrix: Any) -> list[list[int]]:
    arr = np.asarray(matrix)
    if arr.shape != (3, 3):
        raise SymmetryBlockError("selection_matrix must be 3x3")
    out: list[list[int]] = []
    for row in arr:
        coerced = []
        for val in row:
            if isinstance(val, (bool, np.bool_)) or val in (0, 1, 0.0, 1.0, True, False):
                coerced.append(1 if bool(val) else 0)
            else:
                raise SymmetryBlockError("selection_matrix entries must be boolean or 0/1")
        out.append(coerced)
    return out


def connected_blocks(matrix: list[list[int]]) -> list[list[int]]:
    n = len(matrix)
    seen = [False] * n
    blocks = []
    for i in range(n):
        if seen[i]:
            continue
        stack = [i]
        seen[i] = True
        block = []
        while stack:
            u = stack.pop()
            block.append(u)
            for v in range(n):
                if not seen[v] and (matrix[u][v] or matrix[v][u]):
                    seen[v] = True
                    stack.append(v)
        blocks.append(sorted(block))
    return blocks


def require_parent_matrix(matrix: list[list[int]], expected: list[list[int]] | None = None) -> None:
    exp = expected or EXPECTED_MATRIX
    if matrix != exp:
        raise SymmetryBlockError(f"selection_matrix {matrix} disagrees with parent CAMPAIGN matrix {exp}")


def apply_channel_permutation(matrix: list[list[int]], perm: list[int]) -> list[list[int]]:
    if sorted(perm) != list(range(len(matrix))):
        raise SymmetryBlockError("permutation_to_provider_basis must be a permutation of channel ids")
    # perm[i] is the provider-basis index of canonical body channel i.
    return [[matrix[perm[i]][perm[j]] for j in range(len(perm))] for i in range(len(perm))]


def emit_symmetry_blocks(
    selection_matrix: Any,
    *,
    parent_gate_input_sha256: str | None = None,
    parent_provenance_sha256: str | None = None,
    permutation_to_provider_basis: list[int] | None = None,
    provider_basis_hash: str | None = None,
    source_id: str = "A037-v0.3.2",
    require_expected: bool = True,
) -> dict[str, Any]:
    matrix = coerce_selection_matrix(selection_matrix)
    perm = permutation_to_provider_basis or [0, 1, 2]
    ordered = apply_channel_permutation(matrix, perm) if perm != [0, 1, 2] else matrix
    if require_expected:
        require_parent_matrix(ordered)
    blocks = connected_blocks(ordered)
    membership = {str(i): bid for bid, block in enumerate(blocks) for i in block}
    record = {
        "schema": SCHEMA,
        "schema_version": "1.0",
        "record_type": "symmetry_blocks",
        "source_id": source_id,
        "provider_id": "A037",
        "parent_hashes": {
            "gate_input_sha256": parent_gate_input_sha256,
            "provenance_sha256": parent_provenance_sha256,
        },
        "code_hash": hashlib.sha256(f"symmetry_blocks:{__version__}".encode()).hexdigest(),
        "blind_status": "not_applicable",
        "selection_matrix": ordered,
        "blocks": blocks,
        "channel_ids": [0, 1, 2],
        "channel_labels": list(CHANNEL_LABELS),
        "basis_order": "body_xyz",
        "mirror_matrix": PROTOCOL_R,
        "block_membership": membership,
        "permutation_to_provider_basis": perm,
        "provider_basis_hash": provider_basis_hash,
        "measured_response_claim": False,
    }
    record["output_sha256"] = hashlib.sha256(
        json.dumps({k: v for k, v in record.items() if k != "output_sha256"}, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return record
