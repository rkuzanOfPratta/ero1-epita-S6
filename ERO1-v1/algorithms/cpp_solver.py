import copy
import networkx as nx


def _compute_imbalances(G: nx.MultiDiGraph) -> dict:
    imbalances = {}
    for node in G.nodes():
        imbalances[node] = G.in_degree(node) - G.out_degree(node)
    return imbalances


def _build_flow_graph(G: nx.MultiDiGraph, imbalances: dict) -> nx.DiGraph:
    flow_graph = nx.DiGraph()
    flow_graph.add_node("source")
    flow_graph.add_node("sink")

    surplus = {n: v for n, v in imbalances.items() if v > 0}
    deficit = {n: v for n, v in imbalances.items() if v < 0}

    for s_node, s_val in surplus.items():
        flow_graph.add_edge("source", s_node, capacity=s_val, weight=0)

    for d_node, d_val in deficit.items():
        flow_graph.add_edge(d_node, "sink", capacity=-d_val, weight=0)

    for s_node in surplus:
        for d_node in deficit:
            try:
                cost = nx.shortest_path_length(G, s_node, d_node, weight="weight")
            except nx.NetworkXNoPath:
                continue
            flow_graph.add_edge(s_node, d_node, capacity=min(surplus[s_node], -deficit[d_node]), weight=int(cost * 1000))

    return flow_graph


def _add_balancing_edges(G: nx.MultiDiGraph, flow_graph: nx.DiGraph, flow_dict: dict) -> nx.MultiDiGraph:
    G = copy.deepcopy(G)
    for u in flow_dict:
        if u == "source":
            continue
        for v, flow in flow_dict[u].items():
            if v == "sink" or flow == 0:
                continue
            try:
                path = nx.shortest_path(G, u, v, weight="weight")
            except nx.NetworkXNoPath:
                continue
            for _ in range(flow):
                for i in range(len(path) - 1):
                    a, b = path[i], path[i + 1]
                    edge_data = min(G[a][b].values(), key=lambda d: d.get("weight", d.get("length", 1.0)))
                    G.add_edge(a, b, **edge_data)
    return G


def solve_cpp(G: nx.MultiDiGraph) -> list:
    imbalances = _compute_imbalances(G)

    if all(v == 0 for v in imbalances.values()):
        balanced = G
    else:
        flow_graph = _build_flow_graph(G, imbalances)
        try:
            flow_dict = nx.max_flow_min_cost(flow_graph, "source", "sink")
        except nx.NetworkXUnfeasible:
            balanced = G
        else:
            balanced = _add_balancing_edges(G, flow_graph, flow_dict)

    if not nx.is_eulerian(balanced):
        largest_scc = max(nx.strongly_connected_components(balanced), key=len)
        balanced = balanced.subgraph(largest_scc).copy()
        imbalances2 = _compute_imbalances(balanced)
        if not all(v == 0 for v in imbalances2.values()):
            flow_graph2 = _build_flow_graph(balanced, imbalances2)
            try:
                flow_dict2 = nx.max_flow_min_cost(flow_graph2, "source", "sink")
                balanced = _add_balancing_edges(balanced, flow_graph2, flow_dict2)
            except nx.NetworkXUnfeasible:
                pass

    return list(nx.eulerian_circuit(balanced))


def circuit_total_distance(G: nx.MultiDiGraph, circuit: list) -> float:
    total = 0.0
    for u, v in circuit:
        if G.has_edge(u, v):
            edge_data = min(G[u][v].values(), key=lambda d: d.get("length", 0))
            total += edge_data.get("length", 0)
    return total / 1000.0
