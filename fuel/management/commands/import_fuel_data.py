from decimal import Decimal
from pathlib import Path

import pandas as pd

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from fuel.models import FuelStation, FuelPrice


class Command(BaseCommand):
    help = "Import fuel stations and maintain fuel price history"

    @transaction.atomic
    def handle(self, *args, **kwargs):

        csv_path = (
            Path(settings.BASE_DIR)
            / "data"
            / "fuel-prices-for-be-assessment.csv"
        )

        if not csv_path.exists():
            self.stdout.write(
                self.style.ERROR(
                    f"CSV not found: {csv_path}"
                )
            )
            return

        df = pd.read_csv(csv_path)

        stations_created = 0
        prices_created = 0
        prices_updated = 0
        prices_skipped = 0

        for _, row in df.iterrows():

            opis_truckstop_id = int(
                row["OPIS Truckstop ID"]
            )

            rack_id = int(
                row["Rack ID"]
            )

            new_price = Decimal(
                str(row["Retail Price"])
            )

            station, created = (
                FuelStation.objects.get_or_create(
                    opis_truckstop_id=opis_truckstop_id,
                    defaults={
                        "truckstop_name": row["Truckstop Name"],
                        "address": row["Address"],
                        "city": row["City"],
                        "state": row["State"]
                    }
                )
            )

            if created:
                stations_created += 1

            else:
                station.truckstop_name = row[
                    "Truckstop Name"
                ]

                station.address = row[
                    "Address"
                ]

                station.city = row[
                    "City"
                ]

                station.state = row[
                    "State"
                ]

                station.save(
                    update_fields=[
                        "truckstop_name",
                        "address",
                        "city",
                        "state"
                    ]
                )

            current_price = (
                FuelPrice.objects.filter(
                    station=station,
                    rack_id=rack_id,
                    is_current=True
                )
                .order_by("-effective_from")
                .first()
            )

            if current_price is None:

                FuelPrice.objects.create(
                    station=station,
                    rack_id=rack_id,
                    retail_price=new_price,
                    is_current=True
                )

                prices_created += 1
                continue

            if current_price.retail_price == new_price:

                prices_skipped += 1
                continue

            current_price.is_current = False

            current_price.effective_to = (
                timezone.now()
            )

            current_price.save(
                update_fields=[
                    "is_current",
                    "effective_to"
                ]
            )

            FuelPrice.objects.create(
                station=station,
                rack_id=rack_id,
                retail_price=new_price,
                is_current=True
            )

            prices_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                "\nImport Completed"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Stations Created: "
                f"{stations_created}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"New Prices: "
                f"{prices_created}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Price Changes: "
                f"{prices_updated}"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                f"Unchanged Prices: "
                f"{prices_skipped}"
            )
        )