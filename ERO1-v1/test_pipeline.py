import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import networkx as nx

from data.download_graphs import get_graph
from scenarios.scenarios import apply_scenario, apply_s1_urgences, apply_s2_residentiel
from algorithms.cpp_solver import solve_cpp, circuit_total_distance
from cost_model.cost import compute_cost, optimal_vehicles, cost_by_vehicles
from visualization.maps import save_folium_map, save_cost_chart


def test_download():
    G = get_graph("outremont")
    assert G.number_of_nodes() > 0, "Graph has no nodes"
    assert G.number_of_edges() > 0, "Graph has no edges"
    print(f"  [OK] download: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")


def test_scenarios():
    G = get_graph("outremont")

    G1 = apply_s1_urgences(G)
    weights1 = [d.get("weight", 1) for _, _, d in G1.edges(data=True)]
    assert any(w < 1.0 for w in weights1), "S1 weights not modified"
    print("  [OK] S1_urgences: weights modified")

    G2 = apply_s2_residentiel(G)
    weights2 = [d.get("weight", 1) for _, _, d in G2.edges(data=True)]
    assert any(w < 1.0 for w in weights2), "S2 weights not modified"
    print("  [OK] S2_residentiel: weights modified")

    G3 = apply_scenario(G, "S3_baseline")
    for _, _, d in G3.edges(data=True):
        assert "weight" in d
    print("  [OK] S3_baseline: weights assigned")


def test_cpp():
    G = get_graph("outremont")
    G_s = apply_scenario(G, "S3_baseline")
    circuit = solve_cpp(G_s)
    assert len(circuit) > 0, "Circuit is empty"
    dist = circuit_total_distance(G, circuit)
    assert dist > 0, "Circuit distance is zero"
    print(f"  [OK] cpp: circuit has {len(circuit)} edges, {dist:.2f} km")


def test_cost():
    cost = compute_cost(50.0, 2)
    assert cost > 0
    n_star, min_cost = optimal_vehicles(50.0)
    assert isinstance(n_star, int) and n_star >= 1
    assert min_cost > 0
    costs = cost_by_vehicles(50.0)
    assert len(costs) == 20
    print(f"  [OK] cost: n*={n_star}, coût={min_cost:.2f} $")


def test_viz():
    G = get_graph("outremont")
    G_s = apply_scenario(G, "S3_baseline")
    circuit = solve_cpp(G_s)
    dist = circuit_total_distance(G, circuit)
    n_star, _ = optimal_vehicles(dist)
    costs = cost_by_vehicles(dist)

    output_dir = os.path.join(os.path.dirname(__file__), "outremont")
    map_path = save_folium_map(G, circuit, "outremont", "S3_baseline", output_dir)
    chart_path = save_cost_chart(costs, "outremont", "S3_baseline", output_dir, n_star)

    assert os.path.exists(map_path), f"Map not found: {map_path}"
    assert os.path.exists(chart_path), f"Chart not found: {chart_path}"
    print(f"  [OK] viz: {map_path}")
    print(f"  [OK] viz: {chart_path}")


TESTS = [
    ("download", test_download),
    ("scenarios", test_scenarios),
    ("cpp", test_cpp),
    ("cost", test_cost),
    ("viz", test_viz),
]

if __name__ == "__main__":
    failed = 0
    for name, fn in TESTS:
        print(f"\nTest: {name}")
        try:
            fn()
        except Exception as e:
            print(f"  [FAIL] {e}")
            failed += 1

    print(f"\n{'='*40}")
    if failed == 0:
        print("Tous les tests sont passés.")
    else:
        print(f"{failed} test(s) échoué(s).")
        sys.exit(1)
