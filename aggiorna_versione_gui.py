#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aggiorna il numero di versione di Songpress++ nei file del progetto.

Aggiorna in modo *sicuro* e simultaneo i file principali (sempre richiesti,
nella radice del progetto):
    - pyproject.toml     -> la riga  version = "X.Y.Z"  del progetto
    - README.md          -> gli esempi di versione (nome .deb, blocco codice)
    - README_italian.md  -> gli esempi di versione (nome .deb, blocco codice)

Se presenti, aggiorna anche i file aggiuntivi (opzionali), cercati pure nelle
sottocartelle come build/ o build_deb/ — vedi EXTRA_FILE_NAMES:
    - README_PORTABLE_BUILD_en.md -> esempi di versione (nome ZIP portabile, ...)
    - README_PORTABLE_BUILD_it.md -> esempi di versione (nome ZIP portabile, ...)
    - DEB_INSTALLATION.md         -> esempi di versione (nome .deb, blocco codice)
    - INSTALLAZIONE_DEB.md        -> esempi di versione (nome .deb, blocco codice)

Il programma NON fa una sostituzione cieca: analizza i file, riconosce ogni
occorrenza di versione e la classifica.  Sono escluse automaticamente:

    * le versioni delle DIPENDENZE in pyproject.toml (wxPython, requests, ...)
      -> viene toccata solo la riga  ^version = "..."  del progetto;
    * i riferimenti STORICI nei README/guide ("Fino alla 7.0.1" / "Up to 7.0.1"),
      che documentano un rilascio passato.

Ogni modifica è mostrata in anteprima con una checkbox: si conferma o si
esclude una per una prima di scrivere su disco.  Facoltativamente crea un
backup .bak di ogni file modificato.

Dipendenze: solo libreria standard (tkinter).  Nessun pacchetto esterno.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
#  LOGICA PURA (indipendente dalla GUI, così è testabile senza display)
# ─────────────────────────────────────────────────────────────────────────────

# Nomi dei file gestiti, nell'ordine in cui vanno mostrati.
FILE_NAMES = ("pyproject.toml", "README.md", "README_italian.md")

# File aggiuntivi (opzionali), cercati anche in una sottocartella (es. build/,
# build_deb/). Oltre ai README della build portabile, include le due guide
# all'installazione del pacchetto .deb, che vivono di norma in build_deb/ e
# contengono anch'esse la versione del programma (nome .deb, blocchi codice).
EXTRA_FILE_NAMES = ("README_PORTABLE_BUILD_en.md", "README_PORTABLE_BUILD_it.md",
                    "INSTALLAZIONE_DEB.md", "DEB_INSTALLATION.md")

# Cartelle da ignorare nella ricerca ricorsiva dei file aggiuntivi (generate,
# nascoste o pesanti). Le cartelle di output cx_Freeze iniziano con "exe.".
_IGNORED_DIRS = {".git", ".venv", ".venv-build", "__pycache__", "dist",
                 "node_modules"}

# Un numero di versione semantico completo: 8.0.0 (tre componenti).
# I tre componenti evitano di intercettare le versioni di Python (3.12, 3.4...).
_SEMVER_RE = re.compile(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)")

# La riga di versione del PROGETTO in pyproject.toml (ancorata a inizio riga:
# le dipendenze non iniziano mai con  version = ).
_PYPROJECT_VERSION_RE = re.compile(r'^(version\s*=\s*")([^"]+)(")', re.MULTILINE)

# Il nome del pacchetto Debian, che contiene la versione del PROGRAMMA:
#   songpressplusplus_8.0.0_all.deb
_DEB_RE = re.compile(r"songpressplusplus_(\d+\.\d+\.\d+)_all\.deb")

# Il nome dello ZIP portabile, che contiene la versione del PROGRAMMA:
#   Songpress++-3.0.1-portable.zip
_ZIP_RE = re.compile(r"Songpress\+\+-(\d+\.\d+\.\d+)-portable\.zip",
                     re.IGNORECASE)

# Riga di assegnazione  version = "X.Y.Z"  (nei blocchi di codice dei README).
_VERSION_ASSIGN_RE = re.compile(r'version\s*=\s*"(\d+\.\d+\.\d+)"')

# Parole che segnalano un riferimento STORICO a un rilascio passato.
_HISTORICAL_HINTS = ("up to", "fino alla", "fino a ", "earlier version",
                     "versioni precedenti", "prima della")

# Nomi di librerie/dipendenze: se compaiono sulla stessa riga, la versione
# quasi certamente NON è quella del programma (es. "wxPython 4.2.3").
_DEP_HINTS = ("wxpython", "requests", "python-pptx", "pptx", "pyshortcuts",
              "reportlab", "pypdf", "markdown", "mistune", "hatchling",
              "cx_freeze", "cxfreeze", "python 3", "python3")

# Etichette leggibili per ogni tipologia di occorrenza.
KIND_LABEL = {
    "project": "versione progetto",
    "deb": "nome pacchetto .deb",
    "zip": "nome ZIP portabile",
    "version_assign": 'riga version = "…"',
    "tag": "tag versione (vX.Y.Z)",
    "dependency": "versione dipendenza",
    "historical": "rif. storico",
    "other": "altro",
}
# Tipologie pre-selezionate (sono la versione del programma).
_SELECTED_KINDS = {"project", "deb", "zip", "version_assign", "tag"}


def parse_semver(text: str) -> tuple[int, int, int] | None:
    """Restituisce (major, minor, patch) se `text` è un semver X.Y.Z, else None."""
    m = re.fullmatch(r"\s*(\d+)\.(\d+)\.(\d+)\s*", text or "")
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def is_valid_version(text: str) -> bool:
    """True se `text` è una versione semantica valida (X.Y.Z)."""
    return parse_semver(text) is not None


def bump(version: str, part: str) -> str:
    """Incrementa una parte della versione ('major' | 'minor' | 'patch')."""
    parsed = parse_semver(version)
    if parsed is None:
        return version
    major, minor, patch = parsed
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    return version


@dataclass
class Candidate:
    """Una singola occorrenza di versione trovata in un file."""

    file_name: str
    line_index: int          # 0-based
    col_start: int           # offset all'interno della riga
    col_end: int
    old_value: str
    line_text: str           # riga completa (senza newline finale)
    kind: str                # "project" | "deb" | "version_assign" | ...
    selected: bool           # stato iniziale della checkbox

    @property
    def line_no(self) -> int:
        """Numero di riga 1-based, per visualizzazione."""
        return self.line_index + 1

    @property
    def historical(self) -> bool:
        """Comodità: True se è un riferimento storico."""
        return self.kind == "historical"

    @property
    def kind_label(self) -> str:
        """Etichetta leggibile della tipologia."""
        return KIND_LABEL.get(self.kind, self.kind)


def read_pyproject_version(text: str) -> str | None:
    """Estrae la versione del progetto da pyproject.toml (None se assente)."""
    m = _PYPROJECT_VERSION_RE.search(text)
    return m.group(2) if m else None


def scan_pyproject(text: str) -> list[Candidate]:
    """Trova SOLO la riga  version = "..."  del progetto (non le dipendenze)."""
    lines = text.splitlines()
    out: list[Candidate] = []
    for i, line in enumerate(lines):
        m = _PYPROJECT_VERSION_RE.match(line)
        if m:
            out.append(Candidate(
                file_name="pyproject.toml",
                line_index=i,
                col_start=m.start(2),
                col_end=m.end(2),
                old_value=m.group(2),
                line_text=line,
                kind="project",
                selected=True,
            ))
            break  # esiste una sola riga di versione del progetto
    return out


