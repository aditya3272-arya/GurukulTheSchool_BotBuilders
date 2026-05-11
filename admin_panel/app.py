from __future__ import annotations

import bcrypt
import customtkinter as ctk
from tkinter import messagebox
from typing import Any, Dict

from .database import db_manager
from .ui_components import DataTable
from .login import LoginScreen

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

_BG        = "#0f0f1a"
_SIDEBAR   = "#13132a"
_CARD      = "#1a1a2e"
_BORDER    = "#2e2e50"
_ACCENT    = "#7C6FFF"
_ACCENT_HO = "#6254cc"
_DANGER    = "#e05c5c"
_DANGER_HO = "#c0392b"
_TEXT_DIM  = "#6b6b8a"
_TEXT_MID  = "#9a8fff"



class FormDialog(ctk.CTkToplevel):
    def __init__(self, master, title_text: str, fields: list[str],
                 initial_data: Dict | None = None, on_save=None):
        super().__init__(master)
        self.title(title_text)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color=_BG)
        self.on_save = on_save
        self.entries: Dict[str, ctk.CTkEntry | ctk.CTkTextbox] = {}

        header = ctk.CTkFrame(self, fg_color=_SIDEBAR, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text=title_text,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left", padx=24, pady=14)

        body = ctk.CTkScrollableFrame(self, fg_color="transparent", width=460)
        body.pack(fill="both", expand=True, padx=0, pady=0)
        body.grid_columnconfigure(1, weight=1)

        for row_idx, field in enumerate(fields):
            ctk.CTkLabel(
                body,
                text=field.replace("_", " ").upper(),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=_TEXT_DIM,
                anchor="w",
            ).grid(row=row_idx * 2, column=0, columnspan=2, padx=24, pady=(16, 2), sticky="w")

            is_password = "password" in field.lower()
            is_content  = field.lower() == "content"

            if is_content:
                widget = ctk.CTkTextbox(
                    body, width=420, height=100,
                    fg_color="#12122a", border_color=_BORDER,
                    border_width=1, corner_radius=8,
                )
                if initial_data and field in initial_data and initial_data[field]:
                    widget.insert("1.0", str(initial_data[field]))
                widget.grid(row=row_idx * 2 + 1, column=0, columnspan=2, padx=24, pady=(0, 0), sticky="ew")
            else:
                widget = ctk.CTkEntry(
                    body, width=420, height=40,
                    show="●" if is_password else "",
                    fg_color="#12122a", border_color=_BORDER,
                    border_width=1, corner_radius=8,
                )
                if initial_data and field in initial_data and initial_data[field] and not is_password:
                    widget.insert(0, str(initial_data[field]))
                widget.grid(row=row_idx * 2 + 1, column=0, columnspan=2, padx=24, pady=(0, 0), sticky="ew")

            self.entries[field] = widget

        if any("password" in f.lower() for f in fields):
            ctk.CTkLabel(
                body,
                text="Leave Password blank when editing to keep existing password.",
                font=ctk.CTkFont(size=11),
                text_color=_TEXT_DIM,
                wraplength=420,
                anchor="w",
                justify="left",
            ).grid(row=len(fields) * 2, column=0, columnspan=2, padx=24, pady=(12, 4), sticky="w")

        footer = ctk.CTkFrame(self, fg_color=_SIDEBAR, corner_radius=0, height=64)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer, text="Cancel", width=110,
            fg_color="#2e2e50", hover_color="#3a3a60",
            command=self.destroy,
        ).pack(side="right", padx=(8, 20), pady=14)

        ctk.CTkButton(
            footer, text="Save", width=110,
            fg_color=_ACCENT, hover_color=_ACCENT_HO,
            command=self._save,
        ).pack(side="right", padx=8, pady=14)

        h = min(120 + len(fields) * 72 + 80, 720)
        self.geometry(f"500x{h}")

    def _save(self):
        data = {}
        for field, widget in self.entries.items():
            if isinstance(widget, ctk.CTkTextbox):
                data[field] = widget.get("1.0", "end-1c")
            else:
                data[field] = widget.get()
        if self.on_save:
            self.on_save(data)
        self.destroy()




