from django.core.cache import cache
from django.db.models import OuterRef, Subquery
from fuel.models import FuelStation, FuelPrice

STATIONS_CACHE_KEY = "all_geocoded_stations"
STATIONS_CACHE_TTL = 60 * 60 * 24  # 24 hours


def fetch_geocoded_stations_with_cheapest_price():
    """
    Returns a list of dicts - one per geocoded FuelStation - where 'price'
    is the LOWEST retail_price among that station's current (is_current=True)
    FuelPrice rows (across all racks).

    This is the single source of truth for "station price" used everywhere
    in the app. No other code should query FuelPrice directly.
    """
    cheapest_current_price = FuelPrice.objects.filter(
        station=OuterRef("pk"), is_current=True
    ).order_by("retail_price").values("retail_price")[:1]

    stations = FuelStation.objects.filter(
        latitude__isnull=False, longitude__isnull=False
    ).annotate(current_price=Subquery(cheapest_current_price))

    return [
        {
            "station_id": s.id,
            "station_name": s.truckstop_name,
            "city": s.city,
            "state": s.state,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "price": float(s.current_price),
        }
        for s in stations
        if s.current_price is not None
    ]


def get_all_geocoded_stations():
    """
    Returns the cached list of geocoded stations with cheapest current price.
    Falls back to a fresh DB fetch (and re-caches) if the cache is empty/cold.
    """
    data = cache.get(STATIONS_CACHE_KEY)
    if data is None:
        data = fetch_geocoded_stations_with_cheapest_price()
        cache.set(STATIONS_CACHE_KEY, data, timeout=STATIONS_CACHE_TTL)
    return data


def warm_station_cache():
    """
    Force-refreshes the station cache from the DB. Call this after data
    loads/price updates, or via the warm_station_cache management command.
    """
    data = fetch_geocoded_stations_with_cheapest_price()
    cache.set(STATIONS_CACHE_KEY, data, timeout=STATIONS_CACHE_TTL)
    return len(data)