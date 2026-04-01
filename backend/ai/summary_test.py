"""Summary module using Gemini API."""
import os
import json
from typing import Any, Dict, List, Optional


def summarize(transcript_text: str) -> Dict[str, Any]:
    """Summarize transcript using Gemini API.

    Returns dict with:
    - summary: string summary under 200 words
    - key_points: list of key decisions
    - action_items: list of action items
    - keywords: list of keywords
    """
    if not transcript_text or not transcript_text.strip():
        return {
            "summary": "Chua the tao tom tat.",
            "key_points": [],
            "action_items": [],
            "keywords": [],
        }

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini_api_key")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY")

    import requests

    schema_hint = (
        "Return JSON with schema: {"
        '"summary": string (under 200 words), '
        '"key_points": [string], '
        '"action_items": [{"task": string, "assignee": string, "deadline": string, "status": string}], '
        '"keywords": [string]'
        "}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You are an AI assistant. Summarize the meeting transcript in under 200 words, "
                            "list key decisions, action items, and keywords. Return only JSON matching the schema.\n"
                            f"{schema_hint}\n\nTranscript:\n{transcript_text}"
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        },
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    resp = requests.post(url, json=payload, timeout=60)

    if resp.status_code != 200:
        raise RuntimeError(f"Gemini summary failed: {resp.status_code} {resp.text}")

    data = resp.json()

    default_result = {
        "summary": "Chua the tao tom tat tu dong.",
        "key_points": [],
        "action_items": [],
        "keywords": [],
    }

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        parsed = json.loads(text)
        return {
            "summary": parsed.get("summary") or default_result["summary"],
            "key_points": parsed.get("key_points") or [],
            "action_items": parsed.get("action_items") or [],
            "keywords": parsed.get("keywords") or [],
        }
    except Exception:
        # Fallback: extract first few sentences as summary
        parts = [p.strip() for p in transcript_text.split(".") if p.strip()]
        fallback_summary = ". ".join(parts[:3])
        return {
            "summary": fallback_summary + "." if fallback_summary else default_result["summary"],
            "key_points": [],
            "action_items": [],
            "keywords": [],
        }
