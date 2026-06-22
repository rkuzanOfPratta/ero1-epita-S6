import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from data.download_graphs import get_graph
from scenarios.scenarios import apply_scenario
from algorithms.cpp_solver import solve_cpp, circuit_total_distance
from cost_model.cost import optimal_vehicles, cost_by_vehicles
from visualization.maps import save_folium_map, save_cost_chart

SECTORS = ["outremont", "verdun", "anjou", "riviere-des-prairies"]
SCENARIOS = ["S1_urgences", "S2_residentiel", "S3_baseline"]

OUTPUT_DIRS = {
    "outremont": "outremont",
    "verdun": "verdun",
    "anjou": "anjou",
    "riviere-des-prairies": "riviere-des-prairies",
}


def run(sector: str, scenario: str):
    print(f"\n[{sector}] [{scenario}] Chargement du graphe...")
    G_raw = get_graph(sector)

    print(f"[{sector}] [{scenario}] Application du scénario...")
    G = apply_scenario(G_raw, scenario)

    print(f"[{sector}] [{scenario}] Résolution CPP...")
    circuit = solve_cpp(G)

    distance_km = circuit_total_distance(G_raw, circuit)

    n_star, min_cost = optimal_vehicles(distance_km)
    costs = cost_by_vehicles(distance_km)

    output_dir = os.path.join(os.path.dirname(__file__), OUTPUT_DIRS[sector])

    map_path = save_folium_map(G_raw, circuit, sector, scenario, output_dir)
    chart_path = save_cost_chart(costs, sector, scenario, output_dir, n_star)

    print(f"\n{'='*60}")
    print(f"  Secteur   : {sector}")
    print(f"  Scénario  : {scenario}")
    print(f"  Distance  : {distance_km:.2f} km")
    print(f"  n*        : {n_star} véhicule(s)")
    print(f"  Coût opt. : {min_cost:.2f} $")
    print(f"  Carte     : {map_path}")
    print(f"  Graphique : {chart_path}")
    print(f"{'='*60}")

    return {
        "sector": sector,
        "scenario": scenario,
        "distance_km": distance_km,
        "n_star": n_star,
        "cost": min_cost,
    }


def main():
    parser = argparse.ArgumentParser(description="ERO1 — Optimisation des routes de chasse-neige")
    parser.add_argument("--sector", choices=SECTORS)
    parser.add_argument("--scenario", choices=SCENARIOS)
    parser.add_argument("--all", action="store_true", help="Génère toutes les combinaisons secteur × scénario")
    args = parser.parse_args()

    if args.all:
        results = []
        for s in SECTORS:
            for sc in SCENARIOS:
                results.append(run(s, sc))
        print("\n\nRécapitulatif global:")
        print(f"{'Secteur':<35} {'Scénario':<20} {'km':>8} {'n*':>4} {'Coût ($)':>12}")
        print("-" * 82)
        for r in results:
            print(f"{r['sector']:<35} {r['scenario']:<20} {r['distance_km']:>8.1f} {r['n_star']:>4} {r['cost']:>12.0f}")
    else:
        if not args.sector or not args.scenario:
            parser.error("--sector et --scenario sont requis (ou utiliser --all)")
        run(args.sector, args.scenario)


if __name__ == "__main__":
    main()
