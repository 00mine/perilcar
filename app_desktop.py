"""
PerilCar ERP — Launcher Desktop
Avvia Flask + apre Edge/Chrome in modalità app (nessuna toolbar visibile).
Funziona su qualsiasi Windows senza dipendenze aggiuntive.
"""
import sys, os, threading, time, socket, logging, subprocess
from pathlib import Path

# ── Percorsi ─────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    ROOT = Path(sys.executable).parent
else:
    ROOT = Path(__file__).parent

os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

# ── Logging ───────────────────────────────────────────────────────────
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


def apri_app_browser(url):
    """
    Apre Edge (o Chrome) in modalità --app: nessuna toolbar, nessun URL visibile.
    Sembra una finestra desktop nativa all'utente.
    """
    # Percorsi Edge su Windows
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    # Percorsi Chrome come fallback
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]

    browser = None
    for p in edge_paths + chrome_paths:
        if os.path.exists(p):
            browser = p
            log.info(f"Browser trovato: {p}")
            break

    if not browser:
        # Fallback: apri nel browser predefinito
        import webbrowser
        log.warning("Edge/Chrome non trovato, apro browser predefinito")
        webbrowser.open(url)
        return None

    # Profilo dedicato PerilCar (separato dal profilo personale)
    profile_dir = ROOT / "browser_profile"
    profile_dir.mkdir(exist_ok=True)

    cmd = [
        browser,
        f"--app={url}",                          # modalità app: niente toolbar
        f"--user-data-dir={profile_dir}",         # profilo separato
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
    return proc


def main():
    log.info("=" * 50)
    log.info("PerilCar ERP — Avvio")

    porta = trova_porta(5000)
    log.info(f"Porta: {porta}")

    # Avvia server Flask in background
    t = threading.Thread(target=avvia_server, args=(porta,), daemon=True)
    t.start()

    # Aspetta che il server risponda
    if not server_pronto(porta):
        log.error("Server non risponde")
        mostra_errore(
            "Impossibile avviare PerilCar ERP.\n\n"
            "Controlla logs\\perilcar.log per dettagli."
        )
        return 1

    log.info("Server pronto")

    url = f"http://127.0.0.1:{porta}/"
    proc = apri_app_browser(url)

    if proc:
        # Aspetta che il browser si chiuda
        proc.wait()
        log.info("Browser chiuso, esco")
    else:
        # Fallback browser: tieni il server vivo
        try:
            while t.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
