"""Script di migrazione DB - esegui una volta sola: python migra_db.py"""
import sqlite3, os, sys

db_path = os.path.join(os.path.dirname(__file__), 'db', 'perilcar.db')
print(f"DB: {db_path}")

conn = sqlite3.connect(db_path, timeout=30)

# Veicoli
vei = [r[1] for r in conn.execute("PRAGMA table_info(veicoli)").fetchall()]
print("Colonne veicoli:", vei)
for col,typ in [("classe","TEXT"),("marca","TEXT"),("modello","TEXT"),
                ("anno_immatricolazione","TEXT"),("num_motore","TEXT"),
                ("colore","TEXT"),("note","TEXT")]:
    if col not in vei:
        conn.execute(f"ALTER TABLE veicoli ADD COLUMN {col} {typ}")
        print(f"  + aggiunta colonna: {col}")

# Demolizioni
dem = [r[1] for r in conn.execute("PRAGMA table_info(demolizioni)").fetchall()]
for col,typ in [("ora_presa_in_carico","TEXT"),("num_albatros","TEXT")]:
    if col not in dem:
        conn.execute(f"ALTER TABLE demolizioni ADD COLUMN {col} {typ}")
        print(f"  + aggiunta colonna demolizioni: {col}")

# Anagrafiche
ana = [r[1] for r in conn.execute("PRAGMA table_info(anagrafiche)").fetchall()]
for col,typ in [("cognome","TEXT"),("nome","TEXT"),("sesso","TEXT"),
                ("data_nascita","TEXT"),("luogo_nascita","TEXT"),
                ("comune","TEXT"),("provincia","TEXT"),("via","TEXT"),
                ("civico","TEXT"),("cap","TEXT"),("tipo_doc","TEXT"),
                ("num_doc","TEXT"),("data_doc","TEXT"),("rilasciato_da","TEXT"),
                ("cellulare","TEXT"),("fax","TEXT")]:
    if col not in ana:
        conn.execute(f"ALTER TABLE anagrafiche ADD COLUMN {col} {typ}")
        print(f"  + aggiunta colonna anagrafiche: {col}")

conn.commit()
conn.close()
print("\nMigrazione completata!")
input("Premi INVIO per chiudere...")
