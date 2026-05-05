"""
PerilCar ERP - UI: Dashboard Principale
Layout: Logo in alto, 3 box (Demolizioni / Personale / Magazzino) + box Shop largo in basso.
Esattamente come il design Canva.
"""

import tkinter as tk
import customtkinter as ctk
from core.auth import AuthManager

C_BG      = "#1a1a2e"
C_PANEL   = "#16213e"
C_CARD    = "#1e3a5f"
C_CARD_HV = "#2a4a70"
C_ORANGE  = "#e94c00"
C_ORANGE2 = "#ff6b35"
C_WHITE   = "#f0f0f0"
C_GRAY    = "#8892a4"
C_DISABLED = "#3a3a4a"
C_DIS_TXT  = "#666677"


class Dashboard(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.auth = AuthManager()

        self.title("PerilCar — Gestionale aziendale")
        self.geometry("1100x680")
        self.minsize(900, 600)
        self.configure(fg_color=C_BG)

        # Centra
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 1100) // 2
        y = (self.winfo_screenheight() - 680)  // 2
        self.geometry(f"1100x680+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()

    def _build_ui(self):
        # ── TOP BAR ──────────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color=C_PANEL, height=56)
        top.pack(fill="x", side="top")
        top.pack_propagate(False)

        ctk.CTkLabel(top, text="PerilCar",
                     font=ctk.CTkFont("Georgia", 20, "bold"),
                     text_color=C_WHITE).pack(side="left", padx=20)
        ctk.CTkLabel(top, text="Gestionale aziendale",
                     font=ctk.CTkFont("Georgia", 12, "italic"),
                     text_color=C_ORANGE).pack(side="left", padx=4)

        # Utente + logout (destra)
        user_lbl = ctk.CTkLabel(top,
            text=f"👤 {self.auth.get_username()}",
            font=ctk.CTkFont(size=12), text_color=C_GRAY)
        user_lbl.pack(side="right", padx=8)

        btn_logout = ctk.CTkButton(top, text="Esci", width=70, height=30,
                                    fg_color=C_CARD, hover_color="#c0392b",
                                    font=ctk.CTkFont(size=12),
                                    command=self._logout)
        btn_logout.pack(side="right", padx=16)

        # ── CENTRO: LOGO ─────────────────────────────────────────────────────
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(pady=(40, 20))

        ctk.CTkLabel(logo_frame, text="PerilCar",
                     font=ctk.CTkFont("Georgia", 64, "bold"),
                     text_color=C_WHITE).pack()
        ctk.CTkLabel(logo_frame, text="Gestionale aziendale",
                     font=ctk.CTkFont("Georgia", 20, "italic"),
                     text_color=C_ORANGE).pack()

        # ── GRIGLIA MODULI ────────────────────────────────────────────────────
        modules_frame = ctk.CTkFrame(self, fg_color="transparent")
        modules_frame.pack(expand=True, fill="both", padx=80, pady=20)

        # Riga 1: Demolizioni | Personale | Magazzino
        row1 = ctk.CTkFrame(modules_frame, fg_color="transparent")
        row1.pack(fill="x", expand=True)

        self._module_card(row1, "Demolizioni", "🔧",
                          "Gestione veicoli\ne demolizioni",
                          disabled=True).pack(side="left", expand=True,
                                               fill="both", padx=8, pady=8)

        self._module_card(row1, "Personale", "👷",
                          "Operai e\nturnazione",
                          disabled=True).pack(side="left", expand=True,
                                               fill="both", padx=8, pady=8)

        self._module_card(row1, "Magazzino", "📦",
                          "Ricambi e\ncomponenti",
                          command=self._apri_magazzino).pack(
                              side="left", expand=True,
                              fill="both", padx=8, pady=8)

        # Riga 2: Shop (largo)
        row2 = ctk.CTkFrame(modules_frame, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 8))

        self._module_card(row2, "Shop", "🛒",
                          "Vendita online e listino prezzi",
                          wide=True, disabled=True).pack(
                              fill="x", padx=8, pady=0)

        # Footer
        ctk.CTkLabel(self,
                     text="Ing. Carmine Perillo  •  PerilCar v1.0.0",
                     font=ctk.CTkFont("Georgia", 10, "italic"),
                     text_color=C_GRAY).pack(side="bottom", pady=8)

    def _module_card(self, parent, title: str, icon: str, subtitle: str,
                     command=None, disabled=False, wide=False) -> ctk.CTkFrame:
        """Crea un box modulo (stile card)."""
        if disabled:
            fg = C_DISABLED
            lbl_color = C_DIS_TXT
            hover = C_DISABLED
        else:
            fg = C_CARD
            lbl_color = C_WHITE
            hover = C_CARD_HV

        h = 100 if wide else 160

        btn = ctk.CTkButton(
            parent,
            text=f"{icon}  {title}",
            height=h,
            corner_radius=14,
            fg_color=fg,
            hover_color=hover,
            font=ctk.CTkFont("Helvetica", 28 if not wide else 32, "bold"),
            text_color=lbl_color,
            command=(command if not disabled else None),
            border_width=1,
            border_color="#2a3a55" if not disabled else "#333344"
        )
        # Subtitle
        # CustomTkinter non supporta subtitle nativo, lo aggiungiamo via frame
        frame = ctk.CTkFrame(parent, fg_color=fg, corner_radius=14,
                              border_width=1,
                              border_color="#2a3a55" if not disabled else "#333344")
        frame.configure(height=h)

        # Usa Button nel frame
        inner_btn = ctk.CTkButton(
            frame,
            text=f"{icon}  {title}",
            height=h - 30,
            corner_radius=0,
            fg_color="transparent",
            hover_color=hover if not disabled else fg,
            font=ctk.CTkFont("Helvetica", 28 if not wide else 32, "bold"),
            text_color=lbl_color,
            command=(command if not disabled else None),
        )
        inner_btn.pack(fill="both", expand=True)

        sub = ctk.CTkLabel(frame, text=subtitle,
                            font=ctk.CTkFont("Helvetica", 11),
                            text_color=C_GRAY,
                            justify="center")
        sub.pack(pady=(0, 8))

        if disabled:
            badge = ctk.CTkLabel(frame, text="Prossimamente",
                                  font=ctk.CTkFont(size=9),
                                  text_color="#555566",
                                  fg_color="#222233",
                                  corner_radius=4)
            badge.pack(pady=(0, 6))

        return frame

    def _apri_magazzino(self):
        from modules.magazzino.ui_magazzino import MagazzinoWindow
        win = MagazzinoWindow(self)
        win.grab_set()

    def _logout(self):
        self.auth.logout()
        self.destroy()
        from ui.login import LoginWindow
        def restart():
            dash = Dashboard()
            dash.mainloop()
        login = LoginWindow(on_success=restart)
        login.mainloop()

    def _on_close(self):
        self.auth.logout()
        self.destroy()
        import sys
        sys.exit(0)
