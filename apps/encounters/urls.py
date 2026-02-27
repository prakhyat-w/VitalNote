from django.urls import path

from .views import DashboardView, EncounterDetailView, UploadView

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("upload/", UploadView.as_view(), name="upload"),
    path("encounters/<uuid:pk>/", EncounterDetailView.as_view(), name="encounter-detail"),
]
