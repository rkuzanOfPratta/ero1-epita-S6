import copy
import networkx as nx

PRIORITY_HIGHWAYS = {"primary", "secondary", "trunk", "motorway",
                     "primary_link", "secondary_link", "trunk_link", "motorway_link"}
RESIDENTIAL_HIGHWAYS = {"residential", "living_street", "unclassified"}


def _highway_matches(edge_data: dict, highway_set: set) -> bool:
    hw = edge_data.get("highway", "")
    if isinstance(hw, list):
        return bool(set(hw) & highway_set)
    return hw in highway_set


def apply_s1_urgences(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    G = copy.deepcopy(G)
    for u, v, k, data in G.edges(keys=True, data=True):
        data["weight"] = data.get("length", 1.0)
        if _highway_matches(data, PRIORITY_HIGHWAYS):
            data["weight"] *= 0.01
    return G


def apply_s2_residentiel(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    G = copy.deepcopy(G)
    for u, v, k, data in G.edges(keys=True, data=True):
        data["weight"] = data.get("length", 1.0)
        if _highway_matches(data, RESIDENTIAL_HIGHWAYS):
            data["weight"] *= 0.3
    return G


def apply_s3_baseline(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    G = copy.deepcopy(G)
    for u, v, k, data in G.edges(keys=True, data=True):
        data["weight"] = data.get("length", 1.0)
    return G


def apply_scenario(G: nx.MultiDiGraph, scenario: str) -> nx.MultiDiGraph:
    dispatch = {
        "S1_urgences": apply_s1_urgences,
        "S2_residentiel": apply_s2_residentiel,
        "S3_baseline": apply_s3_baseline,
    }
    return dispatch[scenario](G)
