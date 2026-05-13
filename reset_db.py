"""
PerilCar ERP — Reset Database
Azzera tutti i dati di test mantenendo la struttura.
Crea l'utente admin iniziale.

Uso:
  python reset_db.py                  # con conferma interattiva
  python reset_db.py --force          # senza conferma (per script)
  python reset_db.py --admin-pwd XXX  # imposta password admin personalizzata
"""
import os, sys, sqlite3, hashlib, argparse, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
DB_DIR = ROOT / "db"
UPLOADS = ROOT / "web" / "static" / "uploads"


def conferma_se_serve(force: bool) -> bool:
    if force:
        return True
    print("\n" + "=" * 60)
    print("⚠️  ATTENZIONE — RESET DATABASE PERILCAR")
    print("=" * 60)
    print("Questa operazione cancellerà TUTTI i dati esistenti:")
    print("  • Tutti i componenti del magazzino")
    print("  • Tutti i movimenti dello storico")
    print("  • Tutte le demolizioni e veicoli/anagrafiche")
    print("  • Tutti gli utenti (creerà nuovo admin)")
    print("  • Tutte le foto caricate")
    print("\nVerrà fatto un BACKUP automatico prima del reset.")
    risposta = input("\nProcedere? Digita 'SI' per confermare: ").strip()
    return risposta == "SI"


def backup_prima_del_reset():
    """Backup completo della cartella db prima del reset."""
    if not DB_DIR.exists():
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = ROOT / "backup_pre_reset" / ts
    backup_dir.mkdir(parents=True, exist_ok=True)
    for f in DB_DIR.iterdir():
        if f.is_file() and f.suffix == ".db":
            shutil.copy2(f, backup_dir / f.name)
    print(f"✓ Backup salvato in: {backup_dir}")
    return backup_dir


def reset_magazzino_db(admin_user: str, admin_pwd: str):
    """Cancella e ricrea il database magazzino."""
    path = DB_DIR / "perilcar.db"
    if path.exists():
        path.unlink()
    DB_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(path))
    c = conn.cursor()
    c.executescript("""
        PRAGMA journal_mode=WAL;

        CREATE TABLE IF NOT EXISTS utenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            ruolo TEXT DEFAULT 'operatore',
            nome_completo TEXT,
            attivo INTEGER DEFAULT 1,
            eliminato INTEGER DEFAULT 0,
            creato_il TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS componenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cmp TEXT, articolo TEXT, tipologia TEXT, categoria TEXT,
            sottocategoria TEXT, cod_udm TEXT DEFAULT 'PZ', cod_iva TEXT,
            listino1 REAL, listino2 REAL, listino3 REAL,
            nota TEXT, cod_barre TEXT, marca TEXT, modello TEXT,
            extra1 TEXT, extra2 TEXT, extra3 TEXT, extra4 TEXT,
            cod_fornitore TEXT, fornitore TEXT, prezzo_forn REAL,
            scorta REAL DEFAULT 0, ubicazione TEXT,
            ord_multipli REAL, gg_ordine INTEGER,
            stato_magazzino TEXT DEFAULT 'attivo',
            colore TEXT, cilindrata TEXT, carburante TEXT, versione TEXT,
            anno_da INTEGER, anno_a INTEGER,
            immagine_path TEXT, files_path TEXT,
            eliminato INTEGER DEFAULT 0,
            creato_il TEXT DEFAULT (datetime('now')),
            aggiornato_il TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS movimenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            componente_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            quantita REAL NOT NULL,
            quantita_prima REAL, quantita_dopo REAL,
            riferimento TEXT, note TEXT,
            utente_id INTEGER, username TEXT,
            creato_il TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (componente_id) REFERENCES componenti(id)
        );

        CREATE TABLE IF NOT EXISTS log_operazioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utente_id INTEGER, username TEXT,
            modulo TEXT, azione TEXT,
            tabella TEXT, record_id INTEGER,
            dettagli TEXT,
            creato_il TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sessioni_inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL, stato TEXT DEFAULT 'aperta',
            ubicazione_filtro TEXT, categoria_filtro TEXT,
            creato_da_id INTEGER, creato_da_username TEXT,
            creato_il TEXT DEFAULT (datetime('now')),
            chiuso_il TEXT
        );

        CREATE TABLE IF NOT EXISTS sessioni_inventario_righe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sessione_id INTEGER NOT NULL,
            componente_id INTEGER NOT NULL,
            ordine INTEGER DEFAULT 0,
            qty_attesa REAL, qty_trovata REAL,
            stato TEXT DEFAULT 'sospeso',
            note TEXT, foto_extra TEXT,
            aggiornato_il TEXT,
            aggiornato_da_username TEXT,
            FOREIGN KEY (sessione_id) REFERENCES sessioni_inventario(id)
        );

        CREATE VIEW IF NOT EXISTS v_giacenza AS
            SELECT c.*,
                   COALESCE((SELECT SUM(CASE WHEN tipo='carico' THEN quantita
                                              WHEN tipo='scarico' THEN -quantita
                                              ELSE 0 END)
                             FROM movimenti WHERE componente_id=c.id), 0) AS esistenza
            FROM componenti c WHERE c.eliminato=0;

        CREATE INDEX IF NOT EXISTS idx_comp_cmp ON componenti(cmp);
        CREATE INDEX IF NOT EXISTS idx_comp_articolo ON componenti(articolo);
        CREATE INDEX IF NOT EXISTS idx_mov_comp ON movimenti(componente_id);
        CREATE INDEX IF NOT EXISTS idx_mov_data ON movimenti(creato_il);
    """)

    pwd_hash = hashlib.sha256(admin_pwd.encode()).hexdigest()
    c.execute(
        "INSERT INTO utenti(username, password_hash, ruolo, nome_completo, attivo) "
        "VALUES (?, ?, 'admin', 'Amministratore', 1)",
        (admin_user, pwd_hash)
    )
    conn.commit()
    conn.close()
    print(f"✓ Magazzino azzerato: {path}")
    print(f"✓ Utente admin creato: {admin_user} (password fornita)")


