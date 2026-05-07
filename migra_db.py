"""Script migrazione DB PerilCar - esegui: python migra_db.py"""
import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'db', 'perilcar.db')
print(f"DB: {db_path}")
conn = sqlite3.connect(db_path, timeout=30)
conn.row_factory = sqlite3.Row

tabelle = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tabelle presenti:", tabelle)

# 1. Ripara tabella veicoli se è rimasta la bak
if 'veicoli_bak' in tabelle and 'veicoli' not in tabelle:
    print("Ripristino veicoli da veicoli_bak...")
    conn.execute("ALTER TABLE veicoli_bak RENAME TO veicoli")
    conn.commit()
    print("  OK")
elif 'veicoli_bak' in tabelle and 'veicoli' in tabelle:
    print("Trovato veicoli_bak residuo - elimino...")
    conn.execute("DROP TABLE veicoli_bak")
    conn.commit()
    print("  OK")

# 2. Ricrea veicoli senza UNIQUE se necessario
sql = conn.execute("SELECT sql FROM sqlite_master WHERE name='veicoli'").fetchone()
if sql and 'UNIQUE' in sql[0].upper():
    print("Rimozione UNIQUE da veicoli...")
    rows = conn.execute("SELECT * FROM veicoli").fetchall()
    conn.executescript("""
        ALTER TABLE veicoli RENAME TO veicoli_old;
        CREATE TABLE veicoli (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            targa TEXT, telaio TEXT, classe TEXT, marca TEXT, modello TEXT,
            anno_immatricolazione TEXT, num_motore TEXT, colore TEXT, note TEXT,
            stato TEXT DEFAULT 'in_attesa', creato_da INTEGER,
            creato_il TEXT DEFAULT (datetime('now'))
        );
    """)
    for r in rows:
        d = dict(r)
        cols = [k for k in ['id','targa','telaio','classe','marca','modello',
                             'anno_immatricolazione','num_motore','colore','note',
                             'stato','creato_da','creato_il'] if k in d]
        vals = [d[k] for k in cols]
        conn.execute(f"INSERT INTO veicoli ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})", vals)
    conn.execute("DROP TABLE IF EXISTS veicoli_old")
    conn.commit()
    print("  OK")
else:
    print("Tabella veicoli OK")

# 3. Aggiungi colonne mancanti
for col,typ in [("classe","TEXT"),("marca","TEXT"),("modello","TEXT"),
                ("anno_immatricolazione","TEXT"),("num_motore","TEXT"),
                ("colore","TEXT"),("note","TEXT"),("stato","TEXT")]:
    vei = [r[1] for r in conn.execute("PRAGMA table_info(veicoli)").fetchall()]
    if col not in vei:
        conn.execute(f"ALTER TABLE veicoli ADD COLUMN {col} {typ}")
        print(f"  + veicoli.{col}")

for col,typ in [("ora_presa_in_carico","TEXT"),("num_albatros","TEXT")]:
    try:
        dem = [r[1] for r in conn.execute("PRAGMA table_info(demolizioni)").fetchall()]
        if col not in dem:
            conn.execute(f"ALTER TABLE demolizioni ADD COLUMN {col} {typ}")
            print(f"  + demolizioni.{col}")
    except: pass

for col,typ in [("cognome","TEXT"),("nome","TEXT"),("sesso","TEXT"),
                ("data_nascita","TEXT"),("luogo_nascita","TEXT"),
                ("comune","TEXT"),("provincia","TEXT"),("via","TEXT"),
                ("civico","TEXT"),("cap","TEXT"),("tipo_doc","TEXT"),
                ("num_doc","TEXT"),("data_doc","TEXT"),("rilasciato_da","TEXT"),
                ("cellulare","TEXT"),("fax","TEXT")]:
    try:
        ana = [r[1] for r in conn.execute("PRAGMA table_info(anagrafiche)").fetchall()]
        if col not in ana:
            conn.execute(f"ALTER TABLE anagrafiche ADD COLUMN {col} {typ}")
            print(f"  + anagrafiche.{col}")
    except: pass

conn.commit()

# Verifica finale
vei = [r[1] for r in conn.execute("PRAGMA table_info(veicoli)").fetchall()]
print(f"\nColonne veicoli: {vei}")
print("classe presente:", 'classe' in vei)
conn.close()
print("\nMigrazione completata!")
input("Premi INVIO per chiudere...")
