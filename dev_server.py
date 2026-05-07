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
from flask_socketio import SocketIO

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
app.secret_key = "perilcar-dev-secret-2024"

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
log.info(f"DB: {cfg.get('db_path')}")

# Pulizia tabelle residue da migrazioni precedenti
try:
    import sqlite3 as _sq3
    _cp = _sq3.connect(cfg.get("db_path"), timeout=10)
    # Elimina tabelle residue
    for _tbak in ['veicoli_bak','veicoli_old','veicoli_tmp']:
        _exists = _cp.execute(f"SELECT 1 FROM sqlite_master WHERE type='table' AND name='{_tbak}'").fetchone()
        if _exists:
            _cp.execute(f"DROP TABLE {_tbak}")
            log.info(f"Rimossa tabella residua: {_tbak}")
    _cp.commit()
    _cp.close()
except Exception as _ce:
    log.warning(f"Pulizia residui: {_ce}")

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
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return wrapper

def cu():
    return session.get("user", {})

# ══════════════════════════════════════════════════════════════════════════════
# PAGINE
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return redirect(url_for("dashboard") if session.get("user") else url_for("login_page"))

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
    user = db.fetchone("SELECT * FROM utenti WHERE username=? AND eliminato=0",
                       (d.get("username","").strip(),))
    if not user:
        return jsonify({"ok": False, "msg": "Utente non trovato"}), 401
    if not user["attivo"]:
        return jsonify({"ok": False, "msg": "Account disabilitato"}), 403
    if user["password_hash"] != pwd_hash:
        return jsonify({"ok": False, "msg": "Password errata"}), 401
    session["user"] = {"id": user["id"], "username": user["username"],
                       "ruolo": user["ruolo"], "nome": user["nome_completo"] or user["username"]}
    db_write([("INSERT INTO log_operazioni(utente_id,username,modulo,azione) VALUES(?,?,?,?)",
               (user["id"], user["username"], "AUTH", "LOGIN"))])
    return jsonify({"ok": True, "user": session["user"]})

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
        db_write([
            ("""INSERT INTO movimenti_magazzino
                (componente_id,tipo,quantita,quantita_prima,quantita_dopo,riferimento,note,utente_id)
                VALUES(?,?,?,?,?,?,?,?)""",
             (cid, tipo, qty, gia_prima, gia_dopo, rif, note, u.get("id"))),
            ("UPDATE magazzino SET aggiornato_il=datetime('now') WHERE componente_id=?", (cid,)),
            ("""INSERT INTO log_operazioni
                (utente_id,username,modulo,azione,tabella,record_id,dati_precedenti,dati_nuovi)
                VALUES(?,?,?,?,?,?,?,?)""",
             (u.get("id"),u.get("username"),"MAGAZZINO",tipo.upper(),
              "movimenti_magazzino",cid,str({"g":gia_prima}),str({"g":gia_dopo})))
        ])
        return jsonify({"ok": True, "msg": f"{tipo.capitalize()} di {qty} pz completato",
                        "giacenza": gia_dopo})
    except Exception as e:
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