def reset_demolizioni_db():
    """Cancella e ricrea il database demolizioni."""
    path = DB_DIR / "demolizioni.db"
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(str(path))
    c = conn.cursor()
    c.executescript("""
        PRAGMA journal_mode=WAL;

        CREATE TABLE IF NOT EXISTS anagrafiche (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT, cognome TEXT, nome TEXT, ragione_sociale TEXT,
            cf TEXT, piva TEXT,
            luogo_nascita TEXT, prov_nascita TEXT, data_nascita TEXT,
            indirizzo TEXT, comune TEXT, prov TEXT, cap TEXT,
            tipo_doc TEXT, num_doc TEXT, rilasciato_da TEXT,
            telefono TEXT, cellulare TEXT, fax TEXT, email TEXT,
            note TEXT,
            creato_il TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS veicoli (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            targa TEXT, telaio TEXT, classe TEXT,
            marca TEXT, modello TEXT, anno_immatricolazione TEXT,
            num_motore TEXT, colore TEXT, note TEXT,
            creato_il TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS demolizioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_presa_in_carico TEXT, ora_presa_in_carico TEXT,
            reg_demolitori TEXT, pag_reg TEXT,
            veicolo_id INTEGER, proprietario_id INTEGER, detentore_id INTEGER,
            ufficio_provinciale TEXT,
            targhe_consegnate INTEGER DEFAULT 0,
            carta_circolazione INTEGER DEFAULT 0,
            concessionaria TEXT,
            peso_effettivo_kg REAL, peso_netto_kg REAL,
            modalita_radiazione TEXT, num_albatros TEXT,
            note TEXT, primo_trattamento INTEGER DEFAULT 0,
            creato_il TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (veicolo_id) REFERENCES veicoli(id),
            FOREIGN KEY (proprietario_id) REFERENCES anagrafiche(id),
            FOREIGN KEY (detentore_id)    REFERENCES anagrafiche(id)
        );

        CREATE TABLE IF NOT EXISTS voci_tendine (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            valore TEXT NOT NULL,
            ordine INTEGER DEFAULT 0,
            creato_il TEXT DEFAULT (datetime('now')),
            UNIQUE(categoria, valore)
        );

        INSERT OR IGNORE INTO voci_tendine(categoria, valore, ordine) VALUES
            ('modalita', 'Cancellazione al PRA',           1),
            ('modalita', 'Solo presa in carico',           2),
            ('modalita', 'Radiazione targa e ciclomotore', 3),
            ('modalita', 'Solo radiazione ciclomotore',    4),
            ('classe', 'Autovettura',       1),
            ('classe', 'Motoveicolo',       2),
            ('classe', 'Autocarro',         3),
            ('classe', 'Rimorchio',         4),
            ('classe', 'Macchina agricola', 5),
            ('classe', 'Altro',             6);

        CREATE TABLE IF NOT EXISTS schede_demolizione (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chiave TEXT UNIQUE,
            righe_json TEXT,
            payload_json TEXT,
            creato_il TEXT DEFAULT (datetime('now')),
            aggiornato_il TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()
    print(f"✓ Demolizioni azzerato: {path}")


def pulisci_uploads():
    """Rimuove tutte le foto caricate."""
    if UPLOADS.exists():
        n = 0
        for f in UPLOADS.iterdir():
            if f.is_file():
                f.unlink()
                n += 1
        print(f"✓ Foto cancellate: {n}")


def main():
    parser = argparse.ArgumentParser(description="Reset PerilCar database")
    parser.add_argument("--force",      action="store_true", help="Salta conferma")
    parser.add_argument("--admin-user", default="admin",     help="Username admin (default: admin)")
    parser.add_argument("--admin-pwd",  default="admin123",  help="Password admin (default: admin123)")
    parser.add_argument("--no-backup",  action="store_true", help="Salta backup pre-reset")
    args = parser.parse_args()

    if not conferma_se_serve(args.force):
        print("\nOperazione annullata.")
        return 1

    print()
    if not args.no_backup:
        backup_prima_del_reset()
    reset_magazzino_db(args.admin_user, args.admin_pwd)
    reset_demolizioni_db()
    pulisci_uploads()

    print("\n" + "=" * 60)
    print("✅ RESET COMPLETATO")
    print("=" * 60)
    print(f"Username admin: {args.admin_user}")
    print(f"Password admin: {args.admin_pwd}")
    print("\n⚠️  Cambia la password admin al primo accesso!")
    print("Avvia il programma con: start.bat\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
