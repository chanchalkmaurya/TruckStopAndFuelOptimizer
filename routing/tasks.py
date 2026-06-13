# fuel/tasks.py

from fuel.models import FuelStation
from fuel.services import (
    GeocodingService
)


def geocode_station(station_id):
    station = FuelStation.objects.get(
        id=station_id
    )
    GeocodingService.geocode_station(
        station
    )