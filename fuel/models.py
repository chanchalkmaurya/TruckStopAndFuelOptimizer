# fuel/models.py

from django.db import models

# fuel/models.py

class FuelStation(models.Model):
    opis_truckstop_id = models.IntegerField()
    truckstop_name = models.CharField(
        max_length=255
    )
    address = models.CharField(
        max_length=500
    )
    city = models.CharField(
        max_length=100
    )
    state = models.CharField(
        max_length=10
    )
    latitude = models.FloatField(
        null=True,
        blank=True
    )
    longitude = models.FloatField(
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "fuel_stations"
        unique_together = (
            "opis_truckstop_id",
            "address"
        )
        indexes = [
            models.Index(fields=["latitude", "longitude"], name="idx_station_lat_lon"),
        ]

    def __str__(self):
        return (
            f"{self.truckstop_name}"
            f" ({self.city})"
        )
        

class FuelPrice(models.Model):
    station = models.ForeignKey(
        FuelStation,
        on_delete=models.CASCADE,
        related_name="prices"
    )
    rack_id = models.IntegerField()
    retail_price = models.DecimalField(
        max_digits=8,
        decimal_places=3
    )
    is_current = models.BooleanField(
        default=True
    )
    effective_from = models.DateTimeField(
        auto_now_add=True
    )
    effective_to = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        db_table = "fuel_prices"
        indexes = [
            models.Index(
                fields=["rack_id"]
            ),
            models.Index(
                fields=["is_current"]
            )
        ]