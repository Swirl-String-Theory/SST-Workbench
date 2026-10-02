from __future__ import annotations

import numpy as np
import pytest

from sst_chiral.symmetry_blocks import (
    SymmetryBlockError,
    coerce_selection_matrix,
    connected_blocks,
    emit_symmetry_blocks,
    require_parent_matrix,
)


def test_full_3x3_protocol_blocks():
    rec = emit_symmetry_blocks(
        [[True, False, False], [False, True, True], [False, True, True]],
        parent_gate_input_sha256="g" * 64,
        parent_provenance_sha256="p" * 64,
    )
    assert rec["selection_matrix"] == [[1, 0, 0], [0, 1, 1], [0, 1, 1]]
    assert rec["blocks"] == [[0], [1, 2]]
    assert rec["channel_labels"] == ["body_x", "body_y", "body_z"]
    assert rec["measured_response_claim"] is False
    assert rec["parent_hashes"]["provenance_sha256"] == "p" * 64


def test_malformed_matrix_rejected():
    with pytest.raises(SymmetryBlockError):
        coerce_selection_matrix([[1, 0], [0, 1]])
    with pytest.raises(SymmetryBlockError):
        coerce_selection_matrix([[1, 2, 0], [0, 1, 0], [0, 0, 1]])


def test_wrong_parent_matrix_rejected():
    with pytest.raises(SymmetryBlockError):
        require_parent_matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])


def test_permutation_must_restore_parent_order():
    permuted = [[1, 1, 0], [1, 1, 0], [0, 0, 1]]
    with pytest.raises(SymmetryBlockError):
        emit_symmetry_blocks(permuted)
    rec = emit_symmetry_blocks(permuted, permutation_to_provider_basis=[2, 0, 1])
    assert rec["selection_matrix"] == [[1, 0, 0], [0, 1, 1], [0, 1, 1]]


def test_connected_blocks_order():
    assert connected_blocks([[1, 0, 0], [0, 1, 1], [0, 1, 1]]) == [[0], [1, 2]]
