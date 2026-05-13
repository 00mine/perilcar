# PerilCar ERP — Setup Produzione

Documentazione per portare PerilCar dall'ambiente di sviluppo a quello aziendale.

## Stato attuale

✅ **Fase 1 — Reset Database** — `reset_db.py`
✅ **Fase 2a — App Desktop** — `app_desktop.py` + `PerilCar.spec` + `build_app.bat`
✅ **Fase 3 — Pannello Stato Sistema in Home** — IP, utenti collegati, ultimo backup, versione

## Da fare prossimamente

⏸️ **Fase 2b** — Installer Windows (`.msi`/`.exe`) — quando NAS configurato
⏸️ **Fase 4** — Sistema aggiornamenti remoti firmati
⏸️ **Fase 5** — Repo produzione `perilcar-prod` separato (GitHub privato + 2FA)
⏸️ **Fase 6** — Connessione NAS (quando saprai marca/modello)

## Come usare cosa abbiamo già

### Reset database (per ripartire da zero)

```bash
python reset_db.py
```

Cancella tutti i dati di test (con backup automatico), crea l'utente admin:
- username: `admin`
- password: `admin123`

Da cambiare al primo login dalla pagina Gestione Utenti.

Opzioni:
- `--force` — niente conferma interattiva
- `--admin-user NOME` — username admin custom
- `--admin-pwd PWD` — password admin custom
- `--no-backup` — salta il backup

### Build app desktop

Sul PC Windows:

```cmd
build_app.bat
```

Crea `dist/PerilCar/PerilCar.exe` — eseguibile autonomo da distribuire.
Doppio click → si apre la finestra desktop. Nessun terminale.

**Nota:** la prima compilazione installa PyInstaller + PyWebView. Successive build sono più veloci.

### Pannello Stato Sistema

Visibile in Home. Mostra:
- 🟢 IP del server (es. `192.168.1.34`)
- 👥 Numero e lista utenti collegati ora
- 💾 Data/ora ultimo backup
- 📦 Versione attuale (3.6.0)

Refresh automatico ogni 15 secondi.

## Architettura finale (target)

```
┌──────────────────────────────────────┐
│ NAS aziendale                        │
│ \\NAS\perilcar\                       │
│   ├── db\                            │
│   │   ├── perilcar.db                │
│   │   └── demolizioni.db             │
│   ├── uploads\  (foto)               │
│   └── backup\  (auto giornaliero)    │
└──────────────────────────────────────┘
              ▲
              │ HTTP :5000 (LAN)
              │
   ┌──────────┴───────────┬────────────┐
   │                      │            │
┌──┴───┐              ┌──┴───┐    ┌──┴───┐
│ PC 1 │              │ PC 2 │    │ PC N │
│ .exe │              │ .exe │    │ .exe │
└──────┘              └──────┘    └──────┘
```

**Per ora** uno dei PC fa da server (esegue l'.exe e tiene il DB), gli altri si collegano via browser allo stesso IP. Quando avremo info sul NAS, sposteremo DB + uploads lì.

## Sicurezza

- Password hashate (SHA-256)
- Soft delete su utenti (no perdita storico)
- Log operazioni con utente + timestamp
- Session cookie HTTP-only
- Backup automatici prima di operazioni critiche
- Repo produzione verrà reso privato (vedi fase 5)
