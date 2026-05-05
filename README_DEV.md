# PerilCar ERP — Guida Sviluppo
### Ambiente di sviluppo con hot reload · v1.0.0

---

## AVVIO RAPIDO (un solo comando)

### Windows
```
Doppio click su  start.bat
```
oppure da terminale:
```cmd
cd perilcar
start.bat
```

### macOS / Linux
```bash
cd perilcar
bash start.sh
```

### Manuale (qualsiasi sistema)
```bash
cd perilcar
pip install flask flask-socketio watchdog
python dev_server.py
```

Il browser si apre automaticamente su **http://localhost:5000**

**Login default:** `admin` / `admin123`

---

## COME FUNZIONA IL HOT RELOAD

```
Salvi un file  →  Watchdog lo rileva  →  SocketIO notifica il browser  →  pagina si ricarica
     .py / .html / .css / .js               (< 1 secondo)
```

Non devi fare nulla: ogni volta che salvi un file, la pagina nel browser
si aggiorna automaticamente. Vedrai un badge verde **"🔄 Hot reload"**
comparire in basso a destra.

---

## STRUTTURA COMPLETA PROGETTO

```
perilcar/
│
├── dev_server.py          ← 🚀 SERVER DEV (Flask + SocketIO + Watchdog)
├── start.bat              ← ▶  Avvio Windows (doppio click)
├── start.sh               ← ▶  Avvio macOS/Linux
├── main.py                ← Desktop app (CustomTkinter) — non usata in dev
├── requirements.txt
│
├── core/                  ← DATA LAYER (non toccare spesso)
│   ├── database.py        ← SQLite, schema, backup, log audit
│   ├── auth.py            ← Login, sessione, ruoli
│   └── config.py          ← Configurazione (db_path, ecc.)
│
├── modules/               ← BUSINESS LOGIC (qui lavori di più)
│   ├── magazzino/
│   │   ├── service.py     ← Logica: carico, scarico, filtri, stats
│   │   ├── ui_magazzino.py  (desktop, non usata in dev)
│   │   ├── ui_form.py       (desktop)
│   │   └── ui_storico.py    (desktop)
│   ├── demolizioni/service.py  ← STUB pronto per sviluppo
│   ├── operai/service.py       ← STUB
│   └── shop/service.py         ← STUB
│
├── web/                   ← UI WEB (qui lavori per l'interfaccia)
│   ├── templates/
│   │   ├── base.html      ← Layout base + hot reload + componenti CSS
│   │   ├── login.html     ← Pagina login
│   │   ├── dashboard.html ← Dashboard con 4 moduli
│   │   ├── magazzino.html ← Modulo magazzino completo
│   │   └── storico.html   ← Storico movimenti
│   └── static/
│       ├── css/           ← CSS aggiuntivi (opzionale)
│       ├── js/            ← JS aggiuntivi (opzionale)
│       └── img/           ← Immagini
│
├── config/
│   └── settings.json      ← Configurazione (auto-creato al primo avvio)
│
├── db/
│   └── perilcar.db        ← Database SQLite (auto-creato, NON toccare)
│
├── backup/                ← Backup automatici DB
└── logs/
    └── perilcar.log       ← Log operazioni
```

---

## API REST DISPONIBILI

Il server espone queste API che puoi usare e testare:

### Auth
| Metodo | URL | Descrizione |
|--------|-----|-------------|
| POST | `/api/login` | Login `{"username":"...","password":"..."}` |
| POST | `/api/logout` | Logout |

### Magazzino
| Metodo | URL | Descrizione |
|--------|-----|-------------|
| GET | `/api/magazzino/componenti` | Lista componenti con giacenza |
| GET | `/api/magazzino/componenti?q=fiat` | Ricerca testo |
| GET | `/api/magazzino/componenti?sotto_scorta=1` | Solo sotto scorta |
| GET | `/api/magazzino/componenti?es_min=5&es_max=20` | Filtro esistenza |
| POST | `/api/magazzino/componenti` | Crea nuovo componente |
| PUT | `/api/magazzino/componenti/<id>` | Modifica componente |
| DELETE | `/api/magazzino/componenti/<id>` | Elimina (soft) |
| POST | `/api/magazzino/movimento` | Carico o scarico |
| GET | `/api/magazzino/movimenti` | Storico movimenti |
| GET | `/api/magazzino/movimenti?componente_id=3` | Storico per componente |
| GET | `/api/magazzino/stats` | Statistiche generali |
| POST | `/api/backup` | Backup manuale DB |

### Esempio chiamata API
```bash
# Login
curl -c cookie.txt -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Crea componente
curl -b cookie.txt -X POST http://localhost:5000/api/magazzino/componenti \
  -H "Content-Type: application/json" \
  -d '{"codice":"ALT-001","nome":"Alternatore Fiat Punto","scorta_minima":2}'

# Carico
curl -b cookie.txt -X POST http://localhost:5000/api/magazzino/movimento \
  -H "Content-Type: application/json" \
  -d '{"componente_id":1,"tipo":"carico","quantita":5,"riferimento":"DDT-001"}'
```

---

## COME AGGIUNGERE UNA NUOVA FUNZIONALITÀ

### 1. Aggiungi la logica in `modules/magazzino/service.py`
```python
def cerca_per_marca(self, marca: str) -> list[dict]:
    return self.db.fetchall(
        "SELECT * FROM v_giacenza WHERE marca LIKE ?",
        (f"%{marca}%",)
    )
```

### 2. Aggiungi la route in `dev_server.py`
```python
@app.route("/api/magazzino/per-marca/<marca>")
@require_login
def api_per_marca(marca):
    from modules.magazzino.service import MagazzinoService
    svc = MagazzinoService()
    return jsonify(svc.cerca_per_marca(marca))
```

### 3. Usa la API nel template HTML
```javascript
const data = await apiFetch('/api/magazzino/per-marca/Fiat');
```

Salvi → hot reload → vedi il risultato. Nessun riavvio manuale.

---

## CONFIGURAZIONE DATABASE SU NAS

Modifica `config/settings.json`:

```json
{
  "db_path": "\\\\192.168.1.100\\PerilCar\\perilcar.db"
}
```

Su Linux/macOS con NAS montato:
```json
{
  "db_path": "/mnt/nas/PerilCar/perilcar.db"
}
```

---

## VARIABILI D'AMBIENTE

```bash
PORT=8080 python dev_server.py     # Cambia porta (default: 5000)
```

---

## DIPENDENZE

```
flask          — web server
flask-socketio — hot reload via WebSocket
watchdog       — monitoraggio file system
customtkinter  — UI desktop (solo per main.py)
pillow         — gestione immagini
```

Reinstalla tutto (se necessario):
```bash
pip install -r requirements.txt
pip install flask flask-socketio watchdog
```

---

*PerilCar ERP · Ing. Carmine Perillo · v1.0.0*
