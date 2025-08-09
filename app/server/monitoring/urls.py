from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health_check, name="health_check"),
    path("telemetry/", views.receive_telemetry, name="receive_telemetry"),
]
