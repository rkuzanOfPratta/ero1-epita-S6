#!/usr/bin/env python3
"""
Point d'entrée principal du projet ERO1 – Optimisation hivernale.
Utilisation : python3 main.py [district] [--vehicules N] [--demo]

  district   : outremont | verdun | anjou | rdp_pat | all  (défaut : all)
  --vehicules: nombre de véhicules par arrondissement       (défaut : 3)
  --demo     : traite uniquement outremont (exécution rapide)
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from src.fetch_data  import (
    charger_graphe, stats_graphe, DISTRICTS,
    charger_pois_urgence, charger_pois_commerce,
)
from src.chinese_postman import solve_directed_cpp, circuit_stats
from src.cost_model  import cout_flotte, rapport_cout
from src.scenarios   import SCENARIOS, edge_priority_map, compute_scenario_metrics
from src.visualize   import carte_circuit, graphe_cout_vehicules, comparaison_scenarios


def traiter_district(district_key: str, n_vehicules: int, dossier_out: str) -> dict:
    """Pipeline complet pour un arrondissement : données → CPP → coût → visualisations."""
    print(f"\n{'='*60}")
    print(f"Arrondissement : {district_key.upper()}")
    print(f"{'='*60}")

    # --- Données ---
    print("Téléchargement/chargement du réseau routier...")
    G = charger_graphe(district_key)
    stats = stats_graphe(G)
    print(f"  Réseau : {stats['noeuds']} nœuds, {stats['arcs']} arcs, "
          f"{stats['longueur_totale_km']:.1f} km total")

    # --- CPP (circuit optimal) ---
    print("Résolution du Problème du Postier Chinois Dirigé...")
    circuit, dist_totale_m, dist_vide_m = solve_directed_cpp(G, weight="length")
    dist_totale_km = dist_totale_m / 1000
    dist_vide_km   = dist_vide_m   / 1000
    print(f"  Circuit : {len(circuit)} arcs, {dist_totale_km:.2f} km "
          f"(dont {dist_vide_km:.2f} km à vide)")

    cstats = circuit_stats(circuit, G)
    print(f"  Couverture : {cstats['coverage_pct']:.1f} %")

    # --- Coûts ---
    flotte = cout_flotte(dist_totale_km, n_vehicules)
    print(rapport_cout(flotte, district_key))

    # --- POI géospatiaux (distinguent S1 "urgences" de S2 "économique") ---
    print("Téléchargement des POI (hôpitaux/casernes, commerces)...")
    try:
        pois_urgence = charger_pois_urgence(district_key)
    except Exception as e:
        print(f"  POI urgences indisponibles ({e}), repli sur le barème highway seul.")
        pois_urgence = []
    try:
        pois_commerce = charger_pois_commerce(district_key)
    except Exception as e:
        print(f"  POI commerces indisponibles ({e}), repli sur le barème highway seul.")
        pois_commerce = []
    print(f"  {len(pois_urgence)} POI urgences, {len(pois_commerce)} POI commerces")

    pois_par_scenario = {
        "urgences": pois_urgence,
        "economique": pois_commerce,
        "residentiel": None,
    }

    # --- Scénarios ---
    metriques_scenarios = []
    for scenario_key in SCENARIOS:
        m = compute_scenario_metrics(
            circuit, G, scenario_key,
            pois=pois_par_scenario.get(scenario_key),
        )
        metriques_scenarios.append(m)
        t50 = f"{m['temps_50pct_h']:.2f}h" if m['temps_50pct_h'] is not None else "N/A"
        t100 = f"{m['temps_100pct_h']:.2f}h" if m.get('temps_100pct_h') is not None else "N/A"
        print(f"  [{scenario_key}] 50% HP en {t50}, 100% HP en {t100}")

    # --- Visualisations ---
    print("Génération des visualisations...")
    for scenario_key in SCENARIOS:
        carte_circuit(
            G, circuit, scenario_key,
            titre=f"{district_key} – {SCENARIOS[scenario_key]['nom']}",
            chemin_sortie=os.path.join(dossier_out, district_key, "results",
                                       f"carte_{scenario_key}.png"),
        )

    graphe_cout_vehicules(
        dist_totale_km,
        chemin_sortie=os.path.join(dossier_out, district_key, "results", "cout_flotte.png"),
        nom_district=district_key,
    )

    comparaison_scenarios(
        metriques_scenarios,
        chemin_sortie=os.path.join(dossier_out, district_key, "results", "comparaison_scenarios.png"),
        nom_district=district_key,
    )

    # --- Sauvegarde JSON des résultats ---
    resultats = {
        "district": district_key,
        "reseau": stats,
        "circuit": {
            "n_arcs": len(circuit),
            "distance_totale_km": dist_totale_km,
            "distance_vide_km": dist_vide_km,
            "couverture_pct": cstats["coverage_pct"],
        },
        "flotte": flotte,
        "scenarios": metriques_scenarios,
    }
    json_path = os.path.join(dossier_out, district_key, "results", "resultats.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)
    print(f"  Résultats JSON : {json_path}")

    return resultats


def main():
    parser = argparse.ArgumentParser(description="ERO1 – Optimisation déneigement Montréal")
    parser.add_argument("district", nargs="?", default="all",
                        choices=list(DISTRICTS.keys()) + ["all"],
                        help="Arrondissement à traiter (défaut: all)")
    parser.add_argument("--vehicules", type=int, default=3,
                        help="Nombre de véhicules par arrondissement (défaut: 3)")
    parser.add_argument("--demo", action="store_true",
                        help="Mode démonstration : traite uniquement Outremont")
    args = parser.parse_args()

    dossier = os.path.join(os.path.dirname(__file__), "districts")
    os.makedirs(dossier, exist_ok=True)

    if args.demo:
        cibles = ["outremont"]
    elif args.district == "all":
        cibles = list(DISTRICTS.keys())
    else:
        cibles = [args.district]

    tous_resultats = {}
    for d in cibles:
        try:
            r = traiter_district(d, args.vehicules, dossier)
            tous_resultats[d] = r
        except Exception as e:
            print(f"  ERREUR [{d}] : {e}")
            import traceback; traceback.print_exc()

    print("\n" + "="*60)
    print("RÉSUMÉ GLOBAL")
    print("="*60)
    for d, r in tous_resultats.items():
        f = r["flotte"]
        print(f"  {d:30s}  {r['circuit']['distance_totale_km']:7.1f} km  "
              f"{f['cout_total_flotte']:8.0f} $  ({f['n_vehicules']} véhicules)")


if __name__ == "__main__":
    main()