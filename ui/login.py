"""
PerilCar ERP - UI: Login
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from core.auth import AuthManager

# Palette colori PerilCar
C_BG      = "#1a1a2e"
C_PANEL   = "#16213e"
C_CARD    = "#0f3460"
C_ORANGE  = "#e94c00"
C_ORANGE2 = "#ff6b35"
C_WHITE   = "#f0f0f0"
C_GRAY    = "#8892a4"
C_GREEN   = "#2ecc71"


class LoginWindow(ctk.CTk):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.auth = AuthManager()

        self.title("PerilCar — Accesso")
        self.geometry("480x580")
        self.resizable(False, False)
        self.configure(fg_color=C_BG)

        # Centra finestra
        self.update_idletasks()
        w, h = 480, 580
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        # Logo
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(pady=(60, 10))

        ctk.CTkLabel(logo_frame, text="PerilCar",
                     font=ctk.CTkFont("Georgia", 48, "bold"),
                     text_color=C_WHITE).pack()
        ctk.CTkLabel(logo_frame, text="Gestionale aziendale",
                     font=ctk.CTkFont("Georgia", 16, "italic"),
                     text_color=C_ORANGE).pack()

        # Card login
        card = ctk.CTkFrame(self, fg_color=C_PANEL, corner_radius=16,
                            border_width=1, border_color=C_CARD)
        card.pack(padx=50, pady=40, fill="x")

        ctk.CTkLabel(card, text="Accedi al sistema",
                     font=ctk.CTkFont("Helvetica", 14),
                     text_color=C_GRAY).pack(pady=(20, 16))

        # Username
        ctk.CTkLabel(card, text="Username", font=ctk.CTkFont(size=12),
                     text_color=C_WHITE, anchor="w").pack(padx=30, fill="x")
        self.entry_user = ctk.CTkEntry(card, height=42, corner_radius=8,
                                       fg_color=C_CARD, border_color=C_CARD,
                                       text_color=C_WHITE,
                                       font=ctk.CTkFont(size=13))
        self.entry_user.pack(padx=30, pady=(4, 12), fill="x")
        self.entry_user.insert(0, "admin")

        # Password
        ctk.CTkLabel(card, text="Password", font=ctk.CTkFont(size=12),
                     text_color=C_WHITE, anchor="w").pack(padx=30, fill="x")
        self.entry_pass = ctk.CTkEntry(card, height=42, corner_radius=8,
                                       show="●", fg_color=C_CARD,
                                       border_color=C_CARD, text_color=C_WHITE,
                                       font=ctk.CTkFont(size=13))
        self.entry_pass.pack(padx=30, pady=(4, 20), fill="x")
        self.entry_pass.insert(0, "admin123")
        self.entry_pass.bind("<Return>", lambda e: self._login())

        # Pulsante
        btn = ctk.CTkButton(card, text="ENTRA", height=44,
                             corner_radius=8, fg_color=C_ORANGE,
                             hover_color=C_ORANGE2,
                             font=ctk.CTkFont("Helvetica", 14, "bold"),
                             command=self._login)
        btn.pack(padx=30, pady=(0, 24), fill="x")

        self.lbl_err = ctk.CTkLabel(card, text="", text_color="#e74c3c",
                                     font=ctk.CTkFont(size=11))
        self.lbl_err.pack(pady=(0, 12))

        # Footer
        ctk.CTkLabel(self, text="Ing. Carmine Perillo",
                     font=ctk.CTkFont("Georgia", 11, "italic"),
                     text_color=C_GRAY).pack(side="bottom", pady=12)

    def _login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get()
        if not username or not password:
            self.lbl_err.configure(text="Inserisci username e password")
            return
        ok, msg = self.auth.login(username, password)
        if ok:
            self.destroy()
            self.on_success()
        else:
            self.lbl_err.configure(text=f"⚠ {msg}")
