"""
PerilCar ERP - Business Logic: Modulo Magazzino
Tutta la logica applicativa è separata dall'interfaccia.
Le quantità NON vengono mai aggiornate direttamente:
si usa sempre la tabella movimenti_magazzino.
"""

from typing import Optional
from core.database import DatabaseManager
from core.auth import AuthManager


class MagazzinoService:
    """
    Servizio per la gestione del magazzino ricambi.
    Separazione completa da UI e Data Layer.
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.auth = AuthManager()

    # ─── COMPONENTI ──────────────────────────────────────────────────────────

    def get_tutti_componenti(self, filtri: dict = None) -> list[dict]:
        """
        Restituisce tutti i componenti con giacenza calcolata dalla view.
        Supporta filtri: testo, esistenza_min, esistenza_max, solo_scorta.
        """
        sql = "SELECT * FROM v_giacenza WHERE 1=1"
        params = []

        if filtri:
            if filtri.get("testo"):
                t = f"%{filtri['testo']}%"
                sql += """ AND (cmp LIKE ? OR articolo LIKE ? OR descrizione LIKE ?
                               OR marca LIKE ? OR modello LIKE ? OR colore LIKE ?)"""
                params.extend([t, t, t, t, t, t])
            if filtri.get("esistenza_min") is not None:
                sql += " AND esistenza >= ?"
                params.append(filtri["esistenza_min"])
            if filtri.get("esistenza_max") is not None:
                sql += " AND esistenza <= ?"
                params.append(filtri["esistenza_max"])
            if filtri.get("solo_scorta"):
                sql += " AND esistenza <= scorta"
            if filtri.get("pubblicato") is not None:
                sql += " AND pubblicato = ?"
                params.append(1 if filtri["pubblicato"] else 0)

        sql += " ORDER BY articolo"
        return self.db.fetchall(sql, params)

    def get_componente_by_id(self, componente_id: int) -> Optional[dict]:
        return self.db.fetchone(
            "SELECT * FROM v_giacenza WHERE componente_id=?", (componente_id,)
        )

    def cerca_componente(self, testo: str) -> list[dict]:
        return self.get_tutti_componenti({"testo": testo})

    def crea_componente(self, dati: dict) -> tuple[bool, str, int]:
        """Crea nuovo componente e record magazzino. Ritorna (ok, messaggio, id)."""
        # Validazione
        if not dati.get("codice"):
            return False, "Codice obbligatorio", 0
        if not dati.get("nome"):
            return False, "Nome articolo obbligatorio", 0

        # Controlla duplicato codice
        esistente = self.db.fetchone(
            "SELECT id FROM componenti WHERE codice=? AND eliminato=0",
            (dati["codice"],)
        )
        if esistente:
            return False, f"Codice '{dati['codice']}' già esistente", 0

        conn = self.db.get_connection()
        try:
            with conn:
                cur = conn.execute("""
                    INSERT INTO componenti
                        (codice, nome, descrizione, marca, modello, cod_modello,
                         colore, cilindrata, carburante, versione,
                         anno_da, anno_a, intervallo,
                         scorta_minima, note, immagine_path, pubblicato,
                         creato_da)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    dati.get("codice"), dati.get("nome"), dati.get("descrizione"),
                    dati.get("marca"), dati.get("modello"), dati.get("cod_modello"),
                    dati.get("colore"), dati.get("cilindrata"), dati.get("carburante"),
                    dati.get("versione"), dati.get("anno_da"), dati.get("anno_a"),
                    dati.get("intervallo"), dati.get("scorta_minima", 0),
                    dati.get("note"), dati.get("immagine_path"), 0,
                    self.auth.get_user_id()
                ))
                comp_id = cur.lastrowid
                # Record magazzino
                conn.execute("""
                    INSERT INTO magazzino(componente_id, scorta_minima)
                    VALUES (?, ?)
                """, (comp_id, dati.get("scorta_minima", 0)))

                conn.execute("""
                    INSERT INTO log_operazioni
                        (utente_id, username, modulo, azione, tabella, record_id, dati_nuovi)
                    VALUES (?,?,?,?,?,?,?)
                """, (self.auth.get_user_id(), self.auth.get_username(),
                      "MAGAZZINO", "CREA_COMPONENTE", "componenti", comp_id, str(dati)))
            return True, "Componente creato", comp_id
        except Exception as e:
            return False, f"Errore: {e}", 0
        finally:
            conn.close()

    def modifica_componente(self, componente_id: int, dati: dict) -> tuple[bool, str]:
        prec = self.db.fetchone("SELECT * FROM componenti WHERE id=?", (componente_id,))
        if not prec:
            return False, "Componente non trovato"

        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute("""
                    UPDATE componenti SET
                        nome=?, descrizione=?, marca=?, modello=?, cod_modello=?,
                        colore=?, cilindrata=?, carburante=?, versione=?,
                        anno_da=?, anno_a=?, intervallo=?,
                        scorta_minima=?, note=?, immagine_path=?,
                        modificato_il=datetime('now')
                    WHERE id=? AND eliminato=0
                """, (
                    dati.get("nome", prec["nome"]),
                    dati.get("descrizione", prec["descrizione"]),
                    dati.get("marca", prec["marca"]),
                    dati.get("modello", prec["modello"]),
                    dati.get("cod_modello", prec["cod_modello"]),
                    dati.get("colore", prec["colore"]),
                    dati.get("cilindrata", prec["cilindrata"]),
                    dati.get("carburante", prec["carburante"]),
                    dati.get("versione", prec["versione"]),
                    dati.get("anno_da", prec["anno_da"]),
                    dati.get("anno_a", prec["anno_a"]),
                    dati.get("intervallo", prec["intervallo"]),
                    dati.get("scorta_minima", prec["scorta_minima"]),
                    dati.get("note", prec["note"]),
                    dati.get("immagine_path", prec["immagine_path"]),
                    componente_id
                ))
                self.db.log(
                    self.auth.get_user_id(), self.auth.get_username(),
                    "MAGAZZINO", "MODIFICA_COMPONENTE", "componenti",
                    componente_id, prec, dati
                )
            return True, "Componente aggiornato"
        except Exception as e:
            return False, f"Errore: {e}"
        finally:
            conn.close()

    def elimina_componente(self, componente_id: int) -> tuple[bool, str]:
        """Soft delete: imposta eliminato=1, non cancella fisicamente."""
        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute("""
                    UPDATE componenti SET eliminato=1, modificato_il=datetime('now')
                    WHERE id=? AND eliminato=0
                """, (componente_id,))
                self.db.log(
                    self.auth.get_user_id(), self.auth.get_username(),
                    "MAGAZZINO", "ELIMINA_COMPONENTE", "componenti", componente_id
                )
            return True, "Componente eliminato"
        except Exception as e:
            return False, f"Errore: {e}"
        finally:
            conn.close()

    # ─── MOVIMENTI (CARICO / SCARICO) ─────────────────────────────────────────

    def carico(self, componente_id: int, quantita: int,
               riferimento: str = None, note: str = None) -> tuple[bool, str]:
        return self._movimento(componente_id, "carico", quantita, riferimento, note)

    def scarico(self, componente_id: int, quantita: int,
                riferimento: str = None, note: str = None) -> tuple[bool, str]:
        # Controlla disponibilità
        comp = self.get_componente_by_id(componente_id)
        if not comp:
            return False, "Componente non trovato"
        if comp["esistenza"] < quantita:
            return False, f"Giacenza insufficiente (disponibile: {comp['esistenza']})"
        return self._movimento(componente_id, "scarico", quantita, riferimento, note)

    def _movimento(self, componente_id: int, tipo: str, quantita: int,
                   riferimento: str, note: str) -> tuple[bool, str]:
        if quantita <= 0:
            return False, "Quantità deve essere > 0"

        comp = self.get_componente_by_id(componente_id)
        if not comp:
            return False, "Componente non trovato"

        giacenza_prima = comp["esistenza"]
        if tipo == "carico":
            giacenza_dopo = giacenza_prima + quantita
        else:
            giacenza_dopo = giacenza_prima - quantita

        import threading
        with self.db._write_lock:
            conn = self.db.get_connection()
            try:
                conn.execute("""
                    INSERT INTO movimenti_magazzino
                        (componente_id, tipo, quantita, quantita_prima,
                         quantita_dopo, riferimento, note, utente_id)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (componente_id, tipo, quantita, giacenza_prima,
                      giacenza_dopo, riferimento, note,
                      self.auth.get_user_id()))
                conn.execute("""
                    UPDATE magazzino SET aggiornato_il=datetime('now')
                    WHERE componente_id=?
                """, (componente_id,))
                conn.execute("""
                    INSERT INTO log_operazioni
                        (utente_id, username, modulo, azione, tabella,
                         record_id, dati_precedenti, dati_nuovi)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (self.auth.get_user_id(), self.auth.get_username(),
                      "MAGAZZINO", tipo.upper(), "movimenti_magazzino",
                      componente_id, str({"giacenza": giacenza_prima}),
                      str({"tipo": tipo, "quantita": quantita, "giacenza": giacenza_dopo})))
                conn.commit()
                return True, f"{tipo.capitalize()} di {quantita} pz completato"
            except Exception as e:
                conn.rollback()
                return False, f"Errore: {e}"
            finally:
                conn.close()

    # ─── STORICO MOVIMENTI ────────────────────────────────────────────────────

    def get_storico_movimenti(self, componente_id: int = None,
                               limit: int = 200) -> list[dict]:
        sql = """
            SELECT m.*, c.codice AS cmp, c.nome AS articolo, u.username
            FROM movimenti_magazzino m
            LEFT JOIN componenti c ON c.id = m.componente_id
            LEFT JOIN utenti     u ON u.id = m.utente_id
        """
        params = []
        if componente_id:
            sql += " WHERE m.componente_id=?"
            params.append(componente_id)
        sql += " ORDER BY m.creato_il DESC LIMIT ?"
        params.append(limit)
        return self.db.fetchall(sql, params)

    # ─── PUBBLICAZIONE (shop futuro) ──────────────────────────────────────────

    def pubblica_componente(self, componente_id: int,
                             pubblica: bool) -> tuple[bool, str]:
        val = 1 if pubblica else 0
        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute(
                    "UPDATE componenti SET pubblicato=? WHERE id=? AND eliminato=0",
                    (val, componente_id)
                )
                self.db.log(
                    self.auth.get_user_id(), self.auth.get_username(),
                    "MAGAZZINO", "PUBBLICA" if pubblica else "NASCONDI",
                    "componenti", componente_id
                )
            return True, "Stato pubblicazione aggiornato"
        except Exception as e:
            return False, f"Errore: {e}"
        finally:
            conn.close()

    # ─── STATISTICHE ─────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        totale = self.db.fetchone("SELECT COUNT(*) AS n FROM v_giacenza")
        sotto_scorta = self.db.fetchone(
            "SELECT COUNT(*) AS n FROM v_giacenza WHERE esistenza <= scorta AND scorta > 0"
        )
        ultimo_movimento = self.db.fetchone(
            "SELECT creato_il FROM movimenti_magazzino ORDER BY id DESC LIMIT 1"
        )
        return {
            "totale_componenti": totale["n"] if totale else 0,
            "sotto_scorta": sotto_scorta["n"] if sotto_scorta else 0,
            "ultimo_movimento": ultimo_movimento["creato_il"] if ultimo_movimento else "—",
        }
