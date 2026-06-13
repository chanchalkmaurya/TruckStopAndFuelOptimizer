from django.shortcuts import render
from django.views.generic import TemplateView

class RouteMapView(TemplateView):
    template_name = "routing/route_map.html"
