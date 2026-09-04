from __future__ import annotations
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import minimize
from .fourier import evaluate
from .models import FourierComponent


def _periodic_scalar_distance(i: int, j: int, n: int) -> int:
    d = abs(int(i) - int(j))
    return min(d, n-d)


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
    return (
        float(np.sqrt(max(res.fun, 0.0))),
        float(np.mod(res.x[0], 2*np.pi)),
        float(np.mod(res.x[1], 2*np.pi)),
    )


def mutual_contacts(
    samples,
    diameter: float,
    tolerance: float,
    refine_seeds: int = 8,
) -> tuple[list[dict], list[dict]]:
    pair_stats, edges = [], []
    threshold = diameter * (1.0 + tolerance)
    for i in range(len(samples)):
        for j in range(i+1, len(samples)):
            a, b = samples[i], samples[j]
            tree_b = cKDTree(b.r)
            dist_ab, idx_ab = tree_b.query(a.r, k=1)
            tree_a = cKDTree(a.r)
            dist_ba, idx_ba = tree_a.query(b.r, k=1)
            order = np.argsort(dist_ab)
            refined = []
            dt = 2*np.pi / max(len(a.r), len(b.r))
            used = set()
            for k in order:
                key = (int(k), int(idx_ab[k]))
                if key in used:
                    continue
                used.add(key)
                refined.append(_refined_mutual_distance(
                    a.component, b.component, a.t[k], b.t[idx_ab[k]], dt
                ))
                if len(refined) >= refine_seeds:
                    break
            refined.sort(key=lambda x: x[0])

            # Symmetric nearest-neighbour union: avoids privileging the denser/faster parameterization.
            edge_map: dict[tuple[int, int], float] = {}
            for ia in np.flatnonzero(dist_ab <= threshold):
                key = (int(ia), int(idx_ab[ia]))
                edge_map[key] = min(edge_map.get(key, np.inf), float(dist_ab[ia]))
            for ib in np.flatnonzero(dist_ba <= threshold):
                key = (int(idx_ba[ib]), int(ib))
                edge_map[key] = min(edge_map.get(key, np.inf), float(dist_ba[ib]))
            local_edges = [{
                "kind": "mutual",
                "component_a": i+1,
                "index_a": ia,
                "component_b": j+1,
                "index_b": ib,
                "distance_D": distance,
            } for (ia, ib), distance in sorted(edge_map.items())]
            edges.extend(local_edges)
            pair_stats.append({
                "component_a": i+1,
                "component_b": j+1,
                "sampled_min_distance_D": float(min(dist_ab.min(), dist_ba.min())),
                "refined_min_distance_D": float(refined[0][0]),
                "refined_t": float(refined[0][1]),
                "refined_u": float(refined[0][2]),
                "contact_sample_count": len(local_edges),
                "contact_coverage_a": float(np.mean(dist_ab <= threshold)),
                "contact_coverage_b": float(np.mean(dist_ba <= threshold)),
                "distance_q01_D": float(np.quantile(np.concatenate([dist_ab, dist_ba]), 0.01)),
                "distance_q05_D": float(np.quantile(np.concatenate([dist_ab, dist_ba]), 0.05)),
            })
    return pair_stats, edges


