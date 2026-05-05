"""
PerilCar ERP - Entry Point
Avvio applicazione desktop.

Struttura:
  main.py          ← questo file
  core/            ← database, config, auth
  modules/         ← logica per modulo
  ui/              ← interfacce grafiche
  db/              ← database SQLite (anche su NAS)
  backup/          ← backup automatici
  logs/            ← log operazioni
  config/          ← settings.json
"""

import sys
import os
import logging
from pathlib import Path

# ── Aggiungi root al path (fondamentale per import relativi) ──────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-20s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "perilcar.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("perilcar.main")

# ── CustomTkinter tema ────────────────────────────────────────────────────────
import customtkinter as ctk
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Init database (crea schema se non esiste) ─────────────────────────────────
from core.config import ConfigManager
from core.database import DatabaseManager

cfg = ConfigManager()
db_path = cfg.get("db_path")
logger.info(f"PerilCar ERP v{cfg.get('app_version')} — avvio")
logger.info(f"Database: {db_path}")

db = DatabaseManager(db_path)

# ── Avvio GUI ─────────────────────────────────────────────────────────────────
from ui.login import LoginWindow


def avvia_dashboard():
    """Apre la dashboard dopo login riuscito."""
    from ui.dashboard import Dashboard
    dash = Dashboard()
    dash.mainloop()


def main():
    logger.info("Avvio interfaccia Login")
    login = LoginWindow(on_success=avvia_dashboard)
    login.mainloop()


if __name__ == "__main__":
    main()
