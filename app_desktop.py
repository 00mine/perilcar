"""
PerilCar ERP — Launcher Desktop
Avvia Flask + Edge in modalità app (nessuna toolbar).
"""
import sys, os, threading, time, socket, logging, subprocess
from pathlib import Path

if getattr(sys, "frozen", False):
    ROOT = Path(sys.executable).parent
else:
    ROOT = Path(__file__).parent

os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / "perilcar.log", encoding="utf-8", mode="a")]
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


def server_pronto(porta, timeout=60):
    """Aspetta fino a 60 secondi che il server risponda."""
    import urllib.request
    fine = time.time() + timeout
    while time.time() < fine:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{porta}/login", timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def mostra_errore(msg):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, "PerilCar ERP — Errore", 0x10)
    except Exception:
        pass


def trova_browser():
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in edge_paths + chrome_paths:
        if os.path.exists(p):
            return p
    return None


def main():
    log.info("=" * 50)
    log.info("PerilCar ERP — Avvio")

    porta = trova_porta(5000)
    log.info(f"Porta: {porta}")

    # Avvia server Flask in background
    t = threading.Thread(target=avvia_server, args=(porta,), daemon=True)
    t.start()

    # ── Aspetta server pronto PRIMA di aprire il browser ─────────────
    log.info("Attendo server...")
    if not server_pronto(porta, timeout=60):
        log.error("Server non risponde dopo 60 secondi")
        mostra_errore(
            "Impossibile avviare PerilCar ERP.\n\n"
            "Controlla logs\\perilcar.log per dettagli."
        )
        return 1

    log.info("Server pronto — apro browser")
    url = f"http://127.0.0.1:{porta}/"

    browser = trova_browser()
    if browser:
        profile_dir = ROOT / "browser_profile"
        profile_dir.mkdir(exist_ok=True)
        cmd = [
            browser,
            f"--app={url}",
            f"--user-data-dir={str(profile_dir)}",
            "--window-size=1400,900",
            "--window-position=60,40",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-translate",
            "--disable-sync",
        ]
        proc = subprocess.Popen(cmd)
        log.info(f"Browser avviato (PID {proc.pid})")
        proc.wait()
    else:
        import webbrowser
        log.warning("Edge/Chrome non trovato, apro browser predefinito")
        webbrowser.open(url)
        try:
            while t.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    log.info("Chiusura")
    return 0


if __name__ == "__main__":
    sys.exit(main())
