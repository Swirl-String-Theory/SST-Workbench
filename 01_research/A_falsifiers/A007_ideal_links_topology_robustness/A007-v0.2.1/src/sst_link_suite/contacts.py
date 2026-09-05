from __future__ import annotations
import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import minimize
from .fourier import evaluate
from .models import FourierComponent

def _periodic_index_distance(i: np.ndarray, j: np.ndarray, n: int) -> np.ndarray:
    d = np.abs(i-j)
    return np.minimum(d, n-d)

def _refined_mutual_distance(
    comp_a: FourierComponent,
    comp_b: FourierComponent,
    seed_t: float,
    seed_u: float,
    dt: float,
) -> tuple[float, float, float]:
    def objective(x):
        t = np.mod(x[0], 2*np.pi)
        u = np.mod(x[1], 2*np.pi)
        d = evaluate(comp_a, np.array([t]))[0] - evaluate(comp_b, np.array([u]))[0]
        return float(d @ d)
    res = minimize(
        objective, np.array([seed_t, seed_u]),
        method="Nelder-Mead",
        options={"maxiter": 250, "xatol": dt*1e-5, "fatol": 1e-16},
    )
    return float(np.sqrt(max(res.fun, 0.0))), float(np.mod(res.x[0], 2*np.pi)), float(np.mod(res.x[1], 2*np.pi))

def mutual_contacts(samples, diameter: float, tolerance: float, refine_seeds: int = 8) -> tuple[list[dict], list[dict]]:
    pair_stats, edges = [], []
    threshold = diameter * (1.0 + tolerance)
    for i in range(len(samples)):
        for j in range(i+1, len(samples)):
            a, b = samples[i], samples[j]
            tree = cKDTree(b.r)
            dist, idx = tree.query(a.r, k=1)
            order = np.argsort(dist)
            refined = []
            dt = 2*np.pi / len(a.r)
            used = set()
            for k in order:
                key = (int(k), int(idx[k]))
                if key in used:
                    continue
                used.add(key)
                refined.append(_refined_mutual_distance(
                    a.component, b.component, a.t[k], b.t[idx[k]], dt
                ))
                if len(refined) >= refine_seeds:
                    break
            refined.sort(key=lambda x: x[0])
            mask = dist <= threshold
            local_edges = []
            for ia in np.flatnonzero(mask):
                local_edges.append({
                    "component_a": i+1, "index_a": int(ia),
                    "component_b": j+1, "index_b": int(idx[ia]),
                    "distance_D": float(dist[ia]),
                })
            edges.extend(local_edges)
            pair_stats.append({
                "component_a": i+1,
                "component_b": j+1,
                "sampled_min_distance_D": float(dist.min()),
                "refined_min_distance_D": float(refined[0][0]),
                "refined_t": float(refined[0][1]),
                "refined_u": float(refined[0][2]),
                "contact_sample_count": int(mask.sum()),
                "contact_coverage_a": float(mask.mean()),
                "distance_q01_D": float(np.quantile(dist, 0.01)),
                "distance_q05_D": float(np.quantile(dist, 0.05)),
            })
    return pair_stats, edges

def _arclength(r: np.ndarray) -> tuple[np.ndarray, float]:
    seg = np.linalg.norm(np.diff(r, axis=0, append=r[:1]), axis=1)
    s = np.concatenate(([0.0], np.cumsum(seg)[:-1]))
    return s, float(seg.sum())

