from django.urls import path

from .views import EncounterCreateAPIView, EncounterPDFAPIView, EncounterStatusAPIView

urlpatterns = [
    path("encounters/", EncounterCreateAPIView.as_view(), name="api-encounter-create"),
    path("encounters/<uuid:pk>/", EncounterStatusAPIView.as_view(), name="api-encounter-status"),
    path("encounters/<uuid:pk>/pdf/", EncounterPDFAPIView.as_view(), name="api-encounter-pdf"),
]