@app.route("/api/magazzino/stats")
@require_login
def api_stats():
    t = db.fetchone("SELECT COUNT(*) AS n FROM v_giacenza")
    s = db.fetchone("SELECT COUNT(*) AS n FROM v_giacenza WHERE esistenza <= scorta AND scorta > 0")
    u = db.fetchone("SELECT creato_il FROM movimenti_magazzino ORDER BY id DESC LIMIT 1")
    return jsonify({"totale_componenti": t["n"] if t else 0,
                    "sotto_scorta": s["n"] if s else 0,
                    "ultimo_movimento": u["creato_il"] if u else "—"})

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
    import xlsxwriter
    rows = db.fetchall("SELECT * FROM v_giacenza ORDER BY articolo")
    buf  = io.BytesIO()
    wb   = xlsxwriter.Workbook(buf, {"in_memory": True})
    ws   = wb.add_worksheet("Magazzino")

    hdr  = wb.add_format({"bold":True,"bg_color":"#E94C00","font_color":"white",
                           "border":1,"align":"center","valign":"vcenter","font_size":10})
    cell = wb.add_format({"border":1,"valign":"vcenter","font_size":10})
    num  = wb.add_format({"border":1,"align":"center","valign":"vcenter","font_size":10})
    alt  = wb.add_format({"border":1,"bg_color":"#FFF3EE","valign":"vcenter","font_size":10})

    # Colonne esatte come Danea + quelle aggiuntive
    cols = [
        ("Cod.",            "cmp",            10),
        ("Descrizione",     "articolo",       36),
        ("Tipologia",       "tipologia",      18),
        ("Categoria",       "categoria",      14),
        ("Sottocategoria",  "sottocategoria", 14),
        ("Cod. Udm",        "cod_udm",        10),
        ("Cod. Iva",        "cod_iva",        10),
        ("Listino 1",       "listino1",       12),
        ("Listino 2",       "listino2",       12),
        ("Listino 3",       "listino3",       12),
        ("Note",            "nota",           30),
        ("Cod. a barre",    "cod_barre",      14),
        ("Internet",        "internet",       10),
        ("Produttore",      "marca",          16),
        ("Extra 1",         "extra1",         12),
        ("Extra 2",         "extra2",         12),
        ("Extra 3",         "extra3",         12),
        ("Extra 4",         "extra4",         12),
        ("Cod. fornitore",  "cod_fornitore",  14),
        ("Fornitore",       "fornitore",      16),
        ("Cod. prod. forn.","cod_prod_forn",  16),
        ("Prezzo forn.",    "prezzo_forn",    12),
        ("Note fornitura",  "note_fornitura", 20),
        ("Ord. a multipli di","ord_multipli", 14),
        ("Gg. ordine",      "gg_ordine",      10),
        ("Scorta min.",     "scorta",         10),
        ("Ubicazione",      "ubicazione",     18),
        ("Q.tà giacenza",   "esistenza",      12),
        ("Stato magazzino", "stato_magazzino",14),
        ("Modello",         "modello",        16),
        ("Colore",          "colore",         12),
        ("Cilindrata",      "cilindrata",     12),
        ("Carburante",      "carburante",     12),
        ("Versione",        "versione",       12),
        ("Anno da",         "anno_da",        10),
        ("Anno a",          "anno_a",         10),
        ("Intervallo",      "intervallo",     14),
        ("File/Immagini",   "files_path",     30),
    ]

    ws.set_row(0, 22)
    for c,(label,_,w) in enumerate(cols):
        ws.write(0, c, label, hdr)
        ws.set_column(c, c, w)

    NUM_KEYS = {"esistenza","scorta","listino1","listino2","listino3",
                "prezzo_forn","ord_multipli","gg_ordine","anno_da","anno_a"}
    for ri, r in enumerate(rows):
        fmt = cell if ri%2==0 else alt
        for c, (_,key,_) in enumerate(cols):
            val = r.get(key) or ""
            if val == "" and key in NUM_KEYS: val = 0
            ws.write(ri+1, c, val, num if key in NUM_KEYS else fmt)

    wb.close(); buf.seek(0)
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
        # Fallback: restituisce dati DB direttamente, sempre funziona
        pass

    return jsonify({"ok": True, "risposta": dati_reali})


# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# DEMOLIZIONI
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/demolizioni")
@require_login
def page_demolizioni():
    return render_template("demolizioni.html", user=cu())

