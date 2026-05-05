# PerilCar ERP — Gestionale Aziendale
### Ing. Carmine Perillo · v1.0.0

---

## INDICE
1. Requisiti
2. Installazione
3. Avvio
4. Configurazione NAS
5. Struttura progetto
6. Schema database
7. Aggiornamenti futuri
8. Note tecniche

---

## 1. REQUISITI

| Componente    | Versione minima |
|---------------|-----------------|
| Python        | 3.11+           |
| customtkinter | 5.2+            |
| Pillow        | 10+             |
| Sistema       | Windows 10/11, macOS 12+, Linux |

---

## 2. INSTALLAZIONE

```bash
# 1. Clona o copia la cartella perilcar/ dove vuoi (incluso NAS)
# 2. Installa dipendenze Python
pip install customtkinter pillow

# 3. (Opzionale) Configura percorso DB su NAS — vedi sezione 4
```

---

## 3. AVVIO

```bash
cd perilcar/
python main.py
```

**Credenziali default:**
- Username: `admin`
- Password:  `admin123`

⚠️ Cambia la password admin dopo il primo accesso.

---

## 4. CONFIGURAZIONE DATABASE SU NAS

Modifica il file `config/settings.json`:

```json
{
  "db_path": "//NAS_IP/cartella_condivisa/perilcar.db",
  "backup_dir": "//NAS_IP/cartella_condivisa/backup",
  "backup_auto": true,
  "backup_interval_ore": 24
}
```

Su **Windows** usa path tipo: `\\\\192.168.1.100\\PerilCar\\perilcar.db`
Su **Linux/macOS** monta il NAS e usa il path del mount point.

Il database SQLite supporta accesso multi-utente tramite modalità WAL
(Write-Ahead Logging), con lock automatici per evitare conflitti.

---

## 5. STRUTTURA PROGETTO

```
perilcar/
├── main.py                        ← ENTRY POINT (avvia qui)
├── config/
│   └── settings.json              ← configurazione (db path, tema, ecc.)
├── core/
│   ├── database.py                ← Data Layer: SQLite, schema, backup
│   ├── config.py                  ← ConfigManager
│   └── auth.py                    ← AuthManager (login, sessione, ruoli)
├── modules/
│   ├── magazzino/
│   │   ├── service.py             ← Business Logic magazzino
│   │   ├── ui_magazzino.py        ← UI modulo magazzino (layout Canva)
│   │   ├── ui_form.py             ← Dialog inserimento/modifica componente
│   │   └── ui_storico.py          ← Dialog storico movimenti
│   ├── demolizioni/
│   │   └── service.py             ← STUB (struttura predisposta)
│   ├── operai/
│   │   └── service.py             ← STUB (struttura predisposta)
│   └── shop/
│       └── service.py             ← STUB (struttura predisposta)
├── ui/
│   ├── login.py                   ← Schermata login
│   └── dashboard.py               ← Dashboard principale (4 moduli)
├── db/
│   └── perilcar.db                ← Database SQLite (auto-creato)
├── backup/                        ← Backup automatici e manuali
├── logs/
│   └── perilcar.log               ← Log operazioni
└── assets/                        ← Immagini, icone (futuro)
```

---

## 6. SCHEMA DATABASE

### Tabelle principali

| Tabella                | Scopo                                        |
|------------------------|----------------------------------------------|
| `utenti`               | Accesso multi-utente con ruoli               |
| `componenti`           | Anagrafica pezzi/ricambi                     |
| `magazzino`            | Ubicazione e scorta minima per componente    |
| `movimenti_magazzino`  | ★ IMMUTABILE — ogni carico/scarico tracciato |
| `veicoli`              | Per futuro modulo demolizioni                |
| `rifiuti`              | Codici CER, per futuro modulo demolizioni    |
| `operai`               | Per futuro modulo personale                  |
| `log_operazioni`       | Audit trail: chi ha fatto cosa e quando      |
| `licenza`              | Struttura predisposta per gestione licenze   |
| `schema_version`       | Versione schema per migrazioni               |

### View fondamentale

```sql
-- v_giacenza: calcola giacenza attuale in tempo reale dai movimenti
SELECT componente_id, cmp, articolo, SUM(quantita carico - scarico) AS esistenza
FROM componenti JOIN movimenti_magazzino ...
```

### Regole CRITICHE database
- ❌ Nessuna `DELETE` fisica — solo `eliminato=1`
- ✅ Tutte le scritture in transazione
- ✅ Tutte le modifiche loggate in `log_operazioni`
- ✅ La giacenza è sempre calcolata da `movimenti_magazzino` (mai aggiornata direttamente)
- ✅ WAL mode per accesso multi-utente su NAS

---

## 7. AGGIORNAMENTI FUTURI

### Come aggiornare il programma

```bash
# 1. Fai un backup del database prima
#    (o usa il bottone "Backup DB" nell'app)

# 2. Sostituisci SOLO i file .py con la nuova versione
#    NON toccare la cartella db/

# 3. Il database viene migrato automaticamente all'avvio
```

### Moduli da implementare (già predisposti)

| Modulo       | File stub pronto     | Tabelle DB pronte          |
|--------------|----------------------|----------------------------|
| Demolizioni  | `modules/demolizioni/service.py` | `veicoli`, `rifiuti` |
| Personale    | `modules/operai/service.py`      | `operai`             |
| Shop online  | `modules/shop/service.py`        | (da aggiungere)      |
| Licenze      | —                               | `licenza`            |

---

## 8. NOTE TECNICHE

### Multi-utente su NAS
- SQLite in modalità WAL gestisce letture concorrenti
- Le scritture usano lock threading interno + timeout 5s
- Per >10 utenti simultanei contemporanei considerare migrazione a PostgreSQL

### Sicurezza
- Password in SHA-256 hash (non in chiaro)
- Ogni operazione loggata con utente + timestamp
- Nessun dato eliminato fisicamente dal database
- Backup automatico schedulabile

### Stack tecnologico
- **GUI**: CustomTkinter (moderno, dark theme, cross-platform)
- **DB**: SQLite 3 con WAL + Foreign Keys
- **Architettura**: UI → Business Logic → Data Layer (separati)
- **Python**: 3.11+ (union types, match, ecc.)

---

*PerilCar ERP — Ing. Carmine Perillo — v1.0.0*
