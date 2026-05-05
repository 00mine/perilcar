"""
PerilCar ERP - UI: Storico Movimenti Magazzino
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from modules.magazzino.service import MagazzinoService

C_BG      = "#1a1a2e"
C_PANEL   = "#16213e"
C_CARD    = "#0f3460"
C_ORANGE  = "#e94c00"
C_GREEN   = "#27ae60"
C_WHITE   = "#f0f0f0"
C_GRAY    = "#8892a4"
C_TABLE_BG  = "#0d1b2e"
C_TABLE_ROW = "#111d30"
C_TABLE_ALT = "#0f2240"
C_TABLE_SEL = "#1e3a6e"
C_TABLE_HDR = "#0a1628"


class StoricoDialog(ctk.CTkToplevel):
    def __init__(self, master, componente_id: int = None):
        super().__init__(master)
        self.svc = MagazzinoService()
        self.componente_id = componente_id

        titolo = "Storico Movimenti" if not componente_id else f"Movimenti — ID {componente_id}"
        self.title(f"PerilCar — {titolo}")
        self.geometry("900x560")
        self.configure(fg_color=C_BG)
        self.grab_set()

        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 900) // 2
        y = (self.winfo_screenheight() - 560) // 2
        self.geometry(f"900x560+{x}+{y}")

        self._build_ui()
        self._carica()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=C_PANEL, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="📋 Storico Movimenti Magazzino",
                     font=ctk.CTkFont("Helvetica", 15, "bold"),
                     text_color=C_WHITE).pack(side="left", padx=20, pady=12)
        ctk.CTkButton(hdr, text="✕ Chiudi", width=90, height=30,
                       corner_radius=8, fg_color=C_CARD,
                       font=ctk.CTkFont(size=12),
                       command=self.destroy).pack(side="right", padx=12)

        # Tabella
        table_frame = ctk.CTkFrame(self, fg_color=C_TABLE_BG, corner_radius=0)
        table_frame.pack(fill="both", expand=True, padx=8, pady=8)

        style = ttk.Style()
        style.configure("Stor.Treeview",
                         background=C_TABLE_ROW, foreground=C_WHITE,
                         fieldbackground=C_TABLE_ROW, rowheight=26,
                         borderwidth=0, font=("Helvetica", 11))
        style.configure("Stor.Treeview.Heading",
                         background=C_TABLE_HDR, foreground=C_GRAY,
                         relief="flat", font=("Helvetica", 10, "bold"))
        style.map("Stor.Treeview",
                  background=[("selected", C_TABLE_SEL)],
                  foreground=[("selected", C_WHITE)])

        cols = ("Data/Ora", "CMP", "Articolo", "Tipo", "Quantità", "Prima", "Dopo", "Rif.", "Utente")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                  style="Stor.Treeview")
        widths = (135, 80, 160, 80, 70, 60, 60, 110, 100)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            anchor = "center" if col in ("Tipo", "Quantità", "Prima", "Dopo") else "w"
            self.tree.column(col, width=w, anchor=anchor)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("carico",    foreground="#2ecc71")
        self.tree.tag_configure("scarico",   foreground="#e74c3c")
        self.tree.tag_configure("rettifica", foreground="#f39c12")

    def _carica(self):
        movimenti = self.svc.get_storico_movimenti(self.componente_id)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, m in enumerate(movimenti):
            tipo = m.get("tipo", "")
            self.tree.insert("", "end", tags=(tipo,), values=(
                m.get("creato_il", "")[:19],
                m.get("cmp", ""),
                m.get("articolo", ""),
                tipo.upper(),
                m.get("quantita", 0),
                m.get("quantita_prima", 0),
                m.get("quantita_dopo", 0),
                m.get("riferimento", "") or "",
                m.get("username", "") or "—",
            ))
