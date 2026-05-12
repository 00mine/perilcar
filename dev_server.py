"""
PerilCar ERP — Dev Server v1.1
Flask + SocketIO con hot reload automatico.
"""
import sys, os, time, threading, logging, io
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

UPLOAD_FOLDER = ROOT / "web" / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s  %(name)-20s  %(levelname)s  %(message)s")
log = logging.getLogger("perilcar.dev")

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_socketio import SocketIO, join_room, leave_room

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
app.secret_key = "8e805f4e5eac7a1f47eb5e377af5a2e64ba46d5463746e980201e5a31bae4d24"

@app.route('/favicon.ico')
def favicon():
    return '', 204  # No content - evita errori 404

app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

@app.after_request
def no_cache(response):
    """Disabilita cache browser per tutti i file durante sviluppo."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

from core.config import ConfigManager
from core.database import DatabaseManager

cfg = ConfigManager()
db  = DatabaseManager(cfg.get("db_path"))
log.info(f"DB magazzino: {cfg.get('db_path')}")

# DB separato per demolizioni
import os as _os
_dem_path = _os.path.join(_os.path.dirname(cfg.get("db_path")), "demolizioni.db")

class _DemDB:
    """Connessione SQLite semplice per DB demolizioni."""
    def __init__(self, path):
        self.path = path
        self._lock = __import__('threading').Lock()
        self._init()
    
    def _init(self):
        import sqlite3 as _sq
        conn = _sq.connect(self.path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS anagrafiche (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nominativo TEXT NOT NULL,
            cognome TEXT, nome TEXT, cf_piva TEXT, sesso TEXT, tipo_societa TEXT,
            tipo TEXT DEFAULT 'privato', data_nascita TEXT, luogo_nascita TEXT,
            prov_nascita TEXT, comune TEXT, provincia TEXT, via TEXT, civico TEXT,
            cap TEXT, tipo_doc TEXT, num_doc TEXT, data_doc TEXT, rilasciato_da TEXT,
            telefono TEXT, cellulare TEXT, fax TEXT, email TEXT, indirizzo TEXT,
            note TEXT, creato_il TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS veicoli (
            id INTEGER PRIMARY KEY AUTOINCREMENT, targa TEXT, telaio TEXT,
            classe TEXT, marca TEXT, modello TEXT, anno_immatricolazione TEXT,
            num_motore TEXT, colore TEXT, note TEXT, creato_il TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS demolizioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT, data_presa_in_carico TEXT,
            ora_presa_in_carico TEXT, reg_demolitori TEXT, pag_reg TEXT,
            veicolo_id INTEGER, proprietario_id INTEGER, detentore_id INTEGER,
            ufficio_provinciale TEXT, targhe_consegnate INTEGER DEFAULT 0,
            carta_circolazione INTEGER DEFAULT 0, concessionaria TEXT,
            peso_effettivo_kg REAL, peso_netto_kg REAL, modalita_radiazione TEXT,
            num_albatros TEXT, certificato_id TEXT, note TEXT,
            creato_da INTEGER, primo_trattamento INTEGER DEFAULT 0,
            creato_il TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS ricambi_sottratti (
            id INTEGER PRIMARY KEY AUTOINCREMENT, demolizione_id INTEGER NOT NULL,
            componente_id INTEGER, peso_kg REAL, note TEXT, pezzo_nome TEXT,
            creato_il TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS schede_demolizione (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dem_ids TEXT NOT NULL,
            data_trattamento TEXT,
            peso_eff_tot REAL, peso_ricambi_tot REAL, peso_netto_tot REAL,
            righe_json TEXT,
            creato_da INTEGER, creato_il TEXT DEFAULT (datetime('now')),
            modificato_il TEXT
        );
        """)
        # Migrazione colonne opzionali
        cols = [r[1] for r in conn.execute("PRAGMA table_info(demolizioni)").fetchall()]
        if 'primo_trattamento' not in cols:
            conn.execute("ALTER TABLE demolizioni ADD COLUMN primo_trattamento INTEGER DEFAULT 0")
            conn.commit()
        conn.commit()
        conn.close()
    
    def conn(self):
        import sqlite3 as _sq
        c = _sq.connect(self.path, timeout=30)
        c.row_factory = _sq.Row
        c.execute("PRAGMA journal_mode=WAL")
        return c
    
    def all(self, sql, params=()):
        with self._lock:
            c = self.conn()
            try:
                rows = c.execute(sql, params).fetchall()
                return [dict(r) for r in rows]
            finally:
                c.close()
    
    def one(self, sql, params=()):
        with self._lock:
            c = self.conn()
            try:
                row = c.execute(sql, params).fetchone()
                return dict(row) if row else None
            finally:
                c.close()
    
    def run(self, sql, params=()):
        with self._lock:
            c = self.conn()
            try:
                cur = c.execute(sql, params)
                c.commit()
                return cur.lastrowid
            finally:
                c.close()

dem = _DemDB(_dem_path)
log.info(f"DB demolizioni: {_dem_path}")

# Pulizia tabelle residue nel magazzino DB
try:
    import sqlite3 as _sq3
    _cp = _sq3.connect(cfg.get("db_path"), timeout=10)
    _cp.execute("PRAGMA journal_mode=WAL")
    for _tbak in ['veicoli_bak','veicoli_old','veicoli_tmp']:
        if _cp.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (_tbak,)).fetchone():
            _cp.execute("DROP TABLE IF EXISTS ["+_tbak+"]")
            log.info(f"Rimossa tabella residua: {_tbak}")
    _cp.commit()
    _cp.close()
except Exception as _ce:
    log.warning(f"Pulizia avvio: {_ce}")


# ── Crea tabelle inventario se non esistono ───────────────────────────────────
try:
    import sqlite3 as _sq_inv
    _inv_conn = _sq_inv.connect(cfg.get("db_path"), timeout=10)
    _inv_conn.executescript("""
    CREATE TABLE IF NOT EXISTS sessioni_inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        categoria TEXT,
        filtro_json TEXT,
        stato TEXT DEFAULT 'attiva',
        totale_pezzi INTEGER DEFAULT 0,
        confermati INTEGER DEFAULT 0,
        mancanti INTEGER DEFAULT 0,
        sospesi INTEGER DEFAULT 0,
        creato_da INTEGER,
        creato_il TEXT DEFAULT (datetime('now')),
        chiuso_il TEXT
    );
    CREATE TABLE IF NOT EXISTS inventario_righe (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessione_id INTEGER NOT NULL,
        componente_id INTEGER NOT NULL,
        stato TEXT DEFAULT 'sospeso',
        qty_attesa INTEGER DEFAULT 0,
        qty_trovata INTEGER,
        foto_url TEXT,
        note TEXT,
        ordine INTEGER DEFAULT 0,
        aggiornato_il TEXT,
        FOREIGN KEY(sessione_id) REFERENCES sessioni_inventario(id)
    );
    CREATE INDEX IF NOT EXISTS idx_inv_sessione ON inventario_righe(sessione_id);
    CREATE INDEX IF NOT EXISTS idx_inv_stato ON inventario_righe(sessione_id, stato);
    """)
    _inv_conn.commit()
    _inv_conn.close()
    log.info("Tabelle inventario pronte")
except Exception as _e:
    log.warning(f"Tabelle inventario: {_e}")

# ── Scrittura sicura: tutte le operazioni passano da qui ─────────────────────
def db_write(statements: list):
    """Esegue più statement in una singola transazione atomica."""
    with db._write_lock:
        conn = db.get_connection()
        try:
            for sql, params in statements:
                conn.execute(sql, params)
            conn.commit()
            conn.close()
        except Exception as e:
            conn.rollback()
            raise

