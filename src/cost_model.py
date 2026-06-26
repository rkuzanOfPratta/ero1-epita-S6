"""Modèle de coût des opérations de déblaiement (données énoncé)."""

COUT_FIXE = 500.0    # $/jour/véhicule
COUT_KM   = 1.1      # $/km
COUT_H    = 1.1      # $/h (8 premières heures)
COUT_H_SUP = 1.3     # $/h (au-delà de 8 h)
VITESSE   = 10.0     # km/h
SEUIL_H   = 8.0      # heures avant déclenchement des heures sup.


def cout_vehicule(distance_km: float) -> dict:
    """Coût d'un seul véhicule parcourant distance_km km."""
    duree_h = distance_km / VITESSE

    if duree_h <= SEUIL_H:
        cout_temps = duree_h * COUT_H
        sup_h = 0.0
    else:
        cout_temps = SEUIL_H * COUT_H + (duree_h - SEUIL_H) * COUT_H_SUP
        sup_h = duree_h - SEUIL_H

    cout_km = distance_km * COUT_KM
    total = COUT_FIXE + cout_km + cout_temps

    return {
        "fixe": COUT_FIXE,
        "km": cout_km,
        "temps": cout_temps,
        "total": total,
        "duree_h": duree_h,
        "sup_h": sup_h,
        "distance_km": distance_km,
    }


def cout_flotte(distance_totale_km: float, n_vehicules: int) -> dict:
    """Coût de la flotte en répartissant la distance équitablement."""
    dist_par_vehicule = distance_totale_km / n_vehicules
    cv = cout_vehicule(dist_par_vehicule)
    return {
        "n_vehicules": n_vehicules,
        "dist_par_vehicule_km": dist_par_vehicule,
        "duree_par_vehicule_h": cv["duree_h"],
        "sup_par_vehicule_h": cv["sup_h"],
        "cout_par_vehicule": cv["total"],
        "cout_total_flotte": cv["total"] * n_vehicules,
    }


def rapport_cout(flotte: dict, nom_district: str = "") -> str:
    """Résumé textuel du coût d'opération."""
    f = flotte
    sup = f" (dont {f['sup_par_vehicule_h']:.2f} h sup.)" if f["sup_par_vehicule_h"] > 0 else ""
    return (
        f"=== Coût – {nom_district} ===\n"
        f"  Véhicules            : {f['n_vehicules']}\n"
        f"  Distance/véhicule    : {f['dist_par_vehicule_km']:.2f} km\n"
        f"  Durée/véhicule       : {f['duree_par_vehicule_h']:.2f} h{sup}\n"
        f"  Coût/véhicule        : {f['cout_par_vehicule']:.2f} $\n"
        f"  Coût total flotte    : {f['cout_total_flotte']:.2f} $"
    )
