"""
PerilCar ERP — Desktop App Launcher
Avvia il server Flask e apre l'app in una finestra desktop nativa (PyWebView).
L'utente non vede mai il terminale.
"""
import sys, os, threading, time, socket, logging
from pathlib import Path

# ── Configurazione percorsi (compatibile con PyInstaller) ─────────────
if getattr(sys, "frozen", False):
    # Eseguibile compilato
    BUNDLE_DIR = Path(sys._MEIPASS)
    APP_DIR    = Path(sys.executable).parent
else:
    BUNDLE_DIR = Path(__file__).parent
    APP_DIR    = BUNDLE_DIR

# Working directory — dove stanno DB e uploads (resta sempre nella cartella app)
os.chdir(APP_DIR)
sys.path.insert(0, str(BUNDLE_DIR))

# ── Setup logging silenzioso (no console) ─────────────────────────────
LOG_DIR = APP_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / "perilcar.log", encoding="utf-8")]
)
log = logging.getLogger("perilcar.app")


def trova_porta_libera(porta_default: int = 5000) -> int:
    """Trova una porta TCP libera, partendo dalla default."""
    porta = porta_default
    while porta < porta_default + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", porta))
                return porta
            except OSError:
                porta += 1
    raise RuntimeError("Nessuna porta libera trovata")


def avvia_server(porta: int):
    """Avvia il server Flask in un thread separato."""
    try:
        from dev_server import app, socketio
        log.info(f"Avvio server su porta {porta}")
        socketio.run(app, host="0.0.0.0", port=porta,
                     debug=False, allow_unsafe_werkzeug=True,
                     log_output=False)
    except Exception as e:
        log.exception(f"Errore avvio server: {e}")


def attendi_server_pronto(porta: int, timeout: int = 30) -> bool:
    """Aspetta che il server risponda."""
    import urllib.request
    fine = time.time() + timeout
    while time.time() < fine:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{porta}/login", timeout=1):
                return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    log.info("=" * 50)
    log.info("PerilCar ERP — Avvio")
    log.info("=" * 50)

    porta = trova_porta_libera(5000)
    log.info(f"Porta selezionata: {porta}")

    # Avvia server in thread
    server_thread = threading.Thread(target=avvia_server, args=(porta,), daemon=True)
    server_thread.start()

    # Aspetta che il server sia pronto
    if not attendi_server_pronto(porta):
        log.error("Server non risponde, esco")
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk(); root.withdraw()
            messagebox.showerror("PerilCar ERP",
                "Impossibile avviare il server interno.\n"
                "Controlla il file logs/perilcar.log per dettagli.")
        except Exception:
            pass
        return 1

    log.info("Server pronto, apro la finestra desktop")

    # Apri finestra desktop con PyWebView
    try:
        import webview
    except ImportError:
        log.error("PyWebView non installato")
        return 1

    # Icona finestra (se presente)
    icon_path = BUNDLE_DIR / "icon.ico"
    if not icon_path.exists():
        icon_path = None

    window = webview.create_window(
        title="PerilCar ERP",
        url=f"http://127.0.0.1:{porta}/login",
        width=1400, height=900,
        min_size=(1024, 700),
        resizable=True,
        confirm_close=False,
        text_select=True,
    )

    # Avvia il loop GUI (bloccante)
    webview.start(debug=False, gui="edgechromium" if sys.platform == "win32" else None)

    log.info("Finestra chiusa, esco")
    return 0


if __name__ == "__main__":
    sys.exit(main())
