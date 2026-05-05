"""
PerilCar ERP - UI: Modulo Magazzino
Layout ESATTO dal design Canva:
- Sinistra: tabella con colonne CMP, Articolo, Descrizione, ES, Scorta, NA,
            Marca, Modello, Cod.Modello, Nota, Colore, Cilindrata,
            Carburante, Versione, Anno, Intervallo, Immagini
            + icona lente di ricerca in cella
- Top sinistra: bottoni "Resoconto" (blu) e "Pubblica" (blu)
- Back button "<" in alto a sinistra
- Destra: pannello con filtri Esistenza/Scorta (pill colorate + Applica viola),
          box Note, sezione Articolo (2 campi), Carico/Scarico (arancio/verde),
          bottoni Carico / Scarico / Conferma
"""

import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
import threading
from modules.magazzino.service import MagazzinoService
from modules.magazzino.ui_form import FormComponenteDialog
from modules.magazzino.ui_storico import StoricoDialog

# ─── Palette ─────────────────────────────────────────────────────────────────
C_BG        = "#1a1a2e"
C_PANEL     = "#16213e"
C_CARD      = "#0f3460"
C_ORANGE    = "#e94c00"
C_ORANGE2   = "#ff6b35"
C_GREEN     = "#27ae60"
C_GREEN2    = "#2ecc71"
C_BLUE      = "#3a5bd9"
C_BLUE2     = "#5a7bf0"
C_PURPLE    = "#8b5cf6"
C_PURPLE2   = "#a78bfa"
C_YELLOW    = "#f1c40f"
C_YELLOW2   = "#f39c12"
C_PINK      = "#d4a5e0"
C_WHITE     = "#f0f0f0"
C_GRAY      = "#8892a4"
C_TABLE_BG  = "#0d1b2e"
C_TABLE_ROW = "#111d30"
C_TABLE_ALT = "#0f2240"
C_TABLE_SEL = "#1e3a6e"
C_TABLE_HDR = "#0a1628"

# Colonne tabella (label display, chiave dati, larghezza)
COLONNE = [
    ("CMP",         "cmp",          70),
    ("Articolo",    "articolo",     130),
    ("Descrizione", "descrizione",  160),
    ("ES",          "esistenza",    50),
    ("Scorta",      "scorta",       60),
    ("NA",          "na",           50),
    ("Marca",       "marca",        90),
    ("Modello",     "modello",      90),
    ("Cod.Modello", "cod_modello",  90),
    ("Nota",        "nota",         90),
    ("Colore",      "colore",       70),
    ("Cilindrata",  "cilindrata",   80),
    ("Carburante",  "carburante",   80),
    ("Versione",    "versione",     70),
    ("Anno",        "anno",         60),
    ("Intervallo",  "intervallo",   80),
    ("Immagini",    "immagini",     70),
]


