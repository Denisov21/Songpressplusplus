#!/usr/bin/env python3
"""
find_unused.py — Trova i file .py non referenziati in un progetto Python.

Uso:
    python find_unused.py <cartella_progetto>

Esempio:
    python find_unused.py "E:\\Users\\Utente\\Downloads\\SongpressV56 OK - BUGFIX\\SongpressPlusPlus\\src\\songpressPlusPlus"

Output:
    - Elenco dei file potenzialmente eliminabili (non importati né referenziati)
    - Elenco dei file usati (con il primo file che li referenzia)
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict


def collect_py_files(root: Path) -> list[Path]:
    """Raccoglie tutti i file .py nella cartella (ricorsivo)."""
    return sorted(root.rglob("*.py"))


def module_name(path: Path, root: Path) -> str:
    """Restituisce il nome del modulo relativo alla root (es. 'SongpressFrame')."""
    rel = path.relative_to(root)
    parts = list(rel.parts)
    # Rimuove l'estensione dall'ultimo elemento
    parts[-1] = parts[-1].removesuffix(".py")
    return parts[-1]  # solo il nome base (come appare negli import)


def find_references(files: list[Path]) -> dict[str, list[str]]:
    """
    Per ogni file, cerca i nomi di modulo che importa o referenzia.
    Restituisce: {nome_modulo_cercato: [file_che_lo_usa, ...]}
    """
    # Pattern per catturare import diretti e from ... import
    import_patterns = [
        re.compile(r'^\s*import\s+([\w,\s]+)', re.MULTILINE),
        re.compile(r'^\s*from\s+\.?([\w.]+)\s+import', re.MULTILINE),
        re.compile(r'^\s*from\s+\.\.([\w.]+)\s+import', re.MULTILINE),
    ]
    # Pattern per referenze come stringhe (es. in XRC o commenti # Name: File.py)
    name_pattern = re.compile(r'(\w+)(?:\.py)?')

    refs: dict[str, list[str]] = defaultdict(list)

    for fpath in files:
        try:
            text = fpath.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue

        fname = fpath.name

        for pattern in import_patterns:
            for m in pattern.finditer(text):
                raw = m.group(1).strip()
                # Gestisce "import a, b, c"
                for part in raw.split(','):
                    part = part.strip().split('.')[0]  # prende solo il nome base
                    if part:
                        refs[part].append(str(fpath))

        # Cerca anche riferimenti al nome file (es. "FontFaceDialog" nel testo)
        for m in name_pattern.finditer(text):
            token = m.group(1)
            if len(token) > 3:  # ignora token troppo corti
                refs[token].append(str(fpath))

    return refs


def analyze(root_str: str):
    root = Path(root_str)
    if not root.exists():
        print(f"❌ Cartella non trovata: {root}")
        sys.exit(1)

    print(f"\n📂 Analisi: {root}\n")
    files = collect_py_files(root)
    print(f"   File .py trovati: {len(files)}\n")

    # Costruisce mappa nome → path
    name_to_path: dict[str, Path] = {}
    for f in files:
        name = module_name(f, root)
        name_to_path[name] = f

    # Raccoglie tutte le referenze
    refs = find_references(files)

    unused = []
    used = []

    for name, fpath in name_to_path.items():
        if name == "__init__":
            continue  # __init__.py è sempre necessario

        # Cerca referenze a questo modulo in file DIVERSI da sé stesso
        referencing = [
            r for r in refs.get(name, [])
            if Path(r) != fpath
        ]
        # Rimuovi duplicati
        referencing = sorted(set(referencing))

        if not referencing:
            unused.append((name, fpath))
        else:
            used.append((name, fpath, referencing))

    # ── Output ──────────────────────────────────────────────────────────────

    print("=" * 70)
    print(f"  🗑️  FILE POTENZIALMENTE ELIMINABILI ({len(unused)})")
    print("=" * 70)
    if unused:
        for name, fpath in sorted(unused):
            print(f"  • {fpath.relative_to(root)}")
    else:
        print("  Nessuno — tutti i file sono referenziati.")

    print()
    print("=" * 70)
    print(f"  ✅  FILE IN USO ({len(used)})")
    print("=" * 70)
    for name, fpath, referencing in sorted(used):
        first_ref = Path(referencing[0])
        try:
            first_ref_rel = first_ref.relative_to(root)
        except ValueError:
            first_ref_rel = first_ref
        extra = f" (+{len(referencing)-1} altri)" if len(referencing) > 1 else ""
        print(f"  • {fpath.relative_to(root)}")
        print(f"      ← {first_ref_rel}{extra}")

    print()
    print("⚠️  ATTENZIONE: questo script usa l'analisi testuale degli import.")
    print("   Verifica manualmente i file nella lista 'eliminabili' prima di")
    print("   cancellarli — alcuni potrebbero essere caricati dinamicamente")
    print("   (es. tramite XRC, plugin, o __import__).\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUso: python find_unused.py <cartella_progetto>")
        sys.exit(0)
    analyze(sys.argv[1])
