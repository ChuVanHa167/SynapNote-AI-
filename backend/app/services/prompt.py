import json
from typing import Any, Dict, List


def get_groq_transcription_prompt(unique_id: str) -> str:
    return (
        f"Ma yeu cau duy nhat: {unique_id}. "
        "Hay chep lai dung nguyen van noi dung nghe duoc bang tieng Viet. "
        "Khong tom tat. Khong dien giai. Khong them noi dung moi."
    )


def get_gemini_diarization_prompt(compact_chunks: List[Dict[str, Any]]) -> str:
    return (
        "TASK: Perform speaker diarization on meeting transcript chunks.\n"
        "Return EXACTLY one JSON object.\n\n"
        "OUTPUT SCHEMA (STRICT):\n"
        "{\n"
        "  \"speaker_turns\": [\n"
        "    {\"speaker\": \"Speaker N\", \"start\": number, \"end\": number, \"text\": string}\n"
        "  ]\n"
        "}\n\n"
        "CONSTRAINTS:\n"
        "- speaker must follow exact format: \"Speaker 1\", \"Speaker 2\", ...\n"
        "- start and end must be within chunk range and end > start.\n"
        "- text must preserve original meaning in Vietnamese. No summarization. No added information.\n"
        "- Do not hallucinate speaker changes. If uncertain, merge into fewer, longer turns.\n"
        "- Use context continuity to group utterances logically.\n\n"
        "VALIDATION RULES (HIGHEST PRIORITY):\n"
        "1. Output must be valid JSON.\n"
        "2. Only one top-level key: \"speaker_turns\".\n"
        "3. No additional fields.\n"
        "4. No markdown, no explanations, no extra text.\n"
        "5. If input is insufficient for diarization, return exactly: {\"speaker_turns\": []}\n\n"
        f"INPUT:\n{json.dumps(compact_chunks, ensure_ascii=False)}"
    )


def get_gemini_summary_prompt(transcript_for_summary: str) -> str:
    return (
        "TASK: Summarize meeting transcript and extract key outcomes.\n"
        "Return EXACTLY one JSON object.\n\n"
        "OUTPUT SCHEMA (STRICT):\n"
        "{\n"
        "  \"summary\": string,\n"
        "  \"decisions\": string[],\n"
        "  \"action_items\": [\n"
        "    {\"task\": string, \"assignee\": string, \"deadline\": string, \"status\": \"pending\" | \"in_progress\" | \"completed\"}\n"
        "  ]\n"
        "}\n\n"
        "CONSTRAINTS:\n"
        "- All output must be in Vietnamese. No English sentences.\n"
        "- summary: concise, <= 180 words, captures overall meeting.\n"
        "- decisions: include ONLY confirmed decisions (agreed/approved).\n"
        "  Exclude proposals, open questions, or speculation. If none, return [].\n"
        "- action_items:\n"
        "  * Each item must include: task, assignee, deadline, status.\n"
        "  * If assignee or deadline is missing, use empty string \"\".\n"
        "  * status must be exactly one of: pending, in_progress, completed.\n"
        "  * Do NOT infer unknown facts; leave fields empty if unclear.\n\n"
        "VALIDATION RULES (HIGHEST PRIORITY):\n"
        "1. Output must be valid JSON.\n"
        "2. Exactly 3 top-level keys: summary, decisions, action_items.\n"
        "3. No extra fields. No missing fields.\n"
        "4. No markdown. No explanations. No text outside JSON.\n"
        "5. If information is insufficient, return empty structures but keep schema.\n\n"
        f"INPUT:\n{transcript_for_summary}"
    )


def get_gemini_transcript_fix_prompt(chunk: str, prev_context: str = "", next_context: str = "") -> str:
    return (
        "TASK: Normalize ASR transcript into fluent Vietnamese.\n\n"
        "CONSTRAINTS:\n"
        "- Preserve meaning exactly. No summarization. No added or omitted information.\n"
        "- Fix ASR errors: malformed phrases, grammar issues, incoherent or contextually incorrect segments.\n"
        "- Limited context-based inference allowed to restore natural phrasing.\n"
        "- Do NOT change facts, numbers, decisions, or proper nouns.\n"
        "- Non-Vietnamese text must be rewritten in Vietnamese (preserve proper nouns and technical terms).\n"
        "- Preserve any existing speaker labels or timestamps exactly as in input.\n\n"
        "OUTPUT RULES:\n"
        "- Return ONLY the corrected text.\n"
        "- No explanations. No context repetition. No markdown.\n\n"
        f"CONTEXT BEFORE:\n{prev_context or '[none]'}\n\n"
        f"INPUT:\n{chunk}\n\n"
        f"CONTEXT AFTER:\n{next_context or '[none]'}"
    )