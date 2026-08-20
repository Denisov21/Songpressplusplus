#!/usr/bin/env python3
###############################################################
# Name:        find_unused.py
# Purpose:     Trova i file .py non referenziati in un progetto
#              Python. Interfaccia grafica (tkinter) + modalità
#              da riga di comando.
# Author:      Denisov21
# License:     GNU GPL v2 (GPL-2.0-only)
###############################################################
"""
find_unused.py — Trova i file .py non referenziati in un progetto Python.

Uso (GUI):
    python find_unused.py

Uso (riga di comando):
    python find_unused.py <cartella_progetto>

Esempio:
    python find_unused.py "E:\\Users\\Utente\\Downloads\\SongpressV56 OK - BUGFIX\\SongpressPlusPlus\\src\\songpressPlusPlus"

Output:
    - Elenco dei file potenzialmente eliminabili (non importati né referenziati)
    - Elenco dei file usati (con il primo file che li referenzia)
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from collections import defaultdict
from typing import Any

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# Drag & drop opzionale: richiede il pacchetto "tkinterdnd2".
# Se non è installato, l'app funziona comunque (senza trascinamento).
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES  # type: ignore[import-not-found]
    _DND_OK = True
except Exception:
    TkinterDnD = None
    DND_FILES = None
    _DND_OK = False

# ── Metadati applicazione ───────────────────────────────────────────────────────
APP_NAME    = "Trova file .py inutilizzati"
APP_AUTHOR  = "Denisov21"
APP_LICENSE = "GNU General Public License, versione 2 (GPL-2.0-only)"


# ── Analisi (logica invariata) ──────────────────────────────────────────────────

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


def analyze_project(root_str: str):
    """
    Esegue l'analisi e restituisce (root, files, unused, used).
    Solleva ValueError se la cartella non esiste.
    """
    root = Path(root_str)
    if not root.exists():
        raise ValueError(f"Cartella non trovata: {root}")

    files = collect_py_files(root)

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

    return root, files, unused, used


def format_report(root: Path, files, unused, used) -> str:
    """Costruisce il report testuale (stesso formato della versione a riga di comando)."""
    lines: list[str] = []
    lines.append(f"📂 Analisi: {root}")
    lines.append(f"   File .py trovati: {len(files)}")
    lines.append("")

    lines.append("=" * 70)
    lines.append(f"  🗑️  FILE POTENZIALMENTE ELIMINABILI ({len(unused)})")
    lines.append("=" * 70)
    if unused:
        for _name, fpath in sorted(unused):
            lines.append(f"  • {fpath.relative_to(root)}")
    else:
        lines.append("  Nessuno — tutti i file sono referenziati.")

    lines.append("")
    lines.append("=" * 70)
    lines.append(f"  ✅  FILE IN USO ({len(used)})")
    lines.append("=" * 70)
    for _name, fpath, referencing in sorted(used):
        first_ref = Path(referencing[0])
        try:
            first_ref_rel = first_ref.relative_to(root)
        except ValueError:
            first_ref_rel = first_ref
        extra = f" (+{len(referencing)-1} altri)" if len(referencing) > 1 else ""
        lines.append(f"  • {fpath.relative_to(root)}")
        lines.append(f"      ← {first_ref_rel}{extra}")

    lines.append("")
    lines.append("⚠️  ATTENZIONE: questo script usa l'analisi testuale degli import.")
    lines.append("   Verifica manualmente i file nella lista 'eliminabili' prima di")
    lines.append("   cancellarli — alcuni potrebbero essere caricati dinamicamente")
    lines.append("   (es. tramite XRC, plugin, o __import__).")
    return "\n".join(lines)


# ── Modalità riga di comando (retrocompatibile) ─────────────────────────────────

def analyze_cli(root_str: str):
    try:
        root, files, unused, used = analyze_project(root_str)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    print()
    print(format_report(root, files, unused, used))
    print()


# ── Spostamento nel cestino (multipiattaforma) ──────────────────────────────────

def move_to_trash(path: str) -> tuple[bool, str | None]:
    """
    Sposta un file/cartella nel cestino. Restituisce (ok, errore).
    Prova nell'ordine: send2trash → gio trash (Linux) → trash-cli (Linux).
    Non elimina mai in modo definitivo.
    """
    # 1. send2trash (Windows / macOS / Linux) — metodo preferito
    try:
        from send2trash import send2trash  # type: ignore[import-untyped]
        send2trash(path)
        return True, None
    except ImportError:
        pass
    except Exception as e:
        return False, str(e)

    # 2. gio trash (presente su molti desktop Linux, incl. KDE/GNOME)
    if shutil.which("gio"):
        r = subprocess.run(["gio", "trash", "--", path],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return True, None
        return False, r.stderr.strip() or f"gio trash: codice {r.returncode}"

    # 3. trash-cli
    if shutil.which("trash"):
        r = subprocess.run(["trash", "--", path],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return True, None
        return False, r.stderr.strip() or f"trash: codice {r.returncode}"

    return False, ("nessun metodo per il cestino disponibile "
                   "(installa «send2trash» con: pip install send2trash)")


# ── Applicazione GUI ────────────────────────────────────────────────────────────

class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.grid(sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._build_menubar(master)

        self.folder_var = tk.StringVar()

        # Stato dell'ultima analisi
        self._last_root = None
        self._unused_files: list[Path] = []

        row = 0
        ttk.Label(self, text="Cartella del progetto da analizzare:"
                  ).grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1
        self.folder_entry = ttk.Entry(self, textvariable=self.folder_var)
        self.folder_entry.grid(row=row, column=0, sticky="ew", pady=(2, 8))
        ttk.Button(self, text="📂 Sfoglia…", command=self._browse
                   ).grid(row=row, column=1, sticky="e", padx=(6, 0), pady=(2, 8))
        row += 1

        btns = ttk.Frame(self)
        btns.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        btns.columnconfigure(2, weight=1)
        self.analyze_btn = ttk.Button(btns, text="🔍 Analizza", command=self._on_analyze)
        self.analyze_btn.grid(row=0, column=0, sticky="w")
        self.trash_btn = ttk.Button(btns, text="🗑 Cestina file inutilizzati…",
                                    command=self._on_trash, state="disabled")
        self.trash_btn.grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.hint_var = tk.StringVar(value=(
            "Suggerimento: puoi anche trascinare una cartella qui dentro."
            if _DND_OK else
            "Drag & drop non attivo (installa «tkinterdnd2» per abilitarlo)."))
        ttk.Label(btns, textvariable=self.hint_var, foreground="#666"
                  ).grid(row=0, column=2, sticky="e")
        row += 1

        ttk.Label(self, text="Risultato:").grid(row=row, column=0, sticky="w")
        row += 1
        self.out = scrolledtext.ScrolledText(self, height=24, wrap="none",
                                             font=("monospace", 10))
        self.out.grid(row=row, column=0, columnspan=2, sticky="nsew")
        self.rowconfigure(row, weight=1)
        self.out.configure(state="disabled")

        # Invio nel campo cartella = avvia analisi
        self.folder_entry.bind("<Return>", lambda e: self._on_analyze())

        # Abilita il drag & drop (se disponibile)
        if _DND_OK:
            self._enable_dnd()

    # ── barra dei menu ──
    def _build_menubar(self, master):
        menubar = tk.Menu(master)

        # Menu «File»
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Apri cartella…", accelerator="Ctrl+O",
                              command=self._browse)
        file_menu.add_command(label="Cestina file inutilizzati…",
                              command=self._on_trash)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", accelerator="Ctrl+Q",
                              command=self._on_exit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Menu «?»
        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Crediti", command=self._show_credits)
        menubar.add_cascade(label="?", menu=help_menu)

        master.config(menu=menubar)
        # Scorciatoie da tastiera
        master.bind_all("<Control-o>", lambda e: self._browse())
        master.bind_all("<Control-O>", lambda e: self._browse())
        master.bind_all("<Control-q>", lambda e: self._on_exit())
        master.bind_all("<Control-Q>", lambda e: self._on_exit())

    def _on_exit(self):
        self.master.destroy()

    def _show_credits(self):
        messagebox.showinfo(
            "Crediti",
            f"{APP_NAME}\n\n"
            "Trova i file .py non referenziati (né importati) in un\n"
            "progetto Python, tramite analisi testuale degli import.\n\n"
            f"Autore:   {APP_AUTHOR}\n"
            f"Licenza:  {APP_LICENSE}\n\n"
            "Questo programma è software libero: puoi ridistribuirlo\n"
            "e/o modificarlo secondo i termini della GNU General Public\n"
            "License, versione 2 — e solo la versione 2 (GPL-2.0-only),\n"
            "come pubblicata dalla Free Software Foundation.\n\n"
            "Il programma è distribuito nella speranza che sia utile,\n"
            "ma SENZA ALCUNA GARANZIA. Vedi la GNU GPL v2 per i dettagli.")

    # ── azioni ──
    def _browse(self):
        start = self.folder_var.get() or os.path.expanduser("~")
        p = filedialog.askdirectory(
            title="Scegli la cartella del progetto",
            initialdir=start if os.path.isdir(start) else os.path.expanduser("~"))
        if p:
            self.folder_var.set(p)

    # ── drag & drop ──
    def _enable_dnd(self):
        """Registra i widget come destinazione di trascinamento (richiede tkinterdnd2)."""
        for widget in (self.folder_entry, self.out, self):
            # I metodi drop_target_register/dnd_bind sono aggiunti da tkinterdnd2
            # solo quando la root è TkinterDnD.Tk(); mypy non li vede sui tipi base.
            w: Any = widget
            try:
                w.drop_target_register(DND_FILES)
                w.dnd_bind("<<Drop>>", self._on_drop)
            except Exception:
                pass

    def _parse_drop(self, data):
        """Estrae i percorsi da un evento di drop (gestisce le graffe dei path con spazi)."""
        try:
            return list(self.tk.splitlist(data))
        except Exception:
            return [p for p in data.strip("{}").split() if p]

    def _on_drop(self, event):
        paths = self._parse_drop(event.data)
        if not paths:
            return
        p = paths[0]
        # Se viene trascinato un file, uso la sua cartella
        if os.path.isfile(p):
            p = os.path.dirname(p)
        if not os.path.isdir(p):
            messagebox.showwarning(
                "Non una cartella",
                f"L'elemento trascinato non è una cartella:\n{p}")
            return
        self.folder_var.set(p)
        self._on_analyze()

    def _on_analyze(self):
        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showwarning(
                "Nessuna cartella",
                "Indica la cartella del progetto da analizzare.")
            return
        self.analyze_btn.configure(state="disabled")
        self.master["cursor"] = "watch"
        self.update_idletasks()
        try:
            root, files, unused, used = analyze_project(folder)
        except ValueError as e:
            messagebox.showerror("Errore", str(e))
            return
        except Exception as e:
            messagebox.showerror("Errore", f"Analisi non riuscita:\n{e}")
            return
        finally:
            self.analyze_btn.configure(state="normal")
            self.master["cursor"] = ""
        # Memorizza lo stato per l'eventuale spostamento nel cestino
        self._last_root = root
        self._unused_files = [fpath for _, fpath in unused]
        self.trash_btn.configure(
            state=("normal" if self._unused_files else "disabled"))
        self._write(format_report(root, files, unused, used))

    def _on_trash(self):
        if not self._unused_files:
            messagebox.showinfo(
                "Nessun file",
                "Esegui prima un'analisi: non ci sono file da cestinare.")
            return

        # Considera solo i file ancora esistenti
        targets = [p for p in self._unused_files if p.is_file()]
        if not targets:
            messagebox.showinfo(
                "Nessun file",
                "I file elencati non esistono più. Riesegui l'analisi.")
            return

        root = self._last_root
        def rel(p):
            try:
                return p.relative_to(root)
            except Exception:
                return p
        elenco = "\n".join(f"  • {rel(p)}" for p in targets)
        if not messagebox.askyesno(
                "Conferma spostamento nel cestino",
                f"Verranno spostati nel cestino {len(targets)} file:\n\n"
                f"{elenco}\n\n"
                "I file NON vengono eliminati definitivamente: potrai\n"
                "recuperarli dal cestino. Procedere?",
                icon="warning"):
            return

        ok_count = 0
        errors = []
        for p in targets:
            ok, err = move_to_trash(str(p))
            if ok:
                ok_count += 1
            else:
                errors.append(f"  • {rel(p)} — {err}")

        if errors:
            messagebox.showwarning(
                "Completato con errori",
                f"{ok_count} file spostati nel cestino.\n\n"
                "Non è stato possibile spostare:\n" + "\n".join(errors))
        else:
            messagebox.showinfo(
                "Completato",
                f"✓ {ok_count} file spostati nel cestino.")

        # Riesegui l'analisi per aggiornare l'elenco
        self._on_analyze()

    def _write(self, text: str):
        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        self.out.insert("end", text)
        self.out.see("1.0")
        self.out.configure(state="disabled")


def main():
    root = TkinterDnD.Tk() if _DND_OK else tk.Tk()
    root.title(APP_NAME)
    root.minsize(720, 520)
    try:
        ttk.Style().theme_use("clam")
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    # Con un argomento → modalità riga di comando (come prima); senza → GUI.
    if len(sys.argv) >= 2:
        analyze_cli(sys.argv[1])
    else:
        main()
