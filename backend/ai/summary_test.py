"""Summary module using Gemini API."""
import os
import json
import re
import uuid
from typing import Any, Dict, List, Optional


def _extract_json_object(raw_text: str) -> Dict[str, Any]:
    if not raw_text:
        return {}

    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    return {}


def _normalize_decisions(decisions: Any) -> List[str]:
    if not isinstance(decisions, list):
        return []

    out: List[str] = []
    seen = set()
    for item in decisions:
        text = str(item or "").strip()
        if len(text) < 8 or "?" in text:
            continue

        lowered = text.lower()
        if lowered.startswith(("co the", "có thể", "de xuat", "đề xuất", "goi y", "gợi ý")):
            continue

        key = re.sub(r"\s+", " ", lowered)
        if key in seen:
            continue
        seen.add(key)
        out.append(text)

    return out[:8]


def _normalize_action_items(action_items: Any) -> List[Dict[str, str]]:
    if not isinstance(action_items, list):
        return []

    out: List[Dict[str, str]] = []
    seen = set()
    for item in action_items:
        if isinstance(item, str):
            task = item.strip()
            assignee = ""
            deadline = ""
            status = "pending"
        elif isinstance(item, dict):
            task = str(item.get("task") or "").strip()
            assignee = str(item.get("assignee") or "").strip()
            deadline = str(item.get("deadline") or "").strip()
            status = str(item.get("status") or "pending").strip().lower()
        else:
            continue

        if len(task) < 6:
            continue

        key = re.sub(r"\s+", " ", task.lower())
        if key in seen:
            continue
        seen.add(key)

        if status not in {"pending", "in_progress", "completed"}:
            status = "pending"

        out.append(
            {
                "id": str(uuid.uuid4()),
                "task": task,
                "assignee": assignee,
                "deadline": deadline,
                "status": status,
            }
        )

    return out[:12]


def _limit_summary_words(text: str, max_words: int = 200) -> str:
    words = (text or "").strip().split()
    if not words:
        return ""
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words])


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

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "Ban la tro ly tong hop cuoc hop toi uu cho Gemini Flash Lite.\n"
                            "Hay tra ve DUY NHAT JSON gom 4 truong: summary, key_points, action_items, keywords.\n"
                            "Rang buoc bat buoc:\n"
                            "- Toan bo output phai bang tieng Viet de hieu.\n"
                            "- summary <= 180 tu, ngan gon, dung trong tam.\n"
                            "- key_points: chi la cac quyet dinh da duoc chot, khong ghi de xuat/cau hoi.\n"
                            "- action_items: ghi viec cu the can lam; neu khong ro assignee/deadline thi de rong.\n"
                            "- status trong action_items chi duoc: pending, in_progress, completed.\n"
                            "- keywords: 5-12 tu khoa quan trong.\n"
                            "Khong markdown. Khong them giai thich.\n\n"
                            f"Transcript:\n{transcript_text}"
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0,
            "topP": 0.9,
            "maxOutputTokens": 2048,
        },
    }

    model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
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
        parsed = _extract_json_object(text)
        normalized_points = _normalize_decisions(parsed.get("key_points"))
        normalized_actions = _normalize_action_items(parsed.get("action_items"))
        keywords = parsed.get("keywords") if isinstance(parsed.get("keywords"), list) else []
        return {
            "summary": _limit_summary_words(parsed.get("summary") or default_result["summary"]),
            "key_points": normalized_points,
            "action_items": normalized_actions,
            "keywords": [str(k).strip() for k in keywords if str(k).strip()][:12],
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
