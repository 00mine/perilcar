"""
PerilCar ERP — Launcher silenzioso
Avvia server Flask + finestra PyWebView senza mostrare terminale.
Fallback automatico su browser se PyWebView non disponibile.
"""
import sys, os, threading, time, socket, logging
from pathlib import Path

# ── Percorsi ─────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    ROOT = Path(sys.executable).parent
else:
    ROOT = Path(__file__).parent

os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

# ── Logging su file (niente terminale) ───────────────────────────────
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / "perilcar.log",
                                   encoding="utf-8", mode="a")]
)
log = logging.getLogger("perilcar")


def trova_porta(start=5000):
    for p in range(start, start + 20):
        with socket.socket() as s:
            try:
                s.bind(("0.0.0.0", p))
                return p
            except OSError:
                continue
    return start


def avvia_server(porta):
    try:
        from dev_server import app, socketio
        socketio.run(app, host="0.0.0.0", port=porta,
                     debug=False, allow_unsafe_werkzeug=True,
                     log_output=False, use_reloader=False)
    except Exception as e:
        log.exception(f"Server error: {e}")


def server_pronto(porta, timeout=30):
    import urllib.request
    fine = time.time() + timeout
    while time.time() < fine:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{porta}/login", timeout=1)
            return True
        except Exception:
            time.sleep(0.4)
    return False


def mostra_errore(msg):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, "PerilCar ERP — Errore", 0x10)
    except Exception:
        pass


def main():
    log.info("=" * 50)
    log.info("PerilCar ERP — Avvio")

    porta = trova_porta(5000)
    log.info(f"Porta: {porta}")

    t = threading.Thread(target=avvia_server, args=(porta,), daemon=True)
    t.start()

    if not server_pronto(porta):
        log.error("Server non risponde")
        mostra_errore(
            "Impossibile avviare PerilCar ERP.\n\n"
            "Controlla logs\\perilcar.log per dettagli."
        )
        return 1

    log.info("Server pronto")

    # Prova PyWebView (finestra nativa)
    try:
        import webview
        window = webview.create_window(
            title="PerilCar ERP",
            url=f"http://127.0.0.1:{porta}/",
            width=1400, height=900,
            min_size=(1024, 700),
            resizable=True,
        )
        webview.start(debug=False)
        log.info("Chiusura finestra desktop")

    except ImportError:
        # Fallback: apri nel browser di sistema (funziona sempre)
        log.warning("PyWebView non disponibile, apertura browser")
        import webbrowser
        webbrowser.open(f"http://127.0.0.1:{porta}/")
        # Mantieni server attivo
        try:
            while t.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
