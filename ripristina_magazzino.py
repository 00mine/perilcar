"""Copia diretta da backup al DB corrente usando ATTACH"""
import sqlite3, os, glob

db_path = os.path.join(os.path.dirname(__file__), 'db', 'perilcar.db')
backup_files = sorted(glob.glob(db_path + '.backup_*'), key=os.path.getsize, reverse=True)

print("Backup disponibili (per dimensione):")
for b in backup_files:
    print(f"  {os.path.basename(b)} - {os.path.getsize(b)//1024//1024} MB")

# Usa il backup più grande
backup = backup_files[0]
print(f"\nUso: {os.path.basename(backup)}")

# Verifica che abbia i componenti
old = sqlite3.connect(backup, timeout=30)
n_old = old.execute("SELECT COUNT(*) FROM componenti").fetchone()[0]
print(f"Componenti nel backup: {n_old}")
if n_old == 0:
    print("ERRORE: backup vuoto!")
    old.close(); input(); exit()
old.close()

# Copia usando ATTACH - copia tutto senza preoccuparsi delle colonne
conn = sqlite3.connect(db_path, timeout=30)
conn.execute(f"ATTACH DATABASE '{backup}' AS bak")

# Ricrea componenti con lo stesso schema del backup
conn.execute("DROP TABLE IF EXISTS componenti")
bak_schema = conn.execute("SELECT sql FROM bak.sqlite_master WHERE name='componenti'").fetchone()[0]
conn.execute(bak_schema)
conn.execute("INSERT INTO componenti SELECT * FROM bak.componenti")

# Ricrea magazzino
conn.execute("DROP TABLE IF EXISTS magazzino")
mag_schema = conn.execute("SELECT sql FROM bak.sqlite_master WHERE name='magazzino'").fetchone()[0]
if mag_schema:
    conn.execute(mag_schema)
    conn.execute("INSERT INTO magazzino SELECT * FROM bak.magazzino")

# Ricrea movimenti
conn.execute("DROP TABLE IF EXISTS movimenti_magazzino")
mov_schema = conn.execute("SELECT sql FROM bak.sqlite_master WHERE name='movimenti_magazzino'").fetchone()[0]
if mov_schema:
    conn.execute(mov_schema)
    conn.execute("INSERT INTO movimenti_magazzino SELECT * FROM bak.movimenti_magazzino")

conn.commit()

n = conn.execute("SELECT COUNT(*) FROM componenti").fetchone()[0]
print(f"Componenti importati: {n}")
conn.execute("DETACH DATABASE bak")
conn.close()
print("\nMagazzino ripristinato!")
input("Premi INVIO...")
