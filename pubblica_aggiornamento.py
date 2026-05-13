#!/usr/bin/env python3
"""
PerilCar ERP — Pubblica Aggiornamento
Uso (sul PC di sviluppo):
  python pubblica_aggiornamento.py 3.7.0 "Fix bug X" "Nuova funzione Y" "Miglioramento Z"

Questo script:
  1. Aggiorna VERSIONE_APP in dev_server.py
  2. Aggiorna version.json con changelog
  3. Fa git commit + push su GitHub
  I PC aziendali vedranno il popup di aggiornamento al prossimo avvio.
"""
import sys, json, re, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent


def aggiorna_versione_server(nuova_ver: str):
    path = ROOT / "dev_server.py"
    content = path.read_text(encoding="utf-8")
    content = re.sub(
        r'VERSIONE_APP\s*=\s*"[\d\.]+"',
        f'VERSIONE_APP = "{nuova_ver}"',
        content
    )
    path.write_text(content, encoding="utf-8")
    print(f"✓ dev_server.py → VERSIONE_APP = {nuova_ver}")


def aggiorna_version_json(nuova_ver: str, changelog: list[str], obbligatorio: bool):
    path = ROOT / "version.json"
    data = {
        "versione":    nuova_ver,
        "data":        datetime.now().strftime("%Y-%m-%d"),
        "obbligatorio": obbligatorio,
        "changelog":   changelog,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ version.json → {nuova_ver}")


def git_push(nuova_ver: str, changelog: list[str]):
    msg = f"v{nuova_ver} — " + "; ".join(changelog[:3])
    subprocess.run(["git", "add", "-A"],               check=True, cwd=ROOT)
    subprocess.run(["git", "commit", "-m", msg],        check=True, cwd=ROOT)
    subprocess.run(["git", "push", "origin", "main"],   check=True, cwd=ROOT)
    print(f"✓ Push su GitHub completato")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        print("Esempio:")
        print('  python pubblica_aggiornamento.py 3.7.0 "Fix bug login" "Nuovo export PDF"')
        return 1

    nuova_ver  = sys.argv[1].strip()
    changelog  = [a.strip() for a in sys.argv[2:]]
    obbligatorio = "--obbligatorio" in changelog
    if obbligatorio:
        changelog.remove("--obbligatorio")

    # Valida versione
    if not re.match(r"^\d+\.\d+\.\d+$", nuova_ver):
        print(f"Versione non valida: {nuova_ver} (usa formato X.Y.Z)")
        return 1

    print(f"\n{'='*50}")
    print(f"  Pubblicazione aggiornamento v{nuova_ver}")
    print(f"{'='*50}")
    print(f"  Changelog ({len(changelog)} voci):")
    for c in changelog:
        print(f"    • {c}")
    if obbligatorio:
        print(f"  ⚠️  AGGIORNAMENTO OBBLIGATORIO")
    print()

    conferma = input("Procedere? (s/N): ").strip().lower()
    if conferma != "s":
        print("Annullato.")
        return 0

    aggiorna_versione_server(nuova_ver)
    aggiorna_version_json(nuova_ver, changelog, obbligatorio)
    git_push(nuova_ver, changelog)

    print(f"\n✅ Aggiornamento v{nuova_ver} pubblicato!")
    print("   I PC aziendali vedranno il popup al prossimo avvio.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
