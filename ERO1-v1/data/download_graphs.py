import os
import osmnx as ox
import networkx as nx

DISTRICT_QUERIES = {
    "outremont": "Outremont, Montreal, Quebec, Canada",
    "verdun": "Verdun, Montreal, Quebec, Canada",
    "anjou": "Anjou, Montreal, Quebec, Canada",
    "riviere-des-prairies": "Rivière-des-Prairies–Pointe-aux-Trembles, Montreal, Quebec, Canada",
}

def get_graph(district_name: str) -> nx.MultiDiGraph:
    cache_dir = os.path.join(os.path.dirname(__file__), district_name)
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, "graph.graphml")

    if os.path.exists(cache_path):
        return ox.load_graphml(cache_path)

    query = DISTRICT_QUERIES[district_name]
    G = ox.graph_from_place(query, network_type="drive")
    ox.save_graphml(G, cache_path)
    return G
