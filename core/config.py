"""
PerilCar ERP - Config Manager
Lettura/scrittura configurazione JSON persistente.
"""

import json
import os
from pathlib import Path


class ConfigManager:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config" / "settings.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _defaults(self) -> dict:
        base = Path(__file__).parent.parent
        return {
            "db_path": str(base / "db" / "perilcar.db"),
            "backup_dir": str(base / "backup"),
            "log_dir": str(base / "logs"),
            "backup_auto": True,
            "backup_interval_ore": 24,
            "app_version": "1.0.0",
            "azienda": "PerilCar",
            "lingua": "it",
            "tema": "dark",
        }

    def _load(self) -> dict:
        defaults = self._defaults()
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                defaults.update(saved)
            except Exception:
                pass
        return defaults

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()

    def save(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def all(self) -> dict:
        return dict(self._data)
