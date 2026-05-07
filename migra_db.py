"""Script migrazione DB PerilCar"""
import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'db', 'perilcar.db')
print(f"DB: {db_path}")
conn = sqlite3.connect(db_path, timeout=30)
conn.execute("PRAGMA journal_mode=WAL")

# Elimina TUTTE le tabelle residue
for bak in ['veicoli_bak','veicoli_old','veicoli_tmp']:
    try:
        conn.execute(f"DROP TABLE IF EXISTS {bak}")
        conn.commit()
        print(f"Rimossa {bak} (se esisteva)")
    except Exception as e:
        print(f"  {bak}: {e}")

# Ricrea veicoli senza UNIQUE
conn.row_factory = sqlite3.Row
sql = conn.execute("SELECT sql FROM sqlite_master WHERE name='veicoli'").fetchone()
if sql and 'UNIQUE' in sql[0].upper():
    print("Rimozione UNIQUE da veicoli...")
    rows = conn.execute("SELECT * FROM veicoli").fetchall()
    conn.execute("""CREATE TABLE veicoli_new (
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
        conn.execute(f"INSERT INTO veicoli_new ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})", vals)
    conn.execute("DROP TABLE veicoli")
    conn.execute("ALTER TABLE veicoli_new RENAME TO veicoli")
    conn.commit()
    print("  OK")

# Aggiungi colonne mancanti
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

# Test finale
try:
    conn.execute("INSERT INTO veicoli (targa,classe,marca) VALUES ('_TEST_','Motociclo','TEST')")
    conn.execute("DELETE FROM veicoli WHERE targa='_TEST_'")
    conn.commit()
    print("\nTest insert: OK ✓")
except Exception as e:
    print(f"\nTest insert FALLITO: {e}")

conn.close()
print("Migrazione completata!")
input("Premi INVIO...")
