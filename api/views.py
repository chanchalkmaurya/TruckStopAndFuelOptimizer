import hashlib

from django.shortcuts import render
from django.core.cache import cache

from rest_framework import status 
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import RouteRequestSerializer, RouteResponseSerializer
from fuel.services.fuel_optimizer import build_route_points, get_candidate_stations, optimize_fuel_stops
from routing.services import OpenRouteServices

FULL_RESPONSE_CACHE_TTL = 60 * 60  # 1 hour

def _full_response_cache_key(start_latlon, end_latlon):
    raw = (
        f"{round(start_latlon[0], 3)},{round(start_latlon[1], 3)}|"
        f"{round(end_latlon[0], 3)},{round(end_latlon[1], 3)}"
    )
    digest = hashlib.md5(raw.encode()).hexdigest()
    return f"route_response:{digest}"


class RouteView(APIView):
    def post(self, request):
        """
            POST /api/route/
            {
                "start": "Chicago, IL",
                "end": "Dallas, TX",
            }
        """
        req = RouteRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        
        #2 geocode calls to get [longitude,latitude]
        try:
            start = OpenRouteServices.geocode(req.validated_data["start"])
            end = OpenRouteServices.geocode(req.validated_data["end"])
            print(start, end)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Full-response cache: identical start/end pairs skip all computation
        resp_cache_key = _full_response_cache_key(start, end)
        cached_payload = cache.get(resp_cache_key)
        if cached_payload is not None:
            return Response(cached_payload)
        
        try:
            geometry, total_distance = OpenRouteServices.get_route(start, end)
        except Exception as e:
            return Response(
                {"error": "Failed to fetch the route from routing provider."},
                status=status.HTTP_502_BAD_GATEWAY
            )
        
        route_points = build_route_points(geometry)
        print(f"--------------------- route_points ------------------------------------\n{route_points}")
        candidates = get_candidate_stations(route_points, geometry)

        try:
            stops = optimize_fuel_stops(total_distance, candidates)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        last_pos = stops[-1]["distance_into_route_miles"] if stops else 0
        if stops:
            stops[-1]["gallons_purchased"] = round((total_distance - last_pos) / 10, 2)
            stops[-1]["cost"] = round(stops[-1]["gallons_purchased"] * stops[-1]["price"], 2)
            total_cost = sum(s["cost"] for s in stops)
        else:
            # whole trip on one tank — price from nearest candidate to start
            price = candidates[0]["price"] if candidates else 0
            total_cost = round((total_distance / 10) * price, 2)

        payload = {
            "total_distance_miles": round(total_distance, 1),
            "total_fuel_cost": round(total_cost, 2),
            "route_geometry": [[lat, lon] for lon, lat in geometry],
            "fuel_stops": stops,
        }
        serialized = RouteResponseSerializer(payload).data
        cache.set(resp_cache_key, serialized, timeout=FULL_RESPONSE_CACHE_TTL)

        return Response(serialized)