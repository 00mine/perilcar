"""
PerilCar ERP - Auth Manager
Gestione autenticazione, sessione e ruoli.
"""

import hashlib
import threading
from core.database import DatabaseManager


class AuthManager:
    """Gestisce login, sessione corrente e controllo permessi."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._current_user = None
        return cls._instance

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username: str, password: str) -> tuple[bool, str]:
        db = DatabaseManager()
        user = db.fetchone(
            "SELECT * FROM utenti WHERE username=? AND eliminato=0",
            (username,)
        )
        if not user:
            return False, "Utente non trovato"
        if not user["attivo"]:
            return False, "Account disabilitato"
        if user["password_hash"] != self._hash(password):
            return False, "Password errata"
        self._current_user = dict(user)
        db.log(user["id"], username, "AUTH", "LOGIN")
        return True, "OK"

    def logout(self):
        if self._current_user:
            db = DatabaseManager()
            db.log(self._current_user["id"], self._current_user["username"],
                   "AUTH", "LOGOUT")
        self._current_user = None

    @property
    def current_user(self) -> dict | None:
        return self._current_user

    @property
    def is_logged_in(self) -> bool:
        return self._current_user is not None

    def has_role(self, *roles) -> bool:
        if not self._current_user:
            return False
        return self._current_user.get("ruolo") in roles

    def is_admin(self) -> bool:
        return self.has_role("admin")

    def get_user_id(self) -> int | None:
        return self._current_user["id"] if self._current_user else None

    def get_username(self) -> str:
        return self._current_user["username"] if self._current_user else "?"
