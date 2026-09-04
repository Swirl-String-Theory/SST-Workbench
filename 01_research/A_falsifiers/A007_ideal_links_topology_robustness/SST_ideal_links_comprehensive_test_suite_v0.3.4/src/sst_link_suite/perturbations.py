from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class ReducedBasis:
    vectors: np.ndarray  # (d, total_points, 3)
    component_slices: tuple[slice, ...]
    weights: np.ndarray  # (total_points,)
    metadata: tuple[dict, ...]
    gauge_rank: int
    discarded_singular_values: tuple[float, ...]


def _unit(vector: np.ndarray, fallback: np.ndarray | None = None) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm > 1e-14:
        return vector / norm
    if fallback is None:
        raise ValueError("Cannot normalize near-zero vector")
    return np.asarray(fallback, dtype=float)


def _rotation_matrix(axis: np.ndarray, angle: float) -> np.ndarray:
    axis = _unit(axis, np.array([1.0, 0.0, 0.0]))
    x, y, z = axis
    K = np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])
    return np.eye(3) + np.sin(angle) * K + (1.0 - np.cos(angle)) * (K @ K)


def _transport_vector(vector: np.ndarray, tangent_a: np.ndarray, tangent_b: np.ndarray) -> np.ndarray:
    cross = np.cross(tangent_a, tangent_b)
    sine = float(np.linalg.norm(cross))
    cosine = float(np.clip(tangent_a @ tangent_b, -1.0, 1.0))
    if sine < 1e-13:
        if cosine > 0:
            return vector.copy()
        # Antiparallel exceptional case: rotate around any axis normal to tangent.
        trial = np.array([1.0, 0.0, 0.0])
        if abs(trial @ tangent_a) > 0.8:
            trial = np.array([0.0, 1.0, 0.0])
        axis = _unit(np.cross(tangent_a, trial))
        return _rotation_matrix(axis, np.pi) @ vector
    axis = cross / sine
    angle = float(np.arctan2(sine, cosine))
    return _rotation_matrix(axis, angle) @ vector


