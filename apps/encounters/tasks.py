"""
Celery pipeline for processing an Encounter end-to-end.

Chain:  PENDING → [transcribe] → TRANSCRIBED
                → [redact PII] → REDACTED
                → [SOAP gen]   → COMPLETED
                                (FAILED on any unrecoverable error)

Each step checks the current status before running so that retries are idempotent.
"""

import logging

from celery import shared_task

from .models import Encounter, QualityMetric, SOAPNote, Transcript
from .services.redaction import redact_pii
from .services.soap import generate_soap_note
from .services.transcription import transcribe_audio

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def process_encounter(self, encounter_id: str):
    """
    Main Celery task — runs the full transcription → redaction → SOAP pipeline.
    Called immediately after an Encounter is created by the upload API view.
    """
    try:
        encounter = Encounter.objects.get(id=encounter_id)
    except Encounter.DoesNotExist:
        logger.error(f"[{encounter_id}] Encounter not found — task aborted.")
        return

    # Accumulate quality metrics across steps
    _metrics: dict = {}

    try:
        # ── Step 1: Transcription ─────────────────────────────────────────────
        if encounter.status == Encounter.Status.PENDING:
            logger.info(f"[{encounter_id}] Starting transcription…")
            result = transcribe_audio(encounter)
            _metrics["transcript_confidence"] = result["confidence"]
            _metrics["transcript_word_count"] = result["word_count"]
            Transcript.objects.get_or_create(
                encounter=encounter,
                defaults={"raw_text": result["text"]},
            )
            encounter.status = Encounter.Status.TRANSCRIBED
            encounter.save(update_fields=["status", "updated_at"])
            logger.info(f"[{encounter_id}] Transcription complete. "
                        f"Confidence: {result['confidence']}, Words: {result['word_count']}")

        # ── Step 2: PII Redaction ─────────────────────────────────────────────
        if encounter.status == Encounter.Status.TRANSCRIBED:
            logger.info(f"[{encounter_id}] Redacting PII…")
            transcript = encounter.transcript
            redacted_text = redact_pii(transcript.raw_text)
            transcript.redacted_text = redacted_text
            transcript.save(update_fields=["redacted_text"])
            encounter.status = Encounter.Status.REDACTED
            encounter.save(update_fields=["status", "updated_at"])
            logger.info(f"[{encounter_id}] Redaction complete.")

        # ── Step 3: SOAP Generation ───────────────────────────────────────────
        if encounter.status == Encounter.Status.REDACTED:
            logger.info(f"[{encounter_id}] Generating SOAP note…")
            result = generate_soap_note(encounter.transcript.redacted_text)
            soap_data = result["soap"]
            _metrics["groq_prompt_tokens"] = result["prompt_tokens"]
            _metrics["groq_completion_tokens"] = result["completion_tokens"]
            _metrics["groq_model"] = result["model"]

            # Count how many sections have substantive content
            _not_doc = "Not documented in this consultation."
            _metrics["soap_sections_complete"] = sum(
                1 for v in soap_data.values() if v.strip() != _not_doc
            )

            SOAPNote.objects.get_or_create(
                encounter=encounter,
                defaults=soap_data,
            )
            encounter.status = Encounter.Status.COMPLETED
            encounter.save(update_fields=["status", "updated_at"])

            # ── Save quality metrics (admin-only) ─────────────────────────────
            QualityMetric.objects.update_or_create(
                encounter=encounter,
                defaults=_metrics,
            )
            logger.info(
                f"[{encounter_id}] Processing complete ✓ | "
                f"SOAP sections: {_metrics.get('soap_sections_complete')}/4 | "
                f"Tokens: {result['prompt_tokens']}→{result['completion_tokens']}"
            )

    except Exception as exc:
        logger.error(f"[{encounter_id}] Pipeline failed: {exc}", exc_info=True)
        # Persist error so the UI can display it
        Encounter.objects.filter(id=encounter_id).update(
            status=Encounter.Status.FAILED,
            error_message=str(exc),
        )
        raise self.retry(exc=exc)
