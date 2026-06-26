# ERO1 – Optimisation hivernale du déneigement de Montréal

## Auteurs
Rayan Kheroua — EPITA S6

## Prérequis

Python 3.10+ avec les paquets suivants :

```
osmnx>=2.0
networkx>=3.0
matplotlib>=3.5
folium>=0.14
scipy>=1.9
```

Installation :
```bash
pip install osmnx networkx matplotlib folium scipy
```

## Structure du projet

```
.
├── AUTHORS                     liste des auteurs
├── README.md                   ce fichier
├── demo.sh                     script de démonstration
├── main.py                     point d'entrée principal
├── rapport.tex                 source LaTeX du rapport
├── src/
│   ├── chinese_postman.py      algorithme PPC dirigé (min-cost flow)
│   ├── cost_model.py           modèle de coût des opérations
│   ├── fetch_data.py           téléchargement OSM via OSMnx
│   ├── scenarios.py            définition des 3 scénarios
│   └── visualize.py            cartes Folium + graphiques Matplotlib
├── districts/
│   ├── outremont/results/      résultats Outremont
│   ├── verdun/results/         résultats Verdun
│   ├── anjou/results/          résultats Anjou
│   └── rdp_pat/results/        résultats Rivière-des-Prairies–PAT
└── ressource/                  documents fournis (énoncé, cours)
```

## Exécution

### Démonstration rapide (Outremont uniquement)

```bash
bash demo.sh
```

### Traitement d'un seul arrondissement

```bash
python3 main.py outremont --vehicules 3
```

### Traitement de tous les arrondissements

```bash
python3 main.py all --vehicules 3
```

### Options disponibles

| Option | Valeur | Description |
|---|---|---|
| `district` | `outremont` / `verdun` / `anjou` / `rdp_pat` / `all` | Arrondissement à traiter |
| `--vehicules N` | entier | Nombre de véhicules par arrondissement (défaut : 3) |
| `--demo` | flag | Alias pour traiter uniquement Outremont |

## Résultats générés

Pour chaque arrondissement, le dossier `districts/<nom>/results/` contient :

| Fichier | Description |
|---|---|
| `carte_urgences.html` | Circuit interactif – scénario urgences |
| `carte_economique.html` | Circuit interactif – scénario économique |
| `carte_residentiel.html` | Circuit interactif – scénario résidentiel |
| `cout_flotte.png` | Courbe coût total vs nombre de véhicules |
| `comparaison_scenarios.png` | Histogramme de comparaison des 3 scénarios |
| `resultats.json` | Données brutes (réseau, circuit, coûts, métriques) |

## Algorithme

Le problème est modélisé comme un **Problème du Postier Chinois Dirigé** :
- Graphe dirigé G=(V, E) extrait d'OpenStreetMap via OSMnx
- Chaque arc doit être parcouru au moins une fois
- Les arcs supplémentaires (deadhead) minimisent la distance totale

La résolution se fait en deux étapes :
1. Calcul du déséquilibre de chaque nœud (degré_sortant – degré_entrant)
2. Résolution d'un problème de flot à coût minimum (NetworkX `min_cost_flow`) pour déterminer les arcs de deadhead optimaux
3. Calcul d'un circuit eulérien sur le graphe augmenté

## Données

Les données routières proviennent d'OpenStreetMap (© contributeurs OpenStreetMap).
Téléchargées automatiquement via OSMnx et mises en cache dans `cache/`.