def _classify(line: str, start: int, end: int) -> str:
    """Determina la tipologia di un'occorrenza X.Y.Z in una riga di README."""
    low = line.lower()
    # 1) fa parte del nome del pacchetto .deb?  -> versione del programma
    for dm in _DEB_RE.finditer(line):
        if dm.start(1) == start and dm.end(1) == end:
            return "deb"
    # 2) fa parte del nome dello ZIP portabile?  -> versione del programma
    for zm in _ZIP_RE.finditer(line):
        if zm.start(1) == start and zm.end(1) == end:
            return "zip"
    # 3) è il valore di una riga  version = "..."  ?  -> versione del programma
    for vm in _VERSION_ASSIGN_RE.finditer(line):
        if vm.start(1) == start and vm.end(1) == end:
            return "version_assign"
    # 4) riferimento storico a un rilascio passato
    if any(h in low for h in _HISTORICAL_HINTS):
        return "historical"
    # 5) versione di una dipendenza citata nel testo (es. wxPython 4.2.3)
    if any(h in low for h in _DEP_HINTS):
        return "dependency"
    # 6) tag di versione  vX.Y.Z  (una 'v' subito prima, a inizio parola)
    #    -> versione del programma (es. "git tag v3.0.1")
    if start > 0 and line[start - 1] in "vV" and (
            start == 1 or not line[start - 2].isalnum()):
        return "tag"
    return "other"


def scan_readme(file_name: str, text: str) -> list[Candidate]:
    """Trova tutte le occorrenze X.Y.Z in un README, classificandole.

    Vengono pre-selezionate solo le occorrenze che rappresentano la versione
    del PROGRAMMA (nome .deb e righe version = "…").  Dipendenze, riferimenti
    storici e altro restano visibili ma deselezionati.
    """
    lines = text.splitlines()
    out: list[Candidate] = []
    for i, line in enumerate(lines):
        for m in _SEMVER_RE.finditer(line):
            kind = _classify(line, m.start(), m.end())
            out.append(Candidate(
                file_name=file_name,
                line_index=i,
                col_start=m.start(),
                col_end=m.end(),
                old_value=m.group(0),
                line_text=line,
                kind=kind,
                selected=kind in _SELECTED_KINDS,
            ))
    return out


def scan_file(file_name: str, text: str) -> list[Candidate]:
    """Instrada la scansione al gestore corretto in base al nome file."""
    if file_name == "pyproject.toml":
        return scan_pyproject(text)
    return scan_readme(file_name, text)


def apply_to_text(text: str, candidates: list[Candidate],
                  new_version: str) -> tuple[str, int]:
    """Applica le sostituzioni SELEZIONATE al testo. Ritorna (nuovo_testo, n)."""
    lines = text.splitlines(keepends=True)
    # Raggruppo i candidati selezionati per riga.
    by_line: dict[int, list[Candidate]] = {}
    for c in candidates:
        if c.selected and c.old_value != new_version:
            by_line.setdefault(c.line_index, []).append(c)

    changed = 0
    for idx, cands in by_line.items():
        raw = lines[idx]
        # Preservo l'eventuale terminatore di riga.
        newline = ""
        body = raw
        for term in ("\r\n", "\n", "\r"):
            if raw.endswith(term):
                newline = term
                body = raw[: -len(term)]
                break
        # Applico da destra a sinistra per non alterare gli offset.
        for c in sorted(cands, key=lambda x: x.col_start, reverse=True):
            body = body[: c.col_start] + new_version + body[c.col_end:]
            changed += 1
        lines[idx] = body + newline

    return "".join(lines), changed


# ─────────────────────────────────────────────────────────────────────────────
#  GUI (Tkinter)
# ─────────────────────────────────────────────────────────────────────────────

# ─── Metadati applicazione (crediti / licenza) ───────────────────────────────
# Modifica liberamente autore, anno e URL secondo le tue esigenze.
APP_AUTHOR = "Denisov21"
APP_URL = "https://github.com/Denisov21/Songpressplusplus"
APP_COPYRIGHT = "Copyright (C) 2024-2026  Denisov21"

# Lingue disponibili nell'interfaccia (codice -> nome mostrato nel selettore).
LANGUAGES = {"it": "Italiano", "en": "English"}
DEFAULT_LANG = "it"

# Limiti (in punti) per la dimensione del testo scelta dall'utente.
MIN_FONT_SIZE = 9
MAX_FONT_SIZE = 18

# Dimensione iniziale (in pixel) della finestra principale.
DEFAULT_WIN_W = 980
DEFAULT_WIN_H = 700

# Avviso di licenza GPL v2 (testo standard raccomandato dalla FSF). Il testo
# COMPLETO e legalmente autoritativo è quello originale in inglese.
GPL2_NOTICE_IT = """\
Questo programma è software libero: puoi ridistribuirlo e/o modificarlo
secondo i termini della GNU General Public License come pubblicata dalla
Free Software Foundation, versione 2 della Licenza, oppure (a tua scelta)
una qualsiasi versione successiva.

Questo programma è distribuito nella speranza che sia utile, ma SENZA ALCUNA
GARANZIA; senza neppure la garanzia implicita di COMMERCIABILITÀ o IDONEITÀ
PER UN PARTICOLARE SCOPO. Consulta la GNU General Public License per maggiori
dettagli.

Dovresti aver ricevuto una copia della GNU General Public License insieme a
questo programma; in caso contrario, scrivi alla Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Il testo completo e ufficiale (in inglese) della licenza è disponibile nel
file COPYING / LICENSE del progetto oppure su:

    https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
"""

GPL2_NOTICE_EN = """\
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

The full official text of the license is available in the project's
COPYING / LICENSE file or at:

    https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
"""

