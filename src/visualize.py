"""Visualisation des circuits de déneigement (Matplotlib uniquement)."""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox
from typing import List, Tuple

COULEURS_SCENARIO = {
    "urgences":    "#e63946",
    "economique":  "#f4a261",
    "residentiel": "#2a9d8f",
}


def carte_circuit(
    G: nx.MultiDiGraph,
    circuit: List[Tuple],
    scenario_key: str,
    titre: str,
    chemin_sortie: str,
) -> None:
    """Génère une image PNG du circuit de déneigement."""
    couleur = COULEURS_SCENARIO.get(scenario_key, "#1d3557")

    # Coordonnées des nœuds (UTM après projection)
    pos = {n: (d["x"], d["y"]) for n, d in G.nodes(data=True)}

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_facecolor("#f8f8f8")

    # Réseau en gris clair
    for u, v, _ in G.edges(keys=True):
        if u in pos and v in pos:
            xs = [pos[u][0], pos[v][0]]
            ys = [pos[u][1], pos[v][1]]
            ax.plot(xs, ys, color="#cccccc", linewidth=0.5, zorder=1)

    # Circuit de déneigement
    circuit_arcs = set(circuit)
    for u, v in circuit_arcs:
        if u in pos and v in pos:
            xs = [pos[u][0], pos[v][0]]
            ys = [pos[u][1], pos[v][1]]
            ax.plot(xs, ys, color=couleur, linewidth=1.2, alpha=0.7, zorder=2)

    ax.set_title(titre, fontsize=11, fontweight="bold", color="#1d3557")
    ax.set_xlabel("Est (m UTM)")
    ax.set_ylabel("Nord (m UTM)")
    ax.tick_params(labelsize=7)
    plt.tight_layout()

    os.makedirs(os.path.dirname(chemin_sortie), exist_ok=True)
    plt.savefig(chemin_sortie, dpi=130)
    plt.close()
    print(f"  Carte sauvegardée : {chemin_sortie}")


def graphe_cout_vehicules(
    distance_totale_km: float,
    chemin_sortie: str,
    nom_district: str = "",
) -> None:
    """Courbe coût total vs nombre de véhicules."""
    from src.cost_model import cout_flotte

    ns = list(range(1, 21))
    couts = [cout_flotte(distance_totale_km, n)["cout_total_flotte"] for n in ns]
    durees = [cout_flotte(distance_totale_km, n)["duree_par_vehicule_h"] for n in ns]

    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax2 = ax1.twinx()

    ax1.plot(ns, couts, "o-", color="#1d3557", label="Coût total ($)")
    ax2.plot(ns, durees, "s--", color="#e63946", label="Durée/véhicule (h)")

    ax1.set_xlabel("Nombre de véhicules")
    ax1.set_ylabel("Coût total ($)", color="#1d3557")
    ax2.set_ylabel("Durée par véhicule (h)", color="#e63946")
    ax1.set_title(f"Coût et durée selon la taille de flotte — {nom_district}")
    ax1.axhline(y=min(couts), color="gray", linestyle=":", alpha=0.5)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    plt.tight_layout()
    os.makedirs(os.path.dirname(chemin_sortie), exist_ok=True)
    plt.savefig(chemin_sortie, dpi=120)
    plt.close()
    print(f"  Graphique coût sauvegardé : {chemin_sortie}")


def comparaison_scenarios(
    metriques: List[dict],
    chemin_sortie: str,
    nom_district: str = "",
) -> None:
    """Graphique de comparaison des trois scénarios."""
    noms = [m["scenario"] for m in metriques]
    t50  = [m.get("temps_50pct_h") or 0 for m in metriques]
    t80  = [m.get("temps_80pct_h") or 0 for m in metriques]
    t100 = [m.get("temps_100pct_h") or 0 for m in metriques]

    x = range(len(noms))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar([i - width for i in x], t50,  width, label="50 % dégagé", color="#2a9d8f")
    ax.bar([i          for i in x], t80,  width, label="80 % dégagé", color="#f4a261")
    ax.bar([i + width  for i in x], t100, width, label="100 % dégagé", color="#e63946")

    ax.set_xticks(list(x))
    ax.set_xticklabels([n.replace(" ", "\n") for n in noms], fontsize=9)
    ax.set_ylabel("Temps (heures)")
    ax.set_title(f"Délai de déneigement des arcs haute priorité — {nom_district}")
    ax.legend()
    plt.tight_layout()
    os.makedirs(os.path.dirname(chemin_sortie), exist_ok=True)
    plt.savefig(chemin_sortie, dpi=120)
    plt.close()
    print(f"  Graphique scénarios sauvegardé : {chemin_sortie}")
