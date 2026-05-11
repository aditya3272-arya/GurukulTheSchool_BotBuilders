from __future__ import annotations

from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import SessionData
from app.models.schemas import ChatTurnIn, ChatTurnOut
from app.routes.deps import require_session
from app.services.access_control import clamp_required_access, denial_reason, has_access
from app.services.composite_ai_service import CompositeAIService
from app.services.heuristics import heuristic_intent
from app.services.repo import Repo
from app.services.supabase_client import get_supabase


router = APIRouter(prefix="/api", tags=["chat"])


def _role_rank(role: str) -> int:
    return 1 if role == "visitor" else (2 if role == "student" else 3)


def _fallback_follow_ups(role: str) -> list[str]:
    if role == "staff":
        return [
            "What is the upcoming staff meeting schedule?",
            "Show my staff timetable.",
            "What are the emergency contact details?",
        ]
    if role == "student":
        return [
            "What is my class timetable?",
            "Are there any upcoming school events?",
            "What is my fee payment status?",
        ]
    return [
        "What are the school timings?",
        "What is the attendance policy?",
        "What facilities does the school have?",
    ]


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except Exception:
        return False



_TIMETABLE_KEYWORDS = [
    "timetable", "time table", "my schedule", "my classes", "class schedule",
    "my timetable", "show timetable", "what are my classes", "my periods",
    "my class", "which class", "which period", "my subjects",
]

def _is_timetable_query(message: str) -> bool:
    msg = message.lower()
    return any(kw in msg for kw in _TIMETABLE_KEYWORDS)



_DAY_EMOJI = {
    "Monday":    "📅",
    "Tuesday":   "📅",
    "Wednesday": "📅",
    "Thursday":  "📅",
    "Friday":    "📅",
}


def _format_student_timetable(data: dict) -> str:
    """
    Formats student timetable into the app's standard section format.

    Example output:
        📘 Overview:
        - Your Class: 9A (Grade 9, Section A)

        📅 Monday:
        - P1  08:00–08:45  Mathematics
        - P2  08:45–09:30  English
        ...
    """
    class_name = data.get("class_name", "Unknown")
    grade      = data.get("grade", "")
    section    = data.get("section", "")
    slots      = data.get("slots", [])

    lines = [
        "📘 Overview:",
        f"- Your Class: {class_name} (Grade {grade}, Section {section})",
        "",
    ]

    from collections import defaultdict
    by_day: dict[str, list] = defaultdict(list)
    for s in slots:
        by_day[s["day"]].append(s)

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for day in day_order:
        day_slots = by_day.get(day)
        if not day_slots:
            continue
        lines.append(f" {day}:")
        for s in day_slots:
            if s.get("is_break"):
                lines.append(f"- ── {s['start_time']}–{s['end_time']}  {s['subject']} ──")
            else:
                lines.append(
                    f"- P{s['period_number']}  {s['start_time']}–{s['end_time']}  {s['subject']}"
                )
        lines.append("")

    return "\n".join(lines).strip()


def _format_teacher_timetable(data: dict, teacher_name: str = "") -> str:
    """
    Formats teacher timetable into the app's standard section format.

    Example output:
        📘 Overview:
        - Your teaching schedule across all classes

        📅 Monday:
        - P1  08:00–08:45  Mathematics  →  Class 9A
        ...
    """
    slots = data.get("slots", [])

    name_line = f" for {teacher_name}" if teacher_name else ""
    lines = [
        "📘 Overview:",
        f"- Teaching schedule{name_line} across all classes",
        "",
    ]

    from collections import defaultdict
    by_day: dict[str, list] = defaultdict(list)
    for s in slots:
        by_day[s["day"]].append(s)

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for day in day_order:
        day_slots = by_day.get(day)
        if not day_slots:
            continue
        lines.append(f"📅 {day}:")
        for s in day_slots:
            lines.append(
                f"- P{s['period_number']}  {s['start_time']}–{s['end_time']}  "
                f"{s['subject']}  →  Class {s['class_name']}"
            )
        lines.append("")

    if not any(by_day.values()):
        lines.append("- No teaching periods assigned yet.")

    return "\n".join(lines).strip()