def rotation_minimizing_frame(tangents: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Return a periodic rotation-minimizing normal frame and raw closure holonomy.

    The closure angle is a geometric normal-bundle holonomy.  It is not a quantum Berry phase.
    """
    tangents = np.asarray(tangents, dtype=float)
    tangents = tangents / np.maximum(np.linalg.norm(tangents, axis=1)[:, None], 1e-300)
    n = len(tangents)
    axis = np.array([1.0, 0.0, 0.0])
    if abs(axis @ tangents[0]) > 0.8:
        axis = np.array([0.0, 1.0, 0.0])
    normal1 = np.empty_like(tangents)
    normal1[0] = _unit(axis - (axis @ tangents[0]) * tangents[0])
    for i in range(1, n):
        transported = _transport_vector(normal1[i - 1], tangents[i - 1], tangents[i])
        transported -= (transported @ tangents[i]) * tangents[i]
        normal1[i] = _unit(transported, normal1[i - 1])
    closure = _transport_vector(normal1[-1], tangents[-1], tangents[0])
    closure -= (closure @ tangents[0]) * tangents[0]
    closure = _unit(closure, normal1[0])
    sine = float(tangents[0] @ np.cross(normal1[0], closure))
    cosine = float(np.clip(normal1[0] @ closure, -1.0, 1.0))
    holonomy = float(np.arctan2(sine, cosine))

    # Distribute the closure mismatch to obtain a periodic computational frame.
    corrected = np.empty_like(normal1)
    for i in range(n):
        correction = -holonomy * i / n
        corrected[i] = _rotation_matrix(tangents[i], correction) @ normal1[i]
        corrected[i] -= (corrected[i] @ tangents[i]) * tangents[i]
        corrected[i] = _unit(corrected[i], normal1[i])
    normal2 = np.cross(tangents, corrected)
    normal2 /= np.maximum(np.linalg.norm(normal2, axis=1)[:, None], 1e-300)
    return corrected, normal2, holonomy


def _component_slices(samples) -> tuple[slice, ...]:
    out = []
    start = 0
    for sample in samples:
        stop = start + len(sample.r)
        out.append(slice(start, stop))
        start = stop
    return tuple(out)


def _weighted_inner(a: np.ndarray, b: np.ndarray, weights: np.ndarray) -> float:
    return float(np.sum(weights[:, None] * a * b))


def _weighted_orthonormalize(
    vectors: list[np.ndarray], weights: np.ndarray, tolerance: float = 1e-10
) -> tuple[list[np.ndarray], list[float]]:
    basis: list[np.ndarray] = []
    discarded: list[float] = []
    for vector in vectors:
        work = np.asarray(vector, dtype=float).copy()
        for existing in basis:
            work -= _weighted_inner(existing, work, weights) * existing
        norm2 = _weighted_inner(work, work, weights)
        if norm2 <= tolerance * tolerance:
            discarded.append(float(np.sqrt(max(norm2, 0.0))))
            continue
        basis.append(work / np.sqrt(norm2))
    return basis, discarded



def _weighted_orthonormalize_with_indices(
    vectors: list[np.ndarray], weights: np.ndarray, tolerance: float = 1e-10
) -> tuple[list[np.ndarray], list[float], list[int]]:
    basis: list[np.ndarray] = []
    discarded: list[float] = []
    kept: list[int] = []
    for index, vector in enumerate(vectors):
        work = np.asarray(vector, dtype=float).copy()
        for existing in basis:
            work -= _weighted_inner(existing, work, weights) * existing
        norm2 = _weighted_inner(work, work, weights)
        if norm2 <= tolerance * tolerance:
            discarded.append(float(np.sqrt(max(norm2, 0.0))))
            continue
        basis.append(work / np.sqrt(norm2))
        kept.append(index)
    return basis, discarded, kept


def _rigid_gauge_vectors(samples, slices: tuple[slice, ...]) -> list[np.ndarray]:
    total = sum(len(sample.r) for sample in samples)
    positions = np.concatenate([sample.r for sample in samples], axis=0)
    center = positions.mean(axis=0)
    vectors = []
    for axis in np.eye(3):
        field = np.repeat(axis[None, :], total, axis=0)
        vectors.append(field)
    relative = positions - center
    for axis in np.eye(3):
        vectors.append(np.cross(np.repeat(axis[None, :], total, axis=0), relative))
    return vectors


def build_reduced_normal_basis(
    samples,
    mode_max: int = 2,
    remove_rigid_gauge: bool = True,
    basis_tolerance: float = 1e-9,
) -> tuple[ReducedBasis, list[dict]]:
    """Build low-harmonic normal deformations and remove rigid Euclidean gauge modes."""
    if mode_max < 0:
        raise ValueError("mode_max must be nonnegative")
    slices = _component_slices(samples)
    total = sum(len(sample.r) for sample in samples)
    weights_parts, frames = [], []
    holonomies = []
    for sample in samples:
        tangent = sample.d1 / np.maximum(np.linalg.norm(sample.d1, axis=1)[:, None], 1e-300)
        n1, n2, angle = rotation_minimizing_frame(tangent)
        dt = 2.0 * np.pi / len(sample.r)
        ds = np.linalg.norm(sample.d1, axis=1) * dt
        weights_parts.append(ds)
        frames.append((n1, n2))
        holonomies.append({
            "component": int(sample.component.index),
            "normal_frame_holonomy_rad": float(angle),
            "normal_frame_holonomy_over_2pi": float(angle / (2.0 * np.pi)),
            "status": "[GEOMETRIC] rotation-minimizing-frame closure; not a Berry phase.",
        })
    weights = np.concatenate(weights_parts)
    weights /= max(float(weights.sum()), 1e-300)

    candidates: list[np.ndarray] = []
    metadata: list[dict] = []
    for component_index, (sample, component_slice, frame) in enumerate(zip(samples, slices, frames)):
        n1, n2 = frame
        t = sample.t
        for mode in range(mode_max + 1):
            functions = [("cos", np.cos(mode * t))]
            if mode > 0:
                functions.append(("sin", np.sin(mode * t)))
            for phase_name, scalar in functions:
                for normal_index, normal in enumerate((n1, n2), 1):
                    field = np.zeros((total, 3), dtype=float)
                    field[component_slice] = scalar[:, None] * normal
                    candidates.append(field)
                    metadata.append({
                        "component": component_index + 1,
                        "component_source_index": int(sample.component.index),
                        "harmonic": mode,
                        "phase": phase_name,
                        "normal_direction": normal_index,
                    })

    gauge_rank = 0
    if remove_rigid_gauge:
        gauge, _ = _weighted_orthonormalize(_rigid_gauge_vectors(samples, slices), weights, basis_tolerance)
        gauge_rank = len(gauge)
        projected = []
        for candidate in candidates:
            work = candidate.copy()
            for vector in gauge:
                work -= _weighted_inner(vector, work, weights) * vector
            projected.append(work)
        candidates = projected

    basis, discarded, kept_indices = _weighted_orthonormalize_with_indices(candidates, weights, basis_tolerance)
    metadata = [metadata[index] for index in kept_indices]
    # The candidate symplectic form can only be nondegenerate in even dimension.
    if len(basis) % 2 == 1:
        discarded.append(float(np.sqrt(_weighted_inner(basis[-1], basis[-1], weights))))
        basis = basis[:-1]
        metadata = metadata[:-1]
    if not basis:
        raise RuntimeError("No physical perturbation basis survived gauge reduction")
    return ReducedBasis(
        vectors=np.stack(basis, axis=0),
        component_slices=slices,
        weights=weights,
        metadata=tuple(metadata),
        gauge_rank=gauge_rank,
        discarded_singular_values=tuple(discarded),
    ), holonomies


def apply_reduced_coordinates(samples, basis: ReducedBasis, coordinates: np.ndarray) -> list[np.ndarray]:
    coordinates = np.asarray(coordinates, dtype=float)
    if coordinates.shape != (basis.vectors.shape[0],):
        raise ValueError(f"Expected coordinates shape {(basis.vectors.shape[0],)}, got {coordinates.shape}")
    displacement = np.tensordot(coordinates, basis.vectors, axes=(0, 0))
    curves = []
    for sample, component_slice in zip(samples, basis.component_slices):
        curves.append(np.ascontiguousarray(sample.r + displacement[component_slice], dtype=float))
    return curves
