import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import get_object_or_404, render
from django.views import View
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Encounter
from .serializers import EncounterCreateSerializer, EncounterSerializer
from .services.pdf import get_pdf_response
from .tasks import process_encounter


# ── Template Views (session-auth, rendered HTML) ──────────────────────────────


class DashboardView(LoginRequiredMixin, View):
    """User's encounter history with pagination."""

    def get(self, request):
        qs = Encounter.objects.filter(user=request.user).select_related(
            "transcript", "soap_note"
        )
        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(request.GET.get("page", 1))
        return render(request, "encounters/dashboard.html", {"page_obj": page_obj})


class UploadView(LoginRequiredMixin, View):
    """Upload form page."""

    def get(self, request):
        return render(request, "encounters/upload.html")


class EncounterDetailView(LoginRequiredMixin, View):
    """Result / polling page for a single encounter."""

    def get(self, request, pk):
        encounter = get_object_or_404(
            Encounter.objects.select_related("transcript", "soap_note"),
            pk=pk,
            user=request.user,
        )
        serializer = EncounterSerializer(encounter)
        encounter_json = json.dumps(dict(serializer.data), cls=DjangoJSONEncoder)
        return render(
            request,
            "encounters/result.html",
            {"encounter": encounter, "encounter_json": encounter_json},
        )


# ── API Views (DRF, session + JWT auth) ──────────────────────────────────────


class EncounterCreateAPIView(APIView):
    """POST /api/encounters/ — upload an audio file and start processing."""

    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=EncounterCreateSerializer,
        responses={201: OpenApiResponse(description="Encounter created, processing queued.")},
        summary="Upload audio and start AI processing pipeline",
    )
    def post(self, request):
        serializer = EncounterCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        audio_file = serializer.validated_data["audio_file"]
        encounter = Encounter.objects.create(
            user=request.user,
            audio_file=audio_file,
            original_filename=audio_file.name,
        )
        process_encounter.delay(str(encounter.id))
        return Response({"id": str(encounter.id)}, status=status.HTTP_201_CREATED)


class EncounterStatusAPIView(APIView):
    """GET /api/encounters/<id>/ — poll status and retrieve results."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: EncounterSerializer},
        summary="Poll encounter status and retrieve SOAP note when complete",
    )
    def get(self, request, pk):
        encounter = get_object_or_404(
            Encounter.objects.select_related("transcript", "soap_note"),
            pk=pk,
            user=request.user,
        )
        return Response(EncounterSerializer(encounter).data)


class EncounterPDFAPIView(APIView):
    """GET /api/encounters/<id>/pdf/ — download SOAP note as PDF."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiResponse(description="PDF file (application/pdf).")},
        summary="Download the SOAP note as a formatted PDF",
    )
    def get(self, request, pk):
        encounter = get_object_or_404(
            Encounter.objects.select_related("transcript", "soap_note"),
            pk=pk,
            user=request.user,
        )
        if encounter.status != Encounter.Status.COMPLETED:
            return Response(
                {"error": "SOAP note is not yet available."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return get_pdf_response(encounter)
