# fuel/tasks.py

from fuel.models import FuelStation
from fuel.services import GeoCodingService

def geocode_station(station_id):

    station = FuelStation.objects.get(
        id=station_id
    )

    GeoCodingService.geocode_stations(
        station
    )