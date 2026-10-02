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

def self_contact_proxy(samples, diameter: float, tolerance: float, local_fraction: float = 0.04) -> list[dict]:
    out = []
    threshold = diameter * (1.0 + tolerance)
    for ci, s in enumerate(samples, 1):
        n = len(s.r)
        k = min(n, max(64, int(2.5 * local_fraction * n)))
        tree = cKDTree(s.r)
        dist, idx = tree.query(s.r, k=k)
        best = np.full(n, np.inf)
        partner = np.full(n, -1, dtype=int)
        min_sep = max(4, int(local_fraction*n))
        rows = np.arange(n)
        for col in range(1, k):
            good = _periodic_index_distance(rows, idx[:, col], n) > min_sep
            improve = good & (dist[:, col] < best)
            best[improve] = dist[improve, col]
            partner[improve] = idx[improve, col]
        finite = np.isfinite(best)
        contact = finite & (best <= threshold)
        out.append({
            "component": ci,
            "sampled_nonlocal_min_distance_D": float(best[finite].min()) if finite.any() else float("nan"),
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
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
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

def contact_summary(samples, diameter: float, tolerance: float) -> dict:
    mutual, edges = mutual_contacts(samples, diameter, tolerance)
    self_stats = self_contact_proxy(samples, diameter, tolerance)
    graph = contact_graph_summary(edges, [len(s.r) for s in samples])
    return {"mutual_pairs": mutual, "self_components": self_stats, "graph": graph, "edges": edges}
