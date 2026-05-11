from supabase import create_client, Client
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from .config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
import os

SCHOOL_ID = os.getenv("SCHOOL_ID", "")

class DatabaseManager:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


    def get_admin_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        response = (
            self.client.table("admin_credentials")
            .select("*")
            .eq("school_id", SCHOOL_ID)
            .eq("username", username)
            .execute()
        )
        return response.data[0] if response.data else None

    def update_admin_last_login(self, admin_id: str):
        self.client.table("admin_credentials").update(
            {"last_login": datetime.now(timezone.utc).isoformat()}
        ).eq("id", admin_id).execute()

    def get_admins(self) -> List[Dict[str, Any]]:
        response = (
            self.client.table("admin_credentials")
            .select("id, username, display_name, is_active, last_login, created_at")
            .eq("school_id", SCHOOL_ID)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def add_admin(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["school_id"] = SCHOOL_ID
        response = self.client.table("admin_credentials").insert(data).execute()
        return response.data[0] if response.data else None

    def update_admin(self, admin_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if "password_hash" in updates and not updates["password_hash"]:
            del updates["password_hash"]

        response = (
            self.client.table("admin_credentials")
            .update(updates)
            .eq("id", admin_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def delete_admin(self, admin_id: str):
        self.client.table("admin_credentials").delete().eq("id", admin_id).execute()


    def get_users(self) -> List[Dict[str, Any]]:
        response = (
            self.client.table("users")
            .select("*")
            .eq("school_id", SCHOOL_ID)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def add_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["school_id"] = SCHOOL_ID
        response = self.client.table("users").insert(data).execute()
        return response.data[0] if response.data else None

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        response = (
            self.client.table("users")
            .update(updates)
            .eq("id", user_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def delete_user(self, user_id: str):
        self.client.table("users").delete().eq("id", user_id).execute()


    def get_knowledge_items(self) -> List[Dict[str, Any]]:
        response = (
            self.client.table("knowledge_items")
            .select("*")
            .eq("school_id", SCHOOL_ID)
            .order("updated_at", desc=True)
            .execute()
        )
        return response.data

    def add_knowledge_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["school_id"] = SCHOOL_ID
        response = self.client.table("knowledge_items").insert(data).execute()
        return response.data[0] if response.data else None

    def update_knowledge_item(self, item_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        response = (
            self.client.table("knowledge_items")
            .update(updates)
            .eq("id", item_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def delete_knowledge_item(self, item_id: str):
        self.client.table("knowledge_items").delete().eq("id", item_id).execute()


    def get_fees(self) -> List[Dict[str, Any]]:
        response = (
            self.client.table("student_fees")
            .select("*")
            .eq("school_id", SCHOOL_ID)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def add_fee(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["school_id"] = SCHOOL_ID
        response = self.client.table("student_fees").insert(data).execute()
        return response.data[0] if response.data else None

    def update_fee(self, fee_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        response = (
            self.client.table("student_fees")
            .update(updates)
            .eq("id", fee_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def delete_fee(self, fee_id: str):
        self.client.table("student_fees").delete().eq("id", fee_id).execute()


    def get_classes(self) -> List[Dict[str, Any]]:
        response = (
            self.client.table("classes")
            .select("*")
            .eq("school_id", SCHOOL_ID)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def add_class(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["school_id"] = SCHOOL_ID
        response = self.client.table("classes").insert(data).execute()
        return response.data[0] if response.data else None

    def update_class(self, class_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        response = (
            self.client.table("classes")
            .update(updates)
            .eq("id", class_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def delete_class(self, class_id: str):
        self.client.table("classes").delete().eq("id", class_id).execute()


    def get_timetable_slots(self) -> List[Dict[str, Any]]:
        response = (
            self.client.table("timetable_slots")
            .select("*")
            .eq("school_id", SCHOOL_ID)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def add_timetable_slot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["school_id"] = SCHOOL_ID
        response = self.client.table("timetable_slots").insert(data).execute()
        return response.data[0] if response.data else None

    def update_timetable_slot(self, slot_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        response = (
            self.client.table("timetable_slots")
            .update(updates)
            .eq("id", slot_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def delete_timetable_slot(self, slot_id: str):
        self.client.table("timetable_slots").delete().eq("id", slot_id).execute()


    def get_student_classes(self) -> List[Dict[str, Any]]:
        response = (
            self.client.table("student_classes")
            .select("*")
            .eq("school_id", SCHOOL_ID)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def add_student_class(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["school_id"] = SCHOOL_ID
        response = self.client.table("student_classes").insert(data).execute()
        return response.data[0] if response.data else None

    def update_student_class(self, record_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        response = (
            self.client.table("student_classes")
            .update(updates)
            .eq("id", record_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def delete_student_class(self, record_id: str):
        self.client.table("student_classes").delete().eq("id", record_id).execute()

db_manager = DatabaseManager()