def _exact_nonlocal_min(r: np.ndarray, arc: np.ndarray, total: float,
                        window: float, max_points: int = 768) -> float:
    """Exact non-local minimum on a decimated grid.

    The k-nearest-neighbour scan saturates whenever all k neighbours fall
    inside the arclength exclusion window (e.g. a round component whose
    total length is only a few D).  This O(m^2) fallback is cheap and never
    returns NaN.
    """
    stride = max(1, len(r) // max_points)
    p, a = r[::stride], arc[::stride]
    d = np.linalg.norm(p[:, None, :] - p[None, :, :], axis=2)
    sep = np.abs(a[:, None] - a[None, :])
    sep = np.minimum(sep, total - sep)
    d[sep <= window] = np.inf
    return float(d.min()) if np.isfinite(d).any() else float("inf")

def self_contact_proxy(
    samples,
    diameter: float,
    tolerance: float,
    exclusion_D: float = 2.0,
    neighbour_cap: int = 256,
) -> list[dict]:
    """Non-local self-approach statistics.

    The exclusion window is expressed in ARCLENGTH (units of the tube
    diameter D), not in sample-index separation.  The v0.2.0 default
    (min_sep = 4% of the index range) corresponds to roughly 0.7 D of
    arclength on a typical component, which is shorter than the local
    chord subtended by a curvature-limited arc.  It therefore measured
    local chords rather than non-local approach: self_contact_coverage
    was 1.0 for every link in the v0.2.0 full run.
    """
    out = []
    threshold = diameter * (1.0 + tolerance)
    for ci, s in enumerate(samples, 1):
        n = len(s.r)
        arc, total_length = _arclength(s.r)
        window = min(exclusion_D * diameter, total_length / 2.5)
        k = min(n, max(64, int(neighbour_cap)))
        tree = cKDTree(s.r)
        dist, idx = tree.query(s.r, k=k)
        best = np.full(n, np.inf)
        partner = np.full(n, -1, dtype=int)
        for col in range(1, k):
            sep = np.abs(arc - arc[idx[:, col]])
            sep = np.minimum(sep, total_length - sep)
            good = sep > window
            improve = good & (dist[:, col] < best)
            best[improve] = dist[improve, col]
            partner[improve] = idx[improve, col]
        finite = np.isfinite(best)
        contact = finite & (best <= threshold)
        exact_min = _exact_nonlocal_min(s.r, arc, total_length, window)
        out.append({
            "component": ci,
            "exclusion_window_D": float(window / max(diameter, 1e-30)),
            "neighbour_cap": int(k),
            "unresolved_sample_count": int((~finite).sum()),
            "sampled_nonlocal_min_distance_D": exact_min,
            "knn_nonlocal_min_distance_D": float(best[finite].min()) if finite.any() else float("nan"),
            "self_contact_sample_count": int(contact.sum()),
            "self_contact_coverage": float(contact.mean()),
            "median_nonlocal_distance_D": float(np.median(best[finite])) if finite.any() else float("nan"),
        })
    return out

def contact_graph_summary(edges: list[dict], component_sizes: list[int]) -> dict:
    # Undirected graph over sampled centerline nodes.
    parent = {}
    degree = {}
    def key(c, i): return (int(c), int(i))
    def find(x):
        # Iterative find with full path compression.  The recursive form
        # overflows for large contact sets (observed: RecursionError after
        # 991 frames at contact_n=1024 on L2a1).
        parent.setdefault(x, x)
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
    for e in edges:
        a = key(e["component_a"], e["index_a"])
        b = key(e["component_b"], e["index_b"])
        union(a, b)
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
    roots = {find(x) for x in parent}
    return {
        "contact_edge_count": len(edges),
        "contact_graph_nodes": len(parent),
        "contact_graph_connected_components": len(roots),
        "contact_graph_max_degree": max(degree.values(), default=0),
        "contact_graph_mean_degree": float(np.mean(list(degree.values()))) if degree else 0.0,
        "contact_graph_cycle_rank": max(0, len(edges) - len(parent) + len(roots)),
    }

def contact_summary(
    samples,
    diameter: float,
    tolerance: float,
    self_exclusion_D: float = 2.0,
    neighbour_cap: int = 256,
) -> dict:
    mutual, edges = mutual_contacts(samples, diameter, tolerance)
    self_stats = self_contact_proxy(
        samples, diameter, tolerance,
        exclusion_D=self_exclusion_D, neighbour_cap=neighbour_cap,
    )
    graph = contact_graph_summary(edges, [len(s.r) for s in samples])
    return {"mutual_pairs": mutual, "self_components": self_stats, "graph": graph, "edges": edges}