def require_login(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            # API → 401 JSON; pagine → redirect login
            if request.path.startswith('/api/'):
                return jsonify({"ok": False, "msg": "Non autenticato"}), 401
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper

def cu():
    return session.get("user", {})

# ══════════════════════════════════════════════════════════════════════════════
# PAGINE
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    if session.get("user"):
        return redirect("/dashboard")
    return redirect("/login")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/dashboard")
@require_login
def dashboard():
    return render_template("dashboard.html", user=session["user"])

@app.route("/magazzino")
@require_login
def magazzino():
    return render_template("magazzino.html", user=session["user"])

@app.route("/storico")
@require_login
def storico():
    return render_template("storico.html", user=session["user"])

# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/login", methods=["POST"])
def api_login():
    import hashlib
    d = request.json or {}
    pwd_hash = hashlib.sha256(d.get("password","").encode()).hexdigest()
    user = db.fetchone("SELECT * FROM utenti WHERE username=?",
                       (d.get("username","").strip(),))
    if not user:
        return jsonify({"ok": False, "msg": "Utente non trovato"}), 401
    if user.get("eliminato", 0) == 1:
        return jsonify({"ok": False, "msg": "Account eliminato"}), 403
    if user.get("attivo", 1) == 0:
        return jsonify({"ok": False, "msg": "Account disabilitato"}), 403
    if user["password_hash"] != pwd_hash:
        return jsonify({"ok": False, "msg": "Password errata"}), 401
    session["user"] = {"id": user["id"], "username": user["username"],
                       "ruolo": user["ruolo"], "nome": (user.get("nome_completo") or user["username"])}
    try:
        db_write([("INSERT INTO log_operazioni(utente_id,username,modulo,azione) VALUES(?,?,?,?)",
                   (user["id"], user["username"], "AUTH", "LOGIN"))])
    except: pass
    # Redirect: mobile -> inventario-mobile, ?next= -> pagina richiesta, default -> dashboard
    ua     = request.headers.get("User-Agent","").lower()
    is_mob = any(x in ua for x in ["mobile","android","iphone","ipad","mobi"])
    nxt    = (request.json or {}).get("next","")
    if nxt:
        redir = nxt
    elif is_mob:
        redir = "/inventario-mobile"
    else:
        redir = "/dashboard"
    return jsonify({"ok": True, "user": session["user"], "redirect": redir})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    u = cu()
    if u:
        db_write([("INSERT INTO log_operazioni(utente_id,username,modulo,azione) VALUES(?,?,?,?)",
                   (u.get("id"), u.get("username"), "AUTH", "LOGOUT"))])
    session.clear()
    return jsonify({"ok": True})

# ══════════════════════════════════════════════════════════════════════════════
# COMPONENTI
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/magazzino/componenti")
@require_login
def api_componenti():
    p = request.args
    sql = "SELECT * FROM v_giacenza WHERE 1=1"
    params = []
    if p.get("q"):
        t = f"%{p['q']}%"
        sql += " AND (cmp LIKE ? OR articolo LIKE ? OR descrizione LIKE ? OR marca LIKE ? OR modello LIKE ? OR colore LIKE ?)"
        params += [t,t,t,t,t,t]
    if p.get("es_min","").isdigit():
        sql += " AND esistenza >= ?"; params.append(int(p["es_min"]))
    if p.get("es_max","").isdigit():
        sql += " AND esistenza <= ?"; params.append(int(p["es_max"]))
    if p.get("sotto_scorta") == "1":
        sql += " AND esistenza <= scorta AND scorta > 0"
    if p.get("marca"):
        sql += " AND marca LIKE ?"; params.append(f"%{p['marca']}%")
    if p.get("modello"):
        sql += " AND modello LIKE ?"; params.append(f"%{p['modello']}%")
    sql += " ORDER BY articolo"
    return jsonify(db.fetchall(sql, params))

@app.route("/api/magazzino/componenti", methods=["POST"])
@require_login
def api_crea_componente():
    dati = request.json or {}
    if not dati.get("codice"):
        return jsonify({"ok": False, "msg": "Codice obbligatorio"}), 400
    if not dati.get("nome"):
        return jsonify({"ok": False, "msg": "Nome obbligatorio"}), 400
    if db.fetchone("SELECT id FROM componenti WHERE codice=? AND eliminato=0", (dati["codice"],)):
        return jsonify({"ok": False, "msg": f"Codice '{dati['codice']}' già esistente"}), 400

    u = cu()
    for campo in ("anno_da","anno_a","scorta_minima"):
        v = str(dati.get(campo,"") or "")
        dati[campo] = int(v) if v.isdigit() else None

    try:
        # Tutti i campi accettati
        CAMPI_COMP = [
            "codice","nome","descrizione","tipologia","categoria","sottocategoria",
            "cod_udm","cod_iva","listino1","listino2","listino3",
            "marca","modello","cod_modello","colore","cilindrata","carburante",
            "versione","anno_da","anno_a","intervallo","scorta_minima",
            "note","cod_barre","internet","extra1","extra2","extra3","extra4",
            "cod_fornitore","fornitore","cod_prod_forn","prezzo_forn",
            "note_fornitura","ord_multipli","gg_ordine","ubicazione",
            "stato_magazzino","immagine_path","files_path"
        ]
        campi_validi = {k: dati.get(k) for k in CAMPI_COMP if dati.get(k) is not None and str(dati.get(k,"")).strip() != ""}
        campi_validi["pubblicato"] = 0
        campi_validi["creato_da"] = u.get("id")

        # Conversioni numeriche
        for nk in ("anno_da","anno_a","scorta_minima","ord_multipli","gg_ordine"):
            if nk in campi_validi:
                try: campi_validi[nk] = int(float(campi_validi[nk]))
                except: del campi_validi[nk]
        for fk in ("listino1","listino2","listino3","prezzo_forn"):
            if fk in campi_validi:
                try: campi_validi[fk] = float(campi_validi[fk])
                except: del campi_validi[fk]

        with db._write_lock:
            conn = db.get_connection()
            try:
                cols_str = ", ".join(campi_validi.keys())
                placeholders = ", ".join(["?"] * len(campi_validi))
                cur = conn.execute(
                    f"INSERT INTO componenti ({cols_str}) VALUES ({placeholders})",
                    list(campi_validi.values()))
                comp_id = cur.lastrowid
                conn.execute("INSERT OR IGNORE INTO magazzino(componente_id,scorta_minima) VALUES(?,?)",
                             (comp_id, campi_validi.get("scorta_minima", 0)))
                conn.execute("""INSERT INTO log_operazioni
                    (utente_id,username,modulo,azione,tabella,record_id,dati_nuovi)
                    VALUES(?,?,?,?,?,?,?)""",
                    (u.get("id"),u.get("username"),"MAGAZZINO","CREA","componenti",comp_id,str(campi_validi)))
                conn.commit()
                conn.close()
                return jsonify({"ok": True, "msg": "Componente creato", "id": comp_id})
            except Exception as e:
                conn.rollback()
                return jsonify({"ok": False, "msg": str(e)}), 500
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/magazzino/componenti/<int:cid>", methods=["PUT"])
@require_login
def api_modifica_componente(cid):
    dati = request.json or {}
    u = cu()
    prec = db.fetchone("SELECT * FROM componenti WHERE id=? AND eliminato=0", (cid,))
    if not prec:
        return jsonify({"ok": False, "msg": "Componente non trovato"}), 404

    def v(key, default=None):
        return dati[key] if key in dati else (prec.get(key) if default is None else default)

    try:
        db_write([
            ("""UPDATE componenti SET
                nome=?, descrizione=?, marca=?, modello=?, cod_modello=?,
                colore=?, cilindrata=?, carburante=?, versione=?, intervallo=?,
                anno_da=?, anno_a=?, scorta_minima=?, note=?,
                immagine_path=?, pubblicato=?, modificato_il=datetime('now')
             WHERE id=? AND eliminato=0""",
             (v("nome"), v("descrizione"), v("marca"), v("modello"), v("cod_modello"),
              v("colore"), v("cilindrata"), v("carburante"), v("versione"), v("intervallo"),
              v("anno_da"), v("anno_a"), v("scorta_minima"), v("note"),
              v("immagine_path"), v("pubblicato", 0), cid)),
            ("""INSERT INTO log_operazioni
                (utente_id,username,modulo,azione,tabella,record_id)
                VALUES(?,?,?,?,?,?)""",
             (u.get("id"),u.get("username"),"MAGAZZINO","MODIFICA","componenti",cid))
        ])
        return jsonify({"ok": True, "msg": "Componente aggiornato"})
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Errore: {e}"}), 500

@app.route("/api/magazzino/componenti/<int:cid>", methods=["DELETE"])
@require_login
def api_elimina_componente(cid):
    u = cu()
    try:
        db_write([
            ("UPDATE componenti SET eliminato=1, modificato_il=datetime('now') WHERE id=?", (cid,)),
            ("""INSERT INTO log_operazioni
                (utente_id,username,modulo,azione,tabella,record_id)
                VALUES(?,?,?,?,?,?)""",
             (u.get("id"),u.get("username"),"MAGAZZINO","ELIMINA","componenti",cid))
        ])
        return jsonify({"ok": True, "msg": "Componente eliminato"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/magazzino/prossimo-codice")
@require_login
def api_prossimo_codice():
    import re
    # Legge TUTTI i codici e trova il massimo numerico
    rows = db.fetchall("SELECT codice FROM componenti WHERE eliminato=0")
    max_num = 0
    prefisso = ""
    lunghezza = 0

    for row in rows:
        cod = row.get("codice","") or ""
        m = re.search(r'(\d+)$', cod)
        if m:
            n = int(m.group(1))
            if n > max_num:
                max_num   = n
                prefisso  = cod[:m.start()]
                lunghezza = len(m.group(1))

    if max_num == 0:
        return jsonify({"codice": ""})

    nuovo_num = max_num + 1
    # Mantieni la stessa lunghezza minima del numero (es. 18725 → 18726)
    nuovo = prefisso + str(nuovo_num).zfill(max(lunghezza, len(str(nuovo_num))))
    return jsonify({"codice": nuovo, "ultimo": f"{prefisso}{max_num}"})

# ── Info movimenti per pannello laterale ─────────────────────────────────────
@app.route("/api/magazzino/info-movimenti/<int:cid>")
@require_login
def api_info_movimenti(cid):
    rows = db.fetchall("""
        SELECT tipo, COUNT(*) as cnt, MAX(creato_il) as ultima
        FROM movimenti_magazzino WHERE componente_id=?
        GROUP BY tipo
    """, (cid,))
    r = {"carichi": 0, "scarichi": 0,
         "ultima_data_carico": None, "ultima_data_scarico": None}
    for row in rows:
        if row["tipo"] == "carico":
            r["carichi"] = row["cnt"]; r["ultima_data_carico"] = row["ultima"]
        elif row["tipo"] == "scarico":
            r["scarichi"] = row["cnt"]; r["ultima_data_scarico"] = row["ultima"]
    return jsonify(r)

# ══════════════════════════════════════════════════════════════════════════════
# MOVIMENTI
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/magazzino/movimento", methods=["POST"])
@require_login
def api_movimento():
    d    = request.json or {}
    cid  = d.get("componente_id")
    tipo = d.get("tipo")
    qty  = int(d.get("quantita", 0))
    rif  = d.get("riferimento")
    note = d.get("note")
    u    = cu()

    if not cid or not tipo or qty <= 0:
        return jsonify({"ok": False, "msg": "Dati mancanti"}), 400

    comp = db.fetchone("SELECT esistenza FROM v_giacenza WHERE componente_id=?", (cid,))
    if not comp:
        return jsonify({"ok": False, "msg": "Componente non trovato"}), 404

    gia_prima = comp["esistenza"] or 0
    if tipo == "scarico" and gia_prima < qty:
        return jsonify({"ok": False, "msg": f"Giacenza insufficiente (disponibile: {gia_prima})"}), 400

    gia_dopo = gia_prima + qty if tipo == "carico" else gia_prima - qty

    try:
        with db._write_lock:
            conn = db.get_connection()
            try:
                conn.execute("PRAGMA foreign_keys=OFF")  # disabilita temporaneamente FK
                # Controlla colonne disponibili in movimenti_magazzino
                mov_cols = [r[1] for r in conn.execute("PRAGMA table_info(movimenti_magazzino)").fetchall()]
                # Costruisci insert dinamico
                m_fields = ["componente_id","tipo","quantita","riferimento","note","utente_id"]
                m_vals   = [cid, tipo, qty, rif, note, u.get("id")]
                for col_name, val in [("quantita_prima", gia_prima),("esistenza_prima", gia_prima),
                                      ("quantita_dopo",  gia_dopo), ("esistenza_dopo",  gia_dopo)]:
                    if col_name in mov_cols and col_name not in m_fields:
                        m_fields.append(col_name); m_vals.append(val)
                        break  # usa solo il primo che trova
                for col_name, val in [("quantita_dopo", gia_dopo),("esistenza_dopo", gia_dopo)]:
                    if col_name in mov_cols and col_name not in m_fields:
                        m_fields.append(col_name); m_vals.append(val)
                        break
                conn.execute(
                    "INSERT INTO movimenti_magazzino ("+",".join(m_fields)+") VALUES ("+",".join(["?"]*len(m_fields))+")",
                    m_vals)
                conn.execute("UPDATE magazzino SET aggiornato_il=datetime('now') WHERE componente_id=?", (cid,))
                try:
                    conn.execute(
                        "INSERT INTO log_operazioni (utente_id,username,modulo,azione,tabella,record_id,dati_precedenti,dati_nuovi) VALUES(?,?,?,?,?,?,?,?)",
                        (u.get("id"),u.get("username"),"MAGAZZINO",tipo.upper(),"movimenti_magazzino",cid,str({"g":gia_prima}),str({"g":gia_dopo})))
                except Exception:
                    pass  # log non bloccante
                conn.commit()
            finally:
                conn.close()
        # Recupera id movimento appena inserito
        mov_id = None
        try:
            last = db.fetchone("SELECT id FROM movimenti_magazzino WHERE componente_id=? ORDER BY id DESC LIMIT 1", (cid,))
            if last: mov_id = last["id"]
        except: pass
        return jsonify({"ok": True, "msg": f"{tipo.capitalize()} di {qty} pz completato",
                        "giacenza": gia_dopo, "movimento_id": mov_id})
    except Exception as e:
        log.error(f"api_movimento: {e}")
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/magazzino/movimenti")
@require_login
def api_movimenti():
    p = request.args
    sql = """SELECT
             m.*,
             c.codice          AS cmp,
             c.nome            AS articolo,
             c.marca           AS produttore,
             c.categoria,
             c.sottocategoria,
             c.modello,
             c.colore,
             c.cilindrata,
             c.carburante,
             c.tipologia,
             c.ubicazione,
             c.stato_magazzino,
             c.extra1,
             c.extra2,
             c.extra3,
             c.extra4,
             u.username
             FROM movimenti_magazzino m
             LEFT JOIN componenti c ON c.id = m.componente_id
             LEFT JOIN utenti     u ON u.id = m.utente_id
             WHERE 1=1"""
    params = []
    if p.get("componente_id"):
        sql += " AND m.componente_id=?"; params.append(int(p["componente_id"]))
    if p.get("tipo"):
        sql += " AND m.tipo=?"; params.append(p["tipo"])
    if p.get("anno"):
        sql += " AND strftime('%Y',m.creato_il)=?"; params.append(p["anno"])
    if p.get("mese"):
        sql += " AND strftime('%m',m.creato_il)=?"; params.append(p["mese"].zfill(2))
    sql += " ORDER BY m.creato_il DESC"
    # Nessun LIMIT
    return jsonify(db.fetchall(sql, params))

@app.route("/api/magazzino/movimenti/albero")
@require_login
def api_movimenti_albero():
    """Struttura anni → mesi disponibili nello storico."""
    rows = db.fetchall("""
        SELECT DISTINCT strftime('%Y',creato_il) AS anno,
                        strftime('%m',creato_il) AS mese
        FROM movimenti_magazzino
        ORDER BY anno DESC, mese DESC
    """)
    tree = {}
    for r in rows:
        a, m = r["anno"], r["mese"]
        tree.setdefault(a, [])
        if m not in tree[a]: tree[a].append(m)
    return jsonify(tree)

# ══════════════════════════════════════════════════════════════════════════════
# STATS / INVENTARIO / LISTA ACQUISTI
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/magazzino/movimenti/<int:mid>", methods=["DELETE"])
@require_login
def api_elimina_movimento(mid):
    """Elimina fisicamente un movimento (usato da undo)."""
    u = cu()
    try:
        mov = db.fetchone("SELECT * FROM movimenti_magazzino WHERE id=?", (mid,))
        if not mov:
            return jsonify({"ok": False, "msg": "Movimento non trovato"}), 404
        with db._write_lock:
            conn = db.get_connection()
            try:
                conn.execute("DELETE FROM movimenti_magazzino WHERE id=?", (mid,))
                conn.execute("""INSERT INTO log_operazioni
                    (utente_id,username,modulo,azione,tabella,record_id)
                    VALUES(?,?,?,?,?,?)""",
                    (u.get("id"),u.get("username"),"MAGAZZINO","UNDO_DELETE","movimenti_magazzino",mid))
                conn.commit()
            finally:
                conn.close()
        return jsonify({"ok": True, "msg": "Movimento annullato", "movimento": dict(mov)})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/magazzino/stats")
@require_login
def api_stats():
    t  = db.fetchone("SELECT COUNT(*) AS n FROM v_giacenza")
    s  = db.fetchone("SELECT COUNT(*) AS n FROM v_giacenza WHERE esistenza <= scorta AND scorta > 0")
    u  = db.fetchone("SELECT creato_il FROM movimenti_magazzino ORDER BY id DESC LIMIT 1")
    pz = db.fetchone("SELECT COALESCE(SUM(esistenza),0) AS n FROM v_giacenza")
    val= db.fetchone("""SELECT COALESCE(SUM(v.esistenza * COALESCE(c.listino1,0)),0) AS n
                         FROM v_giacenza v JOIN componenti c ON c.id=v.componente_id
                         WHERE v.esistenza>0 AND c.listino1>0""")
    foto = db.fetchone("SELECT COUNT(*) AS n FROM componenti WHERE immagine_path IS NOT NULL AND immagine_path!='' AND eliminato=0")
    return jsonify({"totale_componenti": t["n"] if t else 0,
                    "sotto_scorta": s["n"] if s else 0,
                    "ultimo_movimento": u["creato_il"] if u else "—",
                    "pezzi_totali": pz["n"] if pz else 0,
                    "valore_stima": round(float(val["n"]) if val else 0, 2),
                    "con_foto": foto["n"] if foto else 0})

@app.route("/api/backup", methods=["POST"])
@require_login
def api_backup():
    import shutil, datetime
    try:
        src  = cfg.get("db_path")
        bdir = ROOT / "backup"
        bdir.mkdir(exist_ok=True)
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dst  = bdir / f"perilcar_{ts}.db"
        shutil.copy2(src, dst)
        backups = sorted(bdir.glob("perilcar_*.db"))
        for old in backups[:-30]:
            old.unlink()
        u = cu()
        db_write([("INSERT INTO log_operazioni(utente_id,username,modulo,azione) VALUES(?,?,?,?)",
                   (u.get("id"), u.get("username"), "SISTEMA", "BACKUP"))])
        return jsonify({"ok": True, "msg": f"Backup salvato: {dst.name}", "file": dst.name})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/magazzino/inventario")
@require_login
def api_inventario():
    return jsonify(db.fetchall("""
        SELECT cmp, articolo, descrizione, esistenza, scorta,
               marca, modello, cod_modello, colore,
               cilindrata, carburante, versione,
               anno_da, anno_a, intervallo, nota
        FROM v_giacenza ORDER BY articolo
    """))

@app.route("/api/magazzino/lista-acquisti")
@require_login
def api_lista_acquisti():
    p = request.args
    marca   = p.get("marca","").strip()
    modello = p.get("modello","").strip()
    try: soglia = int(p.get("soglia", 1))
    except: soglia = 1

    sql = "SELECT * FROM v_giacenza WHERE esistenza < ?"
    params = [soglia]
    if marca:
        sql += " AND marca LIKE ?"; params.append(f"%{marca}%")
    if modello:
        sql += " AND modello LIKE ?"; params.append(f"%{modello}%")
    sql += " ORDER BY articolo"
    return jsonify(db.fetchall(sql, params))

# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD IMMAGINI
# ══════════════════════════════════════════════════════════════════════════════

ALLOWED = {"png","jpg","jpeg","gif","webp","pdf","xlsx","xls","docx","zip"}

@app.route("/api/magazzino/upload-file/<int:cid>", methods=["POST"])
@require_login
def api_upload_file(cid):
    """Upload immagini o file allegati a un componente (anche multipli)."""
    if "file" not in request.files:
        return jsonify({"ok": False, "msg": "Nessun file"}), 400
    f   = request.files["file"]
    ext = f.filename.rsplit(".",1)[-1].lower() if "." in f.filename else ""
    if ext not in ALLOWED:
        return jsonify({"ok": False, "msg": f"Tipo .{ext} non permesso"}), 400
    import uuid
    fname = f"comp_{cid}_{uuid.uuid4().hex[:8]}.{ext}"
    f.save(UPLOAD_FOLDER / fname)
    url = f"/static/uploads/{fname}"
    # Aggiungi alla lista files_path (separatore |)
    comp = db.fetchone("SELECT files_path, immagine_path FROM componenti WHERE id=?", (cid,))
    imgs_ext = {"png","jpg","jpeg","gif","webp"}
    existing_files = comp["files_path"] or ""
    new_files = (existing_files + "|" + url).strip("|") if existing_files else url
    # Se è immagine e non c'è ancora immagine principale, impostala
    new_img = comp["immagine_path"]
    if ext in imgs_ext and not new_img:
        new_img = url
    try:
        db_write([("""UPDATE componenti
                      SET files_path=?, immagine_path=?, modificato_il=datetime('now')
                      WHERE id=?""", (new_files, new_img, cid))])
        return jsonify({"ok": True, "url": url, "files": new_files.split("|") if new_files else []})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/magazzino/delete-file/<int:cid>", methods=["POST"])
@require_login
def api_delete_file(cid):
    """Rimuove un file dalla lista allegati."""
    url_da_rimuovere = (request.json or {}).get("url","")
    comp = db.fetchone("SELECT files_path, immagine_path FROM componenti WHERE id=?", (cid,))
    files = [f for f in (comp["files_path"] or "").split("|") if f and f != url_da_rimuovere]
    new_files = "|".join(files)
    new_img   = comp["immagine_path"] if comp["immagine_path"] != url_da_rimuovere else (files[0] if files else None)
    try:
        db_write([("""UPDATE componenti SET files_path=?, immagine_path=?, modificato_il=datetime('now') WHERE id=?""",
                   (new_files, new_img, cid))])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
# IMPORT / EXPORT EXCEL — formato Danea + generico
# ══════════════════════════════════════════════════════════════════════════════

# Mappa colonne Danea → campi DB (case-insensitive)
DANEA_MAP = {
    "cod.":             "codice",
    "descrizione":      "nome",
    "tipologia":        "tipologia",
    "categoria":        "categoria",
    "sottocategoria":   "sottocategoria",
    "cod. udm":         "cod_udm",
    "cod. iva":         "cod_iva",
    "listino 1":        "listino1",
    "listino 2":        "listino2",
    "listino 3":        "listino3",
    "note":             "nota",
    "cod. a barre":     "cod_barre",
    "internet":         "internet",
    "produttore":       "marca",
    "extra 1":          "extra1",
    "extra 2":          "extra2",
    "extra 3":          "extra3",
    "extra 4":          "extra4",
    "cod. fornitore":   "cod_fornitore",
    "fornitore":        "fornitore",
    "cod. prod. forn.": "cod_prod_forn",
    "prezzo forn.":     "prezzo_forn",
    "note fornitura":   "note_fornitura",
    "ord. a multipli di": "ord_multipli",
    "gg. ordine":       "gg_ordine",
    "scorta min.":      "scorta_minima",
    "ubicazione":       "ubicazione",
    "q.tà giacenza":    "esistenza",
    "stato magazzino":  "stato_magazzino",
    "immagine":         "immagine_path",
    # alias generici
    "cmp":              "codice",
    "articolo":         "nome",
    "es":               "esistenza",
    "scorta minima":    "scorta_minima",
    "anno da":          "anno_da",
    "anno a":           "anno_a",
    "marca":            "marca",
    "modello":          "modello",
    "colore":           "colore",
}

@app.route("/api/magazzino/export-excel")
@require_login
def api_export_excel():
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.drawing.image import Image as XLImage
    from PIL import Image as PILImage
    import tempfile, os

    rows = db.fetchall("SELECT * FROM v_giacenza ORDER BY articolo")
    wb   = openpyxl.Workbook()
    ws   = wb.active
    ws.title = "Magazzino"

    # Stili
    hdr_fill = PatternFill("solid", fgColor="E94C00")
    alt_fill = PatternFill("solid", fgColor="FFF3EE")
    thin = Side(style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    hdr_font = Font(bold=True, color="FFFFFF", size=10)
    cell_font = Font(size=10)
    center = Alignment(horizontal="center", vertical="center")
    left   = Alignment(horizontal="left",   vertical="center", wrap_text=True)

    cols = [
        ("Cod.",             "cmp",            10),
        ("Descrizione",      "articolo",       36),
        ("Tipologia",        "tipologia",      18),
        ("Categoria",        "categoria",      14),
        ("Sottocategoria",   "sottocategoria", 14),
        ("Cod. Udm",         "cod_udm",        10),
        ("Cod. Iva",         "cod_iva",        10),
        ("Listino 1",        "listino1",       12),
        ("Listino 2",        "listino2",       12),
        ("Listino 3",        "listino3",       12),
        ("Note",             "nota",           30),
        ("Cod. a barre",     "cod_barre",      14),
        ("Produttore",       "marca",          16),
        ("Extra 1",          "extra1",         12),
        ("Extra 2",          "extra2",         12),
        ("Extra 3",          "extra3",         12),
        ("Extra 4",          "extra4",         12),
        ("Cod. fornitore",   "cod_fornitore",  14),
        ("Fornitore",        "fornitore",      16),
        ("Prezzo forn.",     "prezzo_forn",    12),
        ("Scorta min.",      "scorta",         10),
        ("Ubicazione",       "ubicazione",     18),
        ("Q.tà giacenza",    "esistenza",      12),
        ("Stato magazzino",  "stato_magazzino",14),
        ("Modello",          "modello",        16),
        ("Colore",           "colore",         12),
        ("Cilindrata",       "cilindrata",     12),
        ("Carburante",       "carburante",     12),
        ("Versione",         "versione",       12),
        ("Anno da",          "anno_da",        10),
        ("Anno a",           "anno_a",         10),
        ("Foto",             "files_path",     20),
    ]

    NUM_KEYS = {"esistenza","scorta","listino1","listino2","listino3",
                "prezzo_forn","ord_multipli","gg_ordine","anno_da","anno_a"}

    # Intestazioni
    for c, (label, _, w) in enumerate(cols, 1):
        cell = ws.cell(row=1, column=c, value=label)
        cell.font       = hdr_font
        cell.fill       = hdr_fill
        cell.alignment  = center
        cell.border     = border
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[1].height = 20
    ws.freeze_panes = "A2"

    # Dati
    foto_col_idx = next((c+1 for c,(l,k,w) in enumerate(cols) if k=="files_path"), None)
    tmp_files = []

    for ri, r in enumerate(rows, 2):
        is_alt = (ri % 2 == 0)
        ws.row_dimensions[ri].height = 15  # altezza normale

        for ci, (_, key, _) in enumerate(cols, 1):
            if key == "files_path":
                # Scrivi URL come testo per ora, foto sotto
                paths = [p for p in (r.get("files_path") or "").split("|") if p]
                if not paths and r.get("immagine_path"):
                    paths = [r.get("immagine_path")]
                foto_cell = ws.cell(row=ri, column=ci, value="")
                foto_cell.border    = border
                foto_cell.alignment = center
                if paths:
                    # Inserisci immagine
                    img_url = paths[0]
                    if img_url.startswith("/static/"):
                        img_path = ROOT / "web" / img_url[1:]
                    else:
                        img_path = None
                    if img_path and img_path.exists():
                        try:
                            # Ridimensiona a 60x60 con PIL
                            pil = PILImage.open(str(img_path))
                            pil.thumbnail((60, 60), PILImage.LANCZOS)
                            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                            pil.save(tmp.name, "PNG")
                            tmp.close()
                            tmp_files.append(tmp.name)
                            img = XLImage(tmp.name)
                            img.anchor = get_column_letter(ci) + str(ri)
                            ws.add_image(img)
                            ws.row_dimensions[ri].height = 48
                        except Exception as e:
                            log.warning(f"Foto Excel fallita: {e}")
                            cell.value = "📷"
            else:
                val = r.get(key)
                if val is None or val == "":
                    val = 0 if key in NUM_KEYS else ""
                c2 = ws.cell(row=ri, column=ci, value=val)
                c2.font      = cell_font
                c2.border    = border
                c2.alignment = center if key in NUM_KEYS else left
                if is_alt:
                    c2.fill = alt_fill

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    # Pulisci file temporanei
    for f in tmp_files:
        try: os.unlink(f)
        except: pass

    return send_file(buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True, download_name="perilcar_magazzino.xlsx")


@app.route("/api/magazzino/import-excel", methods=["POST"])
@require_login
def api_import_excel():
    if "file" not in request.files:
        return jsonify({"ok": False, "msg": "Nessun file"}), 400
    f = request.files["file"]
    if not f.filename.lower().endswith((".xlsx",".xls")):
        return jsonify({"ok": False, "msg": "Solo file .xlsx o .xls"}), 400

    import openpyxl
    u = cu()

    try:
        wb   = openpyxl.load_workbook(f, data_only=True)
        ws   = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            return jsonify({"ok": False, "msg": "File vuoto o senza dati"}), 400

        # Mappa intestazioni → indice colonna
        header  = [str(h or "").strip().lower() for h in rows[0]]
        col_map = {}
        for i, h in enumerate(header):
            field = DANEA_MAP.get(h, h.replace(" ","_").replace(".","").replace("'",""))
            col_map[field] = i

        def get(row, field, default=None):
            idx = col_map.get(field)
            if idx is None or idx >= len(row): return default
            v = row[idx]
            if v is None: return default
            # datetime → stringa
            import datetime
            if isinstance(v, (datetime.datetime, datetime.date)):
                return str(v.year)
            return str(v).strip() if str(v).strip() not in ("None","nan","") else default

        def toint(row, field):
            try: v = get(row, field, "0"); return int(float(v)) if v else 0
            except: return 0

        def tofloat(row, field):
            try: v = get(row, field, "0"); return float(v) if v else 0.0
            except: return 0.0

        importati = 0; saltati = 0; aggiornati = 0; row_n = 1

        with db._write_lock:
            conn = db.get_connection()
            try:
                for row in rows[1:]:
                    row_n += 1
                    codice = get(row, "codice")
                    nome   = get(row, "nome")
                    if not codice or not nome:
                        saltati += 1; continue

                    scorta    = toint(row, "scorta_minima")
                    esistenza = toint(row, "esistenza")

                    campi = {
                        "nome":           nome,
                        "tipologia":      get(row, "tipologia"),
                        "categoria":      get(row, "categoria"),
                        "sottocategoria": get(row, "sottocategoria"),
                        "cod_udm":        get(row, "cod_udm"),
                        "cod_iva":        get(row, "cod_iva"),
                        "listino1":       tofloat(row, "listino1"),
                        "listino2":       tofloat(row, "listino2"),
                        "listino3":       tofloat(row, "listino3"),
                        "note":           get(row, "nota"),
                        "cod_barre":      get(row, "cod_barre"),
                        "internet":       get(row, "internet"),
                        "marca":          get(row, "marca"),
                        "extra1":         get(row, "extra1"),
                        "extra2":         get(row, "extra2"),
                        "extra3":         get(row, "extra3"),
                        "extra4":         get(row, "extra4"),
                        "cod_fornitore":  get(row, "cod_fornitore"),
                        "fornitore":      get(row, "fornitore"),
                        "cod_prod_forn":  get(row, "cod_prod_forn"),
                        "prezzo_forn":    tofloat(row, "prezzo_forn"),
                        "note_fornitura": get(row, "note_fornitura"),
                        "ord_multipli":   toint(row, "ord_multipli"),
                        "gg_ordine":      toint(row, "gg_ordine"),
                        "scorta_minima":  scorta,
                        "ubicazione":     get(row, "ubicazione"),
                        "stato_magazzino":get(row, "stato_magazzino"),
                    }

                    existing = conn.execute(
                        "SELECT id FROM componenti WHERE codice=? AND eliminato=0",
                        (codice,)).fetchone()

                    if existing:
                        comp_id = existing[0]
                        sets    = ", ".join(f"{k}=?" for k in campi)
                        vals    = list(campi.values()) + [comp_id]
                        conn.execute(
                            f"UPDATE componenti SET {sets}, modificato_il=datetime('now') WHERE id=?",
                            vals)
                        aggiornati += 1
                    else:
                        campi["codice"] = codice
                        campi["pubblicato"] = 0
                        campi["creato_da"]  = u.get("id")
                        cols_str = ", ".join(campi.keys())
                        placeholders = ", ".join(["?"] * len(campi))
                        cur = conn.execute(
                            f"INSERT INTO componenti ({cols_str}) VALUES ({placeholders})",
                            list(campi.values()))
                        comp_id = cur.lastrowid
                        conn.execute(
                            "INSERT OR IGNORE INTO magazzino(componente_id,scorta_minima) VALUES(?,?)",
                            (comp_id, scorta))
                        importati += 1

                    # Carico iniziale se giacenza > 0
                    if esistenza > 0:
                        already = conn.execute(
                            "SELECT id FROM movimenti_magazzino WHERE componente_id=? AND riferimento='Import Excel' LIMIT 1",
                            (comp_id,)).fetchone()
                        if not already:
                            conn.execute("""INSERT INTO movimenti_magazzino
                                (componente_id,tipo,quantita,quantita_prima,quantita_dopo,riferimento,utente_id)
                                VALUES(?,?,?,?,?,?,?)""",
                                (comp_id,"carico",esistenza,0,esistenza,"Import Excel",u.get("id")))

                conn.commit()
                conn.close()
            except Exception as e:
                conn.rollback()
                log.error(f"Import errore riga {row_n}: {e}")
                return jsonify({"ok": False, "msg": f"Errore riga {row_n}: {e}"}), 500

        tot = importati + aggiornati
        return jsonify({"ok": True,
            "msg": f"✅ Import OK: {importati} nuovi, {aggiornati} aggiornati, {saltati} saltati su {tot} totali",
            "importati": importati, "aggiornati": aggiornati, "saltati": saltati})

    except Exception as e:
        log.error(f"Import lettura file: {e}")
        return jsonify({"ok": False, "msg": f"Errore lettura file: {e}"}), 500


@app.route("/api/magazzino/import-excel-stream", methods=["POST"])
@require_login
def api_import_excel_stream():
    """Import Excel - salva su disco locale poi processa per evitare timeout."""
    if "file" not in request.files:
        return jsonify({"ok": False, "msg": "Nessun file"}), 400
    f = request.files["file"]
    if not f.filename.lower().endswith((".xlsx",".xls")):
        return jsonify({"ok": False, "msg": "Solo .xlsx o .xls"}), 400

    import openpyxl, tempfile, os as _os
    u = cu()

    # Salva su disco
    tmp_path = str(ROOT / "db" / "_import_tmp.xlsx")
    f.save(tmp_path)
    log.info(f"File salvato: {tmp_path} ({_os.path.getsize(tmp_path)//1024}KB)")

    try:
        wb = openpyxl.load_workbook(tmp_path, data_only=True, read_only=True)
        ws = wb.active

        header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        header = [str(h or "").strip().lower() for h in header_row]
        col_map = {}
        for i, h in enumerate(header):
            field = DANEA_MAP.get(h, h.replace(" ","_").replace(".","").replace("'",""))
            col_map[field] = i

        def get(row, field, default=None):
            idx = col_map.get(field)
            if idx is None or idx >= len(row): return default
            v = row[idx]
            if v is None: return default
            import datetime
            if isinstance(v, (datetime.datetime, datetime.date)):
                return str(v.year)
            s = str(v).strip()
            return s if s not in ("None","nan","") else default

        def toint(row, field):
            try: v = get(row, field, "0"); return int(float(v)) if v else 0
            except: return 0

        def tofloat(row, field):
            try: v = get(row, field, "0"); return float(v) if v else 0.0
            except: return 0.0

        importati = 0; aggiornati = 0; saltati = 0; row_n = 1
        BATCH = 200

        with db._write_lock:
            conn = db.get_connection()
            try:
                for row in ws.iter_rows(min_row=2, values_only=True):
                    row_n += 1
                    codice = get(row, "codice")
                    nome   = get(row, "nome")
                    if not codice or not nome:
                        saltati += 1; continue

                    scorta    = toint(row, "scorta_minima")
                    esistenza = toint(row, "esistenza")

                    campi = {
                        "nome":           nome,
                        "tipologia":      get(row,"tipologia"),
                        "categoria":      get(row,"categoria"),
                        "sottocategoria": get(row,"sottocategoria"),
                        "cod_udm":        get(row,"cod_udm"),
                        "cod_iva":        get(row,"cod_iva"),
                        "listino1":       tofloat(row,"listino1"),
                        "listino2":       tofloat(row,"listino2"),
                        "listino3":       tofloat(row,"listino3"),
                        "note":           get(row,"nota"),
                        "cod_barre":      get(row,"cod_barre"),
                        "internet":       get(row,"internet"),
                        "marca":          get(row,"marca"),
                        "extra1":         get(row,"extra1"),
                        "extra2":         get(row,"extra2"),
                        "extra3":         get(row,"extra3"),
                        "extra4":         get(row,"extra4"),
                        "cod_fornitore":  get(row,"cod_fornitore"),
                        "fornitore":      get(row,"fornitore"),
                        "cod_prod_forn":  get(row,"cod_prod_forn"),
                        "prezzo_forn":    tofloat(row,"prezzo_forn"),
                        "note_fornitura": get(row,"note_fornitura"),
                        "ord_multipli":   toint(row,"ord_multipli"),
                        "gg_ordine":      toint(row,"gg_ordine"),
                        "scorta_minima":  scorta,
                        "ubicazione":     get(row,"ubicazione"),
                        "stato_magazzino":get(row,"stato_magazzino"),
                    }

                    existing = conn.execute(
                        "SELECT id FROM componenti WHERE codice=? AND eliminato=0",
                        (codice,)).fetchone()

                    if existing:
                        comp_id = existing[0]
                        sets = ", ".join(f"{k}=?" for k in campi)
                        conn.execute(
                            f"UPDATE componenti SET {sets}, modificato_il=datetime('now') WHERE id=?",
                            list(campi.values()) + [comp_id])
                        aggiornati += 1
                    else:
                        campi["codice"]     = codice
                        campi["pubblicato"] = 0
                        campi["creato_da"]  = u.get("id")
                        cols_str     = ", ".join(campi.keys())
                        placeholders = ", ".join(["?"] * len(campi))
                        cur = conn.execute(
                            f"INSERT INTO componenti ({cols_str}) VALUES ({placeholders})",
                            list(campi.values()))
                        comp_id = cur.lastrowid
                        conn.execute(
                            "INSERT OR IGNORE INTO magazzino(componente_id,scorta_minima) VALUES(?,?)",
                            (comp_id, scorta))
                        importati += 1

                    if esistenza > 0:
                        already = conn.execute(
                            "SELECT id FROM movimenti_magazzino WHERE componente_id=? AND riferimento='Import Excel' LIMIT 1",
                            (comp_id,)).fetchone()
                        if not already:
                            conn.execute(
                                "INSERT INTO movimenti_magazzino (componente_id,tipo,quantita,quantita_prima,quantita_dopo,riferimento,utente_id) VALUES(?,?,?,?,?,?,?)",
                                (comp_id,"carico",esistenza,0,esistenza,"Import Excel",u.get("id")))

                    if row_n % BATCH == 0:
                        conn.commit()
                        conn.close()
                        log.info(f"Import progress: riga {row_n}, nuovi={importati}, aggiornati={aggiornati}")
                        socketio.emit("import_progress", {
                            "processed": row_n-1,
                            "importati": importati,
                            "aggiornati": aggiornati
                        })

                conn.commit()
                conn.close()
                wb.close()
            except Exception as e:
                conn.rollback()
                log.error(f"Import errore riga {row_n}: {e}")
                return jsonify({"ok": False, "msg": f"Errore riga {row_n}: {e}"}), 500

    finally:
        try: _os.unlink(tmp_path)
        except: pass

    tot = importati + aggiornati
    socketio.emit("import_done", {"importati": importati, "aggiornati": aggiornati, "saltati": saltati})
    log.info(f"Import completato: {importati} nuovi, {aggiornati} aggiornati, {saltati} saltati")
    return jsonify({"ok": True,
        "msg": f"✅ Import OK: {importati} nuovi, {aggiornati} aggiornati, {saltati} saltati su {tot} totali",
        "importati": importati, "aggiornati": aggiornati, "saltati": saltati})


# ══════════════════════════════════════════════════════════════════════════════
# ASSISTENTE AI — DB cerca i dati, AI formula la risposta
# ══════════════════════════════════════════════════════════════════════════════

import re as _re

def cerca_nel_db(domanda):
    """
    Interpreta la domanda e interroga direttamente il DB.
    Restituisce dati REALI e accurati.
    """
    d = domanda.lower()
    risultati = {}

    # ── DISPONIBILITÀ PEZZO ──────────────────────────────────────────
    # Estrai termini di ricerca (parole > 3 chars che non siano parole comuni)
    stop_words = {'hai','avete','avere','pezzo','pezzi','magazzino','disponibile',
                  'disponibili','quanti','quante','cerco','cerca','serve','hanno',
                  'questo','quella','quello','degli','delle','della','sono','cosa',
                  'come','dove','quando','qual','dici','dirmi','dimmi','voglio'}
    termini = [w for w in _re.findall(r'[a-zA-ZÀ-ÿ]+', d)
               if len(w) > 3 and w not in stop_words]

    if termini:
        # Cerca pezzi che matchano i termini
        conditions = " OR ".join(["(articolo LIKE ? OR marca LIKE ? OR modello LIKE ? OR categoria LIKE ? OR extra1 LIKE ? OR extra2 LIKE ?)"] * len(termini))
        params = []
        for t in termini:
            params.extend([f"%{t}%"] * 6)

        pezzi_trovati = db.fetchall(f"""
            SELECT cmp, articolo, marca, modello, categoria,
                   esistenza, scorta, ubicazione, listino1,
                   cilindrata, carburante, anno_da, anno_a
            FROM v_giacenza
            WHERE {conditions}
            ORDER BY esistenza DESC
            LIMIT 30
        """, params)
        risultati['pezzi_trovati'] = pezzi_trovati

    # ── SOTTO SCORTA ─────────────────────────────────────────────────
    if any(w in d for w in ['scorta','mancano','esauriti','finiti','ordinare','acquistare']):
        sotto = db.fetchall("""
            SELECT cmp, articolo, marca, categoria, esistenza, scorta
            FROM v_giacenza
            WHERE scorta > 0 AND esistenza <= scorta
            ORDER BY (scorta - esistenza) DESC
            LIMIT 20
        """)
        risultati['sotto_scorta'] = sotto

    # ── PIÙ VENDUTI ───────────────────────────────────────────────────
    periodo = 30
    if any(w in d for w in ['anno','annuale','12 mesi']):
        periodo = 365
    elif any(w in d for w in ['settimana','7 giorni']):
        periodo = 7
    elif any(w in d for w in ['trimestre','3 mesi']):
        periodo = 90

    if any(w in d for w in ['venduti','venduto','scaricati','vendite','vendo','vende',
                             'vendono','richiesti','richiesto','popolare']):
        venduti = db.fetchall(f"""
            SELECT c.nome as articolo, c.marca, c.categoria,
                   SUM(m.quantita) as qty, COUNT(*) as n_vendite
            FROM movimenti_magazzino m
            JOIN componenti c ON c.id = m.componente_id
            WHERE m.tipo = 'scarico'
              AND m.creato_il >= date('now', '-{periodo} days')
            GROUP BY m.componente_id
            ORDER BY qty DESC
            LIMIT 15
        """)
        risultati['piu_venduti'] = venduti
        risultati['periodo_giorni'] = periodo

    # ── PEZZI FERMI ───────────────────────────────────────────────────
    if any(w in d for w in ['fermi','fermo','mesi','venduto','movimentati',
                             'giacciono','stagnanti','invenduti']):
        mesi = 6
        if '12' in d or 'anno' in d: mesi = 12
        elif '3' in d or 'trimestre' in d: mesi = 3

        fermi = db.fetchall(f"""
            SELECT c.codice as cmp, c.nome as articolo, c.marca, c.categoria,
                   v.esistenza,
                   MAX(m.creato_il) as ultimo_movimento
            FROM componenti c
            JOIN v_giacenza v ON v.componente_id = c.id
            LEFT JOIN movimenti_magazzino m ON m.componente_id = c.id
            WHERE c.eliminato = 0 AND v.esistenza > 0
            GROUP BY c.id
            HAVING (ultimo_movimento IS NULL
                    OR ultimo_movimento < date('now', '-{mesi*30} days'))
            ORDER BY v.esistenza DESC
            LIMIT 20
        """)
        risultati['pezzi_fermi'] = fermi
        risultati['mesi_fermi'] = mesi

    # ── VALORE MAGAZZINO ──────────────────────────────────────────────
    if any(w in d for w in ['valore','vale','stimato','stima','patrimonio','soldi','euro']):
        valore = db.fetchone("""
            SELECT
                SUM(v.esistenza * COALESCE(c.listino1, 0)) as valore_totale,
                COUNT(CASE WHEN c.listino1 > 0 THEN 1 END) as con_prezzo,
                COUNT(*) as totale,
                SUM(v.esistenza) as pezzi_totali
            FROM v_giacenza v
            JOIN componenti c ON c.id = v.componente_id
            WHERE v.esistenza > 0
        """)
        risultati['valore'] = valore

    # ── STATISTICHE GENERALI ──────────────────────────────────────────
    if any(w in d for w in ['quanti','totale','statistiche','riepilogo',
                             'magazzino','articoli','componenti']):
        stats = db.fetchone("""
            SELECT COUNT(*) as tot,
                   SUM(CASE WHEN esistenza > 0 THEN 1 ELSE 0 END) as disp,
                   SUM(CASE WHEN scorta > 0 AND esistenza <= scorta THEN 1 ELSE 0 END) as sc,
                   SUM(esistenza) as pz_tot
            FROM v_giacenza
        """)
        risultati['statistiche'] = stats

    # ── RECUPERO AUTO ─────────────────────────────────────────────────
    if any(w in d for w in ['recupero','recuperare','smontare','demolire',
                             'arrivata','arrivato','demolizione']):
        # Cerca marca/modello citati nella domanda
        marche_note = ['fiat','ford','volkswagen','vw','golf','opel','renault','peugeot',
                       'citroen','alfa','lancia','bmw','mercedes','audi','toyota','nissan',
                       'hyundai','kia','seat','skoda','volvo','smart','mini','jeep']
        marca_trovata = next((m for m in marche_note if m in d), None)

        if marca_trovata:
            disponibili = db.fetchall("""
                SELECT articolo, categoria, esistenza, scorta, ubicazione
                FROM v_giacenza
                WHERE LOWER(marca) LIKE ?
                  AND esistenza > 0
                ORDER BY categoria, articolo
                LIMIT 40
            """, [f"%{marca_trovata}%"])
            risultati['recupero_auto'] = disponibili
            risultati['marca_recupero'] = marca_trovata

    return risultati


def formatta_risultati(risultati, domanda):
    """Formatta i risultati DB in testo chiaro per l'AI."""
    parti = []

    if risultati.get('pezzi_trovati') is not None:
        pezzi = risultati['pezzi_trovati']
        if pezzi:
            parti.append("PEZZI TROVATI NEL MAGAZZINO (" + str(len(pezzi)) + " risultati):")
            for p in pezzi[:15]:
                es = p['esistenza'] or 0
                stato = "DISPONIBILE" if es > 0 else "ESAURITO"
                riga = f"- {p['articolo']} | {p['marca'] or ''} {p['modello'] or ''} | {stato} | Quantità: {es}"
                if p.get('ubicazione'): riga += f" | Posizione: {p['ubicazione']}"
                if p.get('listino1') and p['listino1'] > 0: riga += f" | Prezzo: €{p['listino1']}"
                if p.get('anno_da'): riga += f" | Anno: {p['anno_da']}"
                parti.append(riga)
        else:
            parti.append("RICERCA NEL MAGAZZINO: Nessun pezzo trovato con questi criteri.")

    if risultati.get('sotto_scorta'):
        sotto = risultati['sotto_scorta']
        parti.append(f"PEZZI SOTTO SCORTA ({len(sotto)} articoli da riordinare):")
        for p in sotto:
            parti.append(f"- {p['articolo']} | {p['marca'] or ''} | Ha: {p['esistenza']} | Minimo: {p['scorta']}")

    if risultati.get('piu_venduti'):
        gg = risultati.get('periodo_giorni', 30)
        periodo_str = f"ultimi {gg} giorni" if gg <= 90 else "ultimo anno"
        venduti = risultati['piu_venduti']
        parti.append(f"PIÙ VENDUTI ({periodo_str}, top {len(venduti)}):")
        for p in venduti:
            parti.append(f"- {p['articolo']} ({p['marca'] or ''}) | {p['qty']} pezzi venduti in {p['n_vendite']} operazioni")

    if risultati.get('pezzi_fermi'):
        mesi = risultati.get('mesi_fermi', 6)
        fermi = risultati['pezzi_fermi']
        parti.append(f"PEZZI FERMI DA {mesi}+ MESI (in magazzino ma non venduti, top {len(fermi)}):")
        for p in fermi:
            ult = (p['ultimo_movimento'] or 'mai')[:10]
            parti.append(f"- {p['articolo']} ({p['marca'] or ''}) | Quantità: {p['esistenza']} | Ultimo movimento: {ult}")

    if risultati.get('valore'):
        v = risultati['valore']
        parti.append(f"VALORE MAGAZZINO (stima su listino):")
        parti.append(f"- Valore totale: €{round(v['valore_totale'] or 0, 2):,.2f}")
        parti.append(f"- Pezzi con prezzo: {v['con_prezzo']} su {v['totale']} disponibili")
        parti.append(f"- Pezzi fisici totali: {v['pezzi_totali']}")

    if risultati.get('statistiche'):
        s = risultati['statistiche']
        parti.append(f"STATISTICHE MAGAZZINO:")
        parti.append(f"- Articoli totali: {s['tot']}")
        parti.append(f"- Disponibili (ES>0): {s['disp']}")
        parti.append(f"- Sotto scorta: {s['sc']}")
        parti.append(f"- Pezzi fisici totali: {s['pz_tot']}")

    if risultati.get('recupero_auto'):
        marca = risultati.get('marca_recupero', '').upper()
        pezzi = risultati['recupero_auto']
        parti.append(f"PEZZI {marca} DISPONIBILI DA RECUPERARE ({len(pezzi)} trovati):")
        for p in pezzi[:20]:
            parti.append(f"- {p['articolo']} | Qtà: {p['esistenza']} | {p['ubicazione'] or ''}")

    return "\n".join(parti) if parti else "Nessun dato trovato per questa ricerca."


@app.route("/api/assistente", methods=["POST"])
@require_login
def api_assistente():
    import urllib.request, json as _j

    d       = request.json or {}
    domanda = (d.get("domanda") or "").strip()
    if not domanda:
        return jsonify({"ok": False, "msg": "Domanda vuota"}), 400

    # 1. Cerca dati REALI nel database
    try:
        risultati = cerca_nel_db(domanda)
        dati_reali = formatta_risultati(risultati, domanda)
    except Exception as e:
        log.error(f"Errore ricerca DB: {e}")
        dati_reali = "Errore nel recupero dati."

    # 2. Usa AI solo per formulare risposta naturale sui dati reali
    system_prompt = """Sei PERI, assistente del magazzino PerilCar.
Ti vengono forniti dati REALI estratti dal database. Usali per rispondere.
REGOLE ASSOLUTE:
- Usa SOLO i dati forniti, non inventare nulla
- Se i dati dicono "ESAURITO" di lo chiaramente
- Se i dati dicono "DISPONIBILE" con quantità X, riporta esattamente X
- Rispondi in italiano, max 5 frasi, sii diretto e preciso
- Non aggiungere informazioni che non sono nei dati forniti"""

    user_msg = f"""Domanda: {domanda}

DATI REALI DAL DATABASE:
{dati_reali}

Rispondi basandoti ESCLUSIVAMENTE sui dati sopra."""

    # Prova a usare Ollama con timeout breve (30s)
    # Se non risponde, restituisce comunque i dati DB
    try:
        payload = _j.dumps({
            "model": "llama3.2:latest",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_msg}
            ],
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 200, "num_ctx": 2048}
        }).encode()

        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = _j.loads(resp.read())
            risposta = result["message"]["content"]
            return jsonify({"ok": True, "risposta": risposta})
    except Exception:
        # Fallback: restituisce dati DB formattati in HTML leggibile
        pass

    # Ollama non disponibile: formatta i dati DB in modo leggibile
    if not dati_reali or dati_reali == "Nessun dato trovato per questa ricerca.":
        risposta_html = "❌ Nessun risultato trovato nel magazzino per questa ricerca."
    else:
        # Converti il plain text in HTML con evidenziazione
        lines = dati_reali.split("\n")
        parts = []
        for line in lines:
            if not line.strip():
                continue
            if line.isupper() or line.endswith(":"):
                parts.append(f"<b style='color:#e94c00'>{line}</b>")
            elif line.startswith("- "):
                parts.append(f"<span style='display:block;padding:1px 0 1px 8px;border-left:2px solid #dde1e8'>{line[2:]}</span>")
            else:
                parts.append(line)
        risposta_html = "<br>".join(parts)
        risposta_html = f"<small style='color:#9ca3af;font-style:italic'>⚙️ Risposta diretta dal DB (Ollama non attivo)</small><br><br>{risposta_html}"

    return jsonify({"ok": True, "risposta": risposta_html})


# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# DEMOLIZIONI — usa dem (db/demolizioni.db) separato da magazzino
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/demolizioni")
@require_login
def page_demolizioni():
    return render_template("demolizioni.html", user=cu())

@app.route("/demolisci")
@require_login
def page_demolisci():
    return render_template("demolisci.html", user=cu())

# ── ANAGRAFICHE ───────────────────────────────────────────────────────────────

@app.route("/api/anagrafiche", methods=["GET"])
@require_login
def api_anagrafiche():
    rows = dem.all("SELECT id, nominativo, cf_piva, telefono, email FROM anagrafiche ORDER BY nominativo")
    return jsonify(rows)

@app.route("/api/anagrafiche", methods=["POST"])
@require_login
def api_anagrafiche_crea():
    d = request.json or {}
    try:
        campi = ["nominativo","cognome","nome","cf_piva","sesso","tipo_societa","tipo",
                 "data_nascita","luogo_nascita","prov_nascita","comune","provincia",
                 "via","civico","cap","tipo_doc","num_doc","data_doc","rilasciato_da",
                 "telefono","cellulare","fax","email","indirizzo","note"]
        cols = [f for f in campi if d.get(f) is not None]
        vals = [d[f] for f in cols]
        nid  = dem.run("INSERT INTO anagrafiche ("+",".join(cols)+") VALUES ("+",".join(["?"]*len(cols))+")", vals)
        return jsonify({"ok": True, "id": nid, "msg": "Salvata", "nominativo": d.get("nominativo","")})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/anagrafiche/<int:aid>", methods=["GET"])
@require_login
def api_anagrafica_get(aid):
    row = dem.one("SELECT * FROM anagrafiche WHERE id=?", (aid,))
    if not row: return jsonify({"ok": False}), 404
    return jsonify({"ok": True, "data": row})

@app.route("/api/anagrafiche/<int:aid>", methods=["PUT"])
@require_login
def api_anagrafica_update(aid):
    d = request.json or {}
    try:
        campi = ["nominativo","cognome","nome","cf_piva","sesso","tipo_societa","tipo",
                 "data_nascita","luogo_nascita","prov_nascita","comune","provincia",
                 "via","civico","cap","tipo_doc","num_doc","data_doc","rilasciato_da",
                 "telefono","cellulare","fax","email","indirizzo","note"]
        cols = [f for f in campi if f in d]
        vals = [d[f] for f in cols] + [aid]
        if cols:
            dem.run("UPDATE anagrafiche SET "+",".join(f+"=?" for f in cols)+" WHERE id=?", vals)
        return jsonify({"ok": True, "id": aid, "msg": "Aggiornata"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/anagrafiche/<int:aid>/allegati", methods=["GET"])
@require_login
def api_anagrafica_allegati(aid):
    import os
    d = os.path.join(os.path.dirname(__file__), "uploads", "anagrafiche", str(aid))
    if not os.path.exists(d): return jsonify([])
    return jsonify([{"nome": f, "size": os.path.getsize(os.path.join(d,f)),
                     "url": f"/uploads/anagrafiche/{aid}/{f}"} for f in os.listdir(d)])

@app.route("/api/anagrafiche/<int:aid>/allegati", methods=["POST"])
@require_login
def api_anagrafica_upload(aid):
    import os
    d = os.path.join(os.path.dirname(__file__), "uploads", "anagrafiche", str(aid))
    os.makedirs(d, exist_ok=True)
    saved = []
    for f in request.files.getlist("files"):
        if f.filename:
            name = f.filename.replace("/","_").replace("\\","_")
            f.save(os.path.join(d, name)); saved.append(name)
    return jsonify({"ok": True, "files": saved})

# ── VEICOLI ───────────────────────────────────────────────────────────────────

@app.route("/api/veicoli", methods=["GET"])
@require_login
def api_veicoli():
    return jsonify(dem.all("SELECT * FROM veicoli ORDER BY id DESC"))

@app.route("/api/veicoli/<int:vid>", methods=["GET"])
@require_login
def api_veicolo_get(vid):
    row = dem.one("SELECT * FROM veicoli WHERE id=?", (vid,))
    if not row: return jsonify({"ok": False}), 404
    return jsonify({"ok": True, "data": row})

@app.route("/api/veicoli", methods=["POST"])
@require_login
def api_veicoli_crea():
    d = request.json or {}
    try:
        campi = ["targa","telaio","classe","marca","modello","anno_immatricolazione","num_motore","colore","note"]
        cols  = [f for f in campi if d.get(f) is not None]
        vals  = [d[f] for f in cols]
        nid   = dem.run("INSERT INTO veicoli ("+",".join(cols)+") VALUES ("+",".join(["?"]*len(cols))+")", vals)
        marca = d.get("marca",""); modello = d.get("modello",""); targa = d.get("targa","")
        label = (marca+" "+modello).strip() + (" ("+targa+")" if targa else "")
        return jsonify({"ok": True, "id": nid, "msg": "Veicolo salvato", "label": label})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/veicoli/<int:vid>", methods=["PUT"])
@require_login
def api_veicolo_update(vid):
    d = request.json or {}
    try:
        campi = ["targa","telaio","classe","marca","modello","anno_immatricolazione","num_motore","colore","note"]
        cols  = [f for f in campi if f in d]
        if cols:
            dem.run("UPDATE veicoli SET "+",".join(f+"=?" for f in cols)+" WHERE id=?",
                    [d[f] for f in cols]+[vid])
        return jsonify({"ok": True, "id": vid})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/veicoli/<int:vid>/allegati", methods=["GET"])
@require_login
def api_veicolo_allegati(vid):
    import os
    d = os.path.join(os.path.dirname(__file__), "uploads", "veicoli", str(vid))
    if not os.path.exists(d): return jsonify([])
    return jsonify([{"nome": f, "size": os.path.getsize(os.path.join(d,f)),
                     "url": f"/uploads/veicoli/{vid}/{f}"} for f in os.listdir(d)])

@app.route("/api/veicoli/<int:vid>/allegati", methods=["POST"])
@require_login
def api_veicolo_upload(vid):
    import os
    d = os.path.join(os.path.dirname(__file__), "uploads", "veicoli", str(vid))
    os.makedirs(d, exist_ok=True)
    saved = []
    for f in request.files.getlist("files"):
        if f.filename:
            name = f.filename.replace("/","_").replace("\\","_")
            f.save(os.path.join(d, name)); saved.append(name)
    return jsonify({"ok": True, "files": saved})

@app.route("/uploads/<path:filename>")
@require_login
def serve_upload(filename):
    import os
    from flask import send_from_directory
    return send_from_directory(os.path.join(os.path.dirname(__file__), "uploads"), filename)

# ── DEMOLIZIONI ───────────────────────────────────────────────────────────────

def _dem_query(q="", params=()):
    sql = """SELECT d.id, d.data_presa_in_carico, d.ora_presa_in_carico,
               d.reg_demolitori, d.pag_reg, d.veicolo_id, d.proprietario_id, d.detentore_id,
               d.ufficio_provinciale, d.targhe_consegnate, d.carta_circolazione,
               d.concessionaria, d.peso_effettivo_kg, d.peso_netto_kg,
               d.modalita_radiazione, d.num_albatros, d.note, COALESCE(d.primo_trattamento,0) AS primo_trattamento,
               COALESCE(v.marca||' '||v.modello||' ('||v.targa||')','') AS veicolo_str,
               COALESCE(p.nominativo,'') AS proprietario_str,
               COALESCE(det.nominativo,'') AS detentore_str
             FROM demolizioni d
             LEFT JOIN veicoli v ON v.id=d.veicolo_id
             LEFT JOIN anagrafiche p ON p.id=d.proprietario_id
             LEFT JOIN anagrafiche det ON det.id=d.detentore_id"""
    if q:
        sql += " WHERE " + q
    sql += " ORDER BY d.id DESC"
    return dem.all(sql, params)

@app.route("/api/demolizioni/cerca")
@require_login
def api_demolizioni_cerca():
    return jsonify(_dem_query())

@app.route("/api/demolizioni/prossimi-progressivi")
@require_login
def api_demolizioni_progressivi():
    import datetime
    nid  = (dem.one("SELECT COALESCE(MAX(id),0)+1 AS v FROM demolizioni") or {}).get("v",1)
    npag = (dem.one("SELECT COALESCE(MAX(CAST(pag_reg AS INTEGER)),0)+1 AS v FROM demolizioni") or {}).get("v",1)
    now  = datetime.datetime.now()
    return jsonify({"ok": True, "next_id": nid, "next_pag": npag,
                    "reg_demolitori": f"01/{now.year}",
                    "data": now.strftime("%Y-%m-%d"), "ora": now.strftime("%H:%M")})

@app.route("/api/demolizioni", methods=["POST"])
@require_login
def api_demolizioni_crea():
    u  = cu(); d = request.json or {}
    campi = ["data_presa_in_carico","ora_presa_in_carico","reg_demolitori","pag_reg",
             "veicolo_id","proprietario_id","detentore_id","ufficio_provinciale",
             "targhe_consegnate","carta_circolazione","concessionaria",
             "peso_effettivo_kg","peso_netto_kg","modalita_radiazione",
             "num_albatros","certificato_id","note","creato_da"]
    vals  = [d.get(f) for f in campi[:-1]] + [u.get("id")]
    try:
        nid = dem.run("INSERT INTO demolizioni ("+",".join(campi)+") VALUES ("+",".join(["?"]*len(campi))+")", vals)
        return jsonify({"ok": True, "id": nid, "msg": "Demolizione salvata"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/demolizioni/<int:did>", methods=["PUT"])
@require_login
def api_demolizioni_update(did):
    d = request.json or {}
    campi = ["data_presa_in_carico","ora_presa_in_carico","reg_demolitori","pag_reg",
             "veicolo_id","proprietario_id","detentore_id","ufficio_provinciale",
             "targhe_consegnate","carta_circolazione","concessionaria",
             "peso_effettivo_kg","peso_netto_kg","modalita_radiazione","note","primo_trattamento"]
    cols = [f for f in campi if f in d]
    if cols:
        dem.run("UPDATE demolizioni SET "+",".join(f+"=?" for f in cols)+" WHERE id=?",
                [d[f] for f in cols]+[did])
    return jsonify({"ok": True, "msg": "Aggiornata"})

@app.route("/api/demolizioni/<int:did>", methods=["DELETE"])
@require_login
def api_demolizioni_delete(did):
    dem.run("DELETE FROM ricambi_sottratti WHERE demolizione_id=?", (did,))
    dem.run("DELETE FROM demolizioni WHERE id=?", (did,))
    return jsonify({"ok": True})

@app.route("/api/demolizioni/<int:did>/ricambi", methods=["GET"])
@require_login
def api_ricambi_get(did):
    return jsonify(dem.all("SELECT * FROM ricambi_sottratti WHERE demolizione_id=? ORDER BY id", (did,)))

@app.route("/api/demolizioni/<int:did>/ricambi", methods=["POST"])
@require_login
def api_ricambi_add(did):
    d    = request.json or {}
    nome = d.get("pezzo_nome") or ""
    peso = d.get("peso_kg", 0)
    dem.run("INSERT INTO ricambi_sottratti (demolizione_id,componente_id,peso_kg,note,pezzo_nome) VALUES (?,?,?,?,?)",
            (did, None, peso, d.get("note",""), nome))
    # Ricalcola peso netto
    tot = (dem.one("SELECT COALESCE(SUM(peso_kg),0) AS t FROM ricambi_sottratti WHERE demolizione_id=?", (did,)) or {}).get("t",0)
    dem.run("UPDATE demolizioni SET peso_netto_kg = MAX(0, COALESCE(peso_effettivo_kg,0)-?) WHERE id=?", (tot, did))
    return jsonify({"ok": True})

@app.route("/api/demolizioni/ricambi/<int:rid>", methods=["DELETE"])
@require_login
def api_ricambi_del(rid):
    row = dem.one("SELECT demolizione_id FROM ricambi_sottratti WHERE id=?", (rid,))
    dem.run("DELETE FROM ricambi_sottratti WHERE id=?", (rid,))
    if row:
        did = row["demolizione_id"]
        tot = (dem.one("SELECT COALESCE(SUM(peso_kg),0) AS t FROM ricambi_sottratti WHERE demolizione_id=?", (did,)) or {}).get("t",0)
        dem.run("UPDATE demolizioni SET peso_netto_kg = MAX(0, COALESCE(peso_effettivo_kg,0)-?) WHERE id=?", (tot, did))
    return jsonify({"ok": True})


# ══════════════════════════════════════════════════════════════════════════════
# SCHEDE DEMOLIZIONE — salvataggio scheda /demolisci nel DB
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/schede-demolizione", methods=["POST"])
@require_login
def api_scheda_salva():
    u = cu(); d = request.json or {}
    dem_ids   = d.get("dem_ids", "")      # es. "3,7,12"
    data_tratt = d.get("data_trattamento")
    righe_json = d.get("righe_json", "[]")  # JSON serializzato
    peso_eff   = d.get("peso_eff_tot", 0)
    peso_ric   = d.get("peso_ricambi_tot", 0)
    peso_netto = d.get("peso_netto_tot", 0)
    if not dem_ids:
        return jsonify({"ok": False, "msg": "dem_ids obbligatorio"}), 400
    try:
        # Upsert: se esiste già una scheda per questi dem_ids, aggiorna
        existing = dem.one("SELECT id FROM schede_demolizione WHERE dem_ids=?", (dem_ids,))
        if existing:
            dem.run("""UPDATE schede_demolizione
                SET data_trattamento=?, peso_eff_tot=?, peso_ricambi_tot=?, peso_netto_tot=?,
                    righe_json=?, modificato_il=datetime('now')
                WHERE id=?""",
                (data_tratt, peso_eff, peso_ric, peso_netto, righe_json, existing["id"]))
            return jsonify({"ok": True, "msg": "Scheda aggiornata nel DB", "id": existing["id"], "action": "update"})
        else:
            nid = dem.run("""INSERT INTO schede_demolizione
                (dem_ids, data_trattamento, peso_eff_tot, peso_ricambi_tot, peso_netto_tot, righe_json, creato_da)
                VALUES (?,?,?,?,?,?,?)""",
                (dem_ids, data_tratt, peso_eff, peso_ric, peso_netto, righe_json, u.get("id")))
            return jsonify({"ok": True, "msg": "Scheda salvata nel DB", "id": nid, "action": "create"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/schede-demolizione/<dem_ids>", methods=["GET"])
@require_login
def api_scheda_get(dem_ids):
    row = dem.one("SELECT * FROM schede_demolizione WHERE dem_ids=? ORDER BY id DESC LIMIT 1", (dem_ids,))
    if not row:
        return jsonify({"ok": False, "found": False})
    return jsonify({"ok": True, "found": True, "data": row})

@app.route("/api/demolizioni/<int:did>", methods=["GET"])
@require_login
def api_demolizione_get(did):
    row = _dem_query(f"d.id={did}")
    if not row:
        return jsonify({"ok": False, "msg": "Non trovata"}), 404
    return jsonify({"ok": True, "data": row[0]})

# ══════════════════════════════════════════════════════════════════════════════
# GESTIONE UTENTI (solo admin)
# ══════════════════════════════════════════════════════════════════════════════

def require_admin(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = cu()
        if not u:
            return jsonify({"ok": False, "msg": "Non autenticato"}), 401
        if u.get("ruolo") != "admin":
            return jsonify({"ok": False, "msg": "Accesso negato — solo admin"}), 403
        return f(*args, **kwargs)
    return wrapper

@app.route("/utenti")
@require_login
def page_utenti():
    if cu().get("ruolo") != "admin":
        return redirect("/dashboard")
    return render_template("utenti.html", user=cu())

@app.route("/api/utenti", methods=["GET"])
@require_admin
def api_utenti_lista():
    try:
        ucols = [r["name"] for r in db.fetchall("PRAGMA table_info(utenti)")]
        sel   = "id,username,ruolo,attivo,creato_il"
        if "nome_completo" in ucols: sel += ",nome_completo"
        where = "WHERE eliminato=0" if "eliminato" in ucols else ""
        rows  = db.fetchall(f"SELECT {sel} FROM utenti {where} ORDER BY username")
        # Normalizza: aggiungi nome_completo se manca
        for r in rows:
            if "nome_completo" not in r.keys():
                r = dict(r); r["nome_completo"] = ""
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        log.warning(f"api_utenti_lista error: {e}")
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/utenti", methods=["POST"])
@require_admin
def api_utenti_crea():
    import hashlib
    d = request.json or {}
    username = (d.get("username") or "").strip().lower()
    password = (d.get("password") or "").strip()
    ruolo    = d.get("ruolo", "operatore")
    nome     = d.get("nome_completo", "").strip()
    if not username or not password:
        return jsonify({"ok": False, "msg": "Username e password obbligatori"}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "msg": "Password minimo 6 caratteri"}), 400
    if db.fetchone("SELECT id FROM utenti WHERE username=? AND eliminato=0", (username,)):
        return jsonify({"ok": False, "msg": f"Username '{username}' già esistente"}), 400
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        with db._write_lock:
            conn = db.get_connection()
            try:
                # Adatta INSERT alle colonne disponibili
                ucols2 = [r[1] for r in conn.execute("PRAGMA table_info(utenti)").fetchall()]
                fields = ["username","password_hash","ruolo","attivo"]
                values = [username, pwd_hash, ruolo, 1]
                if "nome_completo" in ucols2 and nome:
                    fields.append("nome_completo"); values.append(nome)
                if "eliminato" in ucols2:
                    fields.append("eliminato"); values.append(0)
                sql = "INSERT INTO utenti("+",".join(fields)+") VALUES("+",".join(["?"]*len(fields))+")"
                cur = conn.execute(sql, values)
                uid = cur.lastrowid
                conn.execute("INSERT INTO log_operazioni(utente_id,username,modulo,azione,tabella,record_id) VALUES(?,?,?,?,?,?)",
                    (cu().get("id"), cu().get("username"), "UTENTI", "CREA", "utenti", uid))
                conn.commit()
            finally:
                conn.close()
        return jsonify({"ok": True, "msg": f"Utente '{username}' creato", "id": uid})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/utenti/<int:uid>", methods=["PUT"])
@require_admin
def api_utenti_modifica(uid):
    import hashlib
    d = request.json or {}
    updates = []
    vals = []
    if "ruolo" in d:
        updates.append("ruolo=?"); vals.append(d["ruolo"])
    if "nome_completo" in d:
        # Aggiungi colonna se non esiste
        try:
            ucols_m = [r[1] for r in db.fetchall("PRAGMA table_info(utenti)")]
            if "nome_completo" not in ucols_m:
                db_write([("ALTER TABLE utenti ADD COLUMN nome_completo TEXT", ())])
        except: pass
        updates.append("nome_completo=?"); vals.append(d["nome_completo"])
    if "attivo" in d:
        updates.append("attivo=?"); vals.append(1 if d["attivo"] else 0)
    if d.get("password"):
        if len(d["password"]) < 6:
            return jsonify({"ok": False, "msg": "Password minimo 6 caratteri"}), 400
        updates.append("password_hash=?")
        vals.append(hashlib.sha256(d["password"].encode()).hexdigest())
    if not updates:
        return jsonify({"ok": False, "msg": "Nessun campo da aggiornare"}), 400
    vals.append(uid)
    try:
        db_write([(f"UPDATE utenti SET {','.join(updates)} WHERE id=? AND eliminato=0", vals),
                  ("INSERT INTO log_operazioni(utente_id,username,modulo,azione,tabella,record_id) VALUES(?,?,?,?,?,?)",
                   (cu().get("id"), cu().get("username"), "UTENTI", "MODIFICA", "utenti", uid))])
        return jsonify({"ok": True, "msg": "Utente aggiornato"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/utenti/<int:uid>", methods=["DELETE"])
@require_admin
def api_utenti_elimina(uid):
    if uid == cu().get("id"):
        return jsonify({"ok": False, "msg": "Non puoi eliminare te stesso"}), 400
    try:
        db_write([("UPDATE utenti SET eliminato=1 WHERE id=?", (uid,)),
                  ("INSERT INTO log_operazioni(utente_id,username,modulo,azione,tabella,record_id) VALUES(?,?,?,?,?,?)",
                   (cu().get("id"), cu().get("username"), "UTENTI", "ELIMINA", "utenti", uid))])
        return jsonify({"ok": True, "msg": "Utente eliminato"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/utenti/cambia-password", methods=["POST"])
@require_login
def api_cambia_password():
    """Ogni utente può cambiare la propria password."""
    import hashlib
    d = request.json or {}
    vecchia   = d.get("vecchia", "")
    nuova     = d.get("nuova", "")
    if len(nuova) < 6:
        return jsonify({"ok": False, "msg": "Nuova password minimo 6 caratteri"}), 400
    u = cu()
    utente = db.fetchone("SELECT password_hash FROM utenti WHERE id=? AND eliminato=0", (u.get("id"),))
    if not utente:
        return jsonify({"ok": False, "msg": "Utente non trovato"}), 404
    if utente["password_hash"] != hashlib.sha256(vecchia.encode()).hexdigest():
        return jsonify({"ok": False, "msg": "Password attuale errata"}), 400
    db_write([("UPDATE utenti SET password_hash=? WHERE id=?",
               (hashlib.sha256(nuova.encode()).hexdigest(), u.get("id")))])
    return jsonify({"ok": True, "msg": "Password aggiornata"})


# ══════════════════════════════════════════════════════════════════════════════
# MODULO INVENTARIO — PC controller + Mobile client
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/inventario")
@require_login
def page_inventario():
    return render_template("inventario.html", user=cu())

@app.route("/inventario-mobile")
@require_login
def page_inventario_mobile():
    sid = request.args.get("sessione")
    return render_template("inventario_mobile.html", user=cu(), sessione_id=sid or "")

# ── CATEGORIE disponibili ─────────────────────────────────────────────
@app.route("/api/inventario/categorie")
@require_login
def api_inv_categorie():
    rows = db.fetchall("""
        SELECT categoria, COUNT(*) as n, SUM(esistenza) as tot_pezzi
        FROM v_giacenza
        WHERE categoria IS NOT NULL AND categoria != ''
        GROUP BY categoria ORDER BY categoria
    """)
    return jsonify(rows)

@app.route("/api/inventario/descrizioni")
@require_login
def api_inv_descrizioni():
    """Cerca descrizioni/articoli nel magazzino per autocomplete."""
    q = request.args.get("q","").strip()
    if len(q) < 1:
        return jsonify([])
    rows = db.fetchall("""
        SELECT articolo as descrizione, COUNT(*) as n, SUM(esistenza) as tot_pezzi
        FROM v_giacenza
        WHERE articolo LIKE ? AND articolo IS NOT NULL AND articolo != ''
        GROUP BY articolo ORDER BY n DESC, articolo LIMIT 40
    """, (f"%{q}%",))
    return jsonify(rows)

# ── SESSIONI ──────────────────────────────────────────────────────────
@app.route("/api/inventario/sessioni")
@require_login
def api_inv_sessioni():
    rows = db.fetchall("""
        SELECT s.*, u.username as creato_da_nome
        FROM sessioni_inventario s
        LEFT JOIN utenti u ON u.id = s.creato_da
        ORDER BY s.id DESC LIMIT 50
    """)
    return jsonify(rows)

@app.route("/api/inventario/sessioni", methods=["POST"])
@require_login
def api_inv_crea_sessione():
    import json
    d  = request.json or {}
    u  = cu()
    categoria  = d.get("categoria", "").strip()
    descrizione= d.get("descrizione", "").strip()
    nome       = d.get("nome", descrizione or categoria or "Inventario").strip()
    filtro     = descrizione or categoria
    if not filtro:
        return jsonify({"ok": False, "msg": "Seleziona una descrizione"}), 400

    try:
        # Recupera componenti PRIMA di acquisire il write lock (evita deadlock)
        if descrizione:
            comps = db.fetchall(
                "SELECT componente_id, esistenza FROM v_giacenza WHERE articolo=? ORDER BY articolo",
                (descrizione,))
        else:
            comps = db.fetchall(
                "SELECT componente_id, esistenza FROM v_giacenza WHERE categoria=? ORDER BY articolo",
                (categoria,))

        if not comps:
            return jsonify({"ok": False, "msg": f"Nessun componente trovato per '{filtro}'"}), 400

        with db._write_lock:
            conn = db.get_connection()
            conn.execute("PRAGMA synchronous=OFF")
            try:
                # Crea sessione
                cur = conn.execute(
                    "INSERT INTO sessioni_inventario(nome,categoria,stato,creato_da) VALUES(?,?,?,?)",
                    (nome, filtro, "attiva", u.get("id")))
                sid = cur.lastrowid

                # Insert bulk
                conn.executemany(
                    "INSERT INTO inventario_righe(sessione_id,componente_id,qty_attesa,stato,ordine) VALUES(?,?,?,?,?)",
                    [(sid, c["componente_id"], int(c["esistenza"] or 0), "sospeso", i)
                     for i, c in enumerate(comps)])

                conn.execute(
                    "UPDATE sessioni_inventario SET totale_pezzi=? WHERE id=?",
                    (len(comps), sid))
                conn.commit()
                log.info(f"Inventario sessione {sid} creata: {len(comps)} pezzi categoria '{categoria}'")

                # Notifica tutti i client connessi
                socketio.emit("inventario_nuova_sessione", {
                    "sessione_id": sid, "nome": nome, "categoria": categoria,
                    "totale": len(comps)
                })
                return jsonify({"ok": True, "id": sid, "totale": len(comps), "msg": f"Sessione creata: {len(comps)} pezzi"})
            except Exception as e:
                conn.rollback()
                raise
            finally:
                conn.close()
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/inventario/sessioni/<int:sid>")
@require_login
def api_inv_sessione_dettaglio(sid):
    sess = db.fetchone("SELECT * FROM sessioni_inventario WHERE id=?", (sid,))
    if not sess:
        return jsonify({"ok": False, "msg": "Sessione non trovata"}), 404
    righe = db.fetchall("""
        SELECT r.*, c.codice as cmp, c.nome as articolo,
               c.marca, c.categoria, c.immagine_path, c.files_path
        FROM inventario_righe r
        JOIN componenti c ON c.id = r.componente_id
        WHERE r.sessione_id=?
        ORDER BY r.ordine
    """, (sid,))
    return jsonify({"ok": True, "sessione": dict(sess), "righe": righe})

@app.route("/api/inventario/sessioni/<int:sid>/prossimo")
@require_login
def api_inv_prossimo(sid):
    """Restituisce il prossimo pezzo sospeso da inventariare."""
    riga = db.fetchone("""
        SELECT r.*, c.codice as cmp, c.nome as articolo,
               c.marca, c.categoria, c.immagine_path, c.files_path,
               c.colore, c.modello, c.anno_da, c.anno_a,
               c.cod_modello, c.cilindrata, c.carburante, c.versione,
               c.tipologia, c.sottocategoria, c.intervallo,
               c.cod_udm, c.cod_iva, c.listino1, c.listino2, c.listino3,
               c.cod_barre, c.ubicazione, c.stato_magazzino,
               c.prezzo_acquisto, c.prezzo_vendita, c.scorta_minima,
               c.fornitore, c.cod_fornitore, c.note,
               c.extra1, c.extra2, c.extra3, c.extra4,
               c.unita_misura, c.descrizione
        FROM inventario_righe r
        JOIN componenti c ON c.id = r.componente_id
        WHERE r.sessione_id=? AND r.stato='sospeso'
        ORDER BY r.ordine LIMIT 1
    """, (sid,))
    if not riga:
        # Controlla se ci sono rimandati
        rimandato = db.fetchone("""
            SELECT r.*, c.codice as cmp, c.nome as articolo,
                   c.marca, c.categoria, c.immagine_path, c.files_path,
                   c.colore, c.modello, c.anno_da, c.anno_a,
                   c.cod_modello, c.cilindrata, c.carburante, c.versione,
                   c.tipologia, c.sottocategoria, c.intervallo,
                   c.cod_udm, c.cod_iva, c.listino1, c.listino2, c.listino3,
                   c.cod_barre, c.ubicazione, c.stato_magazzino,
                   c.prezzo_acquisto, c.prezzo_vendita, c.scorta_minima,
                   c.fornitore, c.cod_fornitore, c.note,
                   c.extra1, c.extra2, c.extra3, c.extra4,
                   c.unita_misura, c.descrizione
            FROM inventario_righe r
            JOIN componenti c ON c.id = r.componente_id
            WHERE r.sessione_id=? AND r.stato='rimandato'
            ORDER BY r.ordine LIMIT 1
        """, (sid,))
        if rimandato:
            return jsonify({"ok": True, "riga": dict(rimandato), "fase": "rimandati"})
        return jsonify({"ok": True, "riga": None, "fase": "completato"})
    return jsonify({"ok": True, "riga": dict(riga), "fase": "principale"})

@app.route("/api/inventario/sessioni/<int:sid>/stats")
@require_login
def api_inv_stats(sid):
    stats = db.fetchone("""
        SELECT
            COUNT(*) as totale,
            SUM(CASE WHEN stato='confermato' THEN 1 ELSE 0 END) as confermati,
            SUM(CASE WHEN stato='mancante' THEN 1 ELSE 0 END) as mancanti,
            SUM(CASE WHEN stato='rimandato' THEN 1 ELSE 0 END) as rimandati,
            SUM(CASE WHEN stato='sospeso' THEN 1 ELSE 0 END) as sospesi
        FROM inventario_righe WHERE sessione_id=?
    """, (sid,))
    return jsonify(dict(stats) if stats else {})

@app.route("/api/inventario/righe/<int:rid>", methods=["PUT"])
@require_login
def api_inv_aggiorna_riga(rid):
    """Aggiorna stato di una riga inventario (dal mobile o dal PC)."""
    import json
    d     = request.json or {}
    u     = cu()
    stato = d.get("stato")           # confermato | mancante | rimandato
    qty   = d.get("qty_trovata")
    note  = d.get("note", "")

    # Leggi riga PRIMA del write lock
    riga = db.fetchone("SELECT * FROM inventario_righe WHERE id=?", (rid,))
    if not riga:
        return jsonify({"ok": False, "msg": "Riga non trovata"}), 404

    # Pre-calcola valori
    sid  = riga["sessione_id"]
    cid  = riga["componente_id"]
    qatt = riga["qty_attesa"] or 0
    qtrv = qty if qty is not None else qatt

    try:
        with db._write_lock:
            conn = db.get_connection()
            try:
                # Aggiorna riga inventario
                conn.execute("""UPDATE inventario_righe
                    SET stato=?, qty_trovata=?, note=?, aggiornato_il=datetime('now')
                    WHERE id=?""",
                    (stato, qtrv, note, rid))

                # Se confermato o mancante: registra movimento se qty diversa
                if stato in ("confermato", "mancante"):
                    diff = qtrv - qatt
                    if diff != 0:
                        tipo_mov = "carico" if diff > 0 else "scarico"
                        q_mov    = abs(diff)
                        mov_cols = [r[1] for r in conn.execute("PRAGMA table_info(movimenti_magazzino)").fetchall()]
                        m_fields = ["componente_id","tipo","quantita","riferimento","note","utente_id"]
                        m_vals   = [cid, tipo_mov, q_mov, f"INVENTARIO-{sid}", f"Rettifica inventario: trovati {qtrv} attesi {qatt}", u.get("id")]
                        if "quantita_prima" in mov_cols:
                            m_fields += ["quantita_prima","quantita_dopo"]
                            m_vals   += [qatt, qtrv]
                        conn.execute(
                            "INSERT INTO movimenti_magazzino ("+",".join(m_fields)+") VALUES ("+",".join(["?"]*len(m_fields))+")",
                            m_vals)

                # Aggiorna contatori sessione
                stats = conn.execute("""
                    SELECT
                        SUM(CASE WHEN stato='confermato' THEN 1 ELSE 0 END) as c,
                        SUM(CASE WHEN stato='mancante'   THEN 1 ELSE 0 END) as m,
                        SUM(CASE WHEN stato='rimandato'  THEN 1 ELSE 0 END) as r
                    FROM inventario_righe WHERE sessione_id=?
                """, (sid,)).fetchone()
                conn.execute("""UPDATE sessioni_inventario
                    SET confermati=?, mancanti=?, sospesi=?
                    WHERE id=?""",
                    (stats[0] or 0, stats[1] or 0, stats[2] or 0, sid))

                # Log
                try:
                    conn.execute("""INSERT INTO log_operazioni
                        (utente_id,username,modulo,azione,tabella,record_id,dati_nuovi)
                        VALUES(?,?,?,?,?,?,?)""",
                        (u.get("id"),u.get("username"),"INVENTARIO",stato.upper(),
                         "inventario_righe",rid,str({"qty":qtrv,"stato":stato})))
                except: pass

                conn.commit()

                # Notifica PC in tempo reale
                socketio.emit("inventario_aggiornamento", {
                    "sessione_id": sid, "riga_id": rid,
                    "componente_id": cid, "stato": stato,
                    "qty_trovata": qtrv, "qty_attesa": qatt
                }, room=f"inventario_{sid}")

                return jsonify({"ok": True, "msg": f"Pezzo {stato}"})
            except Exception as e:
                conn.rollback(); raise
            finally:
                conn.close()
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/inventario/righe/<int:rid>/foto", methods=["POST"])
@require_login
def api_inv_foto(rid):
    """Upload foto da mobile per un pezzo inventario."""
    import uuid
    if "file" not in request.files:
        return jsonify({"ok": False, "msg": "Nessun file"}), 400
    f   = request.files["file"]
    ext = f.filename.rsplit(".",1)[-1].lower() if "." in f.filename else "jpg"
    if ext not in {"png","jpg","jpeg","webp","gif"}:
        return jsonify({"ok": False, "msg": "Solo immagini"}), 400

    riga = db.fetchone("SELECT * FROM inventario_righe WHERE id=?", (rid,))
    if not riga:
        return jsonify({"ok": False, "msg": "Riga non trovata"}), 404

    fname = f"inv_{rid}_{uuid.uuid4().hex[:8]}.{ext}"
    f.save(UPLOAD_FOLDER / fname)
    url   = f"/static/uploads/{fname}"

    cid = riga["componente_id"]
    try:
        with db._write_lock:
            conn = db.get_connection()
            try:
                # Salva url foto nella riga inventario (append, non sovrascrive)
                old_riga = conn.execute("SELECT foto_url FROM inventario_righe WHERE id=?", (rid,)).fetchone()
                old_foto_url = old_riga[0] if old_riga and old_riga[0] else ""
                new_foto_url = (old_foto_url + "|" + url).strip("|") if old_foto_url else url
                conn.execute("UPDATE inventario_righe SET foto_url=? WHERE id=?", (new_foto_url, rid))
                # Aggiorna immagine_path e files_path del componente
                comp = conn.execute("SELECT immagine_path, files_path FROM componenti WHERE id=?", (cid,)).fetchone()
                if comp:
                    new_img   = comp[0] or url   # prima foto diventa immagine principale
                    old_files = comp[1] or ""
                    # Evita duplicati
                    existing  = set(old_files.split("|")) if old_files else set()
                    if url not in existing:
                        new_files = (old_files + "|" + url).strip("|") if old_files else url
                    else:
                        new_files = old_files
                    conn.execute("UPDATE componenti SET immagine_path=?, files_path=?, modificato_il=datetime('now') WHERE id=?",
                                 (new_img, new_files, cid))
                conn.commit()
            finally:
                conn.close()
        # Notifica il PC in tempo reale
        try:
            socketio.emit("inventario_foto", {
                "sessione_id": riga["sessione_id"],
                "riga_id": rid,
                "componente_id": cid,
                "url": url,
                "foto_url": new_foto_url
            }, room=f"inventario_{riga['sessione_id']}")
        except: pass
        return jsonify({"ok": True, "url": url})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/inventario/sessioni/<int:sid>/chiudi", methods=["POST"])
@require_login
def api_inv_chiudi(sid):
    try:
        db_write([("UPDATE sessioni_inventario SET stato='chiusa', chiuso_il=datetime('now') WHERE id=?", (sid,))])
        socketio.emit("inventario_chiusa", {"sessione_id": sid})
        return jsonify({"ok": True, "msg": "Sessione chiusa"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

# SocketIO room per inventario

@socketio.on("join_inventario")
def on_join_inventario(data):
    sid = data.get("sessione_id")
    if sid:
        join_room(f"inventario_{sid}")
        log.info(f"Client joined inventario_{sid}")

@socketio.on("leave_inventario")
def on_leave_inventario(data):
    sid = data.get("sessione_id")
    if sid:
        leave_room(f"inventario_{sid}")

@app.route("/api/ping")
def api_ping():
    """Endpoint leggero per verificare connessione al server."""
    return jsonify({"ok": True, "ts": __import__("time").time()})

@app.route("/sw.js")
def service_worker():
    from flask import send_from_directory
    resp = send_from_directory("web/static", "sw.js")
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp

# HOT RELOAD
# ══════════════════════════════════════════════════════════════════════════════

def start_file_watcher():
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        class H(FileSystemEventHandler):
            def __init__(self): self._last = 0
            def on_modified(self, ev):
                if ev.is_directory: return
                if not any(ev.src_path.endswith(e) for e in (".py",".html",".css",".js")): return
                now = time.time()
                if now - self._last < 0.8: return
                self._last = now
                socketio.emit("reload", {"file": os.path.relpath(ev.src_path, ROOT)})
        obs = Observer(); obs.schedule(H(), str(ROOT), recursive=True); obs.start()
        log.info("👀 Watchdog attivo")
    except Exception as e:
        log.warning(f"Watchdog non disponibile: {e}")

if __name__ == "__main__":
    import webbrowser
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=lambda: (time.sleep(1.5), webbrowser.open(f"http://localhost:{port}")),
                     daemon=True).start()
    start_file_watcher()
    log.info(f"🚀 PerilCar Dev Server — http://localhost:{port}")
    socketio.run(app, host="0.0.0.0", port=port,
                 debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
