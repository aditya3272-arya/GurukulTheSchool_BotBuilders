from __future__ import annotations

from typing import Any, Dict, List, Literal

AccessLevel = Literal["visitor", "student", "staff"]


def heuristic_intent(message: str) -> Dict[str, Any]:
    """
    Lightweight, offline intent guesser used to:
    - avoid paid/rate-limited model calls when not needed
    - provide a fallback when LLM quota is exhausted
    """
    text = (message or "").lower().strip()

    categories: List[str] = []
    intent = "general_info"
    hint = ""

    def has(*terms: str) -> bool:
        return any(t in text for t in terms)


    if has("staff meeting", "staff-meeting", "meeting for staff", "faculty meeting"):
        categories.append("staff_meetings")

    if has("my timetable", "staff timetable", "teacher timetable", "my schedule") and has("staff", "teacher", "faculty"):
        categories.append("staff_timetable")

    if has("my fee", "pending fee", "fees due", "my dues", "fee status",
           "outstanding balance", "how much do i owe", "my balance"):
        categories.append("fee_status")

    if has("timetable", "class schedule", "period") and not has("staff timetable", "teacher timetable"):
        categories.append("class_schedule")

    if has("competition", "tryout", "inter-school", "interschool"):
        categories.append("competitions")

    if has("teacher", "faculty", "tutor", "homeroom", "class teacher"):
        categories.append("contact_teachers")

    if has("my attendance", "my record", "my leaves", "my absences"):
        categories.append("attendance")

    if has("fee", "fees", "tuition", "payment", "installment", "admission fee") and \
       "fee_status" not in categories:   
        categories.append("fees")

    if has("timing", "hours", "open time", "close time", "school hours", "office hours"):
        categories.append("timings")

    if has("attendance", "absent", "late") and "attendance" not in categories:
        categories.append("policies")   

    if has("discipline", "uniform", "policy", "policies", "rule", "rules", "code of conduct"):
        categories.append("policies")

    if has("facility", "facilities", "lab", "labs", "library", "auditorium",
           "computer", "science lab", "sports", "infirmary", "counseling"):
        categories.append("facilities")

    if has("contact", "phone", "email", "reception", "principal", "admin office"):
        categories.append("contact_admin")

    if has("event", "school event", "annual", "fair", "carnival", "open day"):
        categories.append("events")

    if has("club") and not has("school event", "fair"):
        categories.append("events")   

    if has("emergency", "evacuation", "fire drill", "lockdown"):
        categories.append("emergency")


    categories = list(dict.fromkeys(categories))

    STAFF_CATS   = {"staff_meetings", "staff_timetable"}
    STUDENT_CATS = {"fee_status", "class_schedule", "competitions",
                    "contact_teachers", "attendance"}

    cat_set = set(categories)

    if cat_set & STAFF_CATS:
        required: AccessLevel = "staff"
    elif cat_set & STUDENT_CATS:
        required = "student"
    else:
        required = "visitor"


    INTENT_MAP = {
        "staff_meetings":   ("staff_meetings",   "staff meeting"),
        "staff_timetable":  ("staff_timetable",  "timetable"),
        "emergency":        ("emergency",         "emergency"),
        "fee_status":       ("fee_status",        "fee"),
        "class_schedule":   ("class_schedule",    "timetable"),
        "competitions":     ("competitions",      "competition"),
        "contact_teachers": ("contact_teachers",  "teacher"),
        "attendance":       ("attendance",        "attendance"),
        "fees":             ("fees",              "fee"),
        "timings":          ("timings",           "timing"),
        "policies":         ("policies",          "policy"),
        "facilities":       ("facilities",        "facility"),
        "contact_admin":    ("contacts",          "contact"),
        "events":           ("events",            "event"),
    }

    for cat in categories:
        if cat in INTENT_MAP:
            intent, hint = INTENT_MAP[cat]
            break

    return {
        "intent": intent,
        "categories": categories,        
        "entities": {},
        "required_access": required,   
        "query_hint": hint,
        "heuristic": True,
    }