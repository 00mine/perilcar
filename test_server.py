"""Test rapido per verificare che il server parta correttamente."""
import sys, os, time, socket, threading, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

def trova_porta(start=5000):
    for p in range(start, start+20):
        with socket.socket() as s:
            try: s.bind(("0.0.0.0",p)); return p
            except: continue
    return start

errors = []

def avvia():
    try:
        from dev_server import app, socketio
        socketio.run(app, host="0.0.0.0", port=porta,
                     debug=False, allow_unsafe_werkzeug=True,
                     log_output=False, use_reloader=False)
    except Exception as e:
        errors.append(str(e))

porta = trova_porta(5001)
t = threading.Thread(target=avvia, daemon=True)
t.start()
time.sleep(5)

try:
    urllib.request.urlopen(f"http://127.0.0.1:{porta}/login", timeout=3)
    print(f"✅ Server OK sulla porta {porta}")
except Exception as e:
    print(f"❌ Server non risponde: {e}")
    if errors:
        print(f"❌ Errore: {errors[0]}")
