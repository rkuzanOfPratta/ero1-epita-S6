"""Problème du Postier Chinois Dirigé (Route Inspection Problem)."""

import networkx as nx
from typing import Dict, List, Tuple


def _to_simple_digraph(G: nx.MultiDiGraph) -> nx.DiGraph:
    """Réduit le MultiDiGraph en DiGraph simple (arc le plus court entre chaque paire)."""
    H = nx.DiGraph()
    H.add_nodes_from(G.nodes(data=True))
    for u, v, data in G.edges(data=True):
        w = data.get("length", 1.0)
        if not H.has_edge(u, v) or H[u][v]["length"] > w:
            H.add_edge(u, v, **data)
    return H


def compute_imbalance(G) -> Dict:
    """Retourne le déséquilibre (degré_sortant - degré_entrant) pour chaque nœud."""
    return {v: G.out_degree(v) - G.in_degree(v) for v in G.nodes()}


def solve_directed_cpp(
    G: nx.MultiDiGraph,
    weight: str = "length",
) -> Tuple[List[Tuple], float, float]:
    """
    Résout le PPC dirigé sur G.
    Retourne : (circuit, distance_totale_m, distance_à_vide_m)
    """
    # Composante fortement connexe principale
    if not nx.is_strongly_connected(G):
        sccs = sorted(nx.strongly_connected_components(G), key=len, reverse=True)
        G = G.subgraph(sccs[0]).copy()

    H = _to_simple_digraph(G)
    # Déséquilibre calculé sur le MultiDiGraph original (les arcs parallèles comptent)
    imbalance = compute_imbalance(G)

    neg_nodes = [v for v, b in imbalance.items() if b < 0]
    pos_nodes = [v for v, b in imbalance.items() if b > 0]

    if not neg_nodes and not pos_nodes:
        aug = nx.MultiDiGraph(G)
        circuit = list(nx.eulerian_circuit(aug, keys=False))
        total = sum(H[u][v].get(weight, 0) for u, v in circuit if H.has_edge(u, v))
        return circuit, total, 0.0

    # Réseau de flot : convention NetworkX = demande > 0 → puits, < 0 → source
    # Déséquilibre b = sortant - entrant :
    #   b > 0 → trop d'arcs sortants → besoin d'arcs entrants → puits (demand = b)
    #   b < 0 → trop d'arcs entrants → besoin d'arcs sortants → source (demand = b)
    flow_net = nx.DiGraph()
    for v, b in imbalance.items():
        if b != 0:
            flow_net.add_node(v, demand=b)

    # Capacité suffisante pour ne pas contraindre le routage du flot
    total_supply = sum(-b for b in imbalance.values() if b < 0)
    SCALE = 1000

    for s in neg_nodes:
        try:
            lengths, _ = nx.single_source_dijkstra(H, s, weight=weight)
        except nx.NetworkXError:
            continue
        for t in pos_nodes:
            if t not in lengths or t == s:
                continue
            cost = max(1, int(lengths[t] * SCALE))
            if not flow_net.has_edge(s, t) or flow_net[s][t]["weight"] > cost:
                flow_net.add_edge(s, t, weight=cost, capacity=total_supply)

    try:
        flow_dict = nx.min_cost_flow(flow_net)
    except (nx.NetworkXUnfeasible, nx.NetworkXError):
        flow_dict = _greedy_fallback(H, neg_nodes, pos_nodes, imbalance, weight)

    # Ajout des arcs de deadhead dans le graphe augmenté
    aug = nx.MultiDiGraph(G)
    deadhead_dist = 0.0

    for s in neg_nodes:
        if s not in flow_dict:
            continue
        for t, flow in flow_dict[s].items():
            if flow <= 0:
                continue
            try:
                path_nodes = nx.shortest_path(H, s, t, weight=weight)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue
            for _ in range(flow):
                for i in range(len(path_nodes) - 1):
                    u, v = path_nodes[i], path_nodes[i + 1]
                    arc_len = H[u][v].get(weight, 0)
                    aug.add_edge(u, v, length=arc_len, deadhead=True)
                    deadhead_dist += arc_len

    try:
        circuit = list(nx.eulerian_circuit(aug, keys=False))
    except Exception:
        circuit = []

    total_dist = 0.0
    if circuit:
        for u, v in circuit:
            if aug.has_edge(u, v):
                total_dist += aug[u][v][0].get(weight, 0)

    return circuit, total_dist, deadhead_dist


def _greedy_fallback(H, neg_nodes, pos_nodes, imbalance, weight):
    """Appariement glouton des nœuds déséquilibrés (solution de repli)."""
    flow_dict: Dict = {s: {} for s in neg_nodes}
    pos_remaining = {t: imbalance[t] for t in pos_nodes}
    neg_remaining = {s: -imbalance[s] for s in neg_nodes}

    for s in neg_nodes:
        try:
            lengths = dict(nx.single_source_dijkstra_path_length(H, s, weight=weight))
        except nx.NetworkXError:
            continue
        reachable = sorted(
            [(lengths[t], t) for t in pos_nodes if t in lengths and pos_remaining.get(t, 0) > 0]
        )
        for _, t in reachable:
            if neg_remaining[s] <= 0:
                break
            units = min(neg_remaining[s], pos_remaining[t])
            flow_dict[s][t] = units
            neg_remaining[s] -= units
            pos_remaining[t] -= units

    return flow_dict


def circuit_stats(circuit: List[Tuple], G_original: nx.MultiDiGraph) -> Dict:
    """Statistiques de base sur le circuit calculé."""
    original_arcs = set((u, v) for u, v, _ in G_original.edges(keys=True))
    traversed = set()
    total_dist = 0.0

    for u, v in circuit:
        traversed.add((u, v))
        if G_original.has_edge(u, v):
            arc_len = min(d.get("length", 0) for d in G_original[u][v].values())
            total_dist += arc_len

    coverage = len(traversed & original_arcs) / max(len(original_arcs), 1) * 100

    return {
        "n_arcs": len(circuit),
        "total_dist_m": total_dist,
        "total_dist_km": total_dist / 1000,
        "coverage_pct": coverage,
    }