@app.route("/api/demolizioni", methods=["GET"])
@require_login
def api_demolizioni_list():
    rows = db.fetchall("""
        SELECT d.*,
               COALESCE(v.marca||' '||v.modello||' ('||v.targa||')', '') AS veicolo_str,
               COALESCE(p.nominativo, '') AS proprietario_str,
               COALESCE(det.nominativo, '') AS detentore_str
        FROM demolizioni d
        LEFT JOIN veicoli v ON v.id = d.veicolo_id
        LEFT JOIN anagrafiche p ON p.id = d.proprietario_id
        LEFT JOIN anagrafiche det ON det.id = d.detentore_id
        ORDER BY d.data_presa_in_carico DESC
    """)
    return jsonify([dict(r) for r in rows])

@app.route("/api/demolizioni", methods=["POST"])
@require_login
def api_demolizioni_crea():
    u = cu()
    d = request.json or {}
    # Campi base sempre presenti
    campi_base = ["data_presa_in_carico","reg_demolitori","pag_reg","veicolo_id",
                  "proprietario_id","detentore_id","ufficio_provinciale",
                  "targhe_consegnate","carta_circolazione","concessionaria",
                  "peso_effettivo_kg","peso_netto_kg","modalita_radiazione","note"]
    # Campi opzionali aggiunti dopo
    campi_opt  = ["ora_presa_in_carico","num_albatros","certificato_id"]
    
    def try_insert(conn, campi, vals):
        sql = "INSERT INTO demolizioni ("+",".join(campi)+",creato_da) VALUES ("+",".join(["?"]*len(campi))+",?)"
        return conn.execute(sql, vals + [u.get("id")])
    
    try:
        with db._write_lock:
            conn = db.get_connection()
            # Prima prova con tutti i campi opzionali
            campi_tutti = campi_base + campi_opt
            vals_tutti  = [d.get(k) for k in campi_tutti]
            try:
                cur = try_insert(conn, campi_tutti, vals_tutti)
            except Exception:
                # Fallback: solo campi base
                vals_base = [d.get(k) for k in campi_base]
                cur = try_insert(conn, campi_base, vals_base)
            conn.commit()
            conn.close()
        return jsonify({"ok": True, "id": cur.lastrowid, "msg": "Demolizione salvata"})
    except Exception as e:
        log.error(f"api_demolizioni_crea: {e}")
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/demolizioni/<int:did>", methods=["PUT"])
@require_login
def api_demolizioni_update(did):
    d = request.json or {}
    campi = ["data_presa_in_carico","reg_demolitori","pag_reg","veicolo_id",
             "proprietario_id","detentore_id","ufficio_provinciale",
             "targhe_consegnate","carta_circolazione","concessionaria",
             "peso_effettivo_kg","peso_netto_kg","modalita_radiazione",
             "num_albatros","certificato_id","note"]
    try:
        with db._write_lock:
            conn = db.get_connection()
            sets = ", ".join(f"{k}=?" for k in campi if k in d)
            vals = [d[k] for k in campi if k in d] + [did]
            conn.execute(f"UPDATE demolizioni SET {sets} WHERE id=?", vals)
            conn.commit()
            conn.close()
        return jsonify({"ok": True, "msg": "Aggiornata"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/demolizioni/<int:did>", methods=["DELETE"])
@require_login
def api_demolizioni_delete(did):
    try:
        with db._write_lock:
            conn = db.get_connection()
            conn.execute("DELETE FROM ricambi_sottratti WHERE demolizione_id=?", (did,))
            conn.execute("DELETE FROM demolizioni WHERE id=?", (did,))
            conn.commit()
            conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/demolizioni/<int:did>/ricambi", methods=["GET"])
@require_login
def api_ricambi_get(did):
    rows = db.fetchall("""
        SELECT r.*, COALESCE(c.nome,'') AS pezzo_nome
        FROM ricambi_sottratti r
        LEFT JOIN componenti c ON c.id = r.componente_id
        WHERE r.demolizione_id=?
    """, (did,))
    return jsonify([dict(r) for r in rows])

@app.route("/api/demolizioni/<int:did>/ricambi", methods=["POST"])
@require_login
def api_ricambi_add(did):
    d = request.json or {}
    try:
        with db._write_lock:
            conn = db.get_connection()
            conn.execute(
                "INSERT INTO ricambi_sottratti (demolizione_id,componente_id,peso_kg,note) VALUES (?,?,?,?)",
                (did, d.get("componente_id"), d.get("peso_kg"), d.get("note")))
            tot = conn.execute(
                "SELECT COALESCE(SUM(peso_kg),0) as t FROM ricambi_sottratti WHERE demolizione_id=?",
                (did,)).fetchone()["t"]
            conn.execute(
                "UPDATE demolizioni SET peso_netto_kg=MAX(0, COALESCE(peso_effettivo_kg,0)-?) WHERE id=?",
                (tot, did))
            conn.commit()
            conn.close()
        return jsonify({"ok": True, "msg": "Ricambio aggiunto"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/demolizioni/ricambi/<int:rid>", methods=["DELETE"])
@require_login
def api_ricambi_del(rid):
    try:
        with db._write_lock:
            conn = db.get_connection()
            row = conn.execute("SELECT * FROM ricambi_sottratti WHERE id=?", (rid,)).fetchone()
            conn.execute("DELETE FROM ricambi_sottratti WHERE id=?", (rid,))
            if row:
                tot = conn.execute(
                    "SELECT COALESCE(SUM(peso_kg),0) as t FROM ricambi_sottratti WHERE demolizione_id=?",
                    (row["demolizione_id"],)).fetchone()["t"]
                conn.execute(
                    "UPDATE demolizioni SET peso_netto_kg=MAX(0,COALESCE(peso_effettivo_kg,0)-?) WHERE id=?",
                    (tot, row["demolizione_id"]))
            conn.commit()
            conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/anagrafiche", methods=["GET"])
@require_login
def api_anagrafiche():
    rows = db.fetchall("SELECT * FROM anagrafiche ORDER BY nominativo")
    return jsonify([dict(r) for r in rows])

@app.route("/api/anagrafiche", methods=["POST"])
@require_login
def api_anagrafiche_crea():
    d = request.json or {}
    try:
        with db._write_lock:
            conn = db.get_connection()
            cur = conn.execute(
                "INSERT INTO anagrafiche (nominativo,cf_piva,tipo,telefono,email,indirizzo) VALUES (?,?,?,?,?,?)",
                (d.get("nominativo"), d.get("cf_piva"), d.get("tipo","privato"),
                 d.get("telefono"), d.get("email"), d.get("indirizzo")))
            conn.commit()
            conn.close()
        return jsonify({"ok": True, "id": cur.lastrowid, "msg": "Anagrafica salvata",
                        "nominativo": d.get("nominativo")})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/veicoli", methods=["GET"])
@require_login
def api_veicoli():
    try:
        rows = db.fetchall("SELECT id, targa, telaio, classe, marca, modello, anno_immatricolazione, num_motore, colore, note FROM veicoli ORDER BY id DESC")
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        log.error(f"api_veicoli GET error: {e}")
        return jsonify([])

@app.route("/api/veicoli", methods=["POST"])
@require_login
def api_veicoli_crea():
    d = request.json or {}
    try:
        with db._write_lock:
            conn = db.get_connection()
            try:
                cur = conn.execute(
                    "INSERT INTO veicoli (targa,telaio,classe,marca,modello,anno_immatricolazione,num_motore,note) VALUES (?,?,?,?,?,?,?,?)",
                    (d.get("targa"), d.get("telaio"), d.get("classe",""),
                     d.get("marca"), d.get("modello"),
                     d.get("anno_immatricolazione"), d.get("num_motore"), d.get("note")))
                conn.commit()
                conn.close()
                new_id = cur.lastrowid
            finally:
                conn.close()
        targa   = d.get("targa","") or ""
        marca   = d.get("marca","") or ""
        modello = d.get("modello","") or ""
        label   = (marca+" "+modello).strip() + (" ("+targa+")" if targa else "")
        return jsonify({"ok": True, "id": new_id, "msg": "Veicolo salvato", "label": label})
    except Exception as e:
        log.error(f"api_veicoli POST error: {e}")
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route("/api/demolizioni/prossimi-progressivi")
@require_login
def api_demolizioni_progressivi():
    """Restituisce i valori automatici per una nuova demolizione."""
    import datetime
    try:
        next_id  = db.fetchone("SELECT COALESCE(MAX(id),0)+1 as v FROM demolizioni")["v"]
        next_pag = db.fetchone("SELECT COALESCE(MAX(CAST(pag_reg AS INTEGER)),0)+1 as v FROM demolizioni")["v"]
        anno = datetime.datetime.now().year
        now  = datetime.datetime.now()
        return jsonify({
            "ok": True,
            "next_id": next_id,
            "next_pag": next_pag,
            "reg_demolitori": f"01/{anno}",
            "data": now.strftime("%Y-%m-%d"),
            "ora": now.strftime("%H:%M")
        })
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/demolizioni/cerca")
@require_login  
def api_demolizioni_cerca():
    """Ricerca demolizioni per qualsiasi campo."""
    q = request.args.get("q","").strip()
    if not q:
        rows = db.fetchall("""
            SELECT d.id, d.reg_demolitori, d.pag_reg, d.data_presa_in_carico,
                   d.ufficio_provinciale, d.concessionaria,
                   COALESCE(v.marca||' '||v.modello||' ('||v.targa||')', '') AS veicolo_str,
                   COALESCE(v.targa,'') AS targa,
                   COALESCE(p.nominativo,'') AS proprietario_str,
                   COALESCE(det.nominativo,'') AS detentore_str,
                   d.peso_effettivo_kg, d.peso_netto_kg, d.modalita_radiazione,
                   d.num_albatros, d.targhe_consegnate, d.carta_circolazione,
                   d.veicolo_id, d.proprietario_id, d.detentore_id
            FROM demolizioni d
            LEFT JOIN veicoli v ON v.id=d.veicolo_id
            LEFT JOIN anagrafiche p ON p.id=d.proprietario_id
            LEFT JOIN anagrafiche det ON det.id=d.detentore_id
            ORDER BY d.id DESC LIMIT 200
        """)
    else:
        like = f"%{q}%"
        rows = db.fetchall("""
            SELECT d.id, d.reg_demolitori, d.pag_reg, d.data_presa_in_carico,
                   d.ufficio_provinciale, d.concessionaria,
                   COALESCE(v.marca||' '||v.modello||' ('||v.targa||')', '') AS veicolo_str,
                   COALESCE(v.targa,'') AS targa,
                   COALESCE(p.nominativo,'') AS proprietario_str,
                   COALESCE(det.nominativo,'') AS detentore_str,
                   d.peso_effettivo_kg, d.peso_netto_kg, d.modalita_radiazione,
                   d.num_albatros, d.targhe_consegnate, d.carta_circolazione,
                   d.veicolo_id, d.proprietario_id, d.detentore_id
            FROM demolizioni d
            LEFT JOIN veicoli v ON v.id=d.veicolo_id
            LEFT JOIN anagrafiche p ON p.id=d.proprietario_id
            LEFT JOIN anagrafiche det ON det.id=d.detentore_id
            WHERE d.reg_demolitori LIKE ? OR d.pag_reg LIKE ?
               OR d.ufficio_provinciale LIKE ? OR d.concessionaria LIKE ?
               OR v.targa LIKE ? OR v.marca LIKE ? OR v.modello LIKE ?
               OR p.nominativo LIKE ? OR det.nominativo LIKE ?
               OR CAST(d.id AS TEXT) LIKE ?
            ORDER BY d.id DESC LIMIT 200
        """, [like]*10)
    return jsonify([dict(r) for r in rows])


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
