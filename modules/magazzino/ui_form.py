"""
PerilCar ERP - UI: Form Componente
Dialog per inserimento e modifica componente magazzino.
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from modules.magazzino.service import MagazzinoService

C_BG    = "#1a1a2e"
C_PANEL = "#16213e"
C_CARD  = "#0f3460"
C_ORANGE = "#e94c00"
C_ORANGE2 = "#ff6b35"
C_WHITE = "#f0f0f0"
C_GRAY  = "#8892a4"
C_GREEN = "#27ae60"
C_BLUE  = "#3a5bd9"


class FormComponenteDialog(ctk.CTkToplevel):
    def __init__(self, master, dati_esistenti: dict = None):
        super().__init__(master)
        self.svc = MagazzinoService()
        self.modifica = dati_esistenti is not None
        self.dati_esistenti = dati_esistenti or {}

        title = "Modifica Componente" if self.modifica else "Nuovo Componente"
        self.title(f"PerilCar — {title}")
        self.geometry("680x720")
        self.resizable(False, True)
        self.configure(fg_color=C_BG)
        self.grab_set()

        # Centra
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 680) // 2
        y = (self.winfo_screenheight() - 720) // 2
        self.geometry(f"680x720+{x}+{y}")

        self._vars: dict[str, tk.Variable] = {}
        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=C_PANEL, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr,
                     text="✏ Modifica componente" if self.modifica else "＋ Nuovo componente",
                     font=ctk.CTkFont("Helvetica", 16, "bold"),
                     text_color=C_WHITE).pack(side="left", padx=20, pady=12)

        # Scroll frame
        scroll = ctk.CTkScrollableFrame(self, fg_color=C_BG,
                                         scrollbar_button_color=C_CARD)
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # Grid 2 colonne
        scroll.grid_columnconfigure((0, 1), weight=1)

        campi = [
            ("Codice CMP *",    "codice",       0, 0, False),
            ("Nome articolo *", "nome",         0, 1, False),
            ("Descrizione",     "descrizione",  1, 0, False),
            ("Categoria",       "categoria",    1, 1, False),
            ("Marca",           "marca",        2, 0, False),
            ("Modello",         "modello",      2, 1, False),
            ("Cod. Modello",    "cod_modello",  3, 0, False),
            ("Colore",          "colore",       3, 1, False),
            ("Cilindrata",      "cilindrata",   4, 0, False),
            ("Carburante",      "carburante",   4, 1, False),
            ("Versione",        "versione",     5, 0, False),
            ("Intervallo",      "intervallo",   5, 1, False),
            ("Anno da",         "anno_da",      6, 0, False),
            ("Anno a",          "anno_a",       6, 1, False),
            ("Scorta minima",   "scorta_minima",7, 0, False),
            ("Prezzo acquisto", "prezzo_acquisto", 7, 1, False),
        ]

        for label, key, row, col, wide in campi:
            v = tk.StringVar(value=str(self.dati_esistenti.get(key, "") or ""))
            self._vars[key] = v

            frame = ctk.CTkFrame(scroll, fg_color="transparent")
            frame.grid(row=row, column=col, sticky="ew", padx=12, pady=4)

            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11),
                          text_color=C_GRAY, anchor="w").pack(fill="x")
            e = ctk.CTkEntry(frame, textvariable=v, height=36,
                              corner_radius=8, fg_color=C_CARD,
                              border_color=C_CARD, text_color=C_WHITE,
                              font=ctk.CTkFont(size=12))
            if key == "codice" and self.modifica:
                e.configure(state="disabled")
            e.pack(fill="x")

        # Note (wide)
        note_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        note_frame.grid(row=8, column=0, columnspan=2, sticky="ew", padx=12, pady=4)
        ctk.CTkLabel(note_frame, text="Note", font=ctk.CTkFont(size=11),
                      text_color=C_GRAY, anchor="w").pack(fill="x")
        self.txt_note = ctk.CTkTextbox(note_frame, height=80, corner_radius=8,
                                        fg_color=C_CARD, border_width=1,
                                        border_color="#1e3a5f",
                                        text_color=C_WHITE,
                                        font=ctk.CTkFont(size=12))
        note_val = self.dati_esistenti.get("nota", "") or ""
        self.txt_note.insert("1.0", note_val)
        self.txt_note.pack(fill="x")

        # ── Bottoni ──────────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color=C_PANEL, height=60)
        btn_frame.pack(fill="x", side="bottom")
        btn_frame.pack_propagate(False)

        ctk.CTkButton(btn_frame, text="Annulla", width=120, height=38,
                       corner_radius=8, fg_color=C_CARD, hover_color="#2a3a55",
                       font=ctk.CTkFont(size=13),
                       command=self.destroy).pack(side="right", padx=8, pady=10)

        ctk.CTkButton(btn_frame,
                       text="Salva modifiche" if self.modifica else "Crea componente",
                       width=160, height=38, corner_radius=8,
                       fg_color=C_ORANGE, hover_color=C_ORANGE2,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._salva).pack(side="right", padx=4, pady=10)

    def _salva(self):
        dati = {k: v.get().strip() for k, v in self._vars.items()}
        dati["nota"] = self.txt_note.get("1.0", "end").strip()

        # Conversioni numeriche
        for campo in ("anno_da", "anno_a", "scorta_minima"):
            val = dati.get(campo, "")
            dati[campo] = int(val) if val and val.isdigit() else None

        for campo in ("prezzo_acquisto",):
            val = dati.get(campo, "").replace(",", ".")
            try:
                dati[campo] = float(val)
            except ValueError:
                dati[campo] = 0.0

        if self.modifica:
            comp_id = self.dati_esistenti["componente_id"]
            ok, msg = self.svc.modifica_componente(comp_id, dati)
        else:
            ok, msg, _ = self.svc.crea_componente(dati)

        if ok:
            self.destroy()
        else:
            messagebox.showerror("Errore", msg, parent=self)