class MagazzinoWindow(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.svc = MagazzinoService()
        self._dati: list[dict] = []
        self._sel_id: int | None = None
        self._modo: str | None = None  # "carico" | "scarico"

        self.title("PerilCar — Magazzino")
        self.geometry("1440x820")
        self.minsize(1100, 640)
        self.configure(fg_color=C_BG)

        # Centra
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 1440) // 2
        y = (self.winfo_screenheight() - 820)  // 2
        self.geometry(f"1440x820+{x}+{y}")

        self._build_ui()
        self._carica_dati()

    # ─── BUILD UI ────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Layout: frame sinistro (tabella) + frame destro (pannello)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self._build_left()
        self._build_right()

    # ── FRAME SINISTRO ────────────────────────────────────────────────────────

    def _build_left(self):
        left = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        # ── Riga 0: Titolo + Back ────────────────────────────────────────────
        title_row = ctk.CTkFrame(left, fg_color="transparent", height=56)
        title_row.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 0))
        title_row.grid_propagate(False)

        # Back "<"
        btn_back = ctk.CTkButton(title_row, text="<", width=42, height=42,
                                  corner_radius=8, fg_color=C_CARD,
                                  hover_color=C_BLUE,
                                  font=ctk.CTkFont("Helvetica", 18, "bold"),
                                  text_color=C_WHITE,
                                  command=self.destroy)
        btn_back.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(title_row, text="MAGAZZINO",
                     font=ctk.CTkFont("Helvetica", 28, "bold"),
                     text_color=C_WHITE).pack(side="left")

        # ── Riga 1: Bottoni Resoconto + Pubblica + Nuovo + Cerca ─────────────
        btn_row = ctk.CTkFrame(left, fg_color="transparent", height=46)
        btn_row.grid(row=1, column=0, sticky="ew", padx=12, pady=(10, 6))
        btn_row.grid_propagate(False)

        ctk.CTkButton(btn_row, text="Resoconto", width=160, height=40,
                       corner_radius=20, fg_color=C_BLUE, hover_color=C_BLUE2,
                       font=ctk.CTkFont("Helvetica", 14, "bold"),
                       command=self._resoconto).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text="Pubblica", width=160, height=40,
                       corner_radius=20, fg_color=C_BLUE, hover_color=C_BLUE2,
                       font=ctk.CTkFont("Helvetica", 14, "bold"),
                       command=self._pubblica).pack(side="left", padx=(0, 16))

        ctk.CTkButton(btn_row, text="+ Nuovo", width=110, height=40,
                       corner_radius=20, fg_color=C_ORANGE, hover_color=C_ORANGE2,
                       font=ctk.CTkFont("Helvetica", 13, "bold"),
                       command=self._nuovo_componente).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text="Storico", width=100, height=40,
                       corner_radius=20, fg_color=C_CARD, hover_color=C_BLUE,
                       font=ctk.CTkFont("Helvetica", 13, "bold"),
                       command=self._storico).pack(side="left", padx=(0, 8))

        # Cerca (con icona lente) — destra
        search_frame = ctk.CTkFrame(btn_row, fg_color=C_TABLE_BG,
                                     corner_radius=20, border_width=1,
                                     border_color=C_CARD)
        search_frame.pack(side="right", padx=4)
        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=14),
                      text_color=C_GRAY).pack(side="left", padx=(10, 4))
        self.entry_cerca = ctk.CTkEntry(search_frame, width=220, height=36,
                                         fg_color="transparent",
                                         border_width=0, text_color=C_WHITE,
                                         placeholder_text="Cerca componente...",
                                         placeholder_text_color=C_GRAY)
        self.entry_cerca.pack(side="left", padx=(0, 10))
        self.entry_cerca.bind("<KeyRelease>", lambda e: self._filtra())

        # ── Riga 2: Tabella ──────────────────────────────────────────────────
        table_frame = ctk.CTkFrame(left, fg_color=C_TABLE_BG, corner_radius=8)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

        # Stile ttk Treeview (dark)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Mag.Treeview",
                         background=C_TABLE_ROW,
                         foreground=C_WHITE,
                         fieldbackground=C_TABLE_ROW,
                         rowheight=28,
                         borderwidth=0,
                         relief="flat",
                         font=("Helvetica", 11))
        style.configure("Mag.Treeview.Heading",
                         background=C_TABLE_HDR,
                         foreground=C_GRAY,
                         relief="flat",
                         font=("Helvetica", 10, "bold"),
                         padding=(4, 6))
        style.map("Mag.Treeview",
                  background=[("selected", C_TABLE_SEL)],
                  foreground=[("selected", C_WHITE)])
        style.layout("Mag.Treeview", [
            ('Treeview.treearea', {'sticky': 'nswe'})
        ])

        cols = [c[0] for c in COLONNE]
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                  style="Mag.Treeview", selectmode="browse")

        # Colonne
        for label, key, width in COLONNE:
            self.tree.heading(label, text=label,
                               command=lambda l=label: self._sort_by(l))
            anchor = "center" if label in ("ES", "Scorta", "NA", "Anno") else "w"
            self.tree.column(label, width=width, minwidth=40,
                              stretch=False, anchor=anchor)

        # Scrollbar
        vsb = ttk.Scrollbar(table_frame, orient="vertical",
                              command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal",
                              command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Tag colori righe
        self.tree.tag_configure("alt",    background=C_TABLE_ALT)
        self.tree.tag_configure("scarso", background="#2d1515", foreground="#e74c3c")
        self.tree.tag_configure("ok",     background=C_TABLE_ROW)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>",          self._on_double_click)

        # Status bar
        self.lbl_status = ctk.CTkLabel(left, text="",
                                        font=ctk.CTkFont(size=11),
                                        text_color=C_GRAY)
        self.lbl_status.grid(row=3, column=0, sticky="w", padx=16, pady=(0, 4))

    # ── FRAME DESTRO (pannello) ────────────────────────────────────────────────

    def _build_right(self):
        right = ctk.CTkFrame(self, fg_color=C_PANEL, corner_radius=0,
                              width=360, border_width=1,
                              border_color="#1a2a40")
        right.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        right.grid_propagate(False)
        right.grid_columnconfigure(0, weight=1)

        pad = {"padx": 16, "pady": (8, 0)}

        # ── Sezione filtri Esistenza / Scorta ─────────────────────────────────
        filtri_card = ctk.CTkFrame(right, fg_color=C_CARD, corner_radius=12)
        filtri_card.grid(row=0, column=0, sticky="ew", padx=12, pady=(14, 6))

        # Labels
        lbl_row = ctk.CTkFrame(filtri_card, fg_color="transparent")
        lbl_row.pack(fill="x", padx=12, pady=(10, 2))
        ctk.CTkLabel(lbl_row, text="Esistenza",
                     font=ctk.CTkFont(size=12), text_color=C_WHITE).pack(side="left", expand=True)
        ctk.CTkLabel(lbl_row, text="Scorta",
                     font=ctk.CTkFont(size=12), text_color=C_WHITE).pack(side="left", expand=True)

        # Pills colorate (come Canva: giallo chiaro + giallo per exist, rosa per scorta)
        pill_row = ctk.CTkFrame(filtri_card, fg_color="transparent")
        pill_row.pack(fill="x", padx=12, pady=(0, 4))

        # Esistenza min pill (giallo)
        self.var_es_min = tk.StringVar()
        es_min = ctk.CTkEntry(pill_row, textvariable=self.var_es_min,
                               width=62, height=30, corner_radius=15,
                               fg_color=C_YELLOW2, border_width=0,
                               text_color="#1a1a1a",
                               font=ctk.CTkFont(size=11),
                               placeholder_text="min",
                               placeholder_text_color="#555500")
        es_min.pack(side="left", padx=(0, 4))

        # Esistenza max pill (giallo chiaro)
        self.var_es_max = tk.StringVar()
        es_max = ctk.CTkEntry(pill_row, textvariable=self.var_es_max,
                               width=62, height=30, corner_radius=15,
                               fg_color=C_YELLOW, border_width=0,
                               text_color="#1a1a1a",
                               font=ctk.CTkFont(size=11),
                               placeholder_text="max",
                               placeholder_text_color="#555500")
        es_max.pack(side="left", padx=(0, 12))

        # Scorta pill (rosa/viola chiaro)
        self.var_solo_scorta = tk.BooleanVar(value=False)
        scorta_pill = ctk.CTkButton(pill_row, text="Sotto scorta",
                                     width=100, height=30, corner_radius=15,
                                     fg_color=C_PINK, hover_color="#c084e0",
                                     text_color="#2a0040",
                                     font=ctk.CTkFont(size=11),
                                     command=self._toggle_scorta)
        scorta_pill.pack(side="left", padx=(0, 6))
        self.btn_scorta_pill = scorta_pill

        # Bottone Applica (viola)
        ctk.CTkButton(pill_row, text="Applica", width=76, height=30,
                       corner_radius=15, fg_color=C_PURPLE, hover_color=C_PURPLE2,
                       font=ctk.CTkFont(size=11, weight="bold"),
                       text_color=C_WHITE,
                       command=self._applica_filtri).pack(side="left")

        # ── Note ──────────────────────────────────────────────────────────────
        ctk.CTkLabel(right, text="Note",
                     font=ctk.CTkFont(size=12), text_color=C_WHITE).grid(
                         row=1, column=0, sticky="w", padx=16, pady=(10, 2))

        self.txt_note = ctk.CTkTextbox(right, height=130, corner_radius=8,
                                        fg_color=C_CARD, border_width=1,
                                        border_color="#1e3a5f",
                                        text_color=C_WHITE,
                                        font=ctk.CTkFont(size=12))
        self.txt_note.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 6))

        btn_salva_note = ctk.CTkButton(right, text="Salva nota",
                                        height=30, corner_radius=8,
                                        fg_color=C_CARD, hover_color=C_BLUE,
                                        font=ctk.CTkFont(size=11),
                                        command=self._salva_nota)
        btn_salva_note.grid(row=3, column=0, sticky="e", padx=16, pady=(0, 6))

        # ── Articolo ──────────────────────────────────────────────────────────
        ctk.CTkLabel(right, text="Articolo",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C_WHITE).grid(row=4, column=0,
                                               sticky="w", padx=16, pady=(8, 2))

        art_row = ctk.CTkFrame(right, fg_color="transparent")
        art_row.grid(row=5, column=0, sticky="ew", padx=12, pady=(0, 8))

        self.var_art_cod = tk.StringVar()
        self.var_art_nome = tk.StringVar()
        ctk.CTkEntry(art_row, textvariable=self.var_art_cod,
                      width=90, height=36, corner_radius=8,
                      fg_color=C_CARD, border_color=C_CARD,
                      text_color=C_WHITE,
                      placeholder_text="CMP",
                      placeholder_text_color=C_GRAY,
                      state="disabled").pack(side="left", padx=(0, 6))
        ctk.CTkEntry(art_row, textvariable=self.var_art_nome,
                      height=36, corner_radius=8,
                      fg_color=C_CARD, border_color=C_CARD,
                      text_color=C_WHITE,
                      placeholder_text="Nome articolo",
                      placeholder_text_color=C_GRAY,
                      state="disabled").pack(side="left", fill="x", expand=True)

        # ── Carico / Scarico qty ──────────────────────────────────────────────
        cs_frame = ctk.CTkFrame(right, fg_color="transparent")
        cs_frame.grid(row=6, column=0, sticky="ew", padx=12, pady=(0, 6))

        # Carico
        self.var_q_carico = tk.StringVar()
        ctk.CTkButton(cs_frame, text="Carico", width=84, height=34,
                       corner_radius=17, fg_color=C_ORANGE, hover_color=C_ORANGE2,
                       font=ctk.CTkFont("Helvetica", 12, "bold"),
                       command=lambda: self._set_modo("carico")).pack(
                           side="left", padx=(0, 6))
        ctk.CTkEntry(cs_frame, textvariable=self.var_q_carico,
                      width=130, height=34, corner_radius=8,
                      fg_color=C_CARD, border_color=C_CARD,
                      text_color=C_WHITE,
                      placeholder_text="Quantità carico",
                      placeholder_text_color=C_GRAY).pack(side="left", fill="x", expand=True)

        cs_frame2 = ctk.CTkFrame(right, fg_color="transparent")
        cs_frame2.grid(row=7, column=0, sticky="ew", padx=12, pady=(0, 8))

        # Scarico
        self.var_q_scarico = tk.StringVar()
        ctk.CTkButton(cs_frame2, text="Scarico", width=84, height=34,
                       corner_radius=17, fg_color=C_GREEN, hover_color=C_GREEN2,
                       font=ctk.CTkFont("Helvetica", 12, "bold"),
                       command=lambda: self._set_modo("scarico")).pack(
                           side="left", padx=(0, 6))
        ctk.CTkEntry(cs_frame2, textvariable=self.var_q_scarico,
                      width=130, height=34, corner_radius=8,
                      fg_color=C_CARD, border_color=C_CARD,
                      text_color=C_WHITE,
                      placeholder_text="Quantità scarico",
                      placeholder_text_color=C_GRAY).pack(side="left", fill="x", expand=True)

        # Riferimento
        ctk.CTkLabel(right, text="Riferimento / DDT",
                     font=ctk.CTkFont(size=11), text_color=C_GRAY).grid(
                         row=8, column=0, sticky="w", padx=16, pady=(0, 2))
        self.var_riferimento = tk.StringVar()
        ctk.CTkEntry(right, textvariable=self.var_riferimento,
                      height=34, corner_radius=8,
                      fg_color=C_CARD, border_color=C_CARD,
                      text_color=C_WHITE,
                      placeholder_text="es. DDT 2024-001",
                      placeholder_text_color=C_GRAY).grid(
                          row=9, column=0, sticky="ew", padx=12, pady=(0, 8))

        # ── Bottoni Carico | Scarico ──────────────────────────────────────────
        big_btn_row = ctk.CTkFrame(right, fg_color="transparent")
        big_btn_row.grid(row=10, column=0, sticky="ew", padx=12, pady=(4, 6))

        self.btn_carico = ctk.CTkButton(big_btn_row, text="Carico",
                                         height=48, corner_radius=20,
                                         fg_color=C_ORANGE, hover_color=C_ORANGE2,
                                         font=ctk.CTkFont("Helvetica", 16, "bold"),
                                         command=lambda: self._esegui_movimento("carico"))
        self.btn_carico.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.btn_scarico = ctk.CTkButton(big_btn_row, text="Scarico",
                                          height=48, corner_radius=20,
                                          fg_color=C_GREEN, hover_color=C_GREEN2,
                                          font=ctk.CTkFont("Helvetica", 16, "bold"),
                                          command=lambda: self._esegui_movimento("scarico"))
        self.btn_scarico.pack(side="left", expand=True, fill="x")

        # ── Conferma ─────────────────────────────────────────────────────────
        self.btn_conferma = ctk.CTkButton(right, text="Conferma",
                                           height=46, corner_radius=20,
                                           fg_color="#0ea5e9", hover_color="#38bdf8",
                                           font=ctk.CTkFont("Helvetica", 15, "bold"),
                                           command=self._conferma)
        self.btn_conferma.grid(row=11, column=0, sticky="ew",
                                padx=12, pady=(0, 12))

        # Label feedback
        self.lbl_feedback = ctk.CTkLabel(right, text="",
                                          font=ctk.CTkFont(size=11),
                                          text_color=C_GREEN)
        self.lbl_feedback.grid(row=12, column=0, padx=12, pady=(0, 4))

        # ── Modifica / Elimina ────────────────────────────────────────────────
        edit_row = ctk.CTkFrame(right, fg_color="transparent")
        edit_row.grid(row=13, column=0, sticky="ew", padx=12, pady=(0, 14))

        ctk.CTkButton(edit_row, text="✏ Modifica", height=34,
                       corner_radius=8, fg_color=C_CARD, hover_color=C_BLUE,
                       font=ctk.CTkFont(size=12),
                       command=self._modifica_componente).pack(
                           side="left", expand=True, fill="x", padx=(0, 4))
        ctk.CTkButton(edit_row, text="🗑 Elimina", height=34,
                       corner_radius=8, fg_color="#3d1515", hover_color="#7f1d1d",
                       font=ctk.CTkFont(size=12),
                       command=self._elimina_componente).pack(
                           side="left", expand=True, fill="x")

        # Backup manuale
        ctk.CTkButton(right, text="💾 Backup DB", height=30,
                       corner_radius=8, fg_color="#1a2535", hover_color=C_CARD,
                       font=ctk.CTkFont(size=10), text_color=C_GRAY,
                       command=self._backup).grid(
                           row=14, column=0, sticky="ew", padx=12, pady=(0, 8))

    # ─── LOGICA UI ────────────────────────────────────────────────────────────

    def _carica_dati(self, filtri: dict = None):
        def _task():
            dati = self.svc.get_tutti_componenti(filtri)
            self.after(0, lambda: self._popola_tabella(dati))
        threading.Thread(target=_task, daemon=True).start()

    def _popola_tabella(self, dati: list[dict]):
        self._dati = dati
        # Pulisci
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, row in enumerate(dati):
            es  = row.get("esistenza", 0) or 0
            sc  = row.get("scorta",    0) or 0
            na  = max(0, sc - es)

            anno_str = ""
            if row.get("anno_da"):
                anno_str = str(row["anno_da"])
                if row.get("anno_a") and row["anno_a"] != row["anno_da"]:
                    anno_str += f"–{row['anno_a']}"

            values = (
                row.get("cmp",          ""),
                row.get("articolo",     ""),
                row.get("descrizione",  "") or "",
                es,
                sc,
                na if na > 0 else "",
                row.get("marca",        "") or "",
                row.get("modello",      "") or "",
                row.get("cod_modello",  "") or "",
                row.get("nota",         "") or "",
                row.get("colore",       "") or "",
                row.get("cilindrata",   "") or "",
                row.get("carburante",   "") or "",
                row.get("versione",     "") or "",
                anno_str,
                row.get("intervallo",   "") or "",
                "📷" if row.get("immagini") else "",
            )

            # Tag
            tag = "scarso" if sc > 0 and es <= sc else ("alt" if i % 2 else "ok")
            iid = str(row["componente_id"])
            self.tree.insert("", "end", iid=iid, values=values, tags=(tag,))

        total = len(dati)
        scarsi = sum(1 for r in dati
                     if (r.get("scorta") or 0) > 0
                     and (r.get("esistenza") or 0) <= (r.get("scorta") or 0))
        self.lbl_status.configure(
            text=f"{total} componenti  •  {scarsi} sotto scorta"
        )

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        comp_id = int(iid)
        row = next((r for r in self._dati if r["componente_id"] == comp_id), None)
        if not row:
            return
        self._sel_id = comp_id
        self.var_art_cod.set(row.get("cmp", ""))
        self.var_art_nome.set(row.get("articolo", ""))
        self.txt_note.delete("1.0", "end")
        self.txt_note.insert("1.0", row.get("nota", "") or "")

    def _on_double_click(self, event=None):
        self._storico_componente()

    def _set_modo(self, modo: str):
        self._modo = modo
        if modo == "carico":
            self.btn_carico.configure(border_width=2, border_color=C_WHITE)
            self.btn_scarico.configure(border_width=0)
        else:
            self.btn_scarico.configure(border_width=2, border_color=C_WHITE)
            self.btn_carico.configure(border_width=0)

    def _esegui_movimento(self, tipo: str):
        self._modo = tipo
        self._set_modo(tipo)

    def _conferma(self):
        if not self._sel_id:
            self._feedback("Seleziona un componente dalla tabella", error=True)
            return
        if not self._modo:
            self._feedback("Premi Carico o Scarico prima di confermare", error=True)
            return

        if self._modo == "carico":
            q_str = self.var_q_carico.get().strip()
        else:
            q_str = self.var_q_scarico.get().strip()

        if not q_str or not q_str.isdigit():
            self._feedback("Inserisci una quantità valida", error=True)
            return

        q = int(q_str)
        rif = self.var_riferimento.get().strip() or None
        note = self.txt_note.get("1.0", "end").strip() or None

        if self._modo == "carico":
            ok, msg = self.svc.carico(self._sel_id, q, rif, note)
        else:
            ok, msg = self.svc.scarico(self._sel_id, q, rif, note)

        self._feedback(msg, error=not ok)
        if ok:
            # Reset
            self.var_q_carico.set("")
            self.var_q_scarico.set("")
            self.var_riferimento.set("")
            self._modo = None
            self.btn_carico.configure(border_width=0)
            self.btn_scarico.configure(border_width=0)
            self._carica_dati(self._filtri_correnti())

    def _filtra(self):
        testo = self.entry_cerca.get().strip()
        self._carica_dati({"testo": testo} if testo else None)

    def _toggle_scorta(self):
        current = self.var_solo_scorta.get()
        self.var_solo_scorta.set(not current)
        color = "#7c3aed" if not current else C_PINK
        self.btn_scorta_pill.configure(fg_color=color)

    def _applica_filtri(self):
        filtri = self._filtri_correnti()
        self._carica_dati(filtri)

    def _filtri_correnti(self) -> dict:
        filtri = {}
        testo = self.entry_cerca.get().strip()
        if testo:
            filtri["testo"] = testo
        es_min = self.var_es_min.get().strip()
        es_max = self.var_es_max.get().strip()
        if es_min.isdigit():
            filtri["esistenza_min"] = int(es_min)
        if es_max.isdigit():
            filtri["esistenza_max"] = int(es_max)
        if self.var_solo_scorta.get():
            filtri["solo_scorta"] = True
        return filtri or None

    def _sort_by(self, label: str):
        pass  # Placeholder — implementabile con sorted()

    def _feedback(self, msg: str, error: bool = False):
        color = "#e74c3c" if error else C_GREEN
        self.lbl_feedback.configure(text=msg, text_color=color)
        self.after(4000, lambda: self.lbl_feedback.configure(text=""))

    def _salva_nota(self):
        if not self._sel_id:
            self._feedback("Seleziona prima un componente", error=True)
            return
        note = self.txt_note.get("1.0", "end").strip()
        ok, msg = self.svc.modifica_componente(self._sel_id, {"note": note})
        self._feedback(msg, error=not ok)
        if ok:
            self._carica_dati(self._filtri_correnti())

    def _nuovo_componente(self):
        dlg = FormComponenteDialog(self)
        self.wait_window(dlg)
        self._carica_dati(self._filtri_correnti())

    def _modifica_componente(self):
        if not self._sel_id:
            self._feedback("Seleziona un componente", error=True)
            return
        row = next((r for r in self._dati if r["componente_id"] == self._sel_id), None)
        dlg = FormComponenteDialog(self, dati_esistenti=row)
        self.wait_window(dlg)
        self._carica_dati(self._filtri_correnti())

    def _elimina_componente(self):
        if not self._sel_id:
            self._feedback("Seleziona un componente", error=True)
            return
        row = next((r for r in self._dati if r["componente_id"] == self._sel_id), None)
        nome = row["articolo"] if row else str(self._sel_id)
        if messagebox.askyesno("Conferma eliminazione",
                                f"Eliminare '{nome}'?\nL'operazione è reversibile.",
                                parent=self):
            ok, msg = self.svc.elimina_componente(self._sel_id)
            self._feedback(msg, error=not ok)
            if ok:
                self._sel_id = None
                self._carica_dati(self._filtri_correnti())

    def _storico(self):
        dlg = StoricoDialog(self)
        self.wait_window(dlg)

    def _storico_componente(self):
        if not self._sel_id:
            return
        dlg = StoricoDialog(self, componente_id=self._sel_id)
        self.wait_window(dlg)

    def _pubblica(self):
        if not self._sel_id:
            self._feedback("Seleziona un componente", error=True)
            return
        row = next((r for r in self._dati if r["componente_id"] == self._sel_id), None)
        stato = row.get("pubblicato", 0) if row else 0
        ok, msg = self.svc.pubblica_componente(self._sel_id, not stato)
        self._feedback(msg, error=not ok)
        if ok:
            self._carica_dati(self._filtri_correnti())

    def _resoconto(self):
        stats = self.svc.get_stats()
        messagebox.showinfo("Resoconto Magazzino",
            f"Componenti totali:   {stats['totale_componenti']}\n"
            f"Sotto scorta:        {stats['sotto_scorta']}\n"
            f"Ultimo movimento:    {stats['ultimo_movimento']}",
            parent=self)

    def _backup(self):
        from core.database import DatabaseManager
        path = DatabaseManager().backup()
        messagebox.showinfo("Backup completato", f"Backup salvato:\n{path}", parent=self)
