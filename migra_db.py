"""Script migrazione DB PerilCar - esegui una volta: python migra_db.py"""
import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'db', 'perilcar.db')
print(f"DB: {db_path}")
conn = sqlite3.connect(db_path, timeout=30)
conn.row_factory = sqlite3.Row

# 1. Ricrea tabella veicoli senza UNIQUE su targa/telaio
sql = conn.execute("SELECT sql FROM sqlite_master WHERE name='veicoli'").fetchone()
if sql and ('UNIQUE' in sql[0].upper() or 'unique' in sql[0]):
    print("Rimozione UNIQUE constraint da veicoli...")
    rows = conn.execute("SELECT * FROM veicoli").fetchall()
    conn.executescript("""
        ALTER TABLE veicoli RENAME TO veicoli_bak;
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
        ph = ','.join(['?']*len(cols))
        conn.execute(f"INSERT INTO veicoli ({','.join(cols)}) VALUES ({ph})", vals)
    conn.execute("DROP TABLE veicoli_bak")
    conn.commit()
    print("  OK - UNIQUE rimosso")
else:
    print("Tabella veicoli OK (nessun UNIQUE da rimuovere)")

# 2. Aggiungi colonne mancanti
for col,typ in [("classe","TEXT"),("marca","TEXT"),("modello","TEXT"),
                ("anno_immatricolazione","TEXT"),("num_motore","TEXT"),
                ("colore","TEXT"),("note","TEXT"),("stato","TEXT")]:
    vei = [r[1] for r in conn.execute("PRAGMA table_info(veicoli)").fetchall()]
    if col not in vei:
        conn.execute(f"ALTER TABLE veicoli ADD COLUMN {col} {typ}")
        print(f"  + colonna veicoli.{col}")

for col,typ in [("ora_presa_in_carico","TEXT"),("num_albatros","TEXT")]:
    dem = [r[1] for r in conn.execute("PRAGMA table_info(demolizioni)").fetchall()]
    if col not in dem:
        conn.execute(f"ALTER TABLE demolizioni ADD COLUMN {col} {typ}")
        print(f"  + colonna demolizioni.{col}")

for col,typ in [("cognome","TEXT"),("nome","TEXT"),("sesso","TEXT"),
                ("data_nascita","TEXT"),("luogo_nascita","TEXT"),
                ("comune","TEXT"),("provincia","TEXT"),("via","TEXT"),
                ("civico","TEXT"),("cap","TEXT"),("tipo_doc","TEXT"),
                ("num_doc","TEXT"),("data_doc","TEXT"),("rilasciato_da","TEXT"),
                ("cellulare","TEXT"),("fax","TEXT")]:
    ana = [r[1] for r in conn.execute("PRAGMA table_info(anagrafiche)").fetchall()]
    if col not in ana:
        conn.execute(f"ALTER TABLE anagrafiche ADD COLUMN {col} {typ}")
        print(f"  + colonna anagrafiche.{col}")

conn.commit()
conn.close()
print("\nMigrazione completata!")
input("Premi INVIO per chiudere...")
