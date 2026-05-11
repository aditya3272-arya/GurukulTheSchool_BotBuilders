from __future__ import annotations

import logging
from typing import Any

from app.services.gemini_service import GeminiService
from app.services.cerebras_service import CerebrasService
from app.services.groq_service import GroqService

logger = logging.getLogger(__name__)


_EMPTY_ANSWER_PHRASES = [
    "do not have",
    "don't have",
    "no information",
    "not available",
    "cannot find",
    "unable to find",
    "no details available",
]


_PARTIAL_ANSWER_PHRASES = [
    "not specified in the provided facts",
    "not explicitly stated",
    "exact details are not specified",
    "not mentioned in the",
    "not found in the",
    "however, based on",
    "not explicitly mentioned",
    "not directly stated",
]

_PARTIAL_ANSWER_NUDGE = (
    "\n\n📞 Contact:\n"
    "- For further details, please contact the school administration directly\n"
    "- You can also use the Raise Query button in the sidebar to submit your question"
)


def _is_empty_answer(answer: str) -> bool:
    """True when the answer has NO useful content at all."""
    lowered = answer.strip().lower()
    return any(phrase in lowered for phrase in _EMPTY_ANSWER_PHRASES)


def _is_partial_answer(answer: str) -> bool:
    """True when the answer has some useful content but admits a gap."""
    lowered = answer.strip().lower()
    return any(phrase in lowered for phrase in _PARTIAL_ANSWER_PHRASES)


def _is_weak_answer(answer: str) -> bool:
    """Kept for backward-compat — true for both empty and partial answers."""
    return _is_empty_answer(answer) or _is_partial_answer(answer)


def _enrich_partial_answer(out: dict[str, Any]) -> dict[str, Any]:
    """
    Append the contact/raise-query nudge to a partial answer.
    Avoids throwing away genuinely useful partial responses.
    """
    answer = str(out.get("answer") or "").strip()
    if "Raise Query" not in answer and "school administration" not in answer:
        out = {**out, "answer": answer + _PARTIAL_ANSWER_NUDGE}
    return out


_FILLER_BULLET_PHRASES = [
    "no consequences mentioned",
    "none mentioned",
    "no information available",
    "not applicable",
    "n/a",
    "none",
    "no relevant information",
    "no details available",
    "not available",
    "no data",
]


def _strip_filler_sections(answer: str) -> str:
    """
    Remove sections where the AI hallucinated a placeholder bullet like
    '- No consequences mentioned' instead of omitting the section entirely.

    Works line-by-line:
    - Collects each heading + its bullets into a block
    - Flushes the block to output only if at least one bullet has real content
    - Silently drops the whole block (heading + blanks) if all bullets are filler
    """
    lines = answer.split("\n")
    output: list[str] = []

    current_heading: str | None = None
    current_bullets: list[str] = []
    pending_blanks: list[str] = []

    def _is_filler_bullet(line: str) -> bool:
        stripped = line.lstrip("- ").strip().lower()
        return any(phrase in stripped for phrase in _FILLER_BULLET_PHRASES)

    def _is_section_heading(line: str) -> bool:
        stripped = line.strip()
        return stripped.endswith(":") and len(stripped) > 2

    def flush() -> None:
        nonlocal current_heading, current_bullets, pending_blanks
        if current_heading is None:
            return
        real_bullets = [b for b in current_bullets if not _is_filler_bullet(b)]
        if real_bullets:
            output.extend(pending_blanks)
            output.append(current_heading)
            output.extend(real_bullets)

        pending_blanks = []
        current_heading = None
        current_bullets = []

    for line in lines:
        if _is_section_heading(line):
            flush()
            current_heading = line
        elif line.strip() == "":
            if current_heading is not None:
                pending_blanks.append(line)
            else:
                output.append(line)
        elif line.strip().startswith("-") and current_heading is not None:
            current_bullets.append(line)
        else:
            flush()
            output.append(line)

    flush()
    return "\n".join(output).strip()


def _is_terminal_failure(out: dict[str, Any]) -> bool:
    """True if a service already decided this is an unrecoverable failure."""
    return bool(out.get("raise_query"))


class CompositeAIService:
    def __init__(self) -> None:
        self._groq = None
        self._gemini = None
        self._cerebras = None

        try:
            self._groq = GroqService()
            print(" Groq initialized (PRIMARY)")
        except Exception as e:
            print(" Groq failed:", e)

        try:
            self._gemini = GeminiService()
            print("Gemini initialized (FALLBACK)")
        except Exception as e:
            print("Gemini failed:", e)

        try:
            self._cerebras = CerebrasService()
            print("Cerebras initialized (LAST RESORT)")
        except Exception as e:
            print("Cerebras failed:", e)

    async def infer_intent(self, user_message: str) -> dict[str, Any]:
        for svc_name, svc in [
            ("Groq",     self._groq),
            ("Gemini",   self._gemini),
            ("Cerebras", self._cerebras),
        ]:
            if svc is None:
                continue

            try:
                print(f" Trying intent with {svc_name}")
                result = await svc.infer_intent(user_message)
                if result:
                    return result
            except Exception as exc:
                print(f" {svc_name} intent error:", exc)

        raise RuntimeError("no_llm_intent")

    async def generate_answer(
        self,
        *,
        user_message: str,
        role: str,
        retrieved_facts: list[dict[str, Any]],
    ) -> dict[str, Any]:

        for svc_name, svc in [
            ("Groq",     self._groq),      
            ("Gemini",   self._gemini),    
            ("Cerebras", self._cerebras),  
        ]:
            if svc is None:
                continue

            try:
                print(f" Trying answer with {svc_name}")

                out = await svc.generate_answer(
                    user_message=user_message,
                    role=role,
                    retrieved_facts=retrieved_facts,
                )

                print(f" {svc_name} OUTPUT:", out)

                
                if _is_terminal_failure(out):
                    print(f" {svc_name} returned terminal failure → escalating")
                    return out

                answer = str(out.get("answer") or "").strip()

                if not answer:
                    print(f" {svc_name} returned empty answer → trying next")
                    continue

                if out.get("no_facts"):
                    print(f" {svc_name} had no facts → trying next")
                    continue

                if _is_empty_answer(answer):
                    print(f" {svc_name} gave empty/useless answer → trying next")
                    continue


                if _is_partial_answer(answer):
                    print(f"ℹ {svc_name} gave partial answer → stripping fillers + appending contact nudge")
                    out = {**out, "answer": _strip_filler_sections(answer)}
                    return _enrich_partial_answer(out)

                cleaned = _strip_filler_sections(answer)
                if cleaned != answer:
                    print(f" {svc_name} had filler sections → stripped")
                return {**out, "answer": cleaned}

            except Exception as exc:
                print(f" {svc_name} answer error:", exc)

        print(" All AI models failed → triggering Raise Query failswitch")

        return {
            "answer": (
                " We're currently unable to process your request.\n\n"
                "Our systems are temporarily unavailable. Please use the "
                "Raise Query button in the sidebar to submit your question "
                "directly to the school administration."
            ),
            "follow_ups": [],
            "raise_query": True,                  
            "raise_query_prefill": user_message,  
        }