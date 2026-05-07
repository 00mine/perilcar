"""
PerilCar ERP - Data Layer
Gestione database SQLite con supporto NAS, transazioni e soft-delete.
"""

import sqlite3
import os
import shutil
import threading
import logging
from datetime import datetime
from pathlib import Path

# ─── Versione schema ─────────────────────────────────────────────────────────
DB_SCHEMA_VERSION = 4
APP_VERSION = "1.0.0"

logger = logging.getLogger("perilcar.database")


class DatabaseManager:
    """
    Gestore centralizzato del database SQLite.
    Thread-safe tramite lock. Supporta percorso NAS configurabile.
    Nessuna cancellazione fisica: soft-delete su tutti i record.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = None):
        if self._initialized:
            return
        self._initialized = True
        self._write_lock = threading.Lock()

        # Percorso DB (NAS o locale)
        if db_path:
            self.db_path = db_path
        else:
            from core.config import ConfigManager
            cfg = ConfigManager()
            self.db_path = cfg.get("db_path", str(Path(__file__).parent.parent / "db" / "perilcar.db"))

        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        logger.info(f"Database inizializzato: {self.db_path}")

    # ─── Connessione ─────────────────────────────────────────────────────────

    def get_connection(self) -> sqlite3.Connection:
        """Ritorna sempre la stessa connessione persistente (thread-safe via lock)."""
        if not hasattr(self, '_conn') or self._conn is None:
            self._conn = sqlite3.connect(
                self.db_path, timeout=60,
                check_same_thread=False,
                isolation_level=None  # autocommit off gestito manualmente
            )
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.execute("PRAGMA busy_timeout=30000")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        return self._conn

    # ─── Schema ──────────────────────────────────────────────────────────────

    def _init_schema(self):
        with self._write_lock:
            conn = self.get_connection()
            try:
                with conn:
                    self._create_tables(conn)
                    self._migrate_schema(conn)
            finally:
                conn.close()

    def _create_tables(self, conn: sqlite3.Connection):
        conn.executescript("""
        -- ── META ──────────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS schema_version (
            id              INTEGER PRIMARY KEY,
            version         INTEGER NOT NULL,
            aggiornato_il   TEXT    NOT NULL
        );

        -- ── UTENTI ────────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS utenti (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT    NOT NULL UNIQUE,
            password_hash   TEXT    NOT NULL,
            ruolo           TEXT    NOT NULL DEFAULT 'operatore',
            nome_completo   TEXT,
            attivo          INTEGER NOT NULL DEFAULT 1,
            creato_il       TEXT    NOT NULL DEFAULT (datetime('now')),
            modificato_il   TEXT    NOT NULL DEFAULT (datetime('now')),
            eliminato       INTEGER NOT NULL DEFAULT 0
        );

        -- ── COMPONENTI (anagrafica pezzi) ─────────────────────────────────
        CREATE TABLE IF NOT EXISTS componenti (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            codice          TEXT    NOT NULL UNIQUE,
            nome            TEXT    NOT NULL,
            descrizione     TEXT,
            categoria       TEXT,
            marca           TEXT,
            modello         TEXT,
            cod_modello     TEXT,
            colore          TEXT,
            cilindrata      TEXT,
            carburante      TEXT,
            versione        TEXT,
            anno_da         INTEGER,
            anno_a          INTEGER,
            intervallo      TEXT,
            unita_misura    TEXT    NOT NULL DEFAULT 'pz',
            prezzo_acquisto REAL    DEFAULT 0,
            prezzo_vendita  REAL    DEFAULT 0,
            scorta_minima   INTEGER DEFAULT 0,
            note            TEXT,
            immagine_path   TEXT,
            files_path      TEXT,
            pubblicato      INTEGER NOT NULL DEFAULT 0,
            tipologia       TEXT,
            sottocategoria  TEXT,
            cod_udm         TEXT,
            cod_iva         TEXT,
            listino1        REAL    DEFAULT 0,
            listino2        REAL    DEFAULT 0,
            listino3        REAL    DEFAULT 0,
            cod_barre       TEXT,
            internet        TEXT,
            extra1          TEXT,
            extra2          TEXT,
            extra3          TEXT,
            extra4          TEXT,
            cod_fornitore   TEXT,
            fornitore       TEXT,
            cod_prod_forn   TEXT,
            prezzo_forn     REAL    DEFAULT 0,
            note_fornitura  TEXT,
            ord_multipli    INTEGER DEFAULT 0,
            gg_ordine       INTEGER DEFAULT 0,
            ubicazione      TEXT,
            stato_magazzino TEXT,
            creato_da       INTEGER,
            creato_il       TEXT    NOT NULL DEFAULT (datetime('now')),
            modificato_il   TEXT    NOT NULL DEFAULT (datetime('now')),
            eliminato       INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (creato_da) REFERENCES utenti(id)
        );

        -- ── MAGAZZINO (giacenza calcolata via view) ───────────────────────
        CREATE TABLE IF NOT EXISTS magazzino (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            componente_id   INTEGER NOT NULL UNIQUE,
            ubicazione      TEXT,
            scorta_minima   INTEGER DEFAULT 0,
            note_posizione  TEXT,
            aggiornato_il   TEXT    NOT NULL DEFAULT (datetime('now')),
            eliminato       INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (componente_id) REFERENCES componenti(id)
        );

        -- ── MOVIMENTI MAGAZZINO (tabella fondamentale, immutabile) ────────
        CREATE TABLE IF NOT EXISTS movimenti_magazzino (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            componente_id   INTEGER NOT NULL,
            tipo            TEXT    NOT NULL CHECK(tipo IN ('carico','scarico','rettifica','inventario')),
            quantita        INTEGER NOT NULL,
            quantita_prima  INTEGER NOT NULL DEFAULT 0,
            quantita_dopo   INTEGER NOT NULL DEFAULT 0,
            riferimento     TEXT,
            note            TEXT,
            utente_id       INTEGER,
            creato_il       TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (componente_id) REFERENCES componenti(id),
            FOREIGN KEY (utente_id)     REFERENCES utenti(id)
        );

        -- ── VEICOLI (per futuro modulo demolizioni) ───────────────────────
        CREATE TABLE IF NOT EXISTS veicoli (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            targa           TEXT    UNIQUE,
            telaio          TEXT    UNIQUE,
            anno            INTEGER,
            stato           TEXT    NOT NULL DEFAULT 'in_attesa',
            data_arrivo     TEXT,
            data_demolizione TEXT,
            note            TEXT,
            creato_da       INTEGER,
            creato_il       TEXT    NOT NULL DEFAULT (datetime('now')),
            eliminato       INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (creato_da) REFERENCES utenti(id)
        );

        -- ── RIFIUTI (per futuro modulo demolizioni) ───────────────────────
        CREATE TABLE IF NOT EXISTS rifiuti (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            veicolo_id      INTEGER,
            codice_cer      TEXT,
            descrizione     TEXT,
            quantita_kg     REAL,
            smaltitore      TEXT,
            data_smaltimento TEXT,
            documento       TEXT,
            note            TEXT,
            creato_il       TEXT    NOT NULL DEFAULT (datetime('now')),
            eliminato       INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (veicolo_id) REFERENCES veicoli(id)
        );

        -- ── OPERAI (per futuro modulo personale) ─────────────────────────
        CREATE TABLE IF NOT EXISTS operai (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nome            TEXT    NOT NULL,
            cognome         TEXT    NOT NULL,
            codice_fiscale  TEXT    UNIQUE,
            ruolo           TEXT,
            telefono        TEXT,
            email           TEXT,
            data_assunzione TEXT,
            attivo          INTEGER NOT NULL DEFAULT 1,
            note            TEXT,
            creato_il       TEXT    NOT NULL DEFAULT (datetime('now')),
            eliminato       INTEGER NOT NULL DEFAULT 0
        );

        -- ── LOG OPERAZIONI (audit trail immutabile) ────────────────────────
        CREATE TABLE IF NOT EXISTS log_operazioni (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            utente_id       INTEGER,
            username        TEXT,
            modulo          TEXT    NOT NULL,
            azione          TEXT    NOT NULL,
            tabella         TEXT,
            record_id       INTEGER,
            dati_precedenti TEXT,
            dati_nuovi      TEXT,
            ip_address      TEXT,
            timestamp       TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- ── LICENZA (struttura predisposta) ───────────────────────────────
        CREATE TABLE IF NOT EXISTS licenza (
            id              INTEGER PRIMARY KEY,
            device_id       TEXT    NOT NULL,
            chiave          TEXT,
            stato           TEXT    NOT NULL DEFAULT 'trial',
            scadenza        TEXT,
            azienda         TEXT,
            registrato_il   TEXT    NOT NULL DEFAULT (datetime('now')),
            ultimo_check    TEXT
        );

        -- ── VIEW: giacenza attuale per componente ─────────────────────────
        CREATE VIEW IF NOT EXISTS v_giacenza AS
        SELECT
            c.id              AS componente_id,
            c.codice          AS cmp,
            c.nome            AS articolo,
            c.descrizione,
            c.tipologia,
            c.categoria,
            c.sottocategoria,
            c.cod_udm,
            c.cod_iva,
            c.listino1,
            c.listino2,
            c.listino3,
            c.note            AS nota,
            c.cod_barre,
            c.internet,
            c.marca,
            c.extra1,
            c.extra2,
            c.extra3,
            c.extra4,
            c.cod_fornitore,
            c.fornitore,
            c.cod_prod_forn,
            c.prezzo_forn,
            c.note_fornitura,
            c.ord_multipli,
            c.gg_ordine,
            COALESCE(c.scorta_minima, 0) AS scorta,
            c.ubicazione,
            c.modello,
            c.colore,
            c.cilindrata,
            c.carburante,
            c.versione,
            c.anno_da,
            c.anno_a,
            c.intervallo,
            c.cod_modello,
            c.stato_magazzino,
            c.immagine_path   AS immagini,
            c.files_path,
            c.pubblicato,
            c.eliminato,
            COALESCE(SUM(CASE
                WHEN m.tipo IN ('carico','inventario') THEN  m.quantita
                WHEN m.tipo = 'scarico'               THEN -m.quantita
                WHEN m.tipo = 'rettifica'             THEN  m.quantita
                ELSE 0
            END), 0) AS esistenza
        FROM componenti c
        LEFT JOIN movimenti_magazzino m ON m.componente_id = c.id
        WHERE c.eliminato = 0
        GROUP BY c.id;


        -- Tabelle Demolizioni
        CREATE TABLE IF NOT EXISTS anagrafiche (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nominativo  TEXT    NOT NULL,
            cf_piva     TEXT,
            tipo        TEXT    DEFAULT 'privato',
            telefono    TEXT,
            email       TEXT,
            indirizzo   TEXT,
            creato_il   TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS veicoli (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            targa                 TEXT,
            telaio                TEXT,
            classe                TEXT,
            marca                 TEXT,
            modello               TEXT,
            anno_immatricolazione TEXT,
            num_motore            TEXT,
            colore                TEXT,
            note                  TEXT,
            creato_da             INTEGER,
            creato_il             TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS demolizioni (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            data_presa_in_carico  TEXT,
            ora_presa_in_carico   TEXT,
            reg_demolitori        TEXT,
            pag_reg               TEXT,
            veicolo_id            INTEGER REFERENCES veicoli(id),
            proprietario_id       INTEGER REFERENCES anagrafiche(id),
            detentore_id          INTEGER REFERENCES anagrafiche(id),
            ufficio_provinciale   TEXT,
            targhe_consegnate     INTEGER DEFAULT 0,
            carta_circolazione    INTEGER DEFAULT 0,
            concessionaria        TEXT,
            peso_effettivo_kg     REAL,
            peso_netto_kg         REAL,
            modalita_radiazione   TEXT,
            num_albatros          TEXT,
            certificato_id        TEXT,
            note                  TEXT,
            creato_da             INTEGER,
            creato_il             TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS ricambi_sottratti (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            demolizione_id  INTEGER NOT NULL REFERENCES demolizioni(id),
            componente_id   INTEGER REFERENCES componenti(id),
            peso_kg         REAL,
            note            TEXT,
            creato_il       TEXT DEFAULT (datetime('now'))
        );
        """)

    def _migrate_schema(self, conn: sqlite3.Connection):
        # SEMPRE: aggiungi colonne mancanti (sicuro anche se già esistono)
        try:
            _vei = [r[1] for r in conn.execute("PRAGMA table_info(veicoli)").fetchall()]
            for _col, _typ in [("classe","TEXT"),("marca","TEXT"),("modello","TEXT"),
                               ("anno_immatricolazione","TEXT"),("num_motore","TEXT"),
                               ("colore","TEXT"),("note","TEXT")]:
                if _col not in _vei:
                    conn.execute(f"ALTER TABLE veicoli ADD COLUMN {_col} {_typ}")
                    logger.info(f"Aggiunta colonna veicoli.{_col}")
        except Exception as _e:
            logger.warning(f"Migrazione veicoli: {_e}")
        try:
            _dem = [r[1] for r in conn.execute("PRAGMA table_info(demolizioni)").fetchall()]
            for _col, _typ in [("ora_presa_in_carico","TEXT"),("num_albatros","TEXT"),
                               ("certificato_id","TEXT")]:
                if _col not in _dem:
                    conn.execute(f"ALTER TABLE demolizioni ADD COLUMN {_col} {_typ}")
        except Exception as _e:
            logger.warning(f"Migrazione demolizioni: {_e}")
        try:
            _ana = [r[1] for r in conn.execute("PRAGMA table_info(anagrafiche)").fetchall()]
            for _col, _typ in [("cognome","TEXT"),("nome","TEXT"),("sesso","TEXT"),
                               ("data_nascita","TEXT"),("luogo_nascita","TEXT"),
                               ("comune","TEXT"),("provincia","TEXT"),("via","TEXT"),
                               ("civico","TEXT"),("cap","TEXT"),("tipo_doc","TEXT"),
                               ("num_doc","TEXT"),("data_doc","TEXT"),("rilasciato_da","TEXT"),
                               ("cellulare","TEXT"),("fax","TEXT")]:
                if _col not in _ana:
                    conn.execute(f"ALTER TABLE anagrafiche ADD COLUMN {_col} {_typ}")
        except Exception as _e:
            logger.warning(f"Migrazione anagrafiche: {_e}")

        row = conn.execute("SELECT version FROM schema_version WHERE id=1").fetchone()
        current = row["version"] if row else 0
        if current < DB_SCHEMA_VERSION:
            conn.execute("""
                INSERT OR REPLACE INTO schema_version(id, version, aggiornato_il)
                VALUES (1, ?, datetime('now'))
            """, (DB_SCHEMA_VERSION,))
            # v3: ricrea view con tutte le colonne nuove
            if current < 3:
                conn.execute("DROP VIEW IF EXISTS v_giacenza")
                self._create_tables(conn)
            # Crea utente admin di default se non esiste
            existing = conn.execute("SELECT id FROM utenti WHERE username='admin'").fetchone()
            if not existing:
                import hashlib
                pwd = hashlib.sha256("admin123".encode()).hexdigest()
                conn.execute("""
                    INSERT INTO utenti(username, password_hash, ruolo, nome_completo)
                    VALUES ('admin', ?, 'admin', 'Amministratore')
                """, (pwd,))
            logger.info(f"Schema aggiornato a versione {DB_SCHEMA_VERSION}")

    # ─── Utility ─────────────────────────────────────────────────────────────

    def execute(self, sql: str, params=()) -> sqlite3.Cursor:
        with self._write_lock:
            conn = self.get_connection()
            try:
                cur = conn.execute(sql, params)
                conn.commit()
                return cur
            finally:
                conn.close()

    def fetchall(self, sql: str, params=()) -> list:
        with self._write_lock:
            cur = self.get_connection().execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

    def fetchone(self, sql: str, params=()) -> dict | None:
        with self._write_lock:
            cur = self.get_connection().execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None

    def log(self, utente_id, username, modulo, azione, tabella=None,
            record_id=None, dati_prec=None, dati_nuovi=None):
        self.execute("""
            INSERT INTO log_operazioni
                (utente_id, username, modulo, azione, tabella, record_id,
                 dati_precedenti, dati_nuovi)
            VALUES (?,?,?,?,?,?,?,?)
        """, (utente_id, username, modulo, azione, tabella,
              record_id, str(dati_prec) if dati_prec else None,
              str(dati_nuovi) if dati_nuovi else None))

    # ─── Backup ──────────────────────────────────────────────────────────────

    def backup(self, backup_dir: str = None) -> str:
        if not backup_dir:
            backup_dir = str(Path(self.db_path).parent.parent / "backup")
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(backup_dir, f"perilcar_backup_{ts}.db")
        src_conn = self.get_connection()
        dst_conn = sqlite3.connect(dest)
        try:
            src_conn.backup(dst_conn)
        finally:
            src_conn.close()
            dst_conn.close()
        logger.info(f"Backup completato: {dest}")
        return dest
