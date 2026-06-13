from rest_framework import serializers


class RouteRequestSerializer(serializers.Serializer):
    start = serializers.CharField(help_text="Address string")
    end = serializers.CharField(help_text="Address string")

    def validate(self, attrs):
        return attrs


class FuelStopSerializer(serializers.Serializer):
    station_name = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    price = serializers.FloatField()
    distance_into_route_miles = serializers.FloatField()
    gallons_purchased = serializers.FloatField()
    cost = serializers.FloatField()


class RouteResponseSerializer(serializers.Serializer):
    total_distance_miles = serializers.FloatField()
    total_fuel_cost = serializers.FloatField()
    route_geometry = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField())
    )
    fuel_stops = FuelStopSerializer(many=True)