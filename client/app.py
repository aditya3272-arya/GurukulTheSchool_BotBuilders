from __future__ import annotations

import threading
import tkinter as tk
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tkinter import messagebox, simpledialog
from typing import Any, Callable

import customtkinter as ctk
from PIL import Image

import httpx

from client.api_client import CortexiaApiClient
from client.config import ClientConfig, ROOT_DIR

_IST = timezone(timedelta(hours=5, minutes=30))


def _format_timestamp_ist(value: object) -> str:
    """Format API ISO timestamps in India Standard Time (IST)."""
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    normalized = s.replace("Z", "+00:00")
    dt: datetime | None = None
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        if len(s) >= 19:
            try:
                head = s[:19].replace("T", " ")
                dt = datetime.strptime(head, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                return s[:19].replace("T", " ")
    if dt is None:
        return s
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(_IST)
    return f"{local.strftime('%d %b %Y')}\n{local.strftime('%H:%M')} IST"


class CortexiaDesktopApp(ctk.CTk):
    def __init__(self, config: ClientConfig) -> None:
        super().__init__()
        self.config_data = config
        self.api = CortexiaApiClient(
            base_url=config.api_base_url,
            timeout=httpx.Timeout(
                connect=config.http_connect_timeout,
                read=config.http_read_timeout,
                write=60.0,
                pool=config.http_connect_timeout,
            ),
        )

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.colors = {
            "window_bg": "#F4F3FA",
            "panel_bg": "#FFFFFF",
            "panel_soft": "#F7F5FC",
            "panel_tint": "#EFEDFA",
            "text_primary": "#1E1B33",
            "text_muted": "#6B6588",
            "primary": "#7269E8",
            "primary_hover": "#5F56D4",
            "primary_soft": "#E8E4FA",
            "primary_muted_hover": "#DCD6F3",
            "accent": "#8B82FF",
            "border": "#D4D2EA",
            "danger": "#E4576B",
            "danger_hover": "#CC455A",
            "status_error": "#D83A56",
            "status_ok": "#6E6A8C",
            "chat_user": "#E4E0FA",
            "chat_assistant": "#F6F4FC",
            "chat_active": "#D4CEF5",
            "chat_idle": "#EEEBF8",
            "sidebar_bg": "#F9F8FC",
            "sidebar_border": "#C4BFE0",
        }

        self._pending_outbound: str | None = None

        self.title("Cortexia - School HelpDesk")
        self.geometry("1280x780")
        self.minsize(1240, 700)
        self.configure(fg_color=self.colors["window_bg"])
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.state_data: dict[str, Any] = {
            "role": "visitor",
            "me": None,
            "chats": [],
            "current_session_id": None,
        }

        self.assets = self._load_assets()
        self.frames: dict[str, ctk.CTkFrame] = {}
        self._build_ui()
        self.show_frame("intro")
        self._start_intro_splash()

    def _load_assets(self) -> dict[str, ctk.CTkImage]:
        logo = ROOT_DIR / "Logo.png"
        cortexia_logo = ROOT_DIR / "Cortexia Logo.png"
        round_logo = ROOT_DIR / "Round Logo.png"
        return {
            "logo": ctk.CTkImage(Image.open(logo), size=(44, 44)),
            "hero_logo": ctk.CTkImage(Image.open(cortexia_logo), size=(128, 128)),
            "intro_logo": ctk.CTkImage(Image.open(cortexia_logo), size=(360, 360)),
            "splash_logo": ctk.CTkImage(Image.open(cortexia_logo), size=(268, 268)),
            "round_logo": ctk.CTkImage(Image.open(round_logo), size=(96, 96)),
            "round_logo_above_card": ctk.CTkImage(Image.open(round_logo), size=(118, 118)),
            "round_logo_loader": ctk.CTkImage(Image.open(round_logo), size=(132, 132)),
        }

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=18, pady=18)

        self.frames["intro"] = self._build_intro_splash(container)
        self.frames["splash"] = self._build_splash(container)
        self.frames["loader"] = self._build_loader(container)
        self.frames["role"] = self._build_role(container)
        self.frames["dashboard"] = self._build_dashboard(container)

    def show_frame(self, frame_name: str) -> None:
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[frame_name].pack(fill="both", expand=True)

    def _build_intro_splash(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=self.colors["window_bg"])
        ctk.CTkLabel(frame, image=self.assets["intro_logo"], text="").place(relx=0.5, rely=0.42, anchor="center")

        progress_wrap = ctk.CTkFrame(frame, width=300, height=10, corner_radius=5, fg_color=self.colors["border"])
        progress_wrap.place(relx=0.5, rely=0.73, anchor="center")
        progress_wrap.pack_propagate(False)

        self.intro_progress = ctk.CTkProgressBar(
            progress_wrap,
            width=298,
            height=8,
            corner_radius=4,
            fg_color=self.colors["primary_soft"],
            progress_color=self.colors["accent"],
            border_width=0,
        )
        self.intro_progress.pack(padx=1, pady=1)
        self.intro_progress.set(0)
        return frame

    def _start_intro_splash(self) -> None:
        self._intro_tick = 0
        self._intro_total_ticks = 20   
        self._animate_intro_progress()

    def _animate_intro_progress(self) -> None:
        self._intro_tick += 1
        progress = min(1.0, self._intro_tick / self._intro_total_ticks)
        self.intro_progress.set(progress)
        if self._intro_tick >= self._intro_total_ticks:
            self.show_frame("splash")
            return
        self.after(100, self._animate_intro_progress)

    def _build_splash(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=self.colors["window_bg"])
        _splash_aura = 700
        _splash_card = 640
        aura = ctk.CTkFrame(
            frame,
            width=_splash_aura,
            height=_splash_aura,
            corner_radius=36,
            fg_color=self.colors["panel_tint"],
        )
        aura.place(relx=0.5, rely=0.5, anchor="center")
        aura.grid_propagate(False)

        card = ctk.CTkFrame(
            frame,
            width=_splash_card,
            height=_splash_card,
            corner_radius=28,
            fg_color=self.colors["panel_bg"],
            border_color=self.colors["border"],
            border_width=1,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.grid_propagate(False)
        card.pack_propagate(False)

        top_bar = ctk.CTkFrame(card, fg_color="transparent")
        top_bar.pack(fill="x", padx=48, pady=(22, 6))
        top_bar.grid_columnconfigure(0, weight=1)
        top_bar.grid_columnconfigure(1, weight=0)
        ctk.CTkLabel(
            top_bar,
            text="Smart School Intelligence",
            text_color=self.colors["accent"],
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))
        ctk.CTkLabel(
            top_bar,
            text="Powered by Cortexia",
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont("Segoe UI", 14),
        ).grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(card, image=self.assets["splash_logo"], text="").pack(pady=(18, 20))

        chip_row = ctk.CTkFrame(card, fg_color="transparent")
        chip_row.pack(pady=(8, 32))
        for chip in ("Visitor", "Student", "Staff"):
            ctk.CTkLabel(
                chip_row,
                text=f"  {chip}  ",
                fg_color=self.colors["primary_soft"],
                corner_radius=999,
                text_color=self.colors["text_primary"],
                font=ctk.CTkFont("Segoe UI", 14, "bold"),
            ).pack(side="left", padx=(0, 24))

        ctk.CTkButton(
            card,
            text="Enter Cortexia",
            command=lambda: self.show_frame("role"),
            width=280,
            height=44,
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"],
            text_color="#FFFFFF",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
        ).pack(pady=(24, 24))
        return frame

    def _build_loader(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=self.colors["window_bg"])
        box = ctk.CTkFrame(
            frame,
            width=700,
            height=460,
            corner_radius=28,
            fg_color=self.colors["panel_bg"],
            border_color=self.colors["sidebar_border"],
            border_width=1,
        )
        box.place(relx=0.5, rely=0.5, anchor="center")
        box.grid_propagate(False)

        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, image=self.assets["round_logo_loader"], text="").pack(pady=(0, 22))
        self.loader_text = ctk.CTkLabel(
            inner,
            text="Loading...",
            font=ctk.CTkFont("Segoe UI", 30, "bold"),
            text_color=self.colors["text_primary"],
            wraplength=560,
            justify="center",
        )

        self.loader_subtext = ctk.CTkLabel(
            inner,
            text="",
            font=ctk.CTkFont("Segoe UI", 18),
            text_color=self.colors["text_muted"],
            wraplength=580,
            justify="center",
        )
        self.loader_text.pack(pady=(0, 8))
        self.loader_subtext.pack(pady=(0, 0))
        return frame

    def _build_role(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=self.colors["window_bg"])
        stack = ctk.CTkFrame(frame, fg_color="transparent")
        stack.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(stack, image=self.assets["round_logo_above_card"], text="").pack(pady=(0, 28))

        panel = ctk.CTkFrame(
            stack,
            width=1080,
            height=600,
            corner_radius=22,
            fg_color=self.colors["panel_bg"],
            border_color=self.colors["border"],
            border_width=1,
        )
        panel.pack()
        panel.grid_propagate(False)

        inner = ctk.CTkFrame(panel, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=44, pady=(32, 36))


        ctk.CTkLabel(
            inner, text="Choose your role", font=ctk.CTkFont("Segoe UI", 36, "bold"), text_color=self.colors["text_primary"]
        ).pack(pady=(2, 10))
        ctk.CTkLabel(
            inner,
            text="Set your access level and verify your identity to continue.",
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont("Segoe UI", 17),
        ).pack(pady=(0, 16))
        role_row = ctk.CTkFrame(inner, fg_color="transparent")
        role_row.pack(pady=(2, 14))

        self.role_buttons: dict[str, ctk.CTkButton] = {}
        for role in ("visitor", "student", "staff"):
            button = ctk.CTkButton(
                role_row,
                text=role.title(),
                width=230,
                height=54,
                fg_color=self.colors["chat_idle"],
                hover_color=self.colors["chat_active"],
                text_color=self.colors["text_primary"],
                font=ctk.CTkFont("Segoe UI", 15, "bold"),
                command=lambda r=role: self._select_role(r),
            )
            button.pack(side="left", padx=12)
            self.role_buttons[role] = button

        form_area = ctk.CTkFrame(inner, fg_color="transparent")
        form_area.pack(pady=(6, 12))
        self.name_entry = ctk.CTkEntry(
            form_area,
            width=640,
            height=48,
            placeholder_text="Name",
            fg_color=self.colors["panel_soft"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont("Segoe UI", 15),
        )
        self.name_entry.pack(pady=8)
        self.adm_entry = ctk.CTkEntry(
            form_area,
            width=640,
            height=48,
            placeholder_text="Admission Number",
            fg_color=self.colors["panel_soft"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont("Segoe UI", 15),
        )
        self.staff_entry = ctk.CTkEntry(
            form_area,
            width=640,
            height=48,
            placeholder_text="Staff ID",
            fg_color=self.colors["panel_soft"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont("Segoe UI", 15),
        )
        self.adm_entry.pack_forget()
        self.staff_entry.pack_forget()

        ctk.CTkLabel(
            inner,
            text="Students need Name + Admission Number. Staff need Name + Staff ID.",
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont("Segoe UI", 14),
        ).pack(pady=(2, 14))

        ctk.CTkButton(
            inner,
            text="Enter Dashboard",
            width=260,
            height=50,
            command=self._on_login_continue,
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"],
            text_color="#FFFFFF",
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
        ).pack(pady=(2, 12))
        self.role_status = ctk.CTkLabel(inner, text="", text_color=self.colors["status_ok"])
        self.role_status.pack(pady=(10, 0))

        self._select_role("visitor")
        for w in (self.name_entry, self.adm_entry, self.staff_entry):
            for seq in ("<Return>", "<KP_Enter>"):
                w.bind(seq, lambda _e: (self._on_login_continue(), "break")[-1])
        return frame

    def _build_dashboard(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(
            frame,
            width=396,
            corner_radius=18,
            fg_color=self.colors["sidebar_bg"],
            border_color=self.colors["sidebar_border"],
            border_width=1,
        )
        sidebar.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        sidebar.grid_propagate(False)

        head = ctk.CTkFrame(sidebar, fg_color=self.colors["panel_tint"], corner_radius=12)
        head.pack(fill="x", padx=14, pady=(14, 8))
        ctk.CTkLabel(head, image=self.assets["logo"], text="").pack(side="left", padx=(0, 8))
        title_col = ctk.CTkFrame(head, fg_color="transparent")
        title_col.pack(side="left")
        ctk.CTkLabel(
            title_col, text="Cortexia", font=ctk.CTkFont("Segoe UI", 20, "bold"), text_color=self.colors["text_primary"]
        ).pack(anchor="w")
        self.school_badge = ctk.CTkLabel(title_col, text=self.config_data.school_name, text_color=self.colors["text_muted"])
        self.school_badge.pack(anchor="w")

        ctk.CTkButton(
            sidebar,
            text="✎  New chat",
            command=self._on_new_chat,
            height=40,
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"],
            text_color="#FFFFFF",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            corner_radius=10,
        ).pack(fill="x", padx=14, pady=(4, 10))
        self.chat_list = ctk.CTkScrollableFrame(sidebar, fg_color=self.colors["panel_soft"], corner_radius=12)
        self.chat_list.pack(fill="both", expand=True, padx=14, pady=4)

        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.pack(fill="x", padx=14, pady=(8, 14))
        self.profile_name = ctk.CTkLabel(
            bottom,
            text="Guest",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color=self.colors["text_primary"],
        )
        self.profile_name.pack(anchor="w", padx=(2, 0))
        self.profile_role = ctk.CTkLabel(
            bottom,
            text="Visitor",
            font=ctk.CTkFont("Segoe UI", 14),
            text_color=self.colors["text_muted"],
        )
        self.profile_role.pack(anchor="w", padx=(2, 0), pady=(4, 8))
        ctk.CTkButton(
            bottom,
            text="Raise Query",
            command=self._open_raise_query_dialog,
            fg_color=self.colors["primary_soft"],
            hover_color=self.colors["primary_muted_hover"],
            text_color=self.colors["text_primary"],
        ).pack(fill="x", pady=(0, 8))
        ctk.CTkButton(
            bottom,
            text="Feedback",
            command=self._open_feedback_dialog,
            fg_color=self.colors["primary_soft"],
            hover_color=self.colors["primary_muted_hover"],
            text_color=self.colors["text_primary"],
        ).pack(fill="x", pady=(0, 8))
        ctk.CTkButton(
            bottom,
            text="Sign Out",
            fg_color=self.colors["danger"],
            hover_color=self.colors["danger_hover"],
            command=self._on_sign_out,
            text_color="#FFFFFF",
        ).pack(fill="x")

        main = ctk.CTkFrame(frame, corner_radius=18, fg_color=self.colors["panel_bg"], border_color=self.colors["border"], border_width=1)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(main, fg_color=self.colors["panel_tint"], corner_radius=12)
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        self.chat_title = ctk.CTkLabel(top, text="New chat", font=ctk.CTkFont("Segoe UI", 24, "bold"), text_color=self.colors["text_primary"])
        self.chat_title.pack(anchor="w", padx=12, pady=(10, 0))
        self.chat_subtitle = ctk.CTkLabel(
            top,
            text="Ask anything within your role access. Cortexia will respond with contextual detail.",
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont("Segoe UI", 12),
        )
        self.chat_subtitle.pack(anchor="w", padx=12, pady=(2, 10))

        self.messages_view = ctk.CTkScrollableFrame(main, fg_color=self.colors["panel_soft"], corner_radius=14)
        self.messages_view.grid(row=1, column=0, sticky="nsew", padx=16, pady=(2, 8))

        self.follow_up_row = ctk.CTkFrame(main, fg_color="transparent")
        self.follow_up_row.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 6))

        composer = ctk.CTkFrame(main, fg_color="transparent")
        composer.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))
        composer.grid_columnconfigure(0, weight=1)
        self.message_entry = ctk.CTkEntry(
            composer,
            placeholder_text="Ask Cortexia...",
            fg_color="#FFFFFF",
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
        )
        self.message_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.message_entry.bind("<Return>", lambda _: self._on_send_message())
        ctk.CTkButton(
            composer,
            text="Send",
            width=110,
            command=self._on_send_message,
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"],
            text_color="#FFFFFF",
        ).grid(row=0, column=1)

        self.chat_status = ctk.CTkLabel(main, text="", text_color=self.colors["status_ok"])
        self.chat_status.grid(row=4, column=0, sticky="w", padx=16, pady=(0, 12))
        return frame

    def _start_thinking_animation(self) -> None:
        self._thinking_active = True
        self._thinking_tick = 0
        self._animate_thinking()

    def _animate_thinking(self) -> None:
        if not getattr(self, "_thinking_active", False):
            return
        dots = "●" * ((self._thinking_tick % 3) + 1) + "○" * (2 - (self._thinking_tick % 3))
        self._set_status("chat", f"Cortexia is thinking  {dots}")
        self._thinking_tick += 1
        self.after(400, self._animate_thinking)

    def _stop_thinking_animation(self) -> None:
        self._thinking_active = False
        self._set_status("chat", "")

    def _set_status(self, key: str, text: str, error: bool = False) -> None:
        color = self.colors["status_error"] if error else self.colors["status_ok"]
        target = {
            "school": getattr(self, "school_status", None),
            "role": getattr(self, "role_status", None),
            "chat": getattr(self, "chat_status", None),
        }.get(key)
        if target is not None:
            target.configure(text=text, text_color=color)

    def _show_loader(self, text: str) -> None:
        self.loader_text.configure(text=text)
        if "dashboard" in text.lower():
            self.loader_subtext.configure(text="Setting up your chat workspace.")
        else:
            self.loader_subtext.configure(text="Preparing secure sign-in.")
        self.show_frame("loader")

    def _run_job(
        self,
        target: Callable[[], Any],
        on_success: Callable[[Any], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        def runner() -> None:
            try:
                result = target()
                if on_success:
                    self.after(0, lambda r=result: on_success(r))
            except Exception as exc:
                if on_error:
                    self.after(0, lambda e=exc: on_error(e))
                else:
                    self.after(0, lambda e=exc: messagebox.showerror("Error", str(e)))

        threading.Thread(target=runner, daemon=True).start()

    def _select_role(self, role: str) -> None:
        self.state_data["role"] = role
        self._set_status("role", "")
        for item_role, button in self.role_buttons.items():
            button.configure(
                fg_color=self.colors["primary"] if item_role == role else self.colors["chat_idle"],
                hover_color=self.colors["primary_hover"] if item_role == role else self.colors["chat_active"],
                text_color="#FFFFFF" if item_role == role else self.colors["text_primary"],
            )
        if role == "student":
            self.adm_entry.pack(pady=8)
            self.staff_entry.pack_forget()
        elif role == "staff":
            self.staff_entry.pack(pady=8)
            self.adm_entry.pack_forget()
        else:
            self.adm_entry.pack_forget()
            self.staff_entry.pack_forget()

    def _on_login_continue(self) -> None:
        role = self.state_data["role"]
        name = self.name_entry.get().strip() or None
        adm_no = self.adm_entry.get().strip() or None
        staff_id = self.staff_entry.get().strip() or None

        if role == "student" and (not name or not adm_no):
            self._set_status("role", "Student login needs name and admission number.", error=True)
            return
        if role == "staff" and (not name or not staff_id):
            self._set_status("role", "Staff login needs name and staff ID.", error=True)
            return

        self._set_status("role", "Signing in...")
        self._run_job(
            target=lambda: self.api.login(
                role=role,
                name=name,
                adm_no=adm_no,
                staff_id=staff_id,
            ),
            on_success=lambda _: self._after_login_success(),
            on_error=lambda exc: self._set_status("role", str(exc), error=True),
        )

    def _after_login_success(self) -> None:
        self._show_loader("Loading dashboard")
        self._run_job(
            target=self.api.me,
            on_success=self._set_me_and_dashboard,
            on_error=lambda exc: messagebox.showerror("Login error", str(exc)),
        )

    def _set_me_and_dashboard(self, me_data: dict[str, Any]) -> None:
        self.state_data["me"] = me_data
        self.profile_name.configure(text=me_data.get("name", "User"))
        self.profile_role.configure(text=str(me_data.get("role", "visitor")).replace("_", " ").title())
        self.after(self.config_data.dashboard_loader_delay_ms, self._open_dashboard_and_load_chats)

    def _open_dashboard_and_load_chats(self) -> None:
        self.show_frame("dashboard")
        self._run_job(target=self.api.list_chats, on_success=self._after_list_chats, on_error=self._chat_error)

    def _chat_error(self, exc: Exception) -> None:
        self._stop_thinking_animation()
        self._set_status("chat", str(exc), error=True)

    def _after_list_chats(self, chats: list[dict[str, Any]]) -> None:
        self.state_data["chats"] = chats
        self._render_chat_list()
        if chats:
            self._open_chat(chats[0]["id"])
        else:
            self._on_new_chat()

    def _clear_children(self, widget: ctk.CTkBaseClass) -> None:
        for child in widget.winfo_children():
            child.destroy()

    def _render_chat_list(self) -> None:
        self._clear_children(self.chat_list)
        current_id = self.state_data.get("current_session_id")
        for chat in self.state_data["chats"]:
            card = ctk.CTkFrame(
                self.chat_list,
                fg_color=self.colors["chat_active"] if chat["id"] == current_id else self.colors["chat_idle"],
                corner_radius=10,
                border_color=self.colors["border"],
                border_width=1,
            )

            card.pack(fill="x", pady=5, padx=(2, 8))
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=(10, 8), pady=(8, 4))
            ctk.CTkButton(
                top,
                text=str(chat.get("title", "Chat")),
                fg_color="transparent",
                hover=False,
                anchor="w",
                text_color=self.colors["text_primary"],
                command=lambda cid=chat["id"]: self._open_chat(cid),
            ).pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                top,
                text="✎",
                width=34,
                height=30,
                corner_radius=8,
                fg_color=self.colors["primary_soft"],
                hover_color=self.colors["primary_muted_hover"],
                text_color=self.colors["primary"],
                font=ctk.CTkFont("Segoe UI", 16),
                command=lambda c=chat: self._rename_chat(c),
            ).pack(side="left", padx=(4, 2))
            ctk.CTkButton(
                top,
                text="Del",
                width=44,
                fg_color=self.colors["danger"],
                hover_color=self.colors["danger_hover"],
                text_color="#FFFFFF",
                command=lambda c=chat: self._delete_chat(c),
            ).pack(side="left")
            time_text = _format_timestamp_ist(chat.get("updated_at"))
            time_row = ctk.CTkFrame(card, fg_color="transparent")
            time_row.pack(fill="x", padx=(10, 12), pady=(0, 8))
            ctk.CTkLabel(
                time_row,
                text=f"Updated {time_text}" if time_text else "Updated —",
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=self.colors["text_muted"],
                wraplength=268,
                justify="left",
                anchor="w",
            ).pack(anchor="w", fill="x", padx=(4, 4))

    def _open_chat(self, session_id: str, *, after_load: Callable[[], None] | None = None) -> None:
        self.state_data["current_session_id"] = session_id
        self._render_chat_list()

        def on_messages(messages: list[dict[str, Any]]) -> None:
            self._render_messages(messages, session_id)
            if after_load:
                after_load()

        self._run_job(
            target=lambda: self.api.list_messages(session_id),
            on_success=on_messages,
            on_error=self._chat_error,
        )

    def _render_messages(self, messages: list[dict[str, Any]], session_id: str) -> None:
        if self.state_data.get("current_session_id") != session_id:
            return
        self._clear_children(self.messages_view)
        for msg in messages:
            role = msg.get("role", "assistant")
            content = str(msg.get("content", ""))
            bubble = ctk.CTkFrame(
                self.messages_view,
                fg_color=self.colors["chat_user"] if role == "user" else self.colors["chat_assistant"],
                corner_radius=12,
                border_color=self.colors["border"],
                border_width=1,
            )
            bubble.pack(anchor="e" if role == "user" else "w", pady=6, padx=6, fill="x")
            ctk.CTkLabel(
                bubble,
                text="You" if role == "user" else "Cortexia",
                text_color=self.colors["text_muted"],
                font=ctk.CTkFont("Segoe UI", 11, "bold"),
            ).pack(anchor="w", padx=10, pady=(8, 0))
            ctk.CTkLabel(bubble, text=content, justify="left", wraplength=650, text_color=self.colors["text_primary"]).pack(
                anchor="w", padx=10, pady=8
            )

        chat_title = "Chat"
        for chat in self.state_data["chats"]:
            if chat["id"] == session_id:
                chat_title = str(chat.get("title", "Chat"))
                break
        self.chat_title.configure(text=chat_title)
        self._clear_children(self.follow_up_row)

    def _on_new_chat(self) -> None:
        self._run_job(target=self.api.create_chat, on_success=self._after_new_chat, on_error=self._chat_error)

    def _after_new_chat(self, created: dict[str, Any]) -> None:
        session_id = str(created["id"])
        self.state_data["current_session_id"] = session_id
        self._run_job(target=self.api.list_chats, on_success=lambda chats: self._after_list_chats_focus(chats, session_id), on_error=self._chat_error)

    def _after_list_chats_focus(self, chats: list[dict[str, Any]], session_id: str) -> None:
        self.state_data["chats"] = chats
        self._render_chat_list()
        pending = self._pending_outbound
        if pending:
            self._pending_outbound = None
            self._open_chat(session_id, after_load=lambda p=pending: self._send_message_text(p))
        else:
            self._open_chat(session_id)

    def _rename_chat(self, chat: dict[str, Any]) -> None:
        new_name = simpledialog.askstring("Rename chat", "New chat title:", initialvalue=str(chat.get("title", "")))
        if not new_name:
            return
        self._run_job(
            target=lambda: self.api.rename_chat(chat["id"], new_name.strip()),
            on_success=lambda _: self._run_job(self.api.list_chats, on_success=self._after_rename_refresh, on_error=self._chat_error),
            on_error=self._chat_error,
        )

    def _after_rename_refresh(self, chats: list[dict[str, Any]]) -> None:
        current = self.state_data.get("current_session_id")
        self.state_data["chats"] = chats
        self._render_chat_list()
        if current:
            self._open_chat(current)

    def _delete_chat(self, chat: dict[str, Any]) -> None:
        if not messagebox.askyesno("Delete chat", "Delete this chat permanently?"):
            return
        self._run_job(
            target=lambda: self.api.delete_chat(chat["id"]),
            on_success=lambda _: self._run_job(self.api.list_chats, on_success=self._after_delete_refresh, on_error=self._chat_error),
            on_error=self._chat_error,
        )

    def _after_delete_refresh(self, chats: list[dict[str, Any]]) -> None:
        self.state_data["chats"] = chats
        if not chats:
            self._on_new_chat()
            return
        self._open_chat(chats[0]["id"])

    def _on_send_message(self) -> None:
        message = self.message_entry.get().strip()
        if not message:
            return
        self.message_entry.delete(0, tk.END)
        self._send_message_text(message)

    def _send_message_text(self, message: str) -> None:
        text = message.strip()
        if not text:
            return
        session_id = self.state_data.get("current_session_id")
        if not session_id:
            self._pending_outbound = text
            self._on_new_chat()
            return
        self._append_local_message("user", text)
        self._start_thinking_animation()
        self._run_job(
            target=lambda sid=session_id, msg=text: self.api.chat_turn(session_id=sid, message=msg),
            on_success=self._after_chat_turn,
            on_error=self._chat_error,
        )

    def _append_local_message(self, role: str, text: str) -> None:
        bubble = ctk.CTkFrame(
            self.messages_view,
            fg_color=self.colors["chat_user"] if role == "user" else self.colors["chat_assistant"],
            corner_radius=12,
            border_color=self.colors["border"],
            border_width=1,
        )
        bubble.pack(anchor="e" if role == "user" else "w", pady=6, padx=6, fill="x")
        ctk.CTkLabel(
            bubble,
            text="You" if role == "user" else "Cortexia",
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=10, pady=(8, 0))
        ctk.CTkLabel(bubble, text=text, justify="left", wraplength=650, text_color=self.colors["text_primary"]).pack(
            anchor="w", padx=10, pady=8
        )

    def _after_chat_turn(self, out: dict[str, Any]) -> None:
        self._append_local_message("assistant", str(out.get("answer", "No response generated.")))
        self._stop_thinking_animation()
        self._render_follow_ups(out.get("follow_ups") or [])
        self._run_job(target=self.api.list_chats, on_success=self._refresh_chats_only, on_error=self._chat_error)

    def _refresh_chats_only(self, chats: list[dict[str, Any]]) -> None:
        self.state_data["chats"] = chats
        self._render_chat_list()

    def _render_follow_ups(self, items: list[str]) -> None:
        self._clear_children(self.follow_up_row)
        for text in items[:3]:
            ctk.CTkButton(
                self.follow_up_row,
                text=text,
                height=32,
                command=lambda t=text: self._send_follow_up(t),
                fg_color=self.colors["panel_bg"],
                hover_color=self.colors["primary_muted_hover"],
                text_color=self.colors["text_primary"],
                border_width=1,
                border_color=self.colors["border"],
                corner_radius=10,
                font=ctk.CTkFont("Segoe UI", 12),
            ).pack(side="left", padx=(0, 8), pady=3)

    def _send_follow_up(self, text: str) -> None:
        self._send_message_text(text.strip())

    def _open_raise_query_dialog(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Raise Query")
        dialog.geometry("520x400")
        dialog.grab_set()
        dialog.configure(fg_color=self.colors["panel_bg"])

        ctk.CTkLabel(
            dialog, text="Raise a Query", font=ctk.CTkFont("Segoe UI", 24, "bold"), text_color=self.colors["text_primary"]
        ).pack(pady=(16, 12))
        name = ctk.CTkEntry(
            dialog,
            width=420,
            placeholder_text="Your Name (Required)",
            fg_color=self.colors["panel_soft"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
        )
        name.pack(pady=8)
        email = ctk.CTkEntry(
            dialog,
            width=420,
            placeholder_text="Your Email ID (Required)",
            fg_color=self.colors["panel_soft"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
        )
        email.pack(pady=8)
        message = ctk.CTkTextbox(
            dialog,
            width=420,
            height=140,
            fg_color=self.colors["panel_soft"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
        )
        message.pack(pady=8)
        status = ctk.CTkLabel(dialog, text="", text_color=self.colors["status_ok"])
        status.pack(pady=(0, 8))

        def submit_query() -> None:
            name_val = name.get().strip()
            email_val = email.get().strip()
            body_val = message.get("1.0", tk.END).strip()
            
            if not name_val or not email_val or not body_val:
                status.configure(text="All fields are required.", text_color=self.colors["status_error"])
                return
            
            payload = {
                "name": name_val,
                "email": email_val,
                "message": body_val,
                "school": (self.state_data.get("school") or {}).get("name", ""),
                "role": (self.state_data.get("me") or {}).get("role", ""),
            }
            status.configure(text="Submitting query...", text_color=self.colors["status_ok"])
            self._run_job(
                target=lambda: self.api.submit_feedback(self.config_data.formspree_query_endpoint, payload),
                on_success=lambda _: status.configure(text="Query submitted. We will contact you soon.", text_color="#2E9154"),
                on_error=lambda exc: status.configure(text=str(exc), text_color=self.colors["status_error"]),
            )

        ctk.CTkButton(
            dialog,
            text="Submit Query",
            width=180,
            command=submit_query,
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"],
            text_color="#FFFFFF",
        ).pack(pady=8)

    def _open_feedback_dialog(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Feedback")
        dialog.geometry("520x380")
        dialog.grab_set()
        dialog.configure(fg_color=self.colors["panel_bg"])

        ctk.CTkLabel(
            dialog, text="Share Feedback", font=ctk.CTkFont("Segoe UI", 24, "bold"), text_color=self.colors["text_primary"]
        ).pack(pady=(16, 12))
        category = ctk.CTkComboBox(
            dialog,
            values=["General", "UI", "Response Quality", "Bug"],
            width=260,
            fg_color=self.colors["panel_soft"],
            border_color=self.colors["border"],
            button_color=self.colors["primary"],
            button_hover_color=self.colors["primary_hover"],
            text_color=self.colors["text_primary"],
        )
        category.set("General")
        category.pack(pady=8)
        email = ctk.CTkEntry(
            dialog,
            width=420,
            placeholder_text="Optional email",
            fg_color=self.colors["panel_soft"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
        )
        email.pack(pady=8)
        message = ctk.CTkTextbox(
            dialog,
            width=420,
            height=140,
            fg_color=self.colors["panel_soft"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
        )
        message.pack(pady=8)
        status = ctk.CTkLabel(dialog, text="", text_color=self.colors["status_ok"])
        status.pack(pady=(0, 8))

        def submit_feedback() -> None:
            body = message.get("1.0", tk.END).strip()
            if not body:
                status.configure(text="Feedback message is required.", text_color=self.colors["status_error"])
                return
            payload = {
                "category": category.get(),
                "email": email.get().strip(),
                "message": body,
                "school": (self.state_data.get("school") or {}).get("name", ""),
                "role": (self.state_data.get("me") or {}).get("role", ""),
                "user": (self.state_data.get("me") or {}).get("name", ""),
            }
            status.configure(text="Submitting...")
            self._run_job(
                target=lambda: self.api.submit_feedback(self.config_data.formspree_endpoint, payload),
                on_success=lambda _: status.configure(text="Feedback submitted. Thank you.", text_color="#2E9154"),
                on_error=lambda exc: status.configure(text=str(exc), text_color=self.colors["status_error"]),
            )

        ctk.CTkButton(
            dialog,
            text="Submit",
            width=180,
            command=submit_feedback,
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"],
            text_color="#FFFFFF",
        ).pack(pady=8)

    def _on_sign_out(self) -> None:
        self._run_job(target=self.api.logout, on_success=lambda _: self._after_sign_out(), on_error=self._chat_error)

    def _after_sign_out(self) -> None:
        self._pending_outbound = None
        self.state_data.update({"me": None, "chats": [], "current_session_id": None, "role": "visitor"})
        self.name_entry.delete(0, tk.END)
        self.adm_entry.delete(0, tk.END)
        self.staff_entry.delete(0, tk.END)
        self.show_frame("role")

    def on_close(self) -> None:
        try:
            self.api.close()
        finally:
            self.destroy()
