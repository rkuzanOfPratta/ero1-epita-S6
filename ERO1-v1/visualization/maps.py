import os
import folium
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

SCENARIO_COLORS = {
    "S1_urgences": "red",
    "S2_residentiel": "blue",
    "S3_baseline": "green",
}


def _graph_centroid(G: nx.MultiDiGraph) -> tuple:
    lats = [data["y"] for _, data in G.nodes(data=True) if "y" in data]
    lons = [data["x"] for _, data in G.nodes(data=True) if "x" in data]
    return np.mean(lats), np.mean(lons)


def save_folium_map(G: nx.MultiDiGraph, circuit: list, district: str, scenario: str, output_dir: str):
    lat, lon = _graph_centroid(G)
    fmap = folium.Map(location=[lat, lon], zoom_start=14, tiles="CartoDB positron")

    for u, v, data in G.edges(data=True):
        u_data = G.nodes[u]
        v_data = G.nodes[v]
        if "y" not in u_data or "y" not in v_data:
            continue
        folium.PolyLine(
            locations=[[u_data["y"], u_data["x"]], [v_data["y"], v_data["x"]]],
            color="lightgray",
            weight=1,
            opacity=0.5,
        ).add_to(fmap)

    color = SCENARIO_COLORS.get(scenario, "purple")
    circuit_edges = set()
    for u, v in circuit:
        circuit_edges.add((u, v))

    for u, v in circuit_edges:
        if u not in G.nodes or v not in G.nodes:
            continue
        u_data = G.nodes[u]
        v_data = G.nodes[v]
        if "y" not in u_data or "y" not in v_data:
            continue
        folium.PolyLine(
            locations=[[u_data["y"], u_data["x"]], [v_data["y"], v_data["x"]]],
            color=color,
            weight=2.5,
            opacity=0.8,
        ).add_to(fmap)

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{district}_{scenario}.html")
    fmap.save(out_path)
    return out_path


def save_cost_chart(costs_by_n: dict, district: str, scenario: str, output_dir: str, n_star: int):
    ns = sorted(costs_by_n.keys())
    costs = [costs_by_n[n] for n in ns]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(ns, costs, color="steelblue", alpha=0.7, edgecolor="navy")
    bars[n_star - 1].set_color("orange")
    bars[n_star - 1].set_edgecolor("darkorange")

    ax.annotate(
        f"n*={n_star}\n{costs_by_n[n_star]:.0f} $",
        xy=(n_star, costs_by_n[n_star]),
        xytext=(n_star + 0.5, costs_by_n[n_star] * 1.02),
        arrowprops=dict(arrowstyle="->", color="black"),
        fontsize=9,
    )

    ax.set_xlabel("Nombre de véhicules")
    ax.set_ylabel("Coût total ($)")
    ax.set_title(f"{district.capitalize()} — {scenario}")
    ax.set_xticks(ns)
    fig.tight_layout()

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{district}_{scenario}_cost.png")
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