def self_contacts(
    samples,
    diameter: float,
    tolerance: float,
    local_fraction: float = 0.01,
    tangent_orthogonality_tolerance: float = 0.15,
) -> tuple[list[dict], list[dict]]:
    """Approximate doubly-critical self-struts from a bounded k-nearest search.

    A radius query can return O(N^2) local pairs on smooth arcs. The bounded-neighbour search keeps
    the campaign scalable, then rejects local arc neighbours using cyclic separation and the two
    tangent-orthogonality conditions expected for a self-strut.
    """
    out, all_edges = [], []
    threshold = diameter * (1.0 + tolerance)
    for ci, sample in enumerate(samples, 1):
        n = len(sample.r)
        tree = cKDTree(sample.r)
        min_sep = max(4, int(local_fraction*n))
        k = min(n, max(96, min(512, n//3)))
        dist, idx = tree.query(sample.r, k=k)
        tangents = sample.d1 / np.maximum(np.linalg.norm(sample.d1, axis=1)[:, None], 1e-300)
        rows = np.arange(n)
        best = np.full(n, np.inf)
        edge_map: dict[tuple[int, int], float] = {}
        for col in range(1, k):
            partners = idx[:, col]
            distances = dist[:, col]
            nonlocal_mask = _periodic_index_distance(rows, partners, n) > min_sep
            improve = nonlocal_mask & (distances < best)
            best[improve] = distances[improve]
            candidate_rows = np.flatnonzero(nonlocal_mask & (distances <= threshold))
            if candidate_rows.size == 0:
                continue
            partner_rows = partners[candidate_rows]
            chord = sample.r[partner_rows] - sample.r[candidate_rows]
            d = distances[candidate_rows]
            unit = chord / np.maximum(d[:, None], 1e-300)
            crit_a = np.abs(np.einsum("ij,ij->i", unit, tangents[candidate_rows]))
            crit_b = np.abs(np.einsum("ij,ij->i", unit, tangents[partner_rows]))
            accepted = candidate_rows[np.maximum(crit_a, crit_b) <= tangent_orthogonality_tolerance]
            for ia in accepted:
                ib = int(partners[ia])
                a, b = sorted((int(ia), ib))
                edge_map[(a, b)] = min(edge_map.get((a, b), np.inf), float(distances[ia]))
        edges = [{
            "kind": "self",
            "component_a": ci,
            "index_a": ia,
            "component_b": ci,
            "index_b": ib,
            "distance_D": distance,
        } for (ia, ib), distance in sorted(edge_map.items())]
        all_edges.extend(edges)
        finite = np.isfinite(best)
        contacted_nodes = {e["index_a"] for e in edges} | {e["index_b"] for e in edges}
        out.append({
            "component": ci,
            "sampled_nonlocal_min_distance_D": float(best[finite].min()) if finite.any() else float("nan"),
            "self_contact_edge_count": len(edges),
            "self_contact_sample_count": len(contacted_nodes),
            "self_contact_coverage": float(len(contacted_nodes)/n),
            "median_nonlocal_distance_D": float(np.median(best[finite])) if finite.any() else float("nan"),
            "double_critical_tangent_tolerance": tangent_orthogonality_tolerance,
            "self_contact_knn_k": k,
        })
    return out, all_edges


class _DisjointSet:
    """Iterative union-find; safe for continuous contact chains with thousands of nodes."""
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def add(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x):
        self.add(x)
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != x:
            nxt = self.parent[x]
            self.parent[x] = root
            x = nxt
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


def contact_graph_summary(edges: list[dict], component_sizes: list[int]) -> dict:
    # Raw undirected contact graph over sampled centerline nodes.
    dsu = _DisjointSet()
    degree = {}
    def key(c, i): return (int(c), int(i))
    for e in edges:
        a = key(e["component_a"], e["index_a"])
        b = key(e["component_b"], e["index_b"])
        dsu.union(a, b)
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
    roots = {dsu.find(x) for x in dsu.parent}
    return {
        "contact_edge_count": len(edges),
        "contact_graph_nodes": len(dsu.parent),
        "contact_graph_connected_components": len(roots),
        "contact_graph_max_degree": max(degree.values(), default=0),
        "contact_graph_mean_degree": float(np.mean(list(degree.values()))) if degree else 0.0,
        "raw_contact_graph_cycle_rank": max(0, len(edges) - len(dsu.parent) + len(roots)),
        # Backward-compatible alias; explicitly deprecated in v0.2.1.
        "contact_graph_cycle_rank": max(0, len(edges) - len(dsu.parent) + len(roots)),
    }


def _edge_close(a: dict, b: dict, sizes: list[int], adjacency: int) -> bool:
    if a["kind"] != b["kind"]:
        return False
    if (a["component_a"], a["component_b"]) != (b["component_a"], b["component_b"]):
        return False
    ca, cb = int(a["component_a"]), int(a["component_b"])
    return (
        _periodic_scalar_distance(a["index_a"], b["index_a"], sizes[ca-1]) <= adjacency
        and _periodic_scalar_distance(a["index_b"], b["index_b"], sizes[cb-1]) <= adjacency
    )


def cluster_contact_patches(
    edges: list[dict],
    component_sizes: list[int],
    adjacency: int = 2,
) -> list[dict]:
    groups = defaultdict(list)
    for edge in edges:
        groups[(edge["kind"], edge["component_a"], edge["component_b"])].append(edge)
    patches = []
    patch_id = 0
    for _, group in sorted(groups.items(), key=lambda item: item[0]):
        group = sorted(group, key=lambda e: (e["index_a"], e["index_b"]))
        dsu = _DisjointSet()
        lookup = defaultdict(list)
        ca, cb = int(group[0]["component_a"]), int(group[0]["component_b"])
        na, nb = component_sizes[ca-1], component_sizes[cb-1]
        for i, edge in enumerate(group):
            dsu.add(i)
            lookup[(int(edge["index_a"]), int(edge["index_b"]))].append(i)
        # Torus-neighbour lookup handles periodic wrap and continuous contact families.
        for i, edge in enumerate(group):
            ia, ib = int(edge["index_a"]), int(edge["index_b"])
            for da in range(-adjacency, adjacency+1):
                for db in range(-adjacency, adjacency+1):
                    if da == 0 and db == 0:
                        continue
                    key = ((ia+da) % na, (ib+db) % nb)
                    for j in lookup.get(key, ()):
                        dsu.union(i, j)
                    if edge["kind"] == "self":
                        swapped = ((ib+db) % na, (ia+da) % nb)
                        for j in lookup.get(swapped, ()):
                            dsu.union(i, j)
        members = defaultdict(list)
        for i, edge in enumerate(group):
            members[dsu.find(i)].append(edge)
        for cluster in members.values():
            representative = min(cluster, key=lambda e: e["distance_D"])
            ca, cb = int(representative["component_a"]), int(representative["component_b"])
            unique_a = len({int(e["index_a"]) for e in cluster})
            unique_b = len({int(e["index_b"]) for e in cluster})
            coverage_a = unique_a / component_sizes[ca-1]
            coverage_b = unique_b / component_sizes[cb-1]
            patches.append({
                "patch_id": patch_id,
                "kind": representative["kind"],
                "component_a": ca,
                "index_a": int(representative["index_a"]),
                "component_b": cb,
                "index_b": int(representative["index_b"]),
                "min_distance_D": float(representative["distance_D"]),
                "edge_count": len(cluster),
                "coverage_a": float(coverage_a),
                "coverage_b": float(coverage_b),
                "continuous_contact_family": bool(max(coverage_a, coverage_b) >= 0.20),
            })
            patch_id += 1
    return patches


def _endpoint_records(patches: list[dict]):
    endpoints = []
    for patch in patches:
        p = int(patch["patch_id"])
        endpoints.append({
            "endpoint_id": 2*p,
            "patch_id": p,
            "side": "a",
            "component": int(patch["component_a"]),
            "index": int(patch["index_a"]),
            "partner_endpoint_id": 2*p+1,
        })
        endpoints.append({
            "endpoint_id": 2*p+1,
            "patch_id": p,
            "side": "b",
            "component": int(patch["component_b"]),
            "index": int(patch["index_b"]),
            "partner_endpoint_id": 2*p,
        })
    return endpoints


def _next_endpoint(
    event_ids: list[int],
    endpoints_by_id: dict[int, dict],
    current_id: int,
    n: int,
    direction: int,
) -> tuple[int | None, int | None]:
    if len(event_ids) <= 1:
        return None, None
    ordered = sorted((endpoints_by_id[e]["index"], e) for e in event_ids)
    current_index = endpoints_by_id[current_id]["index"]
    if direction > 0:
        pos = bisect_right(ordered, (current_index, 10**18))
        candidates = ordered[pos:] + ordered[:pos]
        for idx, eid in candidates:
            if eid != current_id:
                delta = (idx-current_index) % n
                if delta > 0:
                    return eid, delta
    else:
        pos = bisect_left(ordered, (current_index, -1))
        candidates = list(reversed(ordered[:pos])) + list(reversed(ordered[pos:]))
        for idx, eid in candidates:
            if eid != current_id:
                delta = (current_index-idx) % n
                if delta > 0:
                    return eid, delta
    return None, None


def _functional_cycles(mapping: dict[int, int]) -> list[list[int]]:
    color = {node: 0 for node in mapping}
    cycles = []
    for start in sorted(mapping):
        if color[start] != 0:
            continue
        path, position = [], {}
        node = start
        while node in mapping and color.get(node, 0) == 0:
            color[node] = 1
            position[node] = len(path)
            path.append(node)
            node = mapping[node]
            if node in position:
                cycles.append(path[position[node]:])
                break
        for item in path:
            color[item] = 2
    # Canonical deduplication.
    unique = {}
    for cycle in cycles:
        rotations = [tuple(cycle[i:]+cycle[:i]) for i in range(len(cycle))]
        key = min(rotations)
        unique[key] = list(key)
    return list(unique.values())


def contact_map_orbits(
    patches: list[dict],
    component_sizes: list[int],
    max_reported_orbits: int = 12,
) -> dict:
    endpoints = _endpoint_records(patches)
    by_id = {e["endpoint_id"]: e for e in endpoints}
    events = defaultdict(list)
    for endpoint in endpoints:
        events[endpoint["component"]].append(endpoint["endpoint_id"])

    direction_reports = {}
    augmented_edges = set()
    # Contact jumps.
    for endpoint in endpoints:
        augmented_edges.add(tuple(sorted((endpoint["endpoint_id"], endpoint["partner_endpoint_id"]))))
    # Centerline arcs between consecutive contact endpoints.
    for component, ids in events.items():
        ordered = sorted(ids, key=lambda eid: (by_id[eid]["index"], eid))
        if len(ordered) >= 2:
            for a, b in zip(ordered, ordered[1:]+ordered[:1]):
                augmented_edges.add(tuple(sorted((a, b))))

    for direction in (+1, -1):
        mapping, arc_steps = {}, {}
        for endpoint in endpoints:
            partner = by_id[endpoint["partner_endpoint_id"]]
            nxt, delta = _next_endpoint(
                events[partner["component"]], by_id, partner["endpoint_id"],
                component_sizes[partner["component"]-1], direction,
            )
            if nxt is not None:
                mapping[endpoint["endpoint_id"]] = nxt
                arc_steps[endpoint["endpoint_id"]] = int(delta)
        cycles = _functional_cycles(mapping)
        cycle_rows = []
        for cycle in sorted(cycles, key=lambda c: (len(c), c)):
            rows = []
            fractions = []
            for eid in cycle:
                endpoint = by_id[eid]
                partner = by_id[endpoint["partner_endpoint_id"]]
                nxt = by_id[mapping[eid]]
                n = component_sizes[partner["component"]-1]
                fraction = arc_steps[eid]/n
                fractions.append(fraction)
                rows.append({
                    "endpoint_id": eid,
                    "patch_id": endpoint["patch_id"],
                    "jump_to_component": partner["component"],
                    "jump_to_index": partner["index"],
                    "advance_to_patch_id": nxt["patch_id"],
                    "advance_to_index": nxt["index"],
                    "arc_fraction": float(fraction),
                })
            cycle_rows.append({
                "period_contacts": len(cycle),
                "mean_arc_fraction": float(np.mean(fractions)),
                "min_arc_fraction": float(np.min(fractions)),
                "max_arc_fraction": float(np.max(fractions)),
                "states": rows,
            })
        histogram = Counter(row["period_contacts"] for row in cycle_rows)
        direction_reports["forward" if direction > 0 else "reverse"] = {
            "mapped_state_count": len(mapping),
            "closed_orbit_count": len(cycle_rows),
            "period_histogram": {str(k): v for k, v in sorted(histogram.items())},
            "candidate_period_9_count": int(histogram.get(9, 0)),
            "shortest_period": min(histogram, default=None),
            "longest_period": max(histogram, default=None),
            "representative_orbits": cycle_rows[:max_reported_orbits],
        }

    # Cycle rank of the augmented endpoint graph: contact jumps + centerline arcs.
    dsu = _DisjointSet()
    for a, b in augmented_edges:
        dsu.union(a, b)
    roots = {dsu.find(x) for x in dsu.parent}
    augmented_rank = max(0, len(augmented_edges)-len(dsu.parent)+len(roots))
    return {
        "patch_count": len(patches),
        "continuous_contact_patch_count": sum(p["continuous_contact_family"] for p in patches),
        "augmented_endpoint_nodes": len(endpoints),
        "augmented_graph_edges": len(augmented_edges),
        "augmented_graph_connected_components": len(roots),
        "augmented_contact_graph_cycle_rank": augmented_rank,
        "directions": direction_reports,
        "total_closed_orbit_count": sum(
            report["closed_orbit_count"] for report in direction_reports.values()
        ),
        "candidate_period_9_count": sum(
            report["candidate_period_9_count"] for report in direction_reports.values()
        ),
        "status": (
            "Discrete contact-map orbit diagnostic. It alternates contact jumps with directed "
            "centerline advance; it does not yet test a specular-reflection law and is therefore "
            "not by itself a billiard-orbit proof."
        ),
    }


def contact_summary(
    samples,
    diameter: float,
    tolerance: float,
    patch_adjacency: int = 2,
) -> dict:
    mutual, mutual_edges = mutual_contacts(samples, diameter, tolerance)
    self_stats, self_edges = self_contacts(samples, diameter, tolerance)
    edges = mutual_edges + self_edges
    component_sizes = [len(s.r) for s in samples]
    graph = contact_graph_summary(edges, component_sizes)
    patches = cluster_contact_patches(edges, component_sizes, patch_adjacency)
    contact_map = contact_map_orbits(patches, component_sizes)
    return {
        "mutual_pairs": mutual,
        "self_components": self_stats,
        "graph": graph,
        "patches": patches,
        "contact_map": contact_map,
        "edges": edges,
    }