# ─── Traduzioni dell'interfaccia (it/en) ─────────────────────────────────────
# Ogni chiave è un identificatore semantico. I testi con {segnaposto} vengono
# riempiti con str.format(...).
TRANSLATIONS: dict[str, dict[str, str]] = {
    "it": {
        "app_title": "Songpress++ — Aggiorna versione",
        # menu
        "menu_file": "File",
        "menu_options": "Opzioni…",
        "menu_exit": "Esci",
        "menu_help": "?",
        "menu_about": "Informazioni / Crediti…",
        "menu_license": "Licenza (GPL v2)…",
        "menu_colors": "Descrizione dei colori…",
        # header / top / azioni
        "lbl_language": "Lingua:",
        "lbl_project_dir": "Cartella progetto:",
        "dir_none": "(nessuna)",
        "btn_browse": "Sfoglia…",
        "lbl_current": "Versione attuale:",
        "current_placeholder": "—",
        "lbl_new": "Nuova versione:",
        "valid_ok": "✓ formato valido",
        "valid_bad": "✗ usa il formato X.Y.Z",
        "btn_scan": "Analizza / Anteprima",
        "btn_select_all": "Seleziona tutto",
        "btn_deselect_all": "Deseleziona tutto",
        "chk_backup": "Crea backup .bak",
        "btn_apply": "Applica modifiche",
        "frame_occurrences": "Occorrenze trovate",
        "frame_log": "Log",
        "btn_close": "Chiudi",
        # opzioni / preferenze
        "options_title": "Opzioni",
        "opt_font_family": "Tipo di carattere:",
        "opt_font_size": "Dimensione:",
        "opt_cursor": "Cambia il cursore sui pulsanti disabilitati",
        "opt_preview": "Anteprima:",
        "opt_preview_text": "Ma la volpe, col suo balzo, raggiunse il quieto "
                           "Fido — Aa Bb 0123",
        "btn_save": "Salva",
        "btn_cancel": "Annulla",
        "prefs_saved": "Preferenze salvate in {path}.",
        "prefs_error": "Impossibile salvare le preferenze: {exc}",
        # tipologie (kind)
        "kind_project": "versione progetto",
        "kind_deb": "nome pacchetto .deb",
        "kind_zip": "nome ZIP portabile",
        "kind_version_assign": 'riga version = "…"',
        "kind_tag": "tag versione (vX.Y.Z)",
        "kind_dependency": "versione dipendenza",
        "kind_historical": "rif. storico",
        "kind_other": "altro",
        # righe
        "row_meta": "riga {line}: {old} → {new}",
        "not_found": "(non trovata)",
        # informazioni / crediti
        "about_title": "Informazioni",
        "about_body": (
            "{title}\n\n"
            "Aggiorna in modo sicuro il numero di versione nei file del\n"
            "progetto (pyproject.toml, README.md, README_italian.md e, se\n"
            "presenti, i README della build portabile e le guide di\n"
            "installazione .deb in build_deb/), con anteprima e conferma\n"
            "di ogni singola occorrenza.\n\n"
            "Autore: {author}\n{url}\n{copyright}\n\n"
            "Licenza: GNU General Public License v2\n"
            "Dipendenze: solo libreria standard (tkinter)."
        ),
        # licenza
        "license_title": "Licenza — GNU General Public License v2",
        # legenda colori
        "colors_title": "Descrizione dei colori",
        "colors_intro": "Colori usati nell'elenco delle occorrenze:",
        "colors_program": "versione del programma — pre-selezionata "
                          "(progetto, nome .deb, ZIP portabile, riga "
                          "version = \"…\", tag vX.Y.Z)",
        "colors_dependency": "versione di una dipendenza — esclusa "
                            "(es. wxPython 4.2.3)",
        "colors_historical": "riferimento storico a un rilascio passato — "
                            "escluso (es. «Fino alla 7.0.1»)",
        "colors_other": "altra occorrenza — non selezionata",
        "colors_log_intro": "Colori del riquadro Log:",
        "colors_log_info": "informazione",
        "colors_log_ok": "operazione riuscita",
        "colors_log_warn": "avviso",
        "colors_log_err": "errore",
        # messaggi / log
        "lang_changed": "Lingua impostata: {lang}",
        "filedialog_title": "Seleziona la cartella del progetto",
        "no_project": "Nessun progetto caricato.",
        "invalid_version_title": "Versione non valida",
        "invalid_version_msg": "Inserisci una nuova versione nel formato "
                              "X.Y.Z (es. 8.1.0).",
        "no_occurrences": "Nessuna occorrenza di versione trovata.",
        "found_summary": "Trovate {total} occorrenze — {selected} "
                        "pre-selezionate (versione del programma). "
                        "Controlla e conferma.",
        "excluded_hist": "{n} riferimenti storici esclusi "
                        "(es. «Fino alla 7.0.1»).",
        "excluded_dep": "{n} versioni di dipendenze escluse "
                       "(es. «wxPython 4.2.3»).",
        "required_format": "Formato richiesto: X.Y.Z",
        "nothing_title": "Niente da fare",
        "nothing_msg": "Nessuna occorrenza selezionata.",
        "confirm_title": "Conferma",
        "confirm_msg": "Applicare la versione {new} a {n} occorrenze "
                      "in {files} file?",
        "confirm_backup": "\n\nVerrà creato un backup .bak di ogni file.",
        "log_backup": "Backup: {name}",
        "log_write_error": "ERRORE scrivendo {name}: {exc}",
        "write_error_title": "Errore di scrittura",
        "log_file_updated": "{name}: {n} occorrenze aggiornate a {new}.",
        "log_completed": "Completato: {occ} occorrenze in {files} file. "
                        "Versione ora {new}.",
        "done_title": "Fatto",
        "done_msg": "Aggiornate {occ} occorrenze in {files} file.\n"
                   "Versione del progetto: {new}",
        "missing_files": "File mancanti in questa cartella: {names}",
        "missing_hint": "Seleziona la cartella che contiene pyproject.toml, "
                       "README.md e README_italian.md.",
        "project_loaded": "Progetto caricato: {folder}",
        "current_in_pyproject": "Versione attuale in pyproject.toml: {v}",
        "extra_found": "File aggiuntivi trovati: {names}",
    },
    "en": {
        "app_title": "Songpress++ — Update version",
        # menu
        "menu_file": "File",
        "menu_options": "Options…",
        "menu_exit": "Exit",
        "menu_help": "?",
        "menu_about": "About / Credits…",
        "menu_license": "License (GPL v2)…",
        "menu_colors": "Colour legend…",
        # header / top / actions
        "lbl_language": "Language:",
        "lbl_project_dir": "Project folder:",
        "dir_none": "(none)",
        "btn_browse": "Browse…",
        "lbl_current": "Current version:",
        "current_placeholder": "—",
        "lbl_new": "New version:",
        "valid_ok": "✓ valid format",
        "valid_bad": "✗ use the format X.Y.Z",
        "btn_scan": "Analyse / Preview",
        "btn_select_all": "Select all",
        "btn_deselect_all": "Deselect all",
        "chk_backup": "Create .bak backup",
        "btn_apply": "Apply changes",
        "frame_occurrences": "Occurrences found",
        "frame_log": "Log",
        "btn_close": "Close",
        # options / preferences
        "options_title": "Options",
        "opt_font_family": "Font family:",
        "opt_font_size": "Size:",
        "opt_cursor": "Change the cursor on disabled buttons",
        "opt_preview": "Preview:",
        "opt_preview_text": "The quick brown fox jumps over the lazy dog "
                           "— Aa Bb 0123",
        "btn_save": "Save",
        "btn_cancel": "Cancel",
        "prefs_saved": "Preferences saved to {path}.",
        "prefs_error": "Could not save preferences: {exc}",
        # kinds
        "kind_project": "project version",
        "kind_deb": ".deb package name",
        "kind_zip": "portable ZIP name",
        "kind_version_assign": 'version = "…" line',
        "kind_tag": "version tag (vX.Y.Z)",
        "kind_dependency": "dependency version",
        "kind_historical": "historical ref.",
        "kind_other": "other",
        # rows
        "row_meta": "line {line}: {old} → {new}",
        "not_found": "(not found)",
        # about / credits
        "about_title": "About",
        "about_body": (
            "{title}\n\n"
            "Safely updates the version number across the project files\n"
            "(pyproject.toml, README.md, README_italian.md and, if present,\n"
            "the portable-build READMEs and the .deb installation guides in\n"
            "build_deb/), with a preview and per-occurrence confirmation.\n\n"
            "Author: {author}\n{url}\n{copyright}\n\n"
            "License: GNU General Public License v2\n"
            "Dependencies: standard library only (tkinter)."
        ),
        # license
        "license_title": "License — GNU General Public License v2",
        # colour legend
        "colors_title": "Colour legend",
        "colors_intro": "Colours used in the occurrences list:",
        "colors_program": "program version — pre-selected "
                          "(project, .deb name, portable ZIP, version = \"…\" "
                          "line, vX.Y.Z tag)",
        "colors_dependency": "a dependency version — excluded "
                            "(e.g. wxPython 4.2.3)",
        "colors_historical": "historical reference to a past release — "
                            "excluded (e.g. \"Up to 7.0.1\")",
        "colors_other": "other occurrence — not selected",
        "colors_log_intro": "Colours in the Log panel:",
        "colors_log_info": "information",
        "colors_log_ok": "operation succeeded",
        "colors_log_warn": "warning",
        "colors_log_err": "error",
        # messages / log
        "lang_changed": "Language set to: {lang}",
        "filedialog_title": "Select the project folder",
        "no_project": "No project loaded.",
        "invalid_version_title": "Invalid version",
        "invalid_version_msg": "Enter a new version in the format "
                              "X.Y.Z (e.g. 8.1.0).",
        "no_occurrences": "No version occurrence found.",
        "found_summary": "Found {total} occurrences — {selected} "
                        "pre-selected (program version). Review and confirm.",
        "excluded_hist": "{n} historical references excluded "
                        "(e.g. \"Up to 7.0.1\").",
        "excluded_dep": "{n} dependency versions excluded "
                       "(e.g. \"wxPython 4.2.3\").",
        "required_format": "Required format: X.Y.Z",
        "nothing_title": "Nothing to do",
        "nothing_msg": "No occurrence selected.",
        "confirm_title": "Confirm",
        "confirm_msg": "Apply version {new} to {n} occurrences "
                      "in {files} files?",
        "confirm_backup": "\n\nA .bak backup of every file will be created.",
        "log_backup": "Backup: {name}",
        "log_write_error": "ERROR writing {name}: {exc}",
        "write_error_title": "Write error",
        "log_file_updated": "{name}: {n} occurrences updated to {new}.",
        "log_completed": "Done: {occ} occurrences in {files} files. "
                        "Version now {new}.",
        "done_title": "Done",
        "done_msg": "Updated {occ} occurrences in {files} files.\n"
                   "Project version: {new}",
        "missing_files": "Files missing in this folder: {names}",
        "missing_hint": "Select the folder containing pyproject.toml, "
                       "README.md and README_italian.md.",
        "project_loaded": "Project loaded: {folder}",
        "current_in_pyproject": "Current version in pyproject.toml: {v}",
        "extra_found": "Extra files found: {names}",
    },
}

