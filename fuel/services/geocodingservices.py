from fuel.models import FuelStation, FuelPrice
from routing.services import OpenRouteServices

class GeoCodingService:
    @staticmethod
    def geocode_stations(station):
        full_address = (
            f"{station.address}, "
            f"{station.city}, "
            f"{station.state}"
        )
        lng, lat = OpenRouteServices.geocode(full_address=full_address)
        
        FuelStation.objects.filter(
            pk=station.pk
        ).update(
            latitude=lat,
            longitude=lng
        )