"""
Définition des trois scénarios de priorisation du déneigement.

Scénario 1 – Urgences & Sécurité publique
  Priorité aux axes proches des services d'urgence (hôpitaux, pompiers,
  police) et aux artères principales permettant l'accès aux secours.

Scénario 2 – Mobilité économique
  Priorité aux rues commerciales, aux axes de transit et aux voies
  desservant les zones d'emploi pour limiter l'impact économique.

Scénario 3 – Équité résidentielle
  Priorité aux rues résidentielles, notamment celles proches des écoles,
  des garderies et des résidences pour personnes âgées.

Les scénarios 1 et 2 partagent le même barème highway (artères en P3) ;
ils sont distingués via un bonus de priorité géospatial : +1 sur les arcs
situés à moins de RAYON_POI_M d'un POI pertinent au scénario (hôpitaux/
casernes pour S1, commerces/bureaux pour S2). Ce bonus utilise les POI
OSM réels (cf. fetch_data.charger_pois_urgence / charger_pois_commerce),
et non plus uniquement le tag highway.
"""

import networkx as nx
from typing import Dict, List, Optional, Tuple

# Poids OSMnx par type de route (highway tag)
PRIORITE_URGENCES = {
    "primary": 3, "primary_link": 3,
    "secondary": 3, "secondary_link": 3,
    "tertiary": 2, "tertiary_link": 2,
    "residential": 1, "living_street": 1,
    "service": 1, "unclassified": 1,
}

PRIORITE_ECONOMIQUE = {
    "primary": 3, "primary_link": 3,
    "secondary": 3, "secondary_link": 3,
    "tertiary": 2, "tertiary_link": 2,
    "residential": 1, "living_street": 1,
    "service": 1, "unclassified": 1,
}

# Scénario 3 : résidentiel d'abord, artères en dernier
PRIORITE_RESIDENTIELLE = {
    "residential": 3, "living_street": 3,
    "tertiary": 2, "tertiary_link": 2,
    "service": 2, "unclassified": 2,
    "secondary": 1, "secondary_link": 1,
    "primary": 1, "primary_link": 1,
}

# Rayon de proximité (mètres, coordonnées projetées UTM) pour le bonus POI
RAYON_POI_M = 150.0
BONUS_POI = 1

SCENARIOS = {
    "urgences": {
        "nom": "Urgences & Sécurité publique",
        "description": (
            "Priorise les axes permettant l'accès aux services d'urgence "
            "(hôpitaux, pompiers, police) et les artères principales."
        ),
        "priorites": PRIORITE_URGENCES,
        "poi_loader": "charger_pois_urgence",
        "cible": "Services d'urgence, accès hospitalier",
        "indicateurs": [
            "Temps de déneigement des artères principales",
            "% d'artères primaires/secondaires dégagées après 2 h",
            "Distance moyenne entre services d'urgence et route dégagée la plus proche",
        ],
    },
    "economique": {
        "nom": "Mobilité économique",
        "description": (
            "Priorise les rues commerciales et les axes de transit pour "
            "limiter les pertes économiques liées à la neige."
        ),
        "priorites": PRIORITE_ECONOMIQUE,
        "poi_loader": "charger_pois_commerce",
        "cible": "Commerces, employeurs, utilisateurs des transports en commun",
        "indicateurs": [
            "Temps de déneigement des axes commerciaux",
            "% des arrêts de bus accessibles après 3 h",
            "Perte économique estimée évitée ($/h)",
        ],
    },
    "residentiel": {
        "nom": "Équité résidentielle",
        "description": (
            "Priorise les rues résidentielles pour garantir l'accès "
            "aux domiciles, aux écoles et aux résidences pour personnes âgées."
        ),
        "priorites": PRIORITE_RESIDENTIELLE,
        "poi_loader": None,
        "cible": "Résidents, familles, élèves, personnes âgées",
        "indicateurs": [
            "Temps de déneigement des rues résidentielles",
            "% de rues résidentielles dégagées après 4 h",
            "Nombre de quartiers entièrement dégagés après 6 h",
        ],
    },
}