# Testo dell'avviso di licenza per lingua.
_LICENSE_NOTICE = {"it": GPL2_NOTICE_IT, "en": GPL2_NOTICE_EN}


# ─── Preferenze (salvate in un file JSON a fianco a questo script) ────────────
def prefs_path() -> Path:
    """Percorso del file di preferenze, accanto a questo file .py."""
    try:
        base = Path(__file__).resolve()
    except NameError:  # __file__ non disponibile in contesti particolari
        base = (Path.cwd() / "aggiorna_versione_gui.py").resolve()
    return base.with_suffix(".prefs.json")


def load_prefs() -> dict[str, Any]:
    """Carica le preferenze (dict vuoto se il file manca o è illeggibile)."""
    try:
        data = json.loads(prefs_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_prefs(prefs: dict[str, Any]) -> Path:
    """Salva le preferenze nel file JSON e ne restituisce il percorso."""
    path = prefs_path()
    path.write_text(json.dumps(prefs, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    return path


def _launch_gui() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from tkinter import font as tkfont

    # ---- palette log (coerente con lo stile degli altri strumenti) ---------
    C_INFO = "#1565c0"
    C_OK = "#2e7d32"
    C_WARN = "#e65100"
    C_ERR = "#c62828"
    C_OTHER = "#777777"

    @dataclass
    class FileState:
        path: Path
        text: str
        candidates: list[Candidate] = field(default_factory=list)

    class App(tk.Tk):
        def __init__(self) -> None:
            super().__init__()
            self.lang = DEFAULT_LANG
            self.geometry(f"{DEFAULT_WIN_W}x{DEFAULT_WIN_H}")
            self.minsize(820, 560)

            self.project_dir: Path | None = None
            self.files: dict[str, FileState] = {}
            # Ordine dei file da mostrare/elaborare (core + eventuali extra).
            self.file_order: list[str] = list(FILE_NAMES)
            self.current_version: str | None = None
            self.row_vars: list[tuple[Candidate, tk.BooleanVar]] = []
            # Master-checkbox per file (abilita/disabilita le figlie) e
            # riferimenti alle checkbox figlie, raggruppate per nome file.
            self.file_enabled: dict[str, tk.BooleanVar] = {}
            self.file_children: dict[
                str, list[tuple[tk.BooleanVar, ttk.Checkbutton]]] = {}

            # --- font riconfigurabili + preferenze -------------------------
            # Font "base" (proporzionale) e derivati (grassetto, entry) più i
            # font monospazio per log e anteprima. Vengono riconfigurati da
            # _apply_fonts() secondo le preferenze dell'utente.
            self.font_default = tkfont.Font()
            self.font_bold = tkfont.Font()
            self.font_entry = tkfont.Font()
            self.font_mono = tkfont.Font(font="TkFixedFont")
            self.font_mono_small = tkfont.Font(font="TkFixedFont")

            default_family = tkfont.nametofont("TkDefaultFont").actual("family")
            default_size = tkfont.nametofont("TkDefaultFont").actual("size")
            if not isinstance(default_size, int) or default_size <= 0:
                default_size = 10
            prefs = load_prefs()
            # Lingua salvata (se valida), altrimenti quella predefinita.
            lang_pref = prefs.get("language")
            if lang_pref in LANGUAGES:
                self.lang = lang_pref
            self.pref_family = str(prefs.get("font_family") or default_family)
            try:
                self.pref_size = int(prefs.get("font_size") or default_size)
            except (TypeError, ValueError):
                self.pref_size = default_size
            self.pref_size = max(MIN_FONT_SIZE,
                                 min(self.pref_size, MAX_FONT_SIZE))
            # Preferenza: cambiare il cursore sui pulsanti disabilitati?
            self.pref_cursor_disabled = bool(
                prefs.get("cursor_on_disabled", True))
            self._apply_fonts()

            # Cursore da mostrare sui controlli disabilitati (non cliccabili).
            self._disabled_cursor = self._resolve_disabled_cursor()
            self._cursor_widgets: list[ttk.Widget] = []

            self._build_ui()
            # Prova a caricare la cartella corrente all'avvio.
            self._try_load(Path.cwd())
            # Se il font salvato è grande, allarga la finestra di conseguenza.
            self._fit_to_content()

        # ---------- traduzioni ---------------------------------------------
        def t(self, key: str, **kw: object) -> str:
            """Restituisce la stringa tradotta per la lingua corrente."""
            template = TRANSLATIONS.get(self.lang, {}).get(key)
            if template is None:
                template = TRANSLATIONS[DEFAULT_LANG].get(key, key)
            return template.format(**kw) if kw else template

        def _kind_label(self, kind: str) -> str:
            """Etichetta tradotta della tipologia di occorrenza."""
            return self.t(f"kind_{kind}")

        # ---------- cambio lingua ------------------------------------------
        def _on_language_change(self, *_evt: object) -> None:
            disp = self.lang_var.get()
            code = next((k for k, v in LANGUAGES.items() if v == disp),
                        self.lang)
            if code != self.lang:
                # Differisco la ricostruzione per non distruggere il
                # combobox durante la gestione del suo stesso evento.
                self.after(1, lambda: self._set_language(code))

        def _set_language(self, code: str) -> None:
            if code == self.lang:
                return
            self.lang = code
            # Memorizzo lo stato da ripristinare dopo la ricostruzione.
            keep_new = self.new_var.get()
            keep_backup = self.backup_var.get()
            had_preview = bool(self.row_vars)

            # Ricostruisco tutta l'interfaccia nella nuova lingua.
            for w in self.winfo_children():
                w.destroy()
            self.row_vars.clear()
            self.file_enabled.clear()
            self.file_children.clear()
            self._build_ui()

            # Ripristino i valori.
            self.backup_var.set(keep_backup)
            if self.project_dir is not None:
                self.dir_var.set(str(self.project_dir))
            if self.current_version:
                self.cur_var.set(self.current_version)
            if keep_new:
                self.new_var.set(keep_new)
            self._log(self.t("lang_changed", lang=LANGUAGES[self.lang]), "info")
            # Memorizzo la lingua scelta nelle preferenze (senza log extra).
            self._save_current_prefs(announce=False)
            if had_preview and self.files:
                self._scan()

        # ---------- barra dei menu / crediti / licenza ---------------------
        def _build_menu(self) -> None:
            menubar = tk.Menu(self)

            # --- menu File ---
            file_menu = tk.Menu(menubar, tearoff=False)
            file_menu.add_command(label=self.t("menu_options"),
                                  command=self._show_options)
            file_menu.add_separator()
            file_menu.add_command(label=self.t("menu_exit"),
                                  accelerator="Ctrl+Q", command=self._on_quit)
            menubar.add_cascade(label=self.t("menu_file"), menu=file_menu)

            # --- menu ? (aiuto / guida) ---
            help_menu = tk.Menu(menubar, tearoff=False)
            help_menu.add_command(label=self.t("menu_about"),
                                  command=self._show_about)
            help_menu.add_command(label=self.t("menu_colors"),
                                  command=self._show_colors)
            help_menu.add_command(label=self.t("menu_license"),
                                  command=self._show_license)
            menubar.add_cascade(label=self.t("menu_help"), menu=help_menu)

            self.configure(menu=menubar)
            self.bind_all("<Control-q>", lambda _e: self._on_quit())

        def _on_quit(self) -> None:
            self.destroy()

        def _show_about(self) -> None:
            messagebox.showinfo(
                self.t("about_title"),
                self.t("about_body", title=self.t("app_title"),
                       author=APP_AUTHOR, url=APP_URL, copyright=APP_COPYRIGHT),
                parent=self)

        def _show_license(self) -> None:
            win = tk.Toplevel(self)
            win.title(self.t("license_title"))
            win.geometry("660x460")
            win.minsize(520, 360)
            win.transient(self)

            ttk.Label(
                win, text=f"{self.t('app_title')}\n{APP_COPYRIGHT}",
                font=self.font_bold, justify="left"
            ).pack(fill="x", padx=12, pady=(12, 6))

            frame = ttk.Frame(win)
            frame.pack(fill="both", expand=True, padx=12, pady=(0, 6))
            txt = tk.Text(frame, wrap="word", font=self.font_default,
                          height=10)
            vsb = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=vsb.set)
            txt.pack(side="left", fill="both", expand=True)
            vsb.pack(side="right", fill="y")
            txt.insert("1.0", _LICENSE_NOTICE.get(self.lang, GPL2_NOTICE_EN))
            txt.configure(state="disabled")

            ttk.Button(win, text=self.t("btn_close"),
                       command=win.destroy).pack(pady=(0, 12))
            win.bind("<Escape>", lambda _e: win.destroy())

        def _show_colors(self) -> None:
            """Finestra con la legenda dei colori usati nell'interfaccia."""
            win = tk.Toplevel(self)
            win.title(self.t("colors_title"))
            win.transient(self)
            win.resizable(False, False)

            def _add_swatch(row: int, color: str, desc: str) -> None:
                tk.Label(win, text="   ", background=color, width=3,
                         relief="groove", borderwidth=1).grid(
                    row=row, column=0, sticky="w", padx=(12, 8), pady=3)
                ttk.Label(win, text=desc, wraplength=440,
                          justify="left").grid(
                    row=row, column=1, sticky="w", padx=(0, 12), pady=3)

            ttk.Label(win, text=self.t("colors_intro"),
                      font=self.font_bold).grid(
                row=0, column=0, columnspan=2, sticky="w",
                padx=12, pady=(12, 6))
            _add_swatch(1, C_OK, self.t("colors_program"))
            _add_swatch(2, C_WARN, self.t("colors_dependency"))
            _add_swatch(3, C_ERR, self.t("colors_historical"))
            _add_swatch(4, C_OTHER, self.t("colors_other"))

            ttk.Separator(win, orient="horizontal").grid(
                row=5, column=0, columnspan=2, sticky="ew", padx=12, pady=8)

            ttk.Label(win, text=self.t("colors_log_intro"),
                      font=self.font_bold).grid(
                row=6, column=0, columnspan=2, sticky="w",
                padx=12, pady=(0, 6))
            _add_swatch(7, C_INFO, self.t("colors_log_info"))
            _add_swatch(8, C_OK, self.t("colors_log_ok"))
            _add_swatch(9, C_WARN, self.t("colors_log_warn"))
            _add_swatch(10, C_ERR, self.t("colors_log_err"))

            ttk.Button(win, text=self.t("btn_close"),
                       command=win.destroy).grid(
                row=11, column=0, columnspan=2, pady=(10, 12))
            win.bind("<Escape>", lambda _e: win.destroy())

        # ---------- font / preferenze --------------------------------------
        def _apply_fonts(self) -> None:
            """Applica famiglia e dimensione scelte a tutta l'interfaccia."""
            fam = self.pref_family
            size = max(MIN_FONT_SIZE, min(self.pref_size, MAX_FONT_SIZE))
            # Font base per i widget ttk (via stile) e per i widget tk.
            self.font_default.configure(family=fam, size=size)
            self.font_bold.configure(family=fam, size=size, weight="bold")
            self.font_entry.configure(family=fam,
                                      size=min(size + 1, MAX_FONT_SIZE))
            # Font monospazio (log/anteprima): mantengo la famiglia a spaziatura
            # fissa, adatto solo la dimensione così cresce insieme al resto.
            self.font_mono.configure(size=max(size - 1, MIN_FONT_SIZE))
            self.font_mono_small.configure(size=max(size - 2, MIN_FONT_SIZE))
            # Font con nome standard (menu, testo, didascalie, ...).
            for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont",
                         "TkHeadingFont", "TkCaptionFont", "TkSmallCaptionFont",
                         "TkTooltipFont", "TkIconFont"):
                try:
                    tkfont.nametofont(name).configure(family=fam, size=size)
                except tk.TclError:
                    pass
            # Propago il font base allo stile ttk (temi che non usano
            # TkDefaultFont).
            ttk.Style(self).configure(".", font=self.font_default)

        def _fit_to_content(self) -> None:
            """Ingrandisce la finestra (solo se serve) per non tagliare i
            bottoni quando il testo diventa più grande. Non rimpicciolisce mai
            ciò che l'utente ha eventualmente già allargato."""
            self.update_idletasks()
            req_w = self.winfo_reqwidth()
            req_h = self.winfo_reqheight()
            # La finestra non deve poter scendere sotto lo spazio necessario.
            self.minsize(req_w, req_h)
            cur_w = self.winfo_width()
            cur_h = self.winfo_height()
            if cur_w <= 1 or cur_h <= 1:  # finestra non ancora mappata
                cur_w, cur_h = DEFAULT_WIN_W, DEFAULT_WIN_H
            new_w = max(cur_w, req_w)
            new_h = max(cur_h, req_h)
            if (new_w, new_h) != (cur_w, cur_h):
                self.geometry(f"{new_w}x{new_h}")

        def _save_current_prefs(self, announce: bool = True) -> None:
            """Scrive le preferenze correnti nel file JSON accanto allo script."""
            try:
                path = save_prefs({"language": self.lang,
                                   "font_family": self.pref_family,
                                   "font_size": self.pref_size,
                                   "cursor_on_disabled":
                                       self.pref_cursor_disabled})
                if announce:
                    self._log(self.t("prefs_saved", path=path.name), "ok")
            except OSError as exc:
                self._log(self.t("prefs_error", exc=exc), "err")

        def _show_options(self) -> None:
            """Finestra Opzioni: scelta di famiglia e dimensione del carattere."""
            win = tk.Toplevel(self)
            win.title(self.t("options_title"))
            win.transient(self)
            win.resizable(False, False)
            win.columnconfigure(1, weight=1)

            families = sorted({f for f in tkfont.families()
                               if not f.startswith("@")})
            fam_var = tk.StringVar(value=self.pref_family)
            size_var = tk.StringVar(value=str(self.pref_size))
            cursor_var = tk.BooleanVar(value=self.pref_cursor_disabled)

            ttk.Label(win, text=self.t("opt_font_family")).grid(
                row=0, column=0, sticky="w", padx=12, pady=(12, 4))
            ttk.Combobox(win, textvariable=fam_var, values=families,
                         state="readonly", width=34).grid(
                row=0, column=1, sticky="ew", padx=12, pady=(12, 4))

            ttk.Label(win, text=self.t("opt_font_size")).grid(
                row=1, column=0, sticky="w", padx=12, pady=4)
            ttk.Spinbox(win, from_=MIN_FONT_SIZE, to=MAX_FONT_SIZE,
                        textvariable=size_var, width=6).grid(
                row=1, column=1, sticky="w", padx=12, pady=4)

            ttk.Checkbutton(win, text=self.t("opt_cursor"),
                            variable=cursor_var).grid(
                row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 4))

            ttk.Label(win, text=self.t("opt_preview")).grid(
                row=3, column=0, sticky="nw", padx=12, pady=(8, 4))
            preview_font = tkfont.Font(family=self.pref_family,
                                       size=self.pref_size)
            tk.Label(win, text=self.t("opt_preview_text"), font=preview_font,
                     anchor="w", justify="left", relief="groove",
                     padx=8, pady=8).grid(row=3, column=1, sticky="ew",
                                          padx=12, pady=(8, 4))

            def _update_preview(*_a: object) -> None:
                try:
                    preview_font.configure(family=fam_var.get(),
                                           size=int(size_var.get()))
                except (tk.TclError, ValueError):
                    pass

            fam_var.trace_add("write", _update_preview)
            size_var.trace_add("write", _update_preview)

            def _save() -> None:
                try:
                    size = int(size_var.get())
                except ValueError:
                    return
                self.pref_family = fam_var.get()
                self.pref_size = min(max(size, MIN_FONT_SIZE), MAX_FONT_SIZE)
                self.pref_cursor_disabled = cursor_var.get()
                self._apply_fonts()
                self._refresh_disabled_cursors()
                self._fit_to_content()
                self._save_current_prefs()
                win.destroy()

            btns = ttk.Frame(win)
            btns.grid(row=4, column=0, columnspan=2, sticky="e",
                      padx=12, pady=(10, 12))
            ttk.Button(btns, text=self.t("btn_cancel"),
                       command=win.destroy).pack(side="right", padx=(6, 0))
            ttk.Button(btns, text=self.t("btn_save"),
                       command=_save).pack(side="right")
            win.bind("<Escape>", lambda _e: win.destroy())

        # ---------- cursore per i controlli non cliccabili -----------------
        def _resolve_disabled_cursor(self) -> str:
            """Sceglie un cursore 'non consentito' valido sulla piattaforma."""
            probe = tk.Frame(self)
            chosen = ""
            for name in ("no", "X_cursor", "pirate", "circle"):
                try:
                    probe.configure(cursor=name)
                except tk.TclError:
                    continue
                chosen = name
                break
            probe.destroy()
            return chosen

        def _bind_disabled_cursor(self, widget: ttk.Widget) -> None:
            """Cursore 'non cliccabile' quando il widget è in stato disabled."""
            def _update(_e: object = None) -> None:
                # Se la preferenza è disattivata, lascio sempre il cursore
                # di default.
                if not self.pref_cursor_disabled:
                    try:
                        widget["cursor"] = ""
                    except tk.TclError:
                        pass
                    return
                try:
                    disabled = bool(widget.instate(["disabled"]))
                except tk.TclError:
                    return
                try:
                    widget["cursor"] = (self._disabled_cursor
                                        if disabled else "")
                except tk.TclError:
                    pass
            widget.bind("<Enter>", _update, add="+")
            widget.bind("<Motion>", _update, add="+")
            self._cursor_widgets.append(widget)

        def _refresh_disabled_cursors(self) -> None:
            """Riapplica subito il cursore a tutti i widget registrati."""
            for w in self._cursor_widgets:
                try:
                    if not self.pref_cursor_disabled:
                        w["cursor"] = ""
                    else:
                        w["cursor"] = (self._disabled_cursor
                                       if w.instate(["disabled"]) else "")
                except tk.TclError:
                    continue

        def _apply_disabled_cursor_to_buttons(self, parent: tk.Misc) -> None:
            """Applica il cursore a tutti i pulsanti sotto `parent`."""
            for child in parent.winfo_children():
                if isinstance(child, ttk.Button):
                    self._bind_disabled_cursor(child)
                self._apply_disabled_cursor_to_buttons(child)

        # ---------- costruzione interfaccia --------------------------------
        def _build_ui(self) -> None:
            self._cursor_widgets = []
            self.title(self.t("app_title"))
            self._build_menu()
            pad: dict[str, Any] = {"padx": 8, "pady": 6}

            # ---- intestazione con selettore lingua ------------------------
            head = ttk.Frame(self)
            head.pack(fill="x", padx=8, pady=(6, 0))
            self.lang_var = tk.StringVar(value=LANGUAGES[self.lang])
            lang_combo = ttk.Combobox(
                head, textvariable=self.lang_var, state="readonly", width=10,
                values=list(LANGUAGES.values()))
            lang_combo.pack(side="right")
            ttk.Label(head, text=self.t("lbl_language")).pack(
                side="right", padx=(0, 6))
            lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)

            top = ttk.Frame(self)
            top.pack(fill="x", **pad)

            ttk.Label(top, text=self.t("lbl_project_dir")).grid(
                row=0, column=0, sticky="w")
            self.dir_var = tk.StringVar(value=self.t("dir_none"))
            ttk.Label(top, textvariable=self.dir_var, foreground="#444",
                      width=60, anchor="w").grid(row=0, column=1, sticky="w",
                                                 padx=(4, 8))
            ttk.Button(top, text=self.t("btn_browse"),
                       command=self._choose_dir).grid(row=0, column=2)

            ttk.Label(top, text=self.t("lbl_current")).grid(
                row=1, column=0, sticky="w", pady=(8, 0))
            self.cur_var = tk.StringVar(value=self.t("current_placeholder"))
            ttk.Label(top, textvariable=self.cur_var,
                      font=self.font_bold).grid(
                row=1, column=1, sticky="w", padx=(4, 8), pady=(8, 0))

            newf = ttk.Frame(top)
            newf.grid(row=2, column=0, columnspan=3, sticky="w", pady=(10, 0))
            ttk.Label(newf, text=self.t("lbl_new")).pack(side="left")
            self.new_var = tk.StringVar()
            self.new_entry = ttk.Entry(newf, textvariable=self.new_var,
                                       width=14, font=self.font_entry)
            self.new_entry.pack(side="left", padx=(6, 10))
            self.new_var.trace_add("write", lambda *_: self._validate_new())
            ttk.Button(newf, text="+ major",
                       command=lambda: self._bump("major")).pack(side="left")
            ttk.Button(newf, text="+ minor",
                       command=lambda: self._bump("minor")).pack(side="left",
                                                                 padx=4)
            ttk.Button(newf, text="+ patch",
                       command=lambda: self._bump("patch")).pack(side="left")
            self.valid_lbl = ttk.Label(newf, text="")
            self.valid_lbl.pack(side="left", padx=12)

            # ---- barra azioni ---------------------------------------------
            act = ttk.Frame(self)
            act.pack(fill="x", **pad)
            self.scan_btn = ttk.Button(act, text=self.t("btn_scan"),
                                       command=self._scan)
            self.scan_btn.pack(side="left")
            ttk.Button(act, text=self.t("btn_select_all"),
                       command=lambda: self._set_all(True)).pack(side="left",
                                                                 padx=(12, 4))
            ttk.Button(act, text=self.t("btn_deselect_all"),
                       command=lambda: self._set_all(False)).pack(side="left")
            self.backup_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(act, text=self.t("chk_backup"),
                            variable=self.backup_var).pack(side="left", padx=16)
            self.apply_btn = ttk.Button(act, text=self.t("btn_apply"),
                                        command=self._apply, state="disabled")
            self.apply_btn.pack(side="right")

            # ---- area anteprima (lista scrollabile di checkbox) -----------
            mid = ttk.LabelFrame(self, text=self.t("frame_occurrences"))
            mid.pack(fill="both", expand=True, **pad)

            canvas = tk.Canvas(mid, highlightthickness=0)
            vsb = ttk.Scrollbar(mid, orient="vertical", command=canvas.yview)
            hsb = ttk.Scrollbar(mid, orient="horizontal", command=canvas.xview)
            self.rows_frame = ttk.Frame(canvas)
            self._win = canvas.create_window((0, 0), window=self.rows_frame,
                                             anchor="nw")
            canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

            # Layout a griglia: canvas + barra verticale + barra orizzontale.
            canvas.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")
            hsb.grid(row=1, column=0, sticky="ew")
            mid.rowconfigure(0, weight=1)
            mid.columnconfigure(0, weight=1)

            def _sync_scroll(_event=None) -> None:
                # Aggiorna l'area scrollabile e adatta la larghezza del frame
                # interno: pari al canvas se il contenuto è più stretto,
                # altrimenti alla larghezza naturale del contenuto (così la
                # barra orizzontale ha effettivamente qualcosa da scorrere).
                bbox = canvas.bbox("all")
                if bbox:
                    canvas.configure(scrollregion=bbox)
                req = self.rows_frame.winfo_reqwidth()
                canvas.itemconfigure(
                    self._win, width=max(canvas.winfo_width(), req))

            self.rows_frame.bind("<Configure>", _sync_scroll)
            canvas.bind("<Configure>", _sync_scroll)

            # Scroll con la rotellina: verticale, orizzontale tenendo Shift.
            canvas.bind_all(
                "<MouseWheel>",
                lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))
            canvas.bind_all(
                "<Shift-MouseWheel>",
                lambda e: canvas.xview_scroll(int(-e.delta / 120), "units"))
            canvas.bind_all(
                "<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all(
                "<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
            canvas.bind_all(
                "<Shift-Button-4>", lambda e: canvas.xview_scroll(-1, "units"))
            canvas.bind_all(
                "<Shift-Button-5>", lambda e: canvas.xview_scroll(1, "units"))

            # ---- log ------------------------------------------------------
            logf = ttk.LabelFrame(self, text=self.t("frame_log"))
            logf.pack(fill="both", expand=False, **pad)
            self.log = tk.Text(logf, height=8, wrap="word", state="disabled",
                               font=self.font_mono)
            self.log.pack(fill="both", expand=True, padx=4, pady=4)
            for tag, col in (("info", C_INFO), ("ok", C_OK),
                             ("warn", C_WARN), ("err", C_ERR)):
                self.log.tag_configure(tag, foreground=col)

            # Cursore "non cliccabile" sui pulsanti disabilitati.
            self._apply_disabled_cursor_to_buttons(self)

        # ---------- utilità ------------------------------------------------
        def _log(self, msg: str, tag: str = "info") -> None:
            ts = datetime.now().strftime("%H:%M:%S")
            self.log.configure(state="normal")
            self.log.insert("end", f"[{ts}] {msg}\n", tag)
            self.log.see("end")
            self.log.configure(state="disabled")

        def _choose_dir(self) -> None:
            d = filedialog.askdirectory(title=self.t("filedialog_title"))
            if d:
                self._try_load(Path(d))

        def _find_extra_files(self, folder: Path) -> dict[str, Path]:
            """Cerca i file aggiuntivi (README portabile) nel progetto, anche
            in una sottocartella (es. build/). Ignora cartelle generate/nascoste
            e l'output cx_Freeze (`exe.*`). Restituisce {nome_relativo: path}."""
            matches: dict[str, list[Path]] = {n: [] for n in EXTRA_FILE_NAMES}
            for root, dirs, filenames in os.walk(folder):
                dirs[:] = [d for d in dirs
                           if d not in _IGNORED_DIRS
                           and not d.startswith("exe.")]
                for n in EXTRA_FILE_NAMES:
                    if n in filenames:
                        matches[n].append(Path(root) / n)
            found: dict[str, Path] = {}
            for paths in matches.values():
                if paths:
                    # preferisco il percorso più vicino alla radice
                    best = min(paths,
                               key=lambda q: len(q.relative_to(folder).parts))
                    found[best.relative_to(folder).as_posix()] = best
            return found

        def _try_load(self, folder: Path) -> None:
            missing = [n for n in FILE_NAMES if not (folder / n).is_file()]
            if missing:
                self.dir_var.set(str(folder))
                self._log(self.t("missing_files", names=", ".join(missing)),
                          "warn")
                self._log(self.t("missing_hint"), "warn")
                return

            self.project_dir = folder
            self.dir_var.set(str(folder))
            self.files.clear()
            self.file_order = list(FILE_NAMES)
            for name in FILE_NAMES:
                p = folder / name
                self.files[name] = FileState(path=p,
                                             text=p.read_text(encoding="utf-8"))
            # File aggiuntivi opzionali (README portabile), anche in sottocartelle.
            extras = self._find_extra_files(folder)
            for rel, p in extras.items():
                self.files[rel] = FileState(
                    path=p, text=p.read_text(encoding="utf-8"))
                self.file_order.append(rel)
            self.current_version = read_pyproject_version(
                self.files["pyproject.toml"].text)
            self.cur_var.set(self.current_version or self.t("not_found"))
            if self.current_version:
                self.new_var.set(self.current_version)
            self._log(self.t("project_loaded", folder=folder), "ok")
            self._log(self.t("current_in_pyproject",
                             v=self.current_version), "info")
            if extras:
                self._log(self.t("extra_found",
                                 names=", ".join(extras.keys())), "info")
            self._clear_rows()
            self.apply_btn.configure(state="disabled")

        def _validate_new(self) -> bool:
            v = self.new_var.get().strip()
            if is_valid_version(v):
                self.valid_lbl.configure(text=self.t("valid_ok"),
                                         foreground=C_OK)
                return True
            self.valid_lbl.configure(text=self.t("valid_bad"),
                                     foreground=C_ERR)
            return False

        def _bump(self, part: str) -> None:
            base = self.new_var.get().strip() or (self.current_version or "")
            if is_valid_version(base):
                self.new_var.set(bump(base, part))

        # ---------- scansione / anteprima ----------------------------------
        def _clear_rows(self) -> None:
            for w in self.rows_frame.winfo_children():
                w.destroy()
            self.row_vars.clear()
            self.file_enabled.clear()
            self.file_children.clear()

        def _scan(self) -> None:
            if not self.files:
                self._log(self.t("no_project"), "err")
                return
            new_v = self.new_var.get().strip()
            if not is_valid_version(new_v):
                messagebox.showerror(self.t("invalid_version_title"),
                                     self.t("invalid_version_msg"))
                return

            self._clear_rows()
            total = 0
            selected = 0
            for name in self.file_order:
                fs = self.files[name]
                fs.candidates = scan_file(name, fs.text)
                if not fs.candidates:
                    continue
                # intestazione di sezione per file, con checkbox "master"
                # che abilita/disabilita tutte le checkbox figlie del file.
                self.file_children[name] = []
                enabled_var = tk.BooleanVar(value=True)
                self.file_enabled[name] = enabled_var
                hdr = ttk.Frame(self.rows_frame)
                hdr.pack(fill="x", pady=(8, 2))
                ttk.Checkbutton(
                    hdr, variable=enabled_var,
                    command=partial(self._toggle_file, name)
                ).pack(side="left")
                ttk.Label(hdr, text=name,
                          font=self.font_bold).pack(
                    side="left", padx=(2, 0))
                for c in fs.candidates:
                    total += 1
                    if c.selected:
                        selected += 1
                    self._add_row(c, new_v)
            if total == 0:
                self._log(self.t("no_occurrences"), "warn")
                self.apply_btn.configure(state="disabled")
                return
            self._log(self.t("found_summary", total=total, selected=selected),
                      "info")
            n_dep = sum(1 for c, _ in self.row_vars if c.kind == "dependency")
            n_hist = sum(1 for c, _ in self.row_vars if c.kind == "historical")
            if n_hist:
                self._log(self.t("excluded_hist", n=n_hist), "warn")
            if n_dep:
                self._log(self.t("excluded_dep", n=n_dep), "warn")
            self.apply_btn.configure(state="normal")

        def _add_row(self, c: Candidate, new_v: str) -> None:
            var = tk.BooleanVar(value=c.selected)
            self.row_vars.append((c, var))
            row = ttk.Frame(self.rows_frame)
            row.pack(fill="x", padx=6, pady=1)

            cb = ttk.Checkbutton(row, variable=var)
            cb.pack(side="left")
            self._bind_disabled_cursor(cb)
            self.file_children.setdefault(c.file_name, []).append((var, cb))
            meta = ttk.Label(row, width=24, anchor="w",
                             text=self.t("row_meta", line=c.line_no,
                                         old=c.old_value, new=new_v))
            meta.pack(side="left", padx=(2, 6))

            # colore/etichetta secondo la tipologia
            kcol = {"deb": C_OK, "zip": C_OK, "version_assign": C_OK,
                    "project": C_OK, "tag": C_OK,
                    "historical": C_ERR, "dependency": C_WARN,
                    "other": C_OTHER}.get(c.kind, C_OTHER)
            ttk.Label(row, width=22, anchor="w", foreground=kcol,
                      text=f"[{self._kind_label(c.kind)}]").pack(
                side="left", padx=(0, 6))

            # Riga completa: non viene troncata, la barra orizzontale
            # permette di leggerla per intero.
            ttk.Label(row, text=c.line_text.strip(), foreground="#333",
                      font=self.font_mono_small).pack(side="left")

        def _set_all(self, value: bool) -> None:
            for _, var in self.row_vars:
                var.set(value)

        def _toggle_file(self, name: str) -> None:
            """Abilita/disabilita tutte le checkbox figlie del file `name`."""
            enabled = self.file_enabled[name].get()
            state = "normal" if enabled else "disabled"
            for _var, cb in self.file_children.get(name, []):
                cb.configure(state=state)

        # ---------- applica ------------------------------------------------
        def _apply(self) -> None:
            new_v = self.new_var.get().strip()
            if not is_valid_version(new_v):
                messagebox.showerror(self.t("invalid_version_title"),
                                     self.t("required_format"))
                return
            # riporto lo stato delle checkbox sui candidati: una riga conta
            # solo se la sua checkbox è spuntata E il file è abilitato.
            for c, var in self.row_vars:
                file_on = self.file_enabled.get(c.file_name)
                c.selected = var.get() and (file_on is None or file_on.get())

            n_sel = sum(1 for c, _ in self.row_vars if c.selected)
            if n_sel == 0:
                messagebox.showinfo(self.t("nothing_title"),
                                    self.t("nothing_msg"))
                return
            msg = self.t("confirm_msg", new=new_v, n=n_sel, files=len(self.files))
            if self.backup_var.get():
                msg += self.t("confirm_backup")
            if not messagebox.askyesno(self.t("confirm_title"), msg):
                return

            changed_files = 0
            changed_occ = 0
            for name in self.file_order:
                fs = self.files[name]
                new_text, n = apply_to_text(fs.text, fs.candidates, new_v)
                if n == 0:
                    continue
                try:
                    if self.backup_var.get():
                        bak = fs.path.with_suffix(fs.path.suffix + ".bak")
                        shutil.copy2(fs.path, bak)
                        self._log(self.t("log_backup", name=bak.name), "info")
                    fs.path.write_text(new_text, encoding="utf-8")
                except OSError as exc:
                    self._log(self.t("log_write_error", name=name, exc=exc),
                              "err")
                    messagebox.showerror(self.t("write_error_title"),
                                         f"{name}: {exc}")
                    return
                fs.text = new_text
                changed_files += 1
                changed_occ += n
                self._log(self.t("log_file_updated", name=name, n=n, new=new_v),
                          "ok")

            # ricarico la versione corrente e rinfresco l'anteprima
            self.current_version = read_pyproject_version(
                self.files["pyproject.toml"].text)
            self.cur_var.set(self.current_version or self.t("not_found"))
            self._log(self.t("log_completed", occ=changed_occ,
                             files=changed_files, new=new_v), "ok")
            messagebox.showinfo(
                self.t("done_title"),
                self.t("done_msg", occ=changed_occ, files=changed_files,
                       new=new_v))
            self._scan()  # rigenera l'anteprima sullo stato aggiornato

    App().mainloop()


if __name__ == "__main__":
    _launch_gui()
