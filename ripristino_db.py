"""Ripristino DB PerilCar - risolve veicoli_bak corrotto"""
import sqlite3, os, shutil, datetime

db_path = os.path.join(os.path.dirname(__file__), 'db', 'perilcar.db')
backup_path = db_path + '.backup_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

print(f"DB: {db_path}")
print("Creo backup:", backup_path)
shutil.copy2(db_path, backup_path)

# Connetti al vecchio DB
old = sqlite3.connect(db_path, timeout=30)
old.row_factory = sqlite3.Row

# Leggi tutti i dati importanti
print("Leggo dati...")
try:
    componenti = old.execute("SELECT * FROM componenti").fetchall()
    print(f"  componenti: {len(componenti)}")
except: componenti = []
try:
    magazzino = old.execute("SELECT * FROM magazzino").fetchall()
    print(f"  magazzino: {len(magazzino)}")
except: magazzino = []
try:
    movimenti = old.execute("SELECT * FROM movimenti_magazzino").fetchall()
    print(f"  movimenti: {len(movimenti)}")
except: movimenti = []
try:
    utenti = old.execute("SELECT * FROM utenti").fetchall()
    print(f"  utenti: {len(utenti)}")
except: utenti = []
try:
    anagrafiche = old.execute("SELECT * FROM anagrafiche").fetchall()
    print(f"  anagrafiche: {len(anagrafiche)}")
except: anagrafiche = []
try:
    veicoli = old.execute("SELECT * FROM veicoli").fetchall()
    print(f"  veicoli: {len(veicoli)}")
except: veicoli = []
try:
    demolizioni = old.execute("SELECT * FROM demolizioni").fetchall()
    print(f"  demolizioni: {len(demolizioni)}")
except: demolizioni = []
try:
    ricambi = old.execute("SELECT * FROM ricambi_sottratti").fetchall()
    print(f"  ricambi: {len(ricambi)}")
except: ricambi = []
try:
    schema_ver = old.execute("SELECT version FROM schema_version WHERE id=1").fetchone()
    schema_ver = schema_ver[0] if schema_ver else 4
except: schema_ver = 4

old.close()

# Elimina e ricrea il DB
print("\nElimino vecchio DB e creo nuovo pulito...")
os.remove(db_path)

new = sqlite3.connect(db_path, timeout=30)
new.row_factory = sqlite3.Row
new.execute("PRAGMA journal_mode=WAL")

