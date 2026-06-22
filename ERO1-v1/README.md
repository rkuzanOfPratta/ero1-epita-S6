# ERO1 — Optimisation Hivernale

Projet de recherche opérationnelle — EPITA APPING1 groupe 9

Optimisation des routes de chasse-neige pour 4 arrondissements de Montréal via le Problème du Postier Chinois (CPP) sur graphes orientés OSM.

## Membres

- Rayan KHEROUA
- Yazid TARMOUL
- Arsan ABDI
- Rayan TAIL
- Lucas DEFAUD

## Prérequis

```bash
pip install osmnx networkx matplotlib folium numpy
```

## Utilisation

```bash
python demo.py --sector outremont --scenario S1_urgences
python demo.py --sector verdun --scenario S2_residentiel
python demo.py --sector anjou --scenario S3_baseline
python demo.py --all
```

**Secteurs disponibles :** `outremont`, `verdun`, `anjou`, `riviere-des-prairies`

**Scénarios disponibles :**
- `S1_urgences` — priorité aux axes principaux et accès hôpitaux/casernes (poids × 0.01)
- `S2_residentiel` — priorité aux rues résidentielles (poids × 0.3)
- `S3_baseline` — aucune modification des poids (CPP pur)

## Tests

```bash
python test_pipeline.py
```

## Structure

```
data/download_graphs.py     — téléchargement et cache des graphes OSM
algorithms/cpp_solver.py    — résolution CPP (flot min-coût + circuit eulérien)
scenarios/scenarios.py      — modification des poids selon le scénario
cost_model/cost.py          — modèle de coût et calcul de n*
visualization/maps.py       — génération des cartes HTML et graphiques PNG
demo.py                     — script de démonstration CLI
test_pipeline.py            — tests de bout en bout
outremont/                  — sorties pour Outremont
verdun/                     — sorties pour Verdun
anjou/                      — sorties pour Anjou
riviere-des-prairies/       — sorties pour Rivière-des-Prairies–Pointe-aux-Trembles
```

## Algorithme

1. Téléchargement du réseau routier OSM via `osmnx`
2. Application du scénario (modification des poids des arcs)
3. Calcul des déséquilibres nodaux (in_degree − out_degree)
4. Équilibrage par flot à coût minimum (`networkx.max_flow_min_cost`)
5. Circuit eulérien via l'algorithme de Hierholzer (`networkx.eulerian_circuit`)
6. Calcul du coût total et du nombre optimal de véhicules n*
7. Génération de la carte interactive Folium et du graphique matplotlib
