"""Script migrazione DB PerilCar - esegui: python migra_db.py"""
import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'db', 'perilcar.db')
print(f"DB: {db_path}")
conn = sqlite3.connect(db_path, timeout=30)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")

# Lista TUTTE le tabelle incluse temporanee
tabelle = [r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
print("Tabelle:", tabelle)

# 1. Gestisci residui di migrazione precedente
for bak in ['veicoli_bak','veicoli_old']:
    if bak in tabelle:
        print(f"Trovata {bak} residua...")
        if 'veicoli' not in tabelle:
            conn.execute(f"ALTER TABLE {bak} RENAME TO veicoli")
            print(f"  Rinominata a veicoli OK")
        else:
            conn.execute(f"DROP TABLE {bak}")
            print(f"  Eliminata OK")
        conn.commit()
        tabelle = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]

# 2. Ricrea veicoli senza UNIQUE se necessario
sql = conn.execute("SELECT sql FROM sqlite_master WHERE name='veicoli'").fetchone()
if sql and 'UNIQUE' in sql[0].upper():
    print("Rimozione UNIQUE da veicoli...")
    rows = conn.execute("SELECT * FROM veicoli").fetchall()
    conn.execute("DROP TABLE IF EXISTS veicoli_tmp")
    conn.execute("""CREATE TABLE veicoli_tmp (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        targa TEXT, telaio TEXT, classe TEXT, marca TEXT, modello TEXT,
        anno_immatricolazione TEXT, num_motore TEXT, colore TEXT, note TEXT,
        stato TEXT DEFAULT 'in_attesa', creato_da INTEGER,
        creato_il TEXT DEFAULT (datetime('now'))
    )""")
    for r in rows:
        d = dict(r)
        cols = [k for k in ['id','targa','telaio','classe','marca','modello',
                             'anno_immatricolazione','num_motore','colore','note',
                             'stato','creato_da','creato_il'] if k in d]
        vals = [d[k] for k in cols]
        conn.execute(f"INSERT INTO veicoli_tmp ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})", vals)
    conn.execute("DROP TABLE veicoli")
    conn.execute("ALTER TABLE veicoli_tmp RENAME TO veicoli")
    conn.commit()
    print("  UNIQUE rimosso OK")

# 3. Aggiungi colonne mancanti
colonne_veicoli = [("classe","TEXT"),("marca","TEXT"),("modello","TEXT"),
                   ("anno_immatricolazione","TEXT"),("num_motore","TEXT"),
                   ("colore","TEXT"),("note","TEXT"),("stato","TEXT")]
for col,typ in colonne_veicoli:
    vei = [r[1] for r in conn.execute("PRAGMA table_info(veicoli)").fetchall()]
    if col not in vei:
        conn.execute(f"ALTER TABLE veicoli ADD COLUMN {col} {typ}")
        print(f"  + veicoli.{col}")

colonne_dem = [("ora_presa_in_carico","TEXT"),("num_albatros","TEXT")]
for col,typ in colonne_dem:
    try:
        dem = [r[1] for r in conn.execute("PRAGMA table_info(demolizioni)").fetchall()]
        if col not in dem:
            conn.execute(f"ALTER TABLE demolizioni ADD COLUMN {col} {typ}")
            print(f"  + demolizioni.{col}")
    except: pass

colonne_ana = [("cognome","TEXT"),("nome","TEXT"),("sesso","TEXT"),
               ("data_nascita","TEXT"),("luogo_nascita","TEXT"),
               ("comune","TEXT"),("provincia","TEXT"),("via","TEXT"),
               ("civico","TEXT"),("cap","TEXT"),("tipo_doc","TEXT"),
               ("num_doc","TEXT"),("data_doc","TEXT"),("rilasciato_da","TEXT"),
               ("cellulare","TEXT"),("fax","TEXT")]
for col,typ in colonne_ana:
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
print("classe OK:", 'classe' in vei)

# Test insert
try:
    conn.execute("INSERT INTO veicoli (targa,classe,marca) VALUES ('_TEST_','Motociclo','TEST')")
    conn.execute("DELETE FROM veicoli WHERE targa='_TEST_'")
    conn.commit()
    print("Test insert: OK")
except Exception as e:
    print(f"Test insert FALLITO: {e}")

conn.close()
print("\nMigrazione completata!")
input("Premi INVIO per chiudere...")
