from django.contrib import admin

from .models import Encounter, QualityMetric, SOAPNote, Transcript


class TranscriptInline(admin.StackedInline):
    model = Transcript
    readonly_fields = ["raw_text", "redacted_text", "created_at"]
    extra = 0


class SOAPNoteInline(admin.StackedInline):
    model = SOAPNote
    readonly_fields = ["subjective", "objective", "assessment", "plan", "created_at"]
    extra = 0


class QualityMetricInline(admin.StackedInline):
    model = QualityMetric
    readonly_fields = [
        "transcript_confidence", "transcript_word_count",
        "soap_sections_complete", "groq_prompt_tokens",
        "groq_completion_tokens", "groq_model", "created_at",
    ]
    extra = 0
    verbose_name = "Quality Metric (internal)"


@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "status", "original_filename", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["user__email", "original_filename"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [TranscriptInline, SOAPNoteInline, QualityMetricInline]


@admin.register(SOAPNote)
class SOAPNoteAdmin(admin.ModelAdmin):
    list_display = ["encounter", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(QualityMetric)
class QualityMetricAdmin(admin.ModelAdmin):
    list_display = [
        "encounter", "confidence_pct", "transcript_word_count",
        "soap_completeness_pct", "groq_prompt_tokens",
        "groq_completion_tokens", "groq_model", "created_at",
    ]
    readonly_fields = [
        "encounter", "transcript_confidence", "transcript_word_count",
        "soap_sections_complete", "groq_prompt_tokens",
        "groq_completion_tokens", "groq_model", "created_at",
    ]
    list_filter = ["groq_model", "created_at"]
    search_fields = ["encounter__user__email"]

    def confidence_pct(self, obj):
        return obj.confidence_pct
    confidence_pct.short_description = "Transcript Confidence"

    def soap_completeness_pct(self, obj):
        return obj.soap_completeness_pct
    soap_completeness_pct.short_description = "SOAP Completeness"

    def has_add_permission(self, request):
        return False  # metrics are system-generated only