class StatCard(ctk.CTkFrame):
    def __init__(self, master, label: str, value: str, icon: str, **kwargs):
        super().__init__(master, corner_radius=14, fg_color=_CARD,
                         border_width=1, border_color=_BORDER, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=icon, font=ctk.CTkFont(size=28)).grid(
            row=0, column=0, padx=20, pady=(20, 4), sticky="w"
        )
        ctk.CTkLabel(
            self, text=value,
            font=ctk.CTkFont(size=32, weight="bold"),
        ).grid(row=1, column=0, padx=20, sticky="w")
        ctk.CTkLabel(
            self, text=label,
            font=ctk.CTkFont(size=12),
            text_color=_TEXT_DIM,
        ).grid(row=2, column=0, padx=20, pady=(2, 20), sticky="w")



class AdminApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cortexia Admin Panel")
        self.geometry("1280x800")
        self.minsize(980, 640)
        self.configure(fg_color=_BG)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._current_admin: Dict[str, Any] = {}
        self._show_login()


    def _show_login(self):
        self.login_screen = LoginScreen(self, on_login_success=self._on_login_success)
        self.login_screen.grid(row=0, column=0, sticky="nsew")

    def _on_login_success(self, admin: Dict[str, Any]):
        self._current_admin = admin
        self.login_screen.destroy()
        self._build_main_ui()


    def _build_main_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(
            self, width=230, corner_radius=0,
            fg_color=_SIDEBAR, border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(12, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)

        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=20, pady=(28, 24), sticky="w")

        ctk.CTkLabel(
            brand_frame,
            text="Cortexia",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#ffffff",
        ).pack(side="left")
        ctk.CTkLabel(
            brand_frame,
            text=" Admin",
            font=ctk.CTkFont(size=22),
            text_color=_TEXT_DIM,
        ).pack(side="left")

        ctk.CTkFrame(self.sidebar, height=1, fg_color=_BORDER).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 12)
        )

        admin_frame = ctk.CTkFrame(self.sidebar, fg_color="#1e1e3a", corner_radius=10)
        admin_frame.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="ew")
        ctk.CTkLabel(
            admin_frame,
            text="●",
            font=ctk.CTkFont(size=10),
            text_color="#4ade80",
        ).grid(row=0, column=0, padx=(12, 4), pady=10)
        ctk.CTkLabel(
            admin_frame,
            text=self._current_admin.get("display_name", "Admin"),
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, padx=(0, 12), pady=10, sticky="w")

        self._nav_buttons: Dict[str, ctk.CTkButton] = {}

        nav_sections = [
            ("GENERAL", [
                ("📊  Dashboard",        "dashboard"),
                ("👥  Users",            "users"),
                ("🔐  Admin Accounts",   "admins"),
            ]),
            ("ACADEMICS", [
                ("🏫  Classes",          "classes"),
                ("📅  Timetable Slots",  "timetable"),
                ("🎓  Student Classes",  "student_classes"),
            ]),
            ("CONTENT & FINANCE", [
                ("📚  Knowledge Base",   "kb"),
                ("💰  Student Fees",     "fees"),
            ]),
        ]

        grid_row = 3
        for section_label, items in nav_sections:
            ctk.CTkLabel(
                self.sidebar,
                text=section_label,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=_TEXT_DIM,
                anchor="w",
            ).grid(row=grid_row, column=0, padx=20, pady=(14, 2), sticky="w")
            grid_row += 1

            for label, view in items:
                btn = ctk.CTkButton(
                    self.sidebar,
                    text=label,
                    anchor="w",
                    height=42,
                    corner_radius=10,
                    fg_color="transparent",
                    hover_color="#1e1e3a",
                    text_color="#c5c5e0",
                    font=ctk.CTkFont(size=13),
                    command=lambda v=view: self.select_frame(v),
                )
                btn.grid(row=grid_row, column=0, padx=12, pady=2, sticky="ew")
                self._nav_buttons[view] = btn
                grid_row += 1

        ctk.CTkButton(
            self.sidebar,
            text="Sign Out",
            anchor="w",
            height=42,
            corner_radius=10,
            fg_color="transparent",
            hover_color="#3a1a1a",
            text_color=_DANGER,
            font=ctk.CTkFont(size=13),
            command=self._sign_out,
        ).grid(row=13, column=0, padx=12, pady=(0, 24), sticky="sew")

        self.main_frame = ctk.CTkFrame(
            self, corner_radius=0, fg_color=_BG
        )
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        topbar = ctk.CTkFrame(
            self.main_frame, height=64,
            fg_color=_SIDEBAR, corner_radius=0,
        )
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_columnconfigure(0, weight=1)
        topbar.grid_propagate(False)

        self.header_label = ctk.CTkLabel(
            topbar, text="",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        )
        self.header_label.grid(row=0, column=0, padx=28, pady=18, sticky="w")

        self.add_btn = ctk.CTkButton(
            topbar,
            text="+ Add New",
            width=110,
            height=36,
            fg_color=_ACCENT,
            hover_color=_ACCENT_HO,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.add_item,
        )
        self.add_btn.grid(row=0, column=1, padx=20, pady=14)

        self.content_frame = ctk.CTkFrame(
            self.main_frame, fg_color="transparent"
        )
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=20)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.table = None
        self.current_view = None
        self._dashboard_frame = None

        self.select_frame("dashboard")


    def _sign_out(self):
        if messagebox.askyesno("Sign Out", "Are you sure you want to sign out?"):
            for widget in self.winfo_children():
                widget.destroy()
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=0)
            self._current_admin = {}
            self._show_login()


    def _set_active_nav(self, view: str):
        for v, btn in self._nav_buttons.items():
            if v == view:
                btn.configure(fg_color="#1e1e3a", text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color="#c5c5e0")

    def select_frame(self, view_name: str):
        self.current_view = view_name
        self._set_active_nav(view_name)

        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.table = None
        self._dashboard_frame = None

        self.add_btn.grid() if view_name != "dashboard" else self.add_btn.grid_remove()

        if view_name == "dashboard":
            self.header_label.configure(text="Dashboard")
            self._build_dashboard()
            return

        label_map = {
            "users":           "Users",
            "kb":              "Knowledge Base",
            "fees":            "Student Fees",
            "admins":          "Admin Accounts",
            "classes":         "Classes",
            "timetable":       "Timetable Slots",
            "student_classes": "Student Classes",
        }
        self.header_label.configure(text=label_map.get(view_name, view_name))

        columns = {
            "users":           ["id", "role", "name", "adm_no", "staff_id"],
            "kb":              ["id", "access_level", "category", "title"],
            "fees":            ["id", "adm_no", "total_fees", "paid_amount", "pending_amount", "due_date"],
            "admins":          ["id", "username", "display_name", "is_active", "last_login"],
            "classes":         ["id", "name", "section", "grade", "class_teacher"],
            "timetable":       ["id", "class_id", "subject", "day", "start_time", "end_time", "teacher"],
            "student_classes": ["id", "adm_no", "class_id", "academic_year", "roll_no"],
        }.get(view_name, [])

        self.table = DataTable(
            self.content_frame,
            columns=columns,
            on_edit=self.edit_item,
            on_delete=self.delete_item,
        )
        self.table.grid(row=0, column=0, sticky="nsew")
        self.refresh_data()


    def _build_dashboard(self):
        frame = ctk.CTkScrollableFrame(
            self.content_frame, fg_color="transparent"
        )
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self._dashboard_frame = frame

        ctk.CTkLabel(
            frame,
            text=f"Welcome back, {self._current_admin.get('display_name', 'Admin')} 👋",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=4, pady=(4, 20), sticky="w")

        try:
            n_users           = len(db_manager.get_users())
            n_kb              = len(db_manager.get_knowledge_items())
            n_fees            = len(db_manager.get_fees())
            n_admins          = len(db_manager.get_admins())
            n_classes         = len(db_manager.get_classes())
            n_timetable       = len(db_manager.get_timetable_slots())
            n_student_classes = len(db_manager.get_student_classes())
        except Exception:
            n_users = n_kb = n_fees = n_admins = "—"
            n_classes = n_timetable = n_student_classes = "—"

        stats_row1 = [
            ("Total Users",     str(n_users),   "👥"),
            ("Knowledge Items", str(n_kb),       "📚"),
            ("Fee Records",     str(n_fees),     "💰"),
            ("Admin Accounts",  str(n_admins),   "🔐"),
        ]
        for col, (label, value, icon) in enumerate(stats_row1):
            StatCard(frame, label=label, value=value, icon=icon).grid(
                row=1, column=col,
                padx=(0 if col == 0 else 12, 0),
                pady=(0, 12), sticky="ew",
            )

        stats_row2 = [
            ("Classes",          str(n_classes),         "🏫"),
            ("Timetable Slots",  str(n_timetable),       "📅"),
            ("Student Enrols",   str(n_student_classes), "🎓"),
        ]
        for col, (label, value, icon) in enumerate(stats_row2):
            StatCard(frame, label=label, value=value, icon=icon).grid(
                row=2, column=col,
                padx=(0 if col == 0 else 12, 0),
                pady=(0, 24), sticky="ew",
            )

        ctk.CTkLabel(
            frame,
            text="Quick Actions",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=_TEXT_DIM,
            anchor="w",
        ).grid(row=3, column=0, columnspan=4, pady=(0, 12), sticky="w")

        actions_frame = ctk.CTkFrame(frame, fg_color=_CARD, corner_radius=14,
                                     border_width=1, border_color=_BORDER)
        actions_frame.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(0, 24))
        actions_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        quick = [
            ("👥  Users",            "users"),
            ("📚  Knowledge Base",   "kb"),
            ("💰  Student Fees",     "fees"),
            ("🏫  Classes",          "classes"),
            ("📅  Timetable",        "timetable"),
            ("🎓  Student Classes",  "student_classes"),
            ("🔐  Admin Accounts",   "admins"),
        ]
        for col, (label, view) in enumerate(quick):
            ctk.CTkButton(
                actions_frame,
                text=label,
                height=52,
                anchor="w",
                fg_color="transparent",
                hover_color="#1e1e3a",
                font=ctk.CTkFont(size=13),
                corner_radius=0,
                command=lambda v=view: self.select_frame(v),
            ).grid(row=0, column=col, padx=4, pady=8, sticky="ew")

        ctk.CTkLabel(
            frame,
            text="School Info",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=_TEXT_DIM,
            anchor="w",
        ).grid(row=5, column=0, columnspan=4, pady=(0, 12), sticky="w")

        info_card = ctk.CTkFrame(frame, fg_color=_CARD, corner_radius=14,
                                 border_width=1, border_color=_BORDER)
        info_card.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(0, 8))
        info_card.grid_columnconfigure(1, weight=1)

        info_rows = [
            ("School",    "Demo Public School"),
            ("Platform",  "Cortexia HelpDesk"),
            ("Logged in", self._current_admin.get("display_name", "—")),
        ]
        for i, (key, val) in enumerate(info_rows):
            ctk.CTkLabel(
                info_card, text=key,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=_TEXT_DIM, anchor="w",
            ).grid(row=i, column=0, padx=24, pady=8, sticky="w")
            ctk.CTkLabel(
                info_card, text=val,
                font=ctk.CTkFont(size=13), anchor="w",
            ).grid(row=i, column=1, padx=24, pady=8, sticky="w")


    def refresh_data(self):
        if self.current_view == "dashboard":
            return
        try:
            fetchers = {
                "users":           db_manager.get_users,
                "kb":              db_manager.get_knowledge_items,
                "fees":            db_manager.get_fees,
                "admins":          db_manager.get_admins,
                "classes":         db_manager.get_classes,
                "timetable":       db_manager.get_timetable_slots,
                "student_classes": db_manager.get_student_classes,
            }
            data = fetchers[self.current_view]()
            self.table.set_data(data)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch data:\n{e}")


    def add_item(self):
        fields = self._get_fields_for_view()
        FormDialog(self, f"Add {self.current_view.replace('_', ' ').title()}",
                   fields, on_save=self._save_new_item)

    def edit_item(self, item: Dict[str, Any]):
        fields = self._get_fields_for_view()
        FormDialog(
            self,
            f"Edit {self.current_view.replace('_', ' ').title()}",
            fields,
            initial_data=item,
            on_save=lambda data: self._save_edited_item(item["id"], data),
        )

    def _get_fields_for_view(self) -> list[str]:
        return {
            "users":           ["role", "name", "adm_no", "staff_id"],
            "kb":              ["access_level", "category", "title", "content", "source"],
            "fees":            ["adm_no", "total_fees", "paid_amount", "pending_amount", "due_date"],
            "admins":          ["username", "display_name", "new_password", "is_active"],
            "classes":         ["name", "section", "grade", "class_teacher"],
            "timetable":       ["class_id", "subject", "day", "start_time", "end_time", "teacher"],
            "student_classes": ["adm_no", "class_id", "academic_year", "roll_no"],
        }.get(self.current_view, [])

    def _save_new_item(self, data: Dict[str, Any]):
        try:
            data = self._clean_data(data)
            if self.current_view == "users":
                db_manager.add_user(data)
            elif self.current_view == "kb":
                db_manager.add_knowledge_item(data)
            elif self.current_view == "fees":
                db_manager.add_fee(data)
            elif self.current_view == "admins":
                raw_pw = data.pop("new_password", "") or ""
                if not raw_pw:
                    messagebox.showerror("Error", "Password is required when creating a new admin.")
                    return
                data["password_hash"] = bcrypt.hashpw(
                    raw_pw.encode("utf-8"), bcrypt.gensalt(rounds=12)
                ).decode("utf-8")
                db_manager.add_admin(data)
            elif self.current_view == "classes":
                db_manager.add_class(data)
            elif self.current_view == "timetable":
                db_manager.add_timetable_slot(data)
            elif self.current_view == "student_classes":
                db_manager.add_student_class(data)
            self.refresh_data()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save item:\n{e}")

    def _save_edited_item(self, item_id: str, data: Dict[str, Any]):
        try:
            data = self._clean_data(data)
            if self.current_view == "users":
                db_manager.update_user(item_id, data)
            elif self.current_view == "kb":
                db_manager.update_knowledge_item(item_id, data)
            elif self.current_view == "fees":
                db_manager.update_fee(item_id, data)
            elif self.current_view == "admins":
                raw_pw = data.pop("new_password", "") or ""
                if raw_pw:
                    data["password_hash"] = bcrypt.hashpw(
                        raw_pw.encode("utf-8"), bcrypt.gensalt(rounds=12)
                    ).decode("utf-8")
                db_manager.update_admin(item_id, data)
            elif self.current_view == "classes":
                db_manager.update_class(item_id, data)
            elif self.current_view == "timetable":
                db_manager.update_timetable_slot(item_id, data)
            elif self.current_view == "student_classes":
                db_manager.update_student_class(item_id, data)
            self.refresh_data()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update item:\n{e}")

    def delete_item(self, item: Dict[str, Any]):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?"):
            try:
                deleters = {
                    "users":           db_manager.delete_user,
                    "kb":              db_manager.delete_knowledge_item,
                    "fees":            db_manager.delete_fee,
                    "admins":          db_manager.delete_admin,
                    "classes":         db_manager.delete_class,
                    "timetable":       db_manager.delete_timetable_slot,
                    "student_classes": db_manager.delete_student_class,
                }
                deleters[self.current_view](item["id"])
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete item:\n{e}")


    @staticmethod
    def _clean_data(data: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in data.items():
            if v == "":
                data[k] = None
        for num_field in ["total_fees", "paid_amount", "pending_amount"]:
            if num_field in data and data[num_field] is not None:
                try:
                    data[num_field] = float(data[num_field])
                except ValueError:
                    pass
        return data