@router.post("/chat", response_model=ChatTurnOut)
async def chat_turn(body: ChatTurnIn, session: SessionData = Depends(require_session)):
    sb = get_supabase()
    repo = Repo(sb)
    ai = CompositeAIService()

    if not body.session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required (create a chat first)")
    if not _is_uuid(body.session_id.strip()):
        raise HTTPException(status_code=400, detail="session_id must be a UUID (click 'New chat' first)")
    if not repo.chat_session_exists(session_id=body.session_id, user_id=session.user_id):
        raise HTTPException(status_code=404, detail="Chat session not found")

    repo.add_message(session_id=body.session_id, role="user", content=body.message)

    if repo.count_messages(session_id=body.session_id) == 1:
        title = body.message.strip()[:50]
        if len(body.message.strip()) > 50:
            title += "…"
        repo.rename_chat_session(session_id=body.session_id, user_id=session.user_id, title=title)

    if _is_timetable_query(body.message):

        if session.role == "student" and session.adm_no:
            print(f" Timetable query — student {session.adm_no}")
            timetable_data = repo.get_student_timetable(adm_no=session.adm_no)

            if timetable_data:
                answer = _format_student_timetable(timetable_data)
                follow_ups = [
                    "What are the upcoming school events?",
                    "Who is my class teacher?",
                ]
            else:
                answer = (
                    " Timetable:\n"
                    "- No timetable found for your admission number.\n"
                    "- Please contact the academic office to get your class assigned."
                )
                follow_ups = _fallback_follow_ups(session.role)

            repo.add_message(session_id=body.session_id, role="assistant", content=answer)
            return ChatTurnOut(
                answer=answer,
                follow_ups=follow_ups,
                intent={"intent": "timetable", "categories": ["class_schedule"], "required_access": "student"},
            )

        if session.role == "staff" and session.staff_id:
            print(f" Timetable query — teacher {session.staff_id}")
            timetable_data = repo.get_teacher_timetable(staff_id=session.staff_id)

            answer = _format_teacher_timetable(timetable_data, teacher_name=session.name or "")
            follow_ups = [
                "What is the upcoming staff meeting schedule?",
                "What are the emergency contact details?",
            ]

            repo.add_message(session_id=body.session_id, role="assistant", content=answer)
            return ChatTurnOut(
                answer=answer,
                follow_ups=follow_ups,
                intent={"intent": "timetable", "categories": ["staff_timetable"], "required_access": "staff"},
            )

        if session.role == "visitor":
            answer = (
                "📋 Policies:\n"
                "- Timetables are only available to registered students and staff.\n"
                "- Please log in with your student admission number or staff ID to view your timetable."
            )
            repo.add_message(session_id=body.session_id, role="assistant", content=answer)
            return ChatTurnOut(
                answer=answer,
                follow_ups=_fallback_follow_ups("visitor"),
                intent={"intent": "timetable", "categories": ["class_schedule"], "required_access": "student"},
            )

    intent = heuristic_intent(body.message)
    required_access = intent.get("required_access", "visitor")

    if not has_access(session.role, required_access):
        reason = denial_reason(session.role, required_access)
        answer = (
            f"You don't have access due to {reason}.\n\n"
            "Try asking something you're allowed to access."
        )
        try:
            denial_out = await ai.generate_answer(
                user_message=body.message,
                role=session.role,
                retrieved_facts=[],
            )
            denial_fu = [str(x) for x in (denial_out.get("follow_ups") or [])][:3]
            if not denial_fu:
                denial_fu = _fallback_follow_ups(session.role)
        except Exception as e:
            print("AI ERROR", e)
            denial_fu = _fallback_follow_ups(session.role)

        repo.add_message(session_id=body.session_id, role="assistant", content=answer)
        return ChatTurnOut(answer=answer, follow_ups=denial_fu, intent=intent)

    try:
        ai_intent = await ai.infer_intent(body.message)

        ai_required = clamp_required_access(ai_intent.get("required_access") or "visitor")

        heuristic_rank = _role_rank(required_access)
        ai_rank        = _role_rank(ai_required)

        final_required = ai_required if ai_rank <= heuristic_rank else required_access

        intent = {
            **ai_intent,
            "required_access": final_required,
        }
        required_access = final_required

        print(f" Access: heuristic={heuristic_rank} ai={ai_rank} final={final_required}")

        if not has_access(session.role, required_access):
            reason = denial_reason(session.role, required_access)
            answer = (
                f"You don't have access due to {reason}.\n\n"
                "Try asking something you're allowed to access."
            )
            try:
                denial_out = await ai.generate_answer(
                    user_message=body.message,
                    role=session.role,
                    retrieved_facts=[],
                )
                denial_fu = [str(x) for x in (denial_out.get("follow_ups") or [])][:3]
                if not denial_fu:
                    denial_fu = _fallback_follow_ups(session.role)
            except Exception as e:
                print("AI ERROR", e)
                denial_fu = _fallback_follow_ups(session.role)

            repo.add_message(session_id=body.session_id, role="assistant", content=answer)
            return ChatTurnOut(answer=answer, follow_ups=denial_fu, intent=intent)

    except Exception as e:
        print("AI ERROR", e)
        intent = heuristic_intent(body.message)

    categories = list(intent.get("categories") or [])
    query_hint = str(intent.get("query_hint") or "").strip()

    facts = repo.search_knowledge(
        categories=categories,
        query_hint=query_hint,
        role_rank=_role_rank(session.role),
    )

    print(" First fetch facts:", facts)

    if not facts:
        print(" No facts found with AI intent → trying fallback search")

        facts = repo.search_knowledge(
            categories=[],
            query_hint=body.message[:60],
            role_rank=_role_rank(session.role),
        )

        if not facts:
            print(" FINAL FALLBACK: Fetching ALL visitor data")
            facts = repo.search_knowledge(
                categories=[],
                query_hint="",
                role_rank=1,
            )

        print(" Fallback fetch facts:", facts)

        msg = body.message.lower()

        def matches(f, keyword):
            text = (f.get("category", "") + " " + f.get("title", "") + " " + f.get("content", "")).lower()
            return keyword in text

        if "attendance" in msg:
            facts = [f for f in facts if matches(f, "attendance")]
        elif "fee" in msg:
            facts = [f for f in facts if matches(f, "fee")]
        elif "timing" in msg or "time" in msg:
            facts = [f for f in facts if matches(f, "timing") or matches(f, "time")]
        elif "uniform" in msg:
            facts = [f for f in facts if matches(f, "uniform")]
        elif "facility" in msg:
            facts = [f for f in facts if matches(f, "facility")]

        print(" Filtered facts:", facts)

    cats = intent.get("categories") or []

    is_fee_query      = ("fee_status" in cats or "fees" in cats)
    is_student_with_adm = session.role == "student" and session.adm_no

    logger = logging.getLogger(__name__)
    logger.info(f"Fee query detection - categories: {cats}, role: {session.role}, adm_no: {session.adm_no}")

    if is_fee_query and is_student_with_adm:
        fee_data = repo.get_student_fee_status(adm_no=session.adm_no)
        if fee_data:
            logger.info(f"Retrieved fee data for {session.adm_no}: {fee_data}")
            facts.insert(0, {
                "title": "Personal Fee Status",
                "content": (
                    f"Total: {fee_data.get('total_fees')}, "
                    f"Paid: {fee_data.get('paid_amount')}, "
                    f"Pending: {fee_data.get('pending_amount')}. "
                    f"Due date: {fee_data.get('due_date')}."
                ),
            })
        else:
            logger.warning(f"No fee data found for student {session.adm_no}")
            facts.insert(0, {
                "title": "Personal Fee Status",
                "content": "No specific fee records found for your admission number. Please contact administration.",
            })

    answer = ""
    follow_ups: list[str] = []
    try:
        print(" Calling AI with facts:", facts)
        out = await ai.generate_answer(
            user_message=body.message,
            role=session.role,
            retrieved_facts=facts,
        )
        answer = str(out.get("answer") or "").strip()
        fu = out.get("follow_ups") or []
        if isinstance(fu, list):
            follow_ups = [str(x) for x in fu][:3]
    except Exception as e:
        print("AI ERROR", e)
        if facts:
            lines = ["Here's what I found:"]
            for item in facts[:8]:
                title = item.get("title") or item.get("category") or "Info"
                content = (item.get("content") or "").strip()
                if content:
                    lines.append(f"- {title}: {content}")
            answer = "\n".join(lines)
        else:
            answer = "I couldn't reach the AI service right now, and I don't have enough stored info for that. Try again in a minute."

    if not follow_ups:
        follow_ups = _fallback_follow_ups(session.role)

    if not answer and facts:
        answer = facts[0].get("content", "Here's what I found.")
    elif not answer:
        answer = "I don't have that information right now."

    repo.add_message(session_id=body.session_id, role="assistant", content=answer)

    return ChatTurnOut(answer=answer, follow_ups=follow_ups, intent=intent)