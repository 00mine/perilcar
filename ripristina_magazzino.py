"""Ripristina i componenti del magazzino dal backup"""
import sqlite3, os, glob

db_path = os.path.join(os.path.dirname(__file__), 'db', 'perilcar.db')

# Trova il backup più recente
backup_files = sorted(glob.glob(db_path + '.backup_*'))
if not backup_files:
    print("ERRORE: nessun backup trovato!")
    input("Premi INVIO...")
    exit()

backup = backup_files[-1]
print(f"Backup trovato: {backup}")

# Leggi componenti e magazzino dal backup
old = sqlite3.connect(backup, timeout=30)
old.row_factory = sqlite3.Row

componenti = old.execute("SELECT * FROM componenti").fetchall()
magazzino  = old.execute("SELECT * FROM magazzino").fetchall()
movimenti  = old.execute("SELECT * FROM movimenti_magazzino").fetchall()
print(f"Componenti nel backup: {len(componenti)}")
print(f"Magazzino nel backup:  {len(magazzino)}")
print(f"Movimenti nel backup:  {len(movimenti)}")
old.close()

# Importa nel DB corrente
new = sqlite3.connect(db_path, timeout=30)
new.row_factory = sqlite3.Row

# Svuota prima
new.execute("DELETE FROM movimenti_magazzino")
new.execute("DELETE FROM magazzino")
new.execute("DELETE FROM componenti")
new.commit()

# Reimporta componenti
c_cols = [r[1] for r in new.execute("PRAGMA table_info(componenti)").fetchall()]
imported = 0
for row in componenti:
    d = dict(row)
    cols = [k for k in d.keys() if k in c_cols]
    vals = [d[k] for k in cols]
    try:
        new.execute(f"INSERT INTO componenti ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})", vals)
        imported += 1
    except: pass
new.commit()
print(f"Componenti importati: {imported}")

# Reimporta magazzino
m_cols = [r[1] for r in new.execute("PRAGMA table_info(magazzino)").fetchall()]
for row in magazzino:
    d = dict(row)
    cols = [k for k in d.keys() if k in m_cols]
    vals = [d[k] for k in cols]
    try:
        new.execute(f"INSERT INTO magazzino ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})", vals)
    except: pass
new.commit()
print(f"Magazzino importato")

# Reimporta movimenti
mv_cols = [r[1] for r in new.execute("PRAGMA table_info(movimenti_magazzino)").fetchall()]
for row in movimenti:
    d = dict(row)
    cols = [k for k in d.keys() if k in mv_cols]
    vals = [d[k] for k in cols]
    try:
        new.execute(f"INSERT INTO movimenti_magazzino ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})", vals)
    except: pass
new.commit()
print(f"Movimenti importati")

# Verifica
n = new.execute("SELECT COUNT(*) FROM componenti").fetchone()[0]
print(f"\nComponenti nel DB ora: {n}")
new.close()
print("Ripristino magazzino completato!")
input("Premi INVIO...")
