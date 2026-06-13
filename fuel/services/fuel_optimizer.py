import math
import hashlib
from django.core.cache import cache
from .station_cache import get_all_geocoded_stations

MAX_RANGE_MILES = 500
MPG = 10
OFF_ROUTE_THRESHOLD_MILES = 5
ROUTE_POINT_SAMPLE_STEP = 5  # use every Nth route point for nearest-point search

CANDIDATES_CACHE_TTL = 60 * 60 * 6  # 6 hours


def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8  # miles
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def build_route_points(geometry):
    """geometry: list of [lon, lat]. Returns list of (lat, lon, cumulative_dist_miles)."""
    points = []
    cum = 0.0
    prev = None
    for lon, lat in geometry:
        if prev is not None:
            cum += haversine(prev[0], prev[1], lat, lon)
        points.append((lat, lon, cum))
        prev = (lat, lon)
    return points


def _geometry_cache_key(geometry):
    sample = geometry[::max(1, len(geometry) // 50)]
    raw = "|".join(f"{lon:.4f},{lat:.4f}" for lon, lat in sample)
    digest = hashlib.md5(raw.encode()).hexdigest()
    return f"candidates:{digest}"


def get_candidate_stations(route_points, geometry):
    """
    Returns sorted list of dicts (station info + price + distance_into_route)
    for stations within OFF_ROUTE_THRESHOLD_MILES of the route.

    Reads station/price data from get_all_geocoded_stations(), which already
    guarantees each station's 'price' is its cheapest current rack price.
    """
    cache_key = _geometry_cache_key(geometry)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    all_stations = get_all_geocoded_stations()

    lats = [p[0] for p in route_points]
    lons = [p[1] for p in route_points]
    margin = 0.5  # ~35 miles padding

    lat_min, lat_max = min(lats) - margin, max(lats) + margin
    lon_min, lon_max = min(lons) - margin, max(lons) + margin

    bbox_stations = [
        s for s in all_stations
        if lat_min <= s["latitude"] <= lat_max and lon_min <= s["longitude"] <= lon_max
    ]

    sampled_points = route_points[::ROUTE_POINT_SAMPLE_STEP] or route_points

    candidates = []
    for s in bbox_stations:
        best_point = min(
            sampled_points,
            key=lambda p: haversine(p[0], p[1], s["latitude"], s["longitude"]),
        )
        offset = haversine(best_point[0], best_point[1], s["latitude"], s["longitude"])
        if offset <= OFF_ROUTE_THRESHOLD_MILES:
            candidates.append({
                **s,
                "distance_into_route": best_point[2],
            })

    candidates.sort(key=lambda c: c["distance_into_route"])
    cache.set(cache_key, candidates, timeout=CANDIDATES_CACHE_TTL)
    return candidates


def optimize_fuel_stops(total_distance, candidates):
    """
    Greedy: at each point, refuel at the CHEAPEST reachable station
    (cheapest = lowest 'price', which already reflects each station's
    cheapest current rack price), refilling to full.
    """
    stops = []
    current_pos = 0.0
    remaining_range = MAX_RANGE_MILES

    while current_pos < total_distance:
        if total_distance - current_pos <= remaining_range:
            break  # can finish on current fuel

        reachable = [
            c for c in candidates
            if current_pos < c["distance_into_route"] <= current_pos + remaining_range
        ]
        if not reachable:
            raise ValueError(
                "No reachable fuel station within range of the vehicle's "
                "maximum range — route is infeasible."
            )

        best = min(reachable, key=lambda c: (c["price"], -c["distance_into_route"]))

        gallons_purchased = MAX_RANGE_MILES / MPG
        cost = gallons_purchased * best["price"]

        stops.append({
            "station_name": best["station_name"],
            "city": best["city"],
            "state": best["state"],
            "latitude": best["latitude"],
            "longitude": best["longitude"],
            "price": best["price"],
            "distance_into_route_miles": round(best["distance_into_route"], 1),
            "gallons_purchased": round(gallons_purchased, 2),
            "cost": round(cost, 2),
        })

        current_pos = best["distance_into_route"]
        remaining_range = MAX_RANGE_MILES

    return stops


def finalize_costs(stops, total_distance, candidates):
    """
    Adjusts the last leg's gallons/cost to reflect only the fuel needed
    to reach the end, and computes total cost.
    Handles the zero-stop case using the cheapest nearby candidate's price.
    """
    if stops:
        last_pos = stops[-1]["distance_into_route_miles"]
        remaining_distance = total_distance - last_pos
        remaining_gallons = remaining_distance / MPG
        stops[-1]["gallons_purchased"] = round(remaining_gallons, 2)
        stops[-1]["cost"] = round(remaining_gallons * stops[-1]["price"], 2)
        total_cost = round(sum(s["cost"] for s in stops), 2)
    else:
        price = min((c["price"] for c in candidates), default=0.0)
        total_cost = round((total_distance / MPG) * price, 2)

    return stops, total_cost