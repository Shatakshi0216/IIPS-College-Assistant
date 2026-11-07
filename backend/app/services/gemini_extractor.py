"""
Gemini Document Understanding & Metadata Extraction Service
Uses Google Gemini to analyze uploaded PDF notices and extract structured JSON metadata
(deadlines, eligible branches, minimum CGPA, required actions).
"""
import json
import logging
import urllib.request
import ssl
import warnings
from typing import Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

_ssl_ctx = ssl.create_default_context()

GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-flash-latest",
]


def _call_gemini_extractor(prompt: str, api_key: str) -> str:
    """Direct REST call to Gemini, trying models in order."""
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode("utf-8")

    for model_name in GEMINI_MODELS:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={api_key}"
        )
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, context=_ssl_ctx, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8")
            logger.warning(f"Gemini {model_name} HTTP {e.code}: {err[:100]}")
            if e.code == 404:
                continue
            raise
        except Exception as e:
            logger.warning(f"Gemini {model_name} error: {e}")
            raise

    raise RuntimeError(f"All Gemini models unavailable: {GEMINI_MODELS}")

# System instruction defining exact JSON schema output
EXTRACTION_PROMPT = """
You are an intelligent administrative AI for International Institute of Professional Studies, DAVV (IIPS DAVV).
You are given the extracted text of an official college notice or circular.
Analyze the document carefully and return ONLY a valid JSON object with the following fields:

{
  "title": "A concise, clear title for this notice",
  "summary": "A 2 to 3 sentence concise summary explaining what this notice is about",
  "action_required": "What the student needs to do (e.g. submit form, register online, pay fee), or null if purely informational",
  "deadline": "The final date or deadline mentioned in YYYY-MM-DD format if identifiable, or a human readable date string like 'October 25, 2026', or null",
  "eligible_branches": ["List of eligible branches/courses like MCA, M.Tech, MBA, BCA, B.Com, IT, CSE, or ['ALL'] if open to all"],
  "eligible_years": [List of eligible years as integers, e.g. [3, 4], or [1, 2, 3, 4, 5] if for all students],
  "min_cgpa": 0.0, // Minimum CGPA required as a float (e.g. 7.5), or 0.0 if no CGPA requirement
  "contact_info": "Contact email, phone, or faculty name mentioned, or null",
  "is_urgent": true/false // true if the deadline is within 3 days or marked urgent/mandatory
}

DO NOT include markdown code fences or backticks (e.g. do NOT include ```json). Return ONLY pure JSON text.
"""


def extract_notice_metadata(pdf_text: str) -> Dict[str, Any]:
    """
    Sends notice text to Google Gemini and parses the structured JSON metadata.
    If GEMINI_API_KEY is not configured, provides a sensible fallback parser.
    """
    api_key = settings.GEMINI_API_KEY

    # Check if a real key is present
    if not api_key or "your-gemini-api-key" in api_key.lower():
        logger.warning("GEMINI_API_KEY is not configured. Using fallback metadata extraction.")
        return _fallback_metadata_extractor(pdf_text)

    try:
        full_prompt = f"{EXTRACTION_PROMPT}\n\nDOCUMENT TEXT:\n{pdf_text[:12000]}"
        response_text = _call_gemini_extractor(full_prompt, api_key)

        # Strip accidental code blocks if model added them
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        metadata = json.loads(response_text)
        return metadata

    except Exception as e:
        logger.error(f"Error calling Gemini for metadata extraction: {e}")
        return _fallback_metadata_extractor(pdf_text)


def _fallback_metadata_extractor(text: str) -> Dict[str, Any]:
    """
    Rule-based heuristic fallback if Gemini API is unreachable or key is absent.
    Ensures local testing never crashes.
    """
    first_lines = [line.strip() for line in text.split("\n") if line.strip()][:3]
    guessed_title = first_lines[0] if first_lines else "College Official Notice"

    branches = []
    for b in ["CSE", "IT", "ECE", "ME", "CE", "EE"]:
        if b in text.upper():
            branches.append(b)
    if not branches:
        branches = ["ALL"]

    years = []
    for y, label in [(1, "1st"), (2, "2nd"), (3, "3rd"), (4, "4th")]:
        if label.lower() in text.lower() or f"year {y}" in text.lower():
            years.append(y)
    if not years:
        years = [1, 2, 3, 4]

    return {
        "title": guessed_title[:100],
        "summary": "Official college notice processed. Please review the full document for detailed instructions.",
        "action_required": "Please read the notice carefully and complete necessary steps before the deadline.",
        "deadline": None,
        "eligible_branches": branches,
        "eligible_years": years,
        "min_cgpa": 0.0,
        "contact_info": None,
        "is_urgent": "urgent" in text.lower() or "immediate" in text.lower()
    }
