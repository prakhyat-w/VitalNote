"""
AssemblyAI transcription service.
Supports both local file paths (development) and Cloudflare R2 pre-signed URLs (production).
Speaker labels are mapped: first speaker → DOCTOR, second → PATIENT.
"""

import logging

import assemblyai as aai
import boto3
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_presigned_url(key: str, expiry_seconds: int = 3600) -> str:
    """Generate a temporary pre-signed URL for an R2 object."""
    client = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name="auto",
    )
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
        ExpiresIn=expiry_seconds,
    )


def transcribe_audio(encounter) -> dict:
    """
    Transcribe the encounter's audio file using AssemblyAI.

    Returns a dict:
        {
            "text":       str,    # DOCTOR:/PATIENT: labelled transcript
            "confidence": float,  # average word-level confidence (0.0–1.0)
            "word_count": int,    # total word count
        }
    """
    aai.settings.api_key = settings.ASSEMBLYAI_API_KEY

    # Resolve audio source — pre-signed URL for R2, local path otherwise
    if settings.USE_R2:
        audio_source = _get_presigned_url(encounter.audio_file.name)
        logger.info(f"[{encounter.id}] Using R2 pre-signed URL for transcription.")
    else:
        audio_source = encounter.audio_file.path
        logger.info(f"[{encounter.id}] Using local file path for transcription.")

    config = aai.TranscriptionConfig(
        speaker_labels=True,
        speakers_expected=2,
    )

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_source, config=config)

    if transcript.status == aai.TranscriptStatus.error:
        raise RuntimeError(f"AssemblyAI transcription failed: {transcript.error}")

    # ── Compute word-level confidence metrics ─────────────────────────────────
    words = transcript.words or []
    if words:
        avg_confidence = sum(w.confidence for w in words) / len(words)
        word_count = len(words)
    else:
        avg_confidence = None
        word_count = 0

    # ── Map speaker letters (A, B, …) to DOCTOR / PATIENT ───────────────────
    speaker_map: dict[str, str] = {}
    lines: list[str] = []

    if transcript.utterances:
        for utterance in transcript.utterances:
            if utterance.speaker not in speaker_map:
                label = "DOCTOR" if not speaker_map else "PATIENT"
                speaker_map[utterance.speaker] = label
            lines.append(f"{speaker_map[utterance.speaker]}: {utterance.text}")
        text = "\n".join(lines)
    else:
        # Fallback: plain transcript if diarization produced no utterances
        text = transcript.text or ""

    return {
        "text": text,
        "confidence": avg_confidence,
        "word_count": word_count,
    }
