#!/usr/bin/env bash
# Démonstration rapide : traite l'arrondissement d'Outremont avec 2 véhicules.
# Les résultats (cartes PNG, graphiques, JSON) sont générés dans
# districts/outremont/results/

set -e
cd "$(dirname "$0")"

echo "=== ERO1 – Démo déneigement Montréal ==="
echo "Arrondissement : Outremont | Véhicules : 2"
echo ""

python3 main.py outremont --vehicules 2

echo ""
echo "Résultats générés dans : districts/outremont/results/"
echo "  carte_urgences.png      – Circuit priorité urgences"
echo "  carte_economique.png    – Circuit priorité économique"
echo "  carte_residentiel.png   – Circuit priorité résidentielle"
echo "  cout_flotte.png          – Courbe coût vs flotte"
echo "  comparaison_scenarios.png – Comparaison des 3 scénarios"
echo "  resultats.json           – Données brutes"
