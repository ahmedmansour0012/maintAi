from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.settings import get_settings

logger = logging.getLogger(__name__)


def _truncate(text: str, max_chars: int) -> str:
    t = (text or "").strip()
    return t if len(t) <= max_chars else t[: max(0, max_chars - 3)] + "..."



def _load_prompt_template() -> str:
    # Prefer external template if exists, else built-in fallback
    template_path = Path(__file__).parent / "prompts" / "rag_answering.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    # Fallback minimal template
    return (
        "You are a senior service technician. Use ONLY the provided citations to answer.\n"
        "If a detail is not supported by citations, explicitly say it is not confirmed.\n"
        "Respond in the requested language. Provide a concise, actionable plan.\n"
    )

def compose_grounded_prompt(
    *,
    transcript: str,
    analysis: Dict[str, Any],
    clarifying_questions: List[str],
    language: str,
    part_number: Optional[str] = None,
) -> str:
    tmpl = _load_prompt_template()
    appliance = analysis.get("appliance_type")
    brand = analysis.get("brand_or_model")
    issue = analysis.get("issue_summary")
    part_num = part_number or analysis.get("part_number")

    clarifying_block = "\n".join(f"- {q}" for q in clarifying_questions) if clarifying_questions else "None."

    part_num_note = ""
    if part_num:
        part_source = analysis.get("part_number_source", "unknown")
        if part_source == "predicted":
            part_num_note = " (predicted - not visible in video, but used for context)"
        elif part_source == "extracted":
            part_num_note = " (extracted from video/image)"

    prompt = (
        f"{tmpl}\n\n"
        f"Language: {language}\n"
        f"Appliance: {appliance}\n"
        f"Brand/Model: {brand}\n"
        f"Part Number: {part_num}{part_num_note}\n"
        f"Issue summary: {issue}\n\n"
        "Transcript (verbatim, may be noisy):\n"
        f"{_truncate(transcript, 4000)}\n\n"
        "ClarifyingQuestions (ask only if needed and not already answered):\n"
        f"{clarifying_block}\n\n"
        "Instructions:\n"
        "- Base every technical claim on the knowledge base. If unclear, state uncertainty.\n"
        "- Provide a safe, step-by-step troubleshooting plan tailored to this brand/model.\n"
        "- Include required tools/parts from knowledge base when available.\n"
        "- Keep it concise and practical.\n"
    )
    return prompt




def answer_with_gemini(
    *,
    api_key: str,
    model: str,
    prompt: str,
) -> Dict[str, Any]:
    try:
        from google import genai  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise RuntimeError('Missing dependency "google-genai". Install it with: pip install google-genai') from e

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(model=model, contents=[prompt])
    text = (resp.text or "").strip()
    return {"text": text}


