from django.core.management.base import BaseCommand
from django.db import transaction
from fuel.models import FuelStation
from routing.services import OpenRouteServices
import time


class Command(BaseCommand):
    help="generates latitude and longitude for fuel stations"
    
    def handle(self, *args, **kwargs):
        """One Time Script to generate lat, long for empty sets"""
        stations = FuelStation.objects.filter(
            id=2  
        )
        
        stations_to_update = []
        updated_stations = 0
        for station in stations:
            full_address = (
                f"{station.address}, "
                f"{station.city}, "
                f"{station.state}"
            )
            lng, lat = OpenRouteServices.geocode(full_address=full_address)
            if lat == -1:
                continue
            station.latitude = lat
            station.longitude = lng
            stations_to_update.append(station)
            updated_stations += 1
            
            if updated_stations % 10 == 0:
                FuelStation.objects.bulk_update(stations_to_update, ['latitude', 'longitude'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Latitude and Longitude updated for First {updated_stations} Fuel Stations."
                    )
                )
                stations_to_update.clear()
        #update in bulks instead of individuals
        FuelStation.objects.bulk_update(stations_to_update, ['latitude', 'longitude'])
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Latitude and Longitude updated for {updated_stations} Fuel Stations."
            )
        )
            
                
        
        