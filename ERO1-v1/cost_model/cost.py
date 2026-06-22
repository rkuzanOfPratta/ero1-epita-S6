def compute_cost(distance_km: float, n_vehicles: int) -> float:
    time_hours = distance_km / (10.0 * n_vehicles)
    fixed = 500.0 * n_vehicles
    km_cost = 1.1 * distance_km
    if time_hours <= 8.0:
        hourly = 1.1 * time_hours * n_vehicles
    else:
        hourly = (1.1 * 8.0 + 1.3 * (time_hours - 8.0)) * n_vehicles
    return fixed + km_cost + hourly


def optimal_vehicles(distance_km: float, max_n: int = 20) -> tuple:
    best_n = 1
    best_cost = compute_cost(distance_km, 1)
    for n in range(2, max_n + 1):
        cost = compute_cost(distance_km, n)
        if cost < best_cost:
            best_cost = cost
            best_n = n
    return best_n, best_cost


def cost_by_vehicles(distance_km: float, max_n: int = 20) -> dict:
    return {n: compute_cost(distance_km, n) for n in range(1, max_n + 1)}