def _arc_pres_dun_poi(
    G: nx.MultiDiGraph, u, v, pois: List[Tuple[float, float]], rayon_m: float
) -> bool:
    """Teste si le milieu de l'arc (u, v) est à moins de rayon_m d'un POI."""
    if not pois:
        return False
    xu, yu = G.nodes[u].get("x"), G.nodes[u].get("y")
    xv, yv = G.nodes[v].get("x"), G.nodes[v].get("y")
    if xu is None or xv is None:
        return False
    mx, my = (xu + xv) / 2, (yu + yv) / 2
    for px, py in pois:
        if (mx - px) ** 2 + (my - py) ** 2 <= rayon_m ** 2:
            return True
    return False


def edge_priority_map(
    G: nx.MultiDiGraph,
    scenario_key: str,
    pois: Optional[List[Tuple[float, float]]] = None,
) -> Dict[Tuple, int]:
    """
    Construit un dictionnaire (u, v) → priorité entière pour chaque arc du graphe.
    Si `pois` est fourni (liste de points (x, y) projetés), les arcs proches
    d'un POI reçoivent un bonus BONUS_POI : c'est ce qui distingue S1 (POI =
    services d'urgence) de S2 (POI = commerces), au-delà du seul tag highway.
    """
    prio_table = SCENARIOS[scenario_key]["priorites"]
    pmap: Dict[Tuple, int] = {}

    for u, v, data in G.edges(data=True):
        hw = data.get("highway", "unclassified")
        if isinstance(hw, list):
            hw = hw[0]
        prio = prio_table.get(hw, 1)
        if pois and _arc_pres_dun_poi(G, u, v, pois, RAYON_POI_M):
            prio += BONUS_POI
        pmap[(u, v)] = prio

    return pmap


def compute_scenario_metrics(
    circuit: list,
    G: nx.MultiDiGraph,
    scenario_key: str,
    vitesse_kmh: float = 10.0,
    pois: Optional[List[Tuple[float, float]]] = None,
) -> dict:
    """
    Calcule les métriques de scénario :
    - temps (en heures) pour dégager 50 %, 80 %, 100 % des arcs haute priorité
    - distance totale et à vide

    `pois` (optionnel) : POI géospatiaux propres au scénario (cf. edge_priority_map).
    Sans POI, S1 et S2 partagent le même barème highway et donnent les mêmes
    métriques (limite documentée dans le rapport) ; avec POI, les arcs proches
    d'un hôpital/caserne (S1) ou d'un commerce/bureau (S2) sont distingués.
    """
    prio_table = SCENARIOS[scenario_key]["priorites"]
    total_dist_m = 0.0

    # Arcs haute priorité : barème highway >= 3, OU bonus POI si fourni
    arcs_hp = set()
    for u, v, data in G.edges(data=True):
        hw = data.get("highway", "unclassified")
        if isinstance(hw, list):
            hw = hw[0]
        prio = prio_table.get(hw, 1)
        if pois and _arc_pres_dun_poi(G, u, v, pois, RAYON_POI_M):
            prio += BONUS_POI
        if prio >= 3:
            arcs_hp.add((u, v))

    cleared_hp = set()
    temps_50 = temps_80 = temps_100 = None
    n_hp = max(len(arcs_hp), 1)

    for u, v in circuit:
        if G.has_edge(u, v):
            arc_len = min(d.get("length", 0) for d in G[u][v].values())
        else:
            arc_len = 0.0
        total_dist_m += arc_len

        if (u, v) in arcs_hp:
            cleared_hp.add((u, v))

        t_h = (total_dist_m / 1000) / vitesse_kmh
        pct = len(cleared_hp) / n_hp * 100

        if temps_50 is None and pct >= 50:
            temps_50 = t_h
        if temps_80 is None and pct >= 80:
            temps_80 = t_h
        if temps_100 is None and pct >= 100:
            temps_100 = t_h

    return {
        "scenario": SCENARIOS[scenario_key]["nom"],
        "arcs_haute_prio_total": len(arcs_hp),
        "arcs_haute_prio_degages": len(cleared_hp),
        "pct_hp_degages": len(cleared_hp) / n_hp * 100,
        "temps_50pct_h": temps_50,
        "temps_80pct_h": temps_80,
        "temps_100pct_h": temps_100,
        "distance_totale_km": total_dist_m / 1000,
    }