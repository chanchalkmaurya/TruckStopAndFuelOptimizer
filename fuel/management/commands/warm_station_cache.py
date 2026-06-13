from django.core.management.base import BaseCommand
from fuel.services.station_cache import warm_station_cache


class Command(BaseCommand):
    help = "Preloads all geocoded FuelStation records with their cheapest current price into cache"

    def handle(self, *args, **options):
        count = warm_station_cache()
        self.stdout.write(
            self.style.SUCCESS(f"Cached {count} geocoded stations with cheapest current prices.")
        )