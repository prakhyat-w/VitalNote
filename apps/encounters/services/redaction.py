"""
PII redaction service using Microsoft Presidio (runs entirely in-process).
No external API calls — completely free and private.

Detected entity types and their replacement tags:
  PERSON          → [PERSON]
  PHONE_NUMBER    → [PHONE]
  EMAIL_ADDRESS   → [EMAIL]
  LOCATION        → [LOCATION]
  DATE_TIME       → [DATE]
  US_SSN          → [SSN]
  AU_TFN          → [TFN]
  MEDICAL_LICENSE → [LICENSE]
  URL             → [URL]
"""

import logging
import threading

from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger(__name__)

# Heavy objects are lazy-loaded on first use so gunicorn workers boot fast.
_lock = threading.Lock()
_analyzer = None
_anonymizer = None

# Replacement tags for each entity type
_OPERATORS: dict[str, OperatorConfig] = {
    "PERSON": OperatorConfig("replace", {"new_value": "[PERSON]"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
    "LOCATION": OperatorConfig("replace", {"new_value": "[LOCATION]"}),
    "DATE_TIME": OperatorConfig("replace", {"new_value": "[DATE]"}),
    "US_SSN": OperatorConfig("replace", {"new_value": "[SSN]"}),
    "AU_TFN": OperatorConfig("replace", {"new_value": "[TFN]"}),
    "MEDICAL_LICENSE": OperatorConfig("replace", {"new_value": "[LICENSE]"}),
    "URL": OperatorConfig("replace", {"new_value": "[URL]"}),
    "IP_ADDRESS": OperatorConfig("replace", {"new_value": "[IP]"}),
}


def _get_engines():
    """Return (analyzer, anonymizer), initialising them on first call."""
    global _analyzer, _anonymizer
    if _analyzer is None:
        with _lock:
            if _analyzer is None:  # double-checked locking
                from presidio_analyzer import AnalyzerEngine
                from presidio_analyzer.nlp_engine import NlpEngineProvider
                from presidio_anonymizer import AnonymizerEngine

                logger.info("Initialising Presidio + spaCy (first use)…")
                nlp_engine = NlpEngineProvider(nlp_configuration={
                    "nlp_engine_name": "spacy",
                    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
                }).create_engine()
                _analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
                _anonymizer = AnonymizerEngine()
                logger.info("Presidio + spaCy ready.")
    return _analyzer, _anonymizer


def redact_pii(text: str) -> str:
    """
    Analyse text for PII and return a version with all detected entities
    replaced by their placeholder tags.
    """
    if not text:
        return text

    analyzer, anonymizer = _get_engines()
    results = analyzer.analyze(text=text, language="en")

    if not results:
        logger.debug("Presidio found no PII entities — returning original text.")
        return text

    logger.debug(f"Presidio detected {len(results)} PII entity/ies.")

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=_OPERATORS,
    )
    return anonymized.text
