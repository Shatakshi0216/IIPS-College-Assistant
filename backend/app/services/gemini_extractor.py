"""
Gemini Document Understanding & Metadata Extraction Service
Uses Google Gemini to analyze uploaded PDF notices and extract structured JSON metadata
(deadlines, eligible branches, minimum CGPA, required actions).
"""
import json
import base64
import logging
import urllib.request
import ssl
import warnings
from typing import Dict, Any, Optional, List

from app.config import settings

logger = logging.getLogger(__name__)

_ssl_ctx = ssl.create_default_context()

GEMINI_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-3.5-flash",
    "gemini-2.5-pro",
]


def _call_gemini_extractor(prompt: str, api_key: str, pdf_bytes: Optional[bytes] = None) -> str:
    """Direct REST call to Gemini, trying models in order with optional multimodal PDF support."""
    parts: List[Dict[str, Any]] = [{"text": prompt}]

    if pdf_bytes and len(pdf_bytes) > 0 and len(pdf_bytes) < 18 * 1024 * 1024:
        try:
            b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
            parts.append({
                "inline_data": {
                    "mime_type": "application/pdf",
                    "data": b64_pdf
                }
            })
        except Exception as e:
            logger.warning(f"Error base64 encoding PDF for extractor: {e}")

    body = json.dumps({
        "contents": [{"parts": parts}]
    }).encode("utf-8")

    last_error = None
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
            with urllib.request.urlopen(req, context=_ssl_ctx, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="ignore")
            logger.warning(f"Gemini {model_name} HTTP {e.code}: {err[:200]}")
            last_error = e
            continue
        except Exception as e:
            if "CERTIFICATE_VERIFY_FAILED" in str(e):
                try:
                    with urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=25) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
                except Exception as inner_e:
                    logger.warning(f"Gemini {model_name} unverified SSL error: {inner_e}")
            logger.warning(f"Gemini {model_name} error: {e}")
            last_error = e
            continue

    raise RuntimeError(f"All Gemini models unavailable: {GEMINI_MODELS}. Last error: {last_error}")


# System instruction defining exact JSON schema output
EXTRACTION_PROMPT = """
You are an intelligent administrative AI for International Institute of Professional Studies, DAVV (IIPS DAVV).
You are given an official college notice, circular, holiday circular, cultural festival guideline (which may be in Hindi / Devanagari script), or examination timetable/schedule (table format).
Analyze the document carefully and return ONLY a valid JSON object with the following fields:

{
  "title": "A concise, clear title for this notice (translate to English if original is in Hindi)",
  "summary": "A specific 2 to 4 sentence summary that explains what this notice is about, key guidelines, rules, dates/deadlines, and actions required. If the document is in Hindi, provide the summary in clear English. If it is a table/schedule, list the main schedule dates.",
  "action_required": "What the student needs to do (e.g. follow guidelines, submit form, adhere to dress code), or null if purely informational",
  "deadline": "The date or deadline mentioned in YYYY-MM-DD or readable date string like 'October 25, 2026', or null",
  "eligible_branches": ["List of eligible programmes: MCA, M.Tech, M.Tech (IT), M.Tech (CS), MBA, BCA, B.Com, IT, CSE — or ['ALL'] if open to all students"],
  "eligible_years": [List of eligible years as integers [1, 2, 3, 4, 5], or [1, 2, 3, 4, 5] if open to all],
  "min_cgpa": 0.0,
  "contact_info": "Contact email, phone, or faculty name mentioned, or null",
  "is_urgent": true/false
}

Note: If this document is a general rule, circular, cultural guidelines (e.g. Ganesh Utsav), or college announcement, eligible_branches MUST be ["ALL"] and eligible_years MUST be [1, 2, 3, 4, 5].
DO NOT include markdown code fences or backticks (e.g. do NOT include ```json). Return ONLY pure JSON text.
"""


def extract_notice_metadata(pdf_text: str = "", pdf_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    """
    Sends notice text (and/or raw PDF bytes) to Google Gemini to extract structured JSON metadata.
    Handles Hindi Devanagari script, table layouts, and English seamlessly.
    """
    api_key = settings.GEMINI_API_KEY

    # Check if a real key is present
    if not api_key or "your-gemini-api-key" in api_key.lower():
        logger.warning("GEMINI_API_KEY is not configured. Using fallback metadata extraction.")
        return _fallback_metadata_extractor(pdf_text)

    try:
        text_context = f"\n\nDOCUMENT TEXT:\n{pdf_text[:12000]}" if pdf_text else ""
        full_prompt = f"{EXTRACTION_PROMPT}{text_context}"
        response_text = _call_gemini_extractor(full_prompt, api_key, pdf_bytes=pdf_bytes)

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
    Ensures local testing never crashes and doesn't misclassify words as branches.
    """
    import re

    first_lines = [line.strip() for line in text.split("\n") if line.strip()][:3]
    guessed_title = first_lines[0] if first_lines else "College Official Notice"

    # Whole-word regex matching for programmes
    # Never match substring 'IT' inside words like 'university', 'submit', 'credit', etc.
    programmes_patterns = [
        ("MCA", r"\bMCA\b"),
        ("M.TECH", r"\bM\.?TECH\b"),
        ("MBA", r"\bMBA\b"),
        ("BCA", r"\bBCA\b"),
        ("B.COM", r"\bB\.?COM\b"),
        ("CSE", r"\bCSE\b"),
        ("IT", r"(?:\bINFORMATION\s+TECHNOLOGY\b|\bBRANCH\s*:\s*IT\b|\bIT\s+BRANCH\b|\bM\.?TECH\s*\(?IT\)?|\bMCA\s*\(?IT\)?)"),
    ]

    branches = []
    for prog, pattern in programmes_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            branches.append(prog)

    # If no specific branch was explicitly targeted, it is for ALL branches
    if not branches or len(branches) >= 3:
        branches = ["ALL"]

    # Only match explicit academic year patterns (e.g. "1st year", "year 2"), NOT calendar dates like "1st Dec"
    years = []
    for y, label in [(1, "1st year"), (2, "2nd year"), (3, "3rd year"), (4, "4th year"), (5, "5th year")]:
        if label in text.lower() or f"year {y}" in text.lower() or f"year-{y}" in text.lower():
            years.append(y)
    if not years:
        years = [1, 2, 3, 4, 5]

    return {
        "title": guessed_title[:100],
        "summary": (
            " ".join(first_lines[:3]) if first_lines
            else f"Official IIPS DAVV notice: {guessed_title}. Please open the original PDF for complete details."
        ),
        "action_required": "Please read the notice carefully and complete necessary steps before the deadline.",
        "deadline": None,
        "eligible_branches": branches,
        "eligible_years": years,
        "min_cgpa": 0.0,
        "contact_info": None,
        "is_urgent": "urgent" in text.lower() or "immediate" in text.lower()
    }
