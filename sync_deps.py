"""
sync_deps.py — Sincronizza le dipendenze da pyproject.toml a install_check.vbs
sync_deps.py — Sincronizza le dipendenze da pyproject.toml a requirements.txt
Per disabilitare l'aggiornamento del requirements basta passare --req ""

Uso:
    python sync_deps.py
    python sync_deps.py --toml path/to/pyproject.toml --vbs path/to/install_check.vbs

Aggiorna automaticamente:
  - APP_VERSION  (da [project] version)
  - Dim DEPS(N, 3) + righe DEPS(i,...)
  - For j = 0 To N  (loop installazione)
  - For i = 0 To N  (loop verifica)
"""

import re
import sys
import argparse
from pathlib import Path

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("Errore: installa 'tomli' oppure usa Python >= 3.11")
        print("  pip install tomli")
        sys.exit(1)


def parse_dep(dep_str):
    """
    Analizza una stringa tipo 'wxPython>=4.2.4,<5.0.0'
    Restituisce (nome_pip, ver_min, ver_max) o None se non parsabile.
    """
    m = re.match(r'^([A-Za-z0-9_\-]+)>=([^,]+),<(.+)$', dep_str.strip())
    if not m:
        return None
    return m.group(1), m.group(2).strip(), m.group(3).strip()


def build_deps_block(deps):
    """
    Costruisce le righe VBS per la dichiarazione e il popolamento di DEPS.
    """
    n = len(deps) - 1  # indice massimo (0-based)
    lines = []
    lines.append(f"Dim DEPS({n}, 3)")
    for i, (pip_name, ver_min, ver_max) in enumerate(deps):
        lines.append(
            f'DEPS({i},0) = "{pip_name:<14}" : DEPS({i},1) = "{pip_name:<14}" '
            f': DEPS({i},2) = "{ver_min:<7}" : DEPS({i},3) = "{ver_max}"'
        )
    return "\n".join(lines)


def sync_requirements(req_path, deps_raw):
    """
    Riscrive requirements.txt con le stesse dipendenze del pyproject.toml.
    """
    content = "\n".join(deps_raw) + "\n"
    Path(req_path).write_text(content, encoding="utf-8")
    print(f"  '{req_path}' aggiornato.")


def sync(toml_path, vbs_path, req_path=None):
    # Legge pyproject.toml
    with open(toml_path, "rb") as f:
        toml = tomllib.load(f)

    version = toml["project"]["version"]
    raw_deps = toml["project"]["dependencies"]

    deps = []
    for raw in raw_deps:
        parsed = parse_dep(raw)
        if parsed is None:
            print(f"  ATTENZIONE: dipendenza non parsabile, ignorata: {raw!r}")
            continue
        deps.append(parsed)

    if not deps:
        print("Nessuna dipendenza trovata nel toml.")
        sys.exit(1)

    n = len(deps) - 1
    print(f"  Versione app : {version}")
    print(f"  Dipendenze   : {len(deps)} ({', '.join(d[0] for d in deps)})")

    # Legge il vbs
    vbs_text = Path(vbs_path).read_text(encoding="utf-8")

    # 1. APP_VERSION
    vbs_text = re.sub(
        r'(Const APP_VERSION\s*=\s*")[^"]*(")',
        rf'\g<1>{version}\g<2>',
        vbs_text
    )

    # 2. Blocco DEPS: da "Dim DEPS(" fino all'ultima riga DEPS(N,...)
    new_block = build_deps_block(deps)
    vbs_text = re.sub(
        r'Dim DEPS\(\d+,\s*3\).*?(?=\r?\n\')',
        new_block,
        vbs_text,
        flags=re.DOTALL
    )

    # 3. Loop installazione: For j = 0 To N
    vbs_text = re.sub(
        r'(For j = 0 To )\d+',
        rf'\g<1>{n}',
        vbs_text
    )

    # 4. Loop verifica: For i = 0 To N
    vbs_text = re.sub(
        r'(For i = 0 To )\d+',
        rf'\g<1>{n}',
        vbs_text
    )

    Path(vbs_path).write_text(vbs_text, encoding="utf-8")
    print(f"  '{vbs_path}' aggiornato.")

    # 5. requirements.txt (opzionale)
    if req_path is not None and req_path.exists():
        sync_requirements(req_path, raw_deps)
    elif req_path is not None:
        print(f"  ATTENZIONE: '{req_path}' non trovato, saltato.")


def main():
    parser = argparse.ArgumentParser(description="Sincronizza deps da pyproject.toml a install_check.vbs")
    parser.add_argument("--toml", default="pyproject.toml",        help="Percorso pyproject.toml")
    parser.add_argument("--vbs",  default="src/install_check.vbs", help="Percorso install_check.vbs")
    parser.add_argument("--req",  default="requirements.txt",      help="Percorso requirements.txt (default: stessa cartella del toml)")
    args = parser.parse_args()

    toml_path = Path(args.toml)
    vbs_path  = Path(args.vbs)
    req_path  = Path(args.req) if args.req else None

    if not toml_path.exists():
        print(f"Errore: '{toml_path}' non trovato.")
        sys.exit(1)
    if not vbs_path.exists():
        print(f"Errore: '{vbs_path}' non trovato.")
        sys.exit(1)

    print(f"Sincronizzazione: {toml_path} → {vbs_path}, {req_path}")
    sync(toml_path, vbs_path, req_path)
    print("Fatto.")


if __name__ == "__main__":
    main()
