from __future__ import annotations

import json
from typing import Any, Dict, List, TypedDict

import httpx

from app.core.config import settings


class IntentResult(TypedDict, total=False):
    intent: str
    categories: List[str]
    entities: Dict[str, Any]
    required_access: str
    query_hint: str



def structure_facts(facts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
    structured: Dict[str, List[Dict[str, str]]] = {}

    for f in facts:
        category = (f.get("category") or "general").upper()
        title = f.get("title", "Unknown")
        content = f.get("content", "")

        structured.setdefault(category, []).append({
            "title": title,
            "content": content
        })

    return structured


def format_structured_facts(structured: Dict[str, List[Dict[str, str]]]) -> str:
    output = ""

    for category, items in structured.items():
        output += f"\n### {category}\n"
        for item in items:
            output += f"- {item['title']}: {item['content']}\n"

    return output.strip()



_ANSWER_SYSTEM_RULES = (
    "STRICT RESPONSE RULES:\n\n"

    "1. Understand the user's question and identify relevant categories.\n"
    "2. Use ALL relevant facts across categories.\n"
    "3. NEVER write a plain paragraph. ALWAYS use the section format below.\n\n"

    "REQUIRED FORMAT — always structure your answer like this:\n"
    "📘 Overview:\n"
    "- <point>\n"
    "- <point>\n\n"
    "💰 Fees:\n"
    "- <point>\n"
    "- <point>\n\n"
    "Only include sections that are relevant to the question.\n"
    "NEVER include a section if you have no facts to put in it.\n"
    "NEVER write 'No relevant information found' inside a section — simply omit the section entirely.\n"
    "- Answer ONLY what the user asked. Do not include unrelated policies even if provided in facts.\n"
    "Available section headings (use emoji + label + colon):\n"
    "  📘 Overview:\n"
    "  ⏰ Timings:\n"
    "  💰 Fees:\n"
    "  📋 Policies:\n"
    "  ⚠️ Consequences:\n"
    "  🏫 Facilities:\n"
    "  📞 Contact:\n\n"

    "FORMATTING RULES:\n"
    "- Every section MUST have at least one '-' bullet point\n"
    "- NO plain prose or paragraphs anywhere in the answer\n"
    "- NO markdown bold (**text**) or hash headings (### text)\n"
    "- One blank line between sections\n"
    "- Section heading on its own line, bullets on lines below it\n\n"

    "CRITICAL:\n"
    "- If consequences exist, ALWAYS include them under ⚠️ Consequences:\n"
    "- Do NOT ignore partially relevant facts\n"
    "- If facts are provided, you MUST answer using them\n"
    "- DO NOT say 'I don't have information' if facts exist\n\n"

    "Return ONLY valid JSON with BOTH keys present:\n"
    "answer: string (use \\n for newlines inside the JSON string)\n"
    "follow_ups: array of EXACTLY 2 real, specific follow-up questions a student or parent "
    "would actually ask — NOT placeholders, NOT generic, NOT empty.\n"
)


_FILLER_FOLLOWUPS = {
    "q1?", "q2?", "q1", "q2",
    "question 1?", "question 2?",
    "question 1", "question 2",
    "follow-up 1", "follow-up 2",
    "followup 1", "followup 2",
}


def _is_valid_follow_ups(follow_ups: Any) -> bool:
    if not isinstance(follow_ups, list) or len(follow_ups) != 2:
        return False
    for q in follow_ups:
        s = str(q).strip()
        if len(s) < 10:
            return False
        if s.lower() in _FILLER_FOLLOWUPS:
            return False
    return True



def _terminal_failure(user_message: str) -> Dict[str, Any]:
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



class CerebrasService:
    _DEFAULT_INTENT_MODEL = "llama3.1-8b"
    _DEFAULT_ANSWER_MODEL = "llama-3.3-70b"

    def __init__(self) -> None:
        if not settings.cerebras_api_key:
            raise RuntimeError("CEREBRAS_API_KEY is not set")

        self._api_key = settings.cerebras_api_key
        self._intent_model = getattr(settings, "cerebras_model_intent", self._DEFAULT_INTENT_MODEL)
        self._answer_model = getattr(settings, "cerebras_model_answer", self._DEFAULT_ANSWER_MODEL)

    async def _chat_json(self, *, model: str, system: str, user: str) -> Dict[str, Any]:
        url = "https://api.cerebras.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self._api_key}"}

        payload = {
            "model": model,
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        async with httpx.AsyncClient(timeout=40) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()

            content = data["choices"][0]["message"]["content"]
            return json.loads(content)

    async def _generate_follow_ups(self, user_message: str, role: str = "visitor") -> List[str]:
        system = (
            "You are a School HelpDesk assistant.\n"
            f"The user's role is: {role}.\n"
            "Generate exactly 2 short, specific follow-up questions this role is allowed to ask, "
            "related to the same topic. Questions must be real and meaningful — not placeholders.\n"
            "Role access rules:\n"
            "- visitor: public info only\n"
            "- student: public + personal academic info\n"
            "- staff: public + staff-related info\n"
            "Return ONLY valid JSON: { \"follow_ups\": [\"...\", \"...\"] }"
        )

        try:
            result = await self._chat_json(
                model=self._intent_model,
                system=system,
                user=f"USER_MESSAGE: {user_message}",
            )

            follow_ups = result.get("follow_ups", [])

            if _is_valid_follow_ups(follow_ups):
                return follow_ups

        except Exception:
            pass

        return []


    async def infer_intent(self, user_message: str) -> IntentResult:
        system = (
            "You are an intent parser for a School HelpDesk bot.\n"
            "Return ONLY valid JSON with keys:\n"
            "- intent\n"
            "- categories\n"
            "- entities\n"
            "- required_access (visitor|student|staff)\n"
            "- query_hint\n"
        )

        try:
            return await self._chat_json(
                model=self._intent_model,
                system=system,
                user=f"USER_MESSAGE: {user_message}",
            )
        except Exception:
            return {
                "intent": "unknown",
                "categories": [],
                "entities": {},
                "required_access": "visitor",
                "query_hint": ""
            }


    async def generate_answer(
        self,
        *,
        user_message: str,
        role: str,
        retrieved_facts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        if not retrieved_facts:
            print("No facts received in Cerebras")

            follow_ups = await self._generate_follow_ups(user_message, role)

            return {
                "answer": (
                    "No relevant information found.\n"
                    "- Try rephrasing your question\n"
                    "- Ask about fees, policies, timings, or facilities"
                ),
                "follow_ups": follow_ups,
                "no_facts": True,
            }

        structured = structure_facts(retrieved_facts[:25])
        formatted_facts = format_structured_facts(structured)

        if not formatted_facts.strip():
            print(" Structured facts empty → using raw fallback")
            formatted_facts = "\n".join(
                f"- {f.get('title')}: {f.get('content')}"
                for f in retrieved_facts[:10]
            )

        system = (
            "You are Cortexia, a smart School HelpDesk assistant.\n"
            f"The user role is: {role}.\n\n"
            "You MUST rely ONLY on the provided facts.\n"
            + _ANSWER_SYSTEM_RULES
        )

        try:
            response = await self._chat_json(
                model=self._answer_model,
                system=system,
                user=f"USER_MESSAGE: {user_message}\n\nFACTS:\n{formatted_facts}",
            )

            print("\nCEREBRAS ANSWER RAW:", response)

            if not _is_valid_follow_ups(response.get("follow_ups")):
                print(" Invalid follow_ups — regenerating")
                response["follow_ups"] = await self._generate_follow_ups(user_message, role)

            return response

        except Exception as e:
            print(f"Cerebras generate_answer failed: {e}")
            return _terminal_failure(user_message)