# Schema completo e pulito
new.executescript("""
CREATE TABLE schema_version (id INTEGER PRIMARY KEY, version INTEGER);
INSERT INTO schema_version VALUES (1, 4);

CREATE TABLE sqlite_sequence(name,seq);

CREATE TABLE utenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    ruolo TEXT DEFAULT 'operatore',
    attivo INTEGER DEFAULT 1,
    creato_il TEXT DEFAULT (datetime('now'))
);

CREATE TABLE componenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codice TEXT, nome TEXT, categoria TEXT, marca TEXT, modello TEXT,
    cilindrata TEXT, carburante TEXT, anno_da TEXT, anno_a TEXT,
    colore TEXT, nota TEXT, internet TEXT, extra1 TEXT, extra2 TEXT, extra3 TEXT, extra4 TEXT,
    cod_fornitore TEXT, fornitore TEXT, cod_prod_forn TEXT, prezzo_forn REAL,
    ord_multipli TEXT, gg_ordine TEXT, scorta INTEGER DEFAULT 0,
    listino1 REAL, listino2 REAL, listino3 REAL,
    ubicazione TEXT, stato_magazzino TEXT, files_path TEXT,
    intervallo TEXT, modello_extra TEXT,
    eliminato INTEGER DEFAULT 0,
    creato_da INTEGER, creato_il TEXT DEFAULT (datetime('now'))
);

CREATE TABLE magazzino (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    componente_id INTEGER NOT NULL REFERENCES componenti(id),
    esistenza INTEGER DEFAULT 0,
    creato_il TEXT DEFAULT (datetime('now'))
);

CREATE TABLE movimenti_magazzino (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    componente_id INTEGER REFERENCES componenti(id),
    tipo TEXT NOT NULL,
    quantita INTEGER NOT NULL,
    esistenza_prima INTEGER,
    esistenza_dopo INTEGER,
    riferimento TEXT, note TEXT,
    creato_da INTEGER,
    creato_il TEXT DEFAULT (datetime('now'))
);

CREATE TABLE anagrafiche (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nominativo TEXT NOT NULL,
    cf_piva TEXT, tipo TEXT DEFAULT 'privato',
    telefono TEXT, email TEXT, indirizzo TEXT,
    cognome TEXT, nome TEXT, sesso TEXT,
    data_nascita TEXT, luogo_nascita TEXT, prov_nascita TEXT,
    comune TEXT, provincia TEXT, via TEXT, civico TEXT, cap TEXT,
    tipo_doc TEXT, num_doc TEXT, data_doc TEXT, rilasciato_da TEXT,
    cellulare TEXT, fax TEXT,
    creato_il TEXT DEFAULT (datetime('now'))
);

CREATE TABLE veicoli (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    targa TEXT, telaio TEXT, classe TEXT, marca TEXT, modello TEXT,
    anno_immatricolazione TEXT, num_motore TEXT, colore TEXT,
    note TEXT, stato TEXT DEFAULT 'in_attesa',
    creato_da INTEGER,
    creato_il TEXT DEFAULT (datetime('now'))
);

CREATE TABLE demolizioni (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_presa_in_carico TEXT, ora_presa_in_carico TEXT,
    reg_demolitori TEXT, pag_reg TEXT,
    veicolo_id INTEGER REFERENCES veicoli(id),
    proprietario_id INTEGER REFERENCES anagrafiche(id),
    detentore_id INTEGER REFERENCES anagrafiche(id),
    ufficio_provinciale TEXT, targhe_consegnate INTEGER DEFAULT 0,
    carta_circolazione INTEGER DEFAULT 0, concessionaria TEXT,
    peso_effettivo_kg REAL, peso_netto_kg REAL,
    modalita_radiazione TEXT, num_albatros TEXT, certificato_id TEXT,
    note TEXT, creato_da INTEGER,
    creato_il TEXT DEFAULT (datetime('now'))
);

CREATE TABLE ricambi_sottratti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    demolizione_id INTEGER NOT NULL REFERENCES demolizioni(id),
    componente_id INTEGER REFERENCES componenti(id),
    peso_kg REAL, note TEXT,
    creato_il TEXT DEFAULT (datetime('now'))
);

CREATE TABLE rifiuti (id INTEGER PRIMARY KEY AUTOINCREMENT);
CREATE TABLE operai (id INTEGER PRIMARY KEY AUTOINCREMENT);
CREATE TABLE log_operazioni (id INTEGER PRIMARY KEY AUTOINCREMENT);
CREATE TABLE licenza (id INTEGER PRIMARY KEY AUTOINCREMENT);
""")

# Importa dati
def importa(table, rows, exclude_cols=[]):
    if not rows: return
    sample = dict(rows[0])
    cols = [k for k in sample.keys() if k not in exclude_cols]
    # Verifica colonne esistenti
    existing = [r[1] for r in new.execute(f"PRAGMA table_info({table})").fetchall()]
    cols = [c for c in cols if c in existing]
    if not cols: return
    ph = ','.join(['?']*len(cols))
    for row in rows:
        d = dict(row)
        vals = [d.get(c) for c in cols]
        try:
            new.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({ph})", vals)
        except Exception as e:
            pass  # Skip duplicati

print("Importo dati...")
importa('utenti', utenti)
importa('componenti', componenti)
importa('magazzino', magazzino)
importa('movimenti_magazzino', movimenti)
importa('anagrafiche', anagrafiche)
importa('veicoli', veicoli)
importa('demolizioni', demolizioni)
importa('ricambi_sottratti', ricambi)

new.commit()

# Verifica
n_comp = new.execute("SELECT COUNT(*) FROM componenti").fetchone()[0]
n_mag  = new.execute("SELECT COUNT(*) FROM magazzino").fetchone()[0]
n_ut   = new.execute("SELECT COUNT(*) FROM utenti").fetchone()[0]
print(f"\nDB nuovo creato:")
print(f"  componenti: {n_comp}")
print(f"  magazzino:  {n_mag}")
print(f"  utenti:     {n_ut}")

# Test insert demolizione
try:
    new.execute("INSERT INTO demolizioni (data_presa_in_carico,reg_demolitori) VALUES ('2026-05-07','01/2026')")
    new.execute("DELETE FROM demolizioni WHERE data_presa_in_carico='2026-05-07'")
    new.commit()
    print("  Test insert: OK")
except Exception as e:
    print(f"  Test insert FALLITO: {e}")

new.close()
print("\nDB ripristinato! Backup in:", backup_path)
input("Premi INVIO per chiudere...")
