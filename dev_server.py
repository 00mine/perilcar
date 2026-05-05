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
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

@app.after_request
def no_cache(response):
    """Disabilita cache browser per tutti i template HTML durante sviluppo."""
    if response.content_type and 'text/html' in response.content_type:
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

# ── Scrittura sicura: tutte le operazioni passano da qui ─────────────────────
def db_write(statements: list):
    """Esegue più statement in una singola transazione atomica."""
    with db._write_lock:
        conn = db.get_connection()
        try:
            for sql, params in statements:
                conn.execute(sql, params)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

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
                return jsonify({"ok": True, "msg": "Componente creato", "id": comp_id})
            except Exception as e:
                conn.rollback()
                return jsonify({"ok": False, "msg": str(e)}), 500
            finally:
                conn.close()
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
            except Exception as e:
                conn.rollback()
                log.error(f"Import errore riga {row_n}: {e}")
                return jsonify({"ok": False, "msg": f"Errore riga {row_n}: {e}"}), 500
            finally:
                conn.close()

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
                        log.info(f"Import progress: riga {row_n}, nuovi={importati}, aggiornati={aggiornati}")
                        socketio.emit("import_progress", {
                            "processed": row_n-1,
                            "importati": importati,
                            "aggiornati": aggiornati
                        })

                conn.commit()
                wb.close()
            except Exception as e:
                conn.rollback()
                log.error(f"Import errore riga {row_n}: {e}")
                return jsonify({"ok": False, "msg": f"Errore riga {row_n}: {e}"}), 500
            finally:
                conn.close()

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
# ASSISTENTE AI — usa Claude API
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/assistente", methods=["POST"])
@require_login
def api_assistente():
    """
    Assistente AI che risponde a domande sul magazzino.
    Riceve una domanda in linguaggio naturale e risponde intelligentemente.
    """
    import urllib.request, json as _json

    d        = request.json or {}
    domanda  = (d.get("domanda") or "").strip()
    if not domanda:
        return jsonify({"ok": False, "msg": "Domanda vuota"}), 400

    # Carica tutto il magazzino come contesto
    componenti = db.fetchall("""
        SELECT cmp, articolo, categoria, marca, modello,
               cilindrata, carburante, versione, anno_da, anno_a,
               colore, ubicazione, scorta, esistenza, extra1, extra2, extra3, extra4
        FROM v_giacenza
        ORDER BY articolo
    """)

    # Costruisci un indice compatto (max ~8000 token)
    righe = []
    for r in componenti:
        parts = [f"{r['cmp']}|{r['articolo']}|ES:{r['esistenza']}|SC:{r['scorta']}"]
        for k in ['marca','categoria','modello','cilindrata','carburante',
                  'versione','anno_da','anno_a','colore','ubicazione',
                  'extra1','extra2','extra3','extra4']:
            v = r.get(k)
            if v: parts.append(str(v))
        righe.append(' '.join(parts))

    magazzino_txt = "\n".join(righe[:3000])  # max 3000 righe

    system_prompt = f"""Sei un assistente esperto per un magazzino di autodemolizioni chiamato PerilCar.
Hai accesso al magazzino completo. Rispondi SEMPRE in italiano, in modo conciso e diretto.

REGOLE:
1. Se ti chiedono se c'è un pezzo: cerca nel magazzino per codice, nome, marca, modello, categoria
2. Indica sempre la giacenza attuale (ES = esistenza) e la scorta minima (SC)
3. Se un pezzo non c'è o è sotto scorta, suggerisci pezzi COMPATIBILI (stessa categoria, marca simile, stesso cilindrata/carburante)
4. Rispondi in 2-4 frasi massimo, sii pratico
5. Se non trovi il pezzo, dillo chiaramente e suggerisci alternative

MAGAZZINO ATTUALE (formato: CODICE|NOME|ES:giacenza|SC:scorta|altri dati):
{magazzino_txt}

Se il magazzino è vuoto o non caricato, dillo all'utente."""

    # Usa Ollama (AI locale gratuita)
    payload = _json.dumps({
        "model": "llama3.2:1b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": domanda}
        ],
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 400}
    }).encode()

    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = _json.loads(resp.read())
            risposta = result["message"]["content"]
            return jsonify({"ok": True, "risposta": risposta})
    except urllib.error.URLError as e:
        msg = "Ollama non è avviato. Apri il terminale e scrivi: ollama serve"
        log.error(f"Ollama non raggiungibile: {e}")
        return jsonify({"ok": False, "msg": msg}), 503
    except Exception as e:
        log.error(f"Assistente error: {e}")
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route("/api/backup", methods=["POST"])
@require_login
def api_backup():
    path = db.backup()
    return jsonify({"ok": True, "path": path})

# ══════════════════════════════════════════════════════════════════════════════
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
