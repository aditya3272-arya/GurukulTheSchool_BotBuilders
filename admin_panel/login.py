from __future__ import annotations

import bcrypt
import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
from typing import Callable
from pathlib import Path

from .database import db_manager

_LOGO_FILE = "logo.png"
_LOGO_DISPLAY_SIZE = (180, 60)   


def _load_logo() -> ctk.CTkImage | None:
    logo_path = Path(__file__).parent / _LOGO_FILE
    if not logo_path.exists():
        return None
    try:
        img = Image.open(logo_path)
        return ctk.CTkImage(light_image=img, dark_image=img, size=_LOGO_DISPLAY_SIZE)
    except Exception as e:
        print(f" Could not load logo: {e}")
        return None


class LoginScreen(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk, on_login_success: Callable):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.on_login_success = on_login_success
        self.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.configure(fg_color="#0f0f1a")

        card = ctk.CTkFrame(
            self,
            corner_radius=20,
            fg_color="#1a1a2e",
            border_width=1,
            border_color="#2e2e50",
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.grid_columnconfigure(0, weight=1)

        logo_img = _load_logo()
        if logo_img:
            ctk.CTkLabel(card, image=logo_img, text="").grid(
                row=0, column=0, pady=(40, 8)
            )
        else:
            ctk.CTkLabel(
                card,
                text="CORTEXIA",
                font=ctk.CTkFont(family="Georgia", size=30, weight="bold"),
                text_color="#7C6FFF",
            ).grid(row=0, column=0, pady=(40, 8))

        ctk.CTkLabel(
            card,
            text="Admin Panel",
            font=ctk.CTkFont(size=13),
            text_color="#6b6b8a",
        ).grid(row=1, column=0, pady=(0, 4))

        ctk.CTkLabel(
            card,
            text="Demo Public School",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9a8fff",
        ).grid(row=2, column=0, pady=(0, 32))

        ctk.CTkFrame(card, height=1, fg_color="#2e2e50", width=300).grid(
            row=3, column=0, padx=40, pady=(0, 28)
        )

        ctk.CTkLabel(
            card, text="USERNAME", anchor="w", width=300,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#6b6b8a",
        ).grid(row=4, column=0, padx=40, sticky="w")

        self.username_entry = ctk.CTkEntry(
            card,
            width=300,
            height=42,
            placeholder_text="Enter username",
            fg_color="#12122a",
            border_color="#2e2e50",
            border_width=1,
            corner_radius=8,
        )
        self.username_entry.grid(row=5, column=0, padx=40, pady=(6, 18))

        ctk.CTkLabel(
            card, text="PASSWORD", anchor="w", width=300,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#6b6b8a",
        ).grid(row=6, column=0, padx=40, sticky="w")

        self.password_entry = ctk.CTkEntry(
            card,
            width=300,
            height=42,
            placeholder_text="Enter password",
            show="●",
            fg_color="#12122a",
            border_color="#2e2e50",
            border_width=1,
            corner_radius=8,
        )
        self.password_entry.grid(row=7, column=0, padx=40, pady=(6, 8))
        self.password_entry.bind("<Return>", lambda _: self._attempt_login())

        self.error_label = ctk.CTkLabel(
            card, text="", text_color="#e05c5c",
            font=ctk.CTkFont(size=12), width=300,
        )
        self.error_label.grid(row=8, column=0, pady=(4, 8))

        self.login_btn = ctk.CTkButton(
            card,
            text="Sign In",
            width=300,
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#7C6FFF",
            hover_color="#6254cc",
            corner_radius=10,
            command=self._attempt_login,
        )
        self.login_btn.grid(row=9, column=0, padx=40, pady=(4, 40))

        self.username_entry.focus()

    def _attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self._show_error("Please enter both username and password.")
            return

        self.login_btn.configure(state="disabled", text="Verifying…")
        self.update()

        try:
            admin = db_manager.get_admin_by_username(username)

            if admin is None:
                self._show_error("Invalid username or password.")
                return

            if not admin.get("is_active"):
                self._show_error("This account has been deactivated.")
                return

            if not bcrypt.checkpw(
                password.encode("utf-8"),
                admin["password_hash"].encode("utf-8"),
            ):
                self._show_error("Invalid username or password.")
                return

            db_manager.update_admin_last_login(admin["id"])
            self.on_login_success(admin)

        except Exception as e:
            self._show_error("Connection error. Please try again.")
            print(f" Login error: {e}")
        finally:
            self.login_btn.configure(state="normal", text="Sign In")

    def _show_error(self, message: str):
        self.error_label.configure(text=message)
        self.login_btn.configure(state="normal", text="Sign In")