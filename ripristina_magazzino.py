"""Ripristina i componenti del magazzino dal backup"""
import sqlite3, os, glob

db_path = os.path.join(os.path.dirname(__file__), 'db', 'perilcar.db')

# Trova TUTTI i backup
backup_files = sorted(glob.glob(db_path + '.backup_*'))
print("Backup disponibili:")
for i, b in enumerate(backup_files):
    size = os.path.getsize(b)
    print(f"  [{i}] {os.path.basename(b)} ({size//1024//1024} MB)")

if not backup_files:
    print("ERRORE: nessun backup trovato!")
    input("Premi INVIO..."); exit()

# Usa il backup più grande (quello con i dati)
backup = max(backup_files, key=os.path.getsize)
print(f"\nUso backup: {os.path.basename(backup)} ({os.path.getsize(backup)//1024//1024} MB)")

old = sqlite3.connect(backup, timeout=30)
old.row_factory = sqlite3.Row

# Lista tabelle nel backup
tabelle_bak = [r[0] for r in old.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tabelle nel backup:", tabelle_bak)

# Determina il nome della tabella componenti
tab_comp = 'componenti' if 'componenti' in tabelle_bak else None
tab_mag  = 'magazzino'  if 'magazzino'  in tabelle_bak else None
tab_mov  = 'movimenti_magazzino' if 'movimenti_magazzino' in tabelle_bak else None

if not tab_comp:
    print("ERRORE: tabella componenti non trovata nel backup!")
    old.close(); input("Premi INVIO..."); exit()

componenti = old.execute(f"SELECT * FROM {tab_comp}").fetchall()
magazzino  = old.execute(f"SELECT * FROM {tab_mag}").fetchall() if tab_mag else []
movimenti  = old.execute(f"SELECT * FROM {tab_mov}").fetchall() if tab_mov else []
print(f"Componenti: {len(componenti)}, Magazzino: {len(magazzino)}, Movimenti: {len(movimenti)}")
old.close()

# Importa nel DB corrente
new = sqlite3.connect(db_path, timeout=30)
new.row_factory = sqlite3.Row

new.execute("DELETE FROM movimenti_magazzino")
new.execute("DELETE FROM magazzino")
new.execute("DELETE FROM componenti")
new.commit()

def importa_tabella(conn, table, rows):
    if not rows: return 0
    cols_db = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    n = 0
    for row in rows:
        d = dict(row)
        cols = [k for k in d.keys() if k in cols_db]
        vals = [d[k] for k in cols]
        try:
            conn.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})", vals)
            n += 1
        except: pass
    conn.commit()
    return n

n1 = importa_tabella(new, 'componenti', componenti)
n2 = importa_tabella(new, 'magazzino', magazzino)
n3 = importa_tabella(new, 'movimenti_magazzino', movimenti)
print(f"Importati: {n1} componenti, {n2} magazzino, {n3} movimenti")

# Verifica
tot = new.execute("SELECT COUNT(*) FROM componenti").fetchone()[0]
print(f"\nComponenti nel DB: {tot}")
new.close()
print("Completato!")
input("Premi INVIO...")
