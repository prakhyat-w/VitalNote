from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import include, path
from django.views import View
from drf_spectacular.utils import OpenApiResponse, extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HomeView(View):
    """Public landing page. Authenticated users go straight to the dashboard."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, "home.html")


class HealthCheckView(APIView):
    """
    Simple health-check endpoint.
    Ping this with cron-job.org every 10 minutes to keep the Render dyno alive.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        responses={200: OpenApiResponse(description='Returns {"status": "ok"} when healthy.')},
        summary="Health check",
        tags=["health"],
    )
    def get(self, request):
        return Response({"status": "ok"})


urlpatterns = [
    # ── Admin ────────────────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── Health check (cron-job.org keep-alive) ───────────────────────────────
    path("health/", HealthCheckView.as_view(), name="health"),

    # ── Root → landing page (authenticated → dashboard) ─────────────────────
    path("", HomeView.as_view(), name="home"),

    # ── Auth (register / login / logout) ─────────────────────────────────────
    path("", include("apps.users.urls")),

    # ── Template views (dashboard / upload / result) ──────────────────────────
    path("", include("apps.encounters.urls")),

    # ── DRF API endpoints ─────────────────────────────────────────────────────
    path("api/", include("apps.encounters.api_urls")),

    # ── OpenAPI schema + Swagger UI ───────────────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
