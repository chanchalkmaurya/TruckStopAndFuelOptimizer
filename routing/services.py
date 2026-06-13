import hashlib
import requests
import os
from django.core.cache import cache


ORS_API_KEY = os.getenv("ORS_API_KEY")
GEOCODE_CACHE_TTL = 60 * 60 * 24 * 30  # 30 days - addresses don't move
ROUTE_CACHE_TTL = 60 * 60 * 6           # 6 hours - route geometry/distance is stable

def _cache_key(prefix, *parts):
    raw = "|".join(str(p) for p in parts)
    digest = hashlib.md5(raw.encode()).hexdigest()
    return f"{prefix}:{digest}"

class OpenRouteServices:
    @staticmethod
    def geocode(full_address):
        """
            Returns (lat, lon) for a given address string.
            Cached indefinitely (long TTL) since addresses don't change location.
        """
        key = _cache_key("geocode", full_address.strip().lower())
        cached = cache.get(key)
        if cached:
            return cached
        
        url = "https://api.openrouteservice.org/geocode/search"
        params = {
            "api_key" : ORS_API_KEY,
            "text" : full_address,
            "size" : 1
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        features = response.json().get("features")
        if not features:
            raise ValueError(f"Could not geocode address: {full_address}")

        lon, lat = features[0]["geometry"]["coordinates"]
        result =[lat, lon]
        cache.set(key, result, timeout=GEOCODE_CACHE_TTL)
        return result
        

    @staticmethod
    def get_route(start, end):
        """
            Returns (geometry: list[[lon, lat]], total_distance_miles: float)
            Cached by rounded coordinate pairs (3 decimals ~110m precision)
            so near-identical requests reuse the same route.
        """
        print("get route called")
        key = _cache_key(
            "route",
            round(start[1], 3), round(start[1], 3),
            round(end[0], 3), round(end[1], 3),
        )
        cached = cache.get(key)
        if cached:
            return cached
        
        url = "https://api.openrouteservice.org/v2/directions/driving-car"
        params = {
            "api_key": ORS_API_KEY,
            "start": f"{start[1]},{start[0]}",  # lon,lat
            "end": f"{end[1]},{end[0]}",        # lon,lat
        }
        headers = {
            "Accept": "application/geo+json; charset=utf-8",
        }

        response = requests.get(
            url=url,
            params=params,
            headers=headers,
            timeout=15,
        )
        print(response.status_code)
        data = response.json()
        # print(data)
        feature = data["features"][0]
        geometry = feature["geometry"]["coordinates"] # list of [longitude, latitude]
        distance_meters = feature["properties"]["summary"]["distance"]
        distance_miles = distance_meters * 0.000621371
        result = (geometry, distance_miles)
        print(f"get route returned {result}")
        cache.set(key, result, timeout=ROUTE_CACHE_TTL)
        return result
        

