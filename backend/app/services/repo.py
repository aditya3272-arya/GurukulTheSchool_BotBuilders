from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from supabase import Client

import re

from app.core.config import settings


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_query(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


_CATEGORY_ALIASES: Dict[str, str] = {
    "uniform":              "policies",
    "dress_code":           "policies",
    "dress code":           "policies",
    "discipline":           "policies",
    "rules":                "policies",
    "conduct":              "policies",
    "code_of_conduct":      "policies",
    "code of conduct":      "policies",
    "school rules":         "policies",
    "school_rules":         "policies",
    
    "schedule":             "timings",
    "hours":                "timings",
    "school_hours":         "timings",
    "school hours":         "timings",
    "office_hours":         "timings",
    "office hours":         "timings",
    
    "tuition":              "fees",
    "payment":              "fees",
    "fee_structure":        "fees",
    "fee structure":        "fees",
    
    "infrastructure":       "facilities",
    "campus":               "facilities",
    "lab":                  "facilities",
    "labs":                 "facilities",
    "library":              "facilities",
    "sports":               "facilities",
    "canteen":              "facilities",
    "transport":            "facilities",
    
    "contact":              "contact_admin",
    "contacts":             "contact_admin",
    "administration":       "contact_admin",
    
    "absence":              "policies",
    "absences":             "policies",
    "late":                 "policies",
}

_KEYWORD_PRIORITY = [
    "uniform", "attendance", "mobile", "phone", "discipline",
    "conduct", "library", "canteen", "transport", "sports",
    "auditorium", "infirmary", "counseling", "timetable",
    "timing", "fees", "contact", "emergency", "schedule",
]

_DAY_ORDER: Dict[str, int] = {
    "Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5,
}


def _normalize_categories(categories: List[str]) -> List[str]:
    """
    Map AI-generated subcategories to actual DB category values.
    Deduplicates while preserving order.
    Unrecognized categories are kept as-is (they may be valid DB values).
    """
    normalized: List[str] = []
    for cat in categories:
        mapped = _CATEGORY_ALIASES.get(cat.lower().strip(), cat.lower().strip())
        if mapped not in normalized:
            normalized.append(mapped)
    return normalized


def _sharpen_hint(hint_words: List[str]) -> str:
    """
    Pick the single most specific keyword from hint words for reliable ilike matching.
    Checks priority list first; falls back to first word.
    """
    for kw in _KEYWORD_PRIORITY:
        if any(kw in w.lower() for w in hint_words):
            return kw
    return hint_words[0] if hint_words else ""


class Repo:
    def __init__(self, sb: Client) -> None:
        self.sb = sb

    def get_student_user(self, *, adm_no: str, name: str) -> Optional[Dict[str, Any]]:
        res = (
            self.sb.table("users")
            .select("id,school_id,role,name,adm_no,staff_id")
            .eq("school_id", settings.school_id)
            .eq("role", "student")
            .eq("adm_no", adm_no)
            .ilike("name", name)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def get_staff_user(self, *, staff_id: str, name: str) -> Optional[Dict[str, Any]]:
        res = (
            self.sb.table("users")
            .select("id,school_id,role,name,adm_no,staff_id")
            .eq("school_id", settings.school_id)
            .eq("role", "staff")
            .eq("staff_id", staff_id)
            .ilike("name", name)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def get_visitor_user(self, *, name: str) -> Optional[Dict[str, Any]]:
        display = (name or "Visitor").strip() or "Visitor"
        res = (
            self.sb.table("users")
            .select("id,school_id,role,name,adm_no,staff_id")
            .eq("school_id", settings.school_id)
            .eq("role", "visitor")
            .ilike("name", display)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def create_visitor_user(self, *, name: str) -> Dict[str, Any]:
        payload = {"school_id": settings.school_id, "role": "visitor", "name": name or "Visitor"}
        res = self.sb.table("users").insert(payload, returning="representation").execute()
        if not res.data:
            raise RuntimeError("Failed to create visitor user")
        return res.data[0]

    def get_or_create_visitor_user(self, *, name: str) -> Dict[str, Any]:
        display = (name or "Visitor").strip() or "Visitor"
        existing = self.get_visitor_user(name=display)
        if existing:
            return existing
        return self.create_visitor_user(name=display)

    def create_chat_session(self, *, user_id: str, title: str) -> Dict[str, Any]:
        payload = {"school_id": settings.school_id, "user_id": user_id, "title": title, "updated_at": _now_iso()}
        res = self.sb.table("chat_sessions").insert(payload, returning="representation").execute()
        if not res.data:
            raise RuntimeError("Failed to create chat session")
        return res.data[0]

    def chat_session_exists(self, *, session_id: str, user_id: str) -> bool:
        res = self.sb.table("chat_sessions").select("id").eq("id", session_id).eq("user_id", user_id).limit(1).execute()
        return bool(res.data)

    def list_chat_sessions(self, *, user_id: str) -> List[Dict[str, Any]]:
        res = (
            self.sb.table("chat_sessions")
            .select("id,title,created_at,updated_at")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
        )
        return list(res.data or [])

    def rename_chat_session(self, *, session_id: str, user_id: str, title: str) -> None:
        self.sb.table("chat_sessions").update({"title": title, "updated_at": _now_iso()}).eq("id", session_id).eq(
            "user_id", user_id
        ).execute()

    def delete_chat_session(self, *, session_id: str, user_id: str) -> None:
        self.sb.table("chat_sessions").delete().eq("id", session_id).eq("user_id", user_id).execute()

    def list_messages(self, *, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        ses = (
            self.sb.table("chat_sessions").select("id").eq("id", session_id).eq("user_id", user_id).limit(1).execute()
        )
        if not ses.data:
            return []
        res = (
            self.sb.table("chat_messages")
            .select("id,role,content,created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )
        return list(res.data or [])

    def add_message(self, *, session_id: str, role: str, content: str) -> None:
        self.sb.table("chat_messages").insert({"session_id": session_id, "role": role, "content": content}).execute()
        self.sb.table("chat_sessions").update({"updated_at": _now_iso()}).eq("id", session_id).execute()

    def count_messages(self, *, session_id: str) -> int:
        res = self.sb.table("chat_messages").select("id", count="exact").eq("session_id", session_id).execute()
        return res.count or 0

    def search_knowledge(
        self,
        *,
        categories: List[str],
        query_hint: str,
        max_rows: int = 12,
        role_rank: int = 1,
    ) -> List[Dict[str, Any]]:

        allowed_levels = (
            ["visitor"]
            if role_rank == 1
            else (["visitor", "student"] if role_rank == 2 else ["visitor", "student", "staff"])
        )

        categories = _normalize_categories(categories)
        print(" normalized categories:", categories)

        clean_hint = _clean_query(query_hint) if query_hint else ""
        hint_words = clean_hint.split()[:6] if clean_hint else []
        sharp_hint = _sharpen_hint(hint_words) if hint_words else ""
        print(f"🔍 sharp_hint: '{sharp_hint}'")

        def _base_query():
            return (
                self.sb.table("knowledge_items")
                .select("id,access_level,category,title,content,source,updated_at")
                .eq("school_id", settings.school_id)
                .in_("access_level", allowed_levels)
            )

        if categories and sharp_hint:
            try:
                q = _base_query().in_("category", categories)
                q = q.or_(f"title.ilike.%{sharp_hint}%,content.ilike.%{sharp_hint}%")
                res = q.limit(max_rows).execute()
                if res.data:
                    print(f"🔎 Step 1 (category + hint) found {len(res.data)} facts")
                    return list(res.data)
            except Exception as e:
                print(" Step 1 search error:", e)

        if categories:
            try:
                res = _base_query().in_("category", categories).limit(max_rows).execute()
                if res.data:
                    print(f" Step 2 (category only) found {len(res.data)} facts")
                    return list(res.data)
            except Exception as e:
                print(" Step 2 search error:", e)

        if sharp_hint:
            try:
                q = _base_query()
                q = q.or_(f"title.ilike.%{sharp_hint}%,content.ilike.%{sharp_hint}%")
                res = q.limit(max_rows).execute()
                if res.data:
                    print(f" Step 3 (hint only) found {len(res.data)} facts")
                    return list(res.data)
            except Exception as e:
                print(" Step 3 search error:", e)

        print(" Step 4: no facts found in any search step → returning []")
        return []

    def get_student_fee_status(self, *, adm_no: str) -> Optional[Dict[str, Any]]:
        res = (
            self.sb.table("student_fees")
            .select("*")
            .eq("school_id", settings.school_id)
            .eq("adm_no", adm_no)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None


    def get_student_timetable(self, *, adm_no: str) -> Optional[Dict[str, Any]]:
        """
        Returns the student's class and full week timetable.

        Return shape:
        {
            "class_name": "9A",
            "grade": 9,
            "section": "A",
            "slots": [
                {
                    "day": "Monday",
                    "period_number": 1,
                    "start_time": "08:00",
                    "end_time": "08:45",
                    "subject": "Mathematics",
                    "teacher_staff_id": "STAFF-9001",
                    "is_break": False,
                },
                ...
            ]
        }
        Returns None if the student has no class assignment yet.
        """
        sc_res = (
            self.sb.table("student_classes")
            .select("class_id, classes(name, grade, section)")
            .eq("school_id", settings.school_id)
            .eq("adm_no", adm_no)
            .limit(1)
            .execute()
        )
        if not sc_res.data:
            print(f" No class assignment found for adm_no={adm_no}")
            return None

        row       = sc_res.data[0]
        cls       = row.get("classes") or {}
        class_id  = row["class_id"]
        class_name = cls.get("name", "")
        grade     = cls.get("grade")
        section   = cls.get("section", "")

        slots_res = (
            self.sb.table("timetable_slots")
            .select("day, period_number, start_time, end_time, subject, teacher_staff_id, is_break")
            .eq("school_id", settings.school_id)
            .eq("class_id", class_id)
            .order("day")
            .order("period_number")
            .execute()
        )

        slots = sorted(
            slots_res.data or [],
            key=lambda s: (_DAY_ORDER.get(s["day"], 9), s["period_number"]),
        )

        print(f" Student timetable: class={class_name}, {len(slots)} slots")
        return {
            "class_name": class_name,
            "grade":      grade,
            "section":    section,
            "slots":      slots,
        }

    def get_teacher_timetable(self, *, staff_id: str) -> Dict[str, Any]:
        """
        Returns a teacher's full teaching schedule across all classes.

        Return shape:
        {
            "slots": [
                {
                    "day": "Monday",
                    "period_number": 1,
                    "start_time": "08:00",
                    "end_time": "08:45",
                    "subject": "Mathematics",
                    "class_name": "9A",
                    "is_break": False,
                },
                ...
            ]
        }
        Returns {"slots": []} if no periods are assigned yet.
        """
        slots_res = (
            self.sb.table("timetable_slots")
            .select("day, period_number, start_time, end_time, subject, is_break, class_id, classes(name)")
            .eq("school_id", settings.school_id)
            .eq("teacher_staff_id", staff_id)
            .eq("is_break", False)   
            .order("day")
            .order("period_number")
            .execute()
        )

        raw = slots_res.data or []

        slots = sorted(
            [
                {
                    "day":           s["day"],
                    "period_number": s["period_number"],
                    "start_time":    s["start_time"],
                    "end_time":      s["end_time"],
                    "subject":       s["subject"],
                    "class_name":    (s.get("classes") or {}).get("name", ""),
                    "is_break":      s["is_break"],
                }
                for s in raw
            ],
            key=lambda s: (_DAY_ORDER.get(s["day"], 9), s["period_number"]),
        )

        print(f" Teacher timetable: staff_id={staff_id}, {len(slots)} periods")
        return {"slots": slots}