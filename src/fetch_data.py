"""Téléchargement et préparation des données OSM via OSMnx."""

import os
import osmnx as ox
import networkx as nx

# Cache local pour éviter de retélécharger à chaque exécution
ox.settings.use_cache = True
ox.settings.cache_folder = os.path.join(os.path.dirname(__file__), "..", "cache")

DISTRICTS = {
    "outremont": "Outremont, Montréal, Québec, Canada",
    "verdun":    "Verdun, Montréal, Québec, Canada",
    "anjou":     "Anjou, Montréal, Québec, Canada",
    "rdp_pat":   "Rivière-des-Prairies–Pointe-aux-Trembles, Montréal, Québec, Canada",
}


def charger_graphe(district_key: str) -> nx.MultiDiGraph:
    """
    Télécharge (ou charge depuis le cache) le réseau routier d'un arrondissement.
    Filtre les routes non-carrossables et simplifie la topologie.
    """
    place = DISTRICTS[district_key]
    G = ox.graph_from_place(place, network_type="drive", simplify=True)

    # Projection en mètres (UTM) pour avoir des distances exactes
    G = ox.project_graph(G)

    print(f"  [{district_key}] {G.number_of_nodes()} nœuds, {G.number_of_edges()} arcs")
    return G


def sauvegarder_graphe(G: nx.MultiDiGraph, chemin: str) -> None:
    """Sauvegarde le graphe au format GraphML."""
    nx.write_graphml(G, chemin)


def charger_graphe_local(chemin: str) -> nx.MultiDiGraph:
    """Charge un graphe depuis un fichier GraphML local."""
    return nx.read_graphml(chemin, node_type=int)


def stats_graphe(G: nx.MultiDiGraph) -> dict:
    """Statistiques descriptives du réseau routier."""
    longueurs = [d.get("length", 0) for _, _, d in G.edges(data=True)]
    total_km = sum(longueurs) / 1000
    return {
        "noeuds": G.number_of_nodes(),
        "arcs": G.number_of_edges(),
        "longueur_totale_km": total_km,
        "longueur_moy_arc_m": sum(longueurs) / max(len(longueurs), 1),
    }
