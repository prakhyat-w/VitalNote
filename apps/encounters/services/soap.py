"""
SOAP note generation service using Groq API (Llama 3.3 70B — free tier).
The redacted transcript is sent to the LLM with a strict system prompt that
enforces a JSON SOAP structure, validated with Pydantic before saving.
"""

import json
import logging

from django.conf import settings
from groq import Groq
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# ── Pydantic schema ───────────────────────────────────────────────────────────


class SOAPData(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """
You are a medical scribe assistant. You will be given a doctor-patient consultation
transcript. Speaker labels are either DOCTOR or PATIENT.

Your task is to produce a structured SOAP note in valid JSON format.

Return ONLY a JSON object with this exact structure — no additional text:
{
  "subjective":  "<Patient's chief complaint, history of present illness, reported symptoms, relevant medical/social/family history>",
  "objective":   "<Physical examination findings, vital signs, and any test results or observations mentioned by the doctor>",
  "assessment":  "<Diagnosis or differential diagnoses, clinical reasoning>",
  "plan":        "<Treatment plan: medications, investigations ordered, lifestyle advice, follow-up instructions, referrals>"
}

Rules:
- Use formal clinical language.
- Be concise but clinically complete.
- Do NOT include any personally identifiable information (names, dates of birth, addresses, phone numbers, etc.).
- Speaker-label prefixes (DOCTOR:, PATIENT:) should not appear in the output.
- If a SOAP section cannot be determined from the transcript, write exactly: "Not documented in this consultation."
""".strip()


# ── Main function ─────────────────────────────────────────────────────────────


def generate_soap_note(redacted_transcript: str) -> dict:
    """
    Send the redacted transcript to Groq and return a validated SOAP dict
    with keys: subjective, objective, assessment, plan.
    """
    client = Groq(api_key=settings.GROQ_API_KEY)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Consultation transcript:\n\n{redacted_transcript}",
            },
        ],
        temperature=0.2,
        max_tokens=1500,
        response_format={"type": "json_object"},
    )

    raw_json = response.choices[0].message.content
    logger.debug(f"Groq raw response: {raw_json[:200]}...")

    try:
        data = json.loads(raw_json)
        soap = SOAPData(**data)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.error(f"SOAP validation failed: {exc}. Raw: {raw_json}")
        raise RuntimeError(f"SOAP generation produced invalid output: {exc}") from exc

    # Capture token usage for quality metrics
    usage = response.usage
    return {
        "soap": soap.model_dump(),
        "prompt_tokens": usage.prompt_tokens if usage else None,
        "completion_tokens": usage.completion_tokens if usage else None,
        "model": response.model or "llama-3.3-70b-versatile",
    }
