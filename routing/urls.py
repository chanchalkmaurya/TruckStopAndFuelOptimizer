from django.urls import path
from routing.views import RouteMapView

urlpatterns = [
    path('route_map/', RouteMapView.as_view(), name="route-map"),
]