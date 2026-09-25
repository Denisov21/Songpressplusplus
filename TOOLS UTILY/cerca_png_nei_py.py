#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cerca PNG nei file .py
----------------------
Scegli un file PNG (o scrivi il suo nome) e una cartella principale:
il programma cerca il nome del file in tutti i .py della cartella
(sottocartelle comprese) e risponde SÌ / NO indicando file e riga.

Copyright (C) 2026 Denisov21

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA, or see
<https://www.gnu.org/licenses/old-licenses/gpl-2.0.html>.
"""

import configparser
import importlib
import json
import os
import platform
import subprocess
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

NOME_PROGRAMMA = "Cerca PNG nei file Python"
VERSIONE = "1.6.1"
FILE_CONFIG = os.path.join(os.path.expanduser("~"), ".config", "cerca_png_nei_py.json")
URL_GPL = "https://www.gnu.org/licenses/old-licenses/gpl-2.0.html"
LINGUA_PREDEFINITA = "it"

TESTO_LICENZA_IT = f"""{NOME_PROGRAMMA} — versione {VERSIONE}
Copyright (C) 2026 Denisov21

Questo programma è software libero: puoi ridistribuirlo e/o
modificarlo secondo i termini della GNU General Public License
pubblicata dalla Free Software Foundation, versione 2 della
Licenza oppure (a tua scelta) una versione successiva.

Questo programma è distribuito nella speranza che sia utile,
ma SENZA ALCUNA GARANZIA; senza neppure la garanzia implicita
di COMMERCIABILITÀ o di IDONEITÀ PER UN PARTICOLARE SCOPO.
Per maggiori dettagli consulta la GNU General Public License.

Dovresti aver ricevuto una copia della GNU General Public License
insieme a questo programma. In caso contrario, scrivi alla
Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
Boston, MA 02110-1301 USA, oppure vedi:
{URL_GPL}
"""

TESTO_LICENZA_EN = f"""Find PNG in Python files — version {VERSIONE}
Copyright (C) 2026 Denisov21

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA, or see:
{URL_GPL}
"""

# ---------------------------------------------------------------------------
# Traduzioni (italiano / inglese)
# ---------------------------------------------------------------------------
LINGUE = {"it": "Italiano", "en": "English"}

TESTI = {
    "it": {
        "titolo": NOME_PROGRAMMA,
        "file_png": "File PNG:",
        "cartella": "Cartella principale:",
        "sfoglia": "Sfoglia…",
        "senza_ext": "Cerca anche il nome senza .png",
        "maiuscole": "Ignora maiuscole/minuscole",
        "cerca": "Cerca",
        "file_usano": "File che lo usano:",
        "dettaglio": "Dettaglio (file, riga, codice):",
        "col_file": "File", "col_riga": "Riga", "col_codice": "Codice",
        "pronto": "Pronto.",
        "in_corso": "Ricerca di «{nome}» in corso…",
        "esito_si": "SÌ — «{nome}» è usato in {n} file",
        "esito_no": "NO — «{nome}» non è usato in nessun file .py",
        "occorrenza": "occorrenza", "occorrenze": "occorrenze",
        "stato_fine": "Esaminati {n} file .py — {r} righe trovate.",
        "m_file": "File", "m_esci": "Esci",
        "m_tema": "Tema", "t_chiaro": "Chiaro", "t_scuro": "Scuro", "t_sistema": "Sistema",
        "m_lingua": "Lingua",
        "m_licenza": "Licenza GNU GPL v2…", "m_info": "Informazioni…",
        "esci_titolo": "Esci", "esci_domanda": "Vuoi chiudere il programma?",
        "info_titolo": "Informazioni",
        "info_testo": "{prog}\nVersione {ver}\n\n"
                      "Cerca se un file PNG è usato nei file .py di una cartella.\n\n"
                      "Copyright (C) 2026 Denisov21\n"
                      "Distribuito con licenza GNU GPL v2 o successiva.",
        "lic_titolo": "Licenza GNU GPL v2",
        "lic_testo": TESTO_LICENZA_IT,
        "lic_online": "Testo completo online", "chiudi": "Chiudi",
        "m_sistema": "Info sistema…", "sys_titolo": "Info sistema",
        "sys_copia": "Copia", "sys_copiato": "Copiato negli appunti.",
        "s_programma": "Programma", "s_os": "Sistema operativo",
        "s_distro": "Distribuzione", "s_dispositivo": "Dispositivo",
        "s_arch": "Architettura", "s_cpu": "Processori (core)",
        "s_desktop": "Ambiente desktop", "s_python": "Python",
        "s_eseguibile": "Eseguibile Python", "s_tk": "Tcl/Tk",
        "s_grafica": "Sistema grafico", "s_tema_ttk": "Tema ttk",
        "s_tema_sys": "Tema del sistema rilevato", "s_tema_att": "Tema in uso",
        "s_lingua": "Lingua", "s_schermo": "Schermo",
        "s_scala": "Scala / DPI", "s_config": "File di configurazione",
        "s_programma_file": "File del programma", "s_nd": "non disponibile",
        "dlg_png": "Scegli il file PNG", "dlg_cartella": "Scegli la cartella principale",
        "tipo_png": "Immagini PNG", "tipo_tutti": "Tutti i file",
        "attenzione": "Attenzione",
        "err_png": "Scegli o scrivi il nome di un file PNG.",
        "err_cartella": "La cartella indicata non esiste.",
    },
    "en": {
        "titolo": "Find PNG in Python files",
        "file_png": "PNG file:",
        "cartella": "Main folder:",
        "sfoglia": "Browse…",
        "senza_ext": "Also search the name without .png",
        "maiuscole": "Ignore upper/lower case",
        "cerca": "Search",
        "file_usano": "Files that use it:",
        "dettaglio": "Details (file, line, code):",
        "col_file": "File", "col_riga": "Line", "col_codice": "Code",
        "pronto": "Ready.",
        "in_corso": "Searching for “{nome}”…",
        "esito_si": "YES — “{nome}” is used in {n} file(s)",
        "esito_no": "NO — “{nome}” is not used in any .py file",
        "occorrenza": "occurrence", "occorrenze": "occurrences",
        "stato_fine": "Scanned {n} .py files — {r} matching lines.",
        "m_file": "File", "m_esci": "Exit",
        "m_tema": "Theme", "t_chiaro": "Light", "t_scuro": "Dark", "t_sistema": "System",
        "m_lingua": "Language",
        "m_licenza": "GNU GPL v2 License…", "m_info": "About…",
        "esci_titolo": "Exit", "esci_domanda": "Do you want to close the program?",
        "info_titolo": "About",
        "info_testo": "{prog}\nVersion {ver}\n\n"
                      "Checks whether a PNG file is used in the .py files of a folder.\n\n"
                      "Copyright (C) 2026 Denisov21\n"
                      "Released under the GNU GPL v2 or later.",
        "lic_titolo": "GNU GPL v2 License",
        "lic_testo": TESTO_LICENZA_EN,
        "lic_online": "Full text online", "chiudi": "Close",
        "m_sistema": "System info…", "sys_titolo": "System info",
        "sys_copia": "Copy", "sys_copiato": "Copied to clipboard.",
        "s_programma": "Program", "s_os": "Operating system",
        "s_distro": "Distribution", "s_dispositivo": "Device",
        "s_arch": "Architecture", "s_cpu": "Processors (cores)",
        "s_desktop": "Desktop environment", "s_python": "Python",
        "s_eseguibile": "Python executable", "s_tk": "Tcl/Tk",
        "s_grafica": "Windowing system", "s_tema_ttk": "ttk theme",
        "s_tema_sys": "Detected system theme", "s_tema_att": "Theme in use",
        "s_lingua": "Language", "s_schermo": "Screen",
        "s_scala": "Scaling / DPI", "s_config": "Configuration file",
        "s_programma_file": "Program file", "s_nd": "not available",
        "dlg_png": "Choose the PNG file", "dlg_cartella": "Choose the main folder",
        "tipo_png": "PNG images", "tipo_tutti": "All files",
        "attenzione": "Warning",
        "err_png": "Choose or type the name of a PNG file.",
        "err_cartella": "The selected folder does not exist.",
    },
}
assert TESTI["it"].keys() == TESTI["en"].keys(), "Traduzioni incomplete"

CARTELLE_ESCLUSE = {"__pycache__", ".git", ".venv", "venv", "env",
                    "build", "dist", ".idea", ".vscode", "node_modules"}


# ---------------------------------------------------------------------------
# Temi (chiaro / scuro) e verifica del contrasto WCAG 2.1
# ---------------------------------------------------------------------------
TEMI = {
    "chiaro": {
        "bg": "#f0f0f0", "fg": "#1a1a1a",
        "campo": "#ffffff", "campo_fg": "#1a1a1a",
        "bordo": "#767676", "focus": "#1a5fb4",
        "sel_bg": "#1a5fb4", "sel_fg": "#ffffff",
        "btn_bg": "#e0e0e0", "btn_attivo": "#d0d0d0", "btn_premuto": "#c2c2c2",
        "disab_fg": "#595959", "hover": "#e6e6e6",
        "head_bg": "#e4e4e4", "head_attivo": "#d4d4d4",
        "traccia": "#e4e4e4", "pollice": "#767676", "pollice_attivo": "#555555",
        "menu_bg": "#f7f7f7", "stato_bg": "#e4e4e4",
        "si_bg": "#2e7d32", "no_bg": "#c62828", "esito_fg": "#ffffff",
    },
    "scuro": {
        "bg": "#1f2023", "fg": "#e6e6e6",
        "campo": "#2a2c30", "campo_fg": "#ececec",
        "bordo": "#8a8f98", "focus": "#6ea8fe",
        "sel_bg": "#2f64b5", "sel_fg": "#ffffff",
        "btn_bg": "#34373c", "btn_attivo": "#41454b", "btn_premuto": "#4c5057",
        "disab_fg": "#a3a8b0", "hover": "#292b2f",
        "head_bg": "#2f3236", "head_attivo": "#3a3d42",
        "traccia": "#26282b", "pollice": "#80858d", "pollice_attivo": "#a3a8b0",
        "menu_bg": "#2a2c30", "stato_bg": "#2a2c30",
        "si_bg": "#1b5e20", "no_bg": "#b71c1c", "esito_fg": "#ffffff",
    },
}

# Coppie da verificare: (primo piano, sfondo, descrizione)
COPPIE_TESTO = [  # testo: minimo 4.5:1 (WCAG AA)
    ("fg", "bg", "Testo normale"),
    ("campo_fg", "campo", "Testo nei campi / elenchi"),
    ("sel_fg", "sel_bg", "Testo selezionato / menu attivo"),
    ("fg", "btn_bg", "Testo pulsante"),
    ("fg", "btn_attivo", "Testo pulsante (mouse sopra)"),
    ("fg", "btn_premuto", "Testo pulsante (premuto)"),
    ("disab_fg", "btn_bg", "Pulsante disattivato"),
    ("disab_fg", "bg", "Testo disattivato"),
    ("fg", "hover", "Casella di spunta (mouse sopra)"),
    ("fg", "head_bg", "Intestazioni tabella"),
    ("fg", "head_attivo", "Intestazioni tabella (mouse sopra)"),
    ("fg", "menu_bg", "Voci di menu"),
    ("fg", "stato_bg", "Barra di stato"),
    ("esito_fg", "si_bg", "Esito SÌ"),
    ("esito_fg", "no_bg", "Esito NO"),
]
COPPIE_GRAFICA = [  # bordi ed elementi grafici: minimo 3:1 (WCAG 1.4.11)
    ("bordo", "bg", "Bordi su sfondo"),
    ("bordo", "campo", "Bordi dei campi"),
    ("focus", "bg", "Evidenziazione focus"),
    ("focus", "campo", "Focus nei campi"),
    ("pollice", "traccia", "Barra di scorrimento"),
    ("campo_fg", "campo", "Segno di spunta"),
]


def luminanza(colore):
    r, g, b = (int(colore[i:i + 2], 16) / 255 for i in (1, 3, 5))

    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def rapporto_contrasto(c1, c2):
    l1, l2 = sorted((luminanza(c1), luminanza(c2)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def verifica_contrasto(stampa=True):
    """Controlla tutte le coppie di colori dei temi. Restituisce True se ok."""
    tutto_ok = True
    for nome, p in TEMI.items():
        if stampa:
            print(f"\nTema {nome.upper()}")
        for coppie, minimo in ((COPPIE_TESTO, 4.5), (COPPIE_GRAFICA, 3.0)):
            for a, b, descr in coppie:
                r = rapporto_contrasto(p[a], p[b])
                ok = r >= minimo
                tutto_ok &= ok
                if stampa:
                    print(f"  {'OK ' if ok else 'NO!'} {r:5.2f}:1 (min {minimo}) "
                          f"{descr}  [{p[a]} su {p[b]}]")
    return tutto_ok


# Nome del sistema letto durante l'esecuzione ("Windows", "Darwin", "Linux"…).
# Si usa al posto di sys.platform così i controlli di tipo (mypy) non segnano
# come "irraggiungibile" il codice degli altri sistemi operativi.
SISTEMA = platform.system()


def _esegui(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
    return r.stdout.lower()


def _tema_windows():
    # import dinamico: il modulo esiste solo su Windows
    winreg = importlib.import_module("winreg")
    chiave = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
    valore, _ = winreg.QueryValueEx(chiave, "AppsUseLightTheme")
    return "chiaro" if valore else "scuro"


def _tema_macos():
    uscita = _esegui(["defaults", "read", "-g", "AppleInterfaceStyle"])
    return "scuro" if "dark" in uscita else "chiaro"


def tema_sistema():
    """Rileva se il sistema usa un tema scuro. Restituisce 'chiaro' o 'scuro'."""
    try:
        if SISTEMA == "Windows":
            return _tema_windows()
        if SISTEMA == "Darwin":
            return _tema_macos()
        return _tema_linux()
    except Exception:
        return "chiaro"


def _tema_linux():
    """Linux: GNOME, Raspberry Pi OS, XFCE, KDE…"""
    esegui = _esegui
    parole_scure = ("dark", "noir", "black")   # "PiXnoir" = tema scuro Raspberry Pi
    if any(p in os.environ.get("GTK_THEME", "").lower() for p in parole_scure):
        return "scuro"
    for chiave in ("color-scheme", "gtk-theme"):
        try:
            if any(p in esegui(["gsettings", "get",
                                "org.gnome.desktop.interface", chiave])
                   for p in parole_scure):
                return "scuro"
        except Exception:
            pass
    for ini in ("~/.config/gtk-3.0/settings.ini", "~/.config/gtk-4.0/settings.ini"):
        try:
            cp = configparser.ConfigParser(strict=False)
            cp.read(os.path.expanduser(ini))
            s = cp["Settings"] if cp.has_section("Settings") else {}
            if s.get("gtk-application-prefer-dark-theme", "0").strip() in ("1", "true"):
                return "scuro"
            if any(p in s.get("gtk-theme-name", "").lower() for p in parole_scure):
                return "scuro"
        except Exception:
            pass
    try:
        with open(os.path.expanduser("~/.config/kdeglobals"), encoding="utf-8") as f:
            for riga in f:
                if riga.startswith("ColorScheme=") and "dark" in riga.lower():
                    return "scuro"
    except OSError:
        pass
    return "chiaro"


def contiene_py(cartella):
    try:
        return any(n.endswith(".py") for n in os.listdir(cartella))
    except OSError:
        return False


def cartella_suggerita(percorso_png, max_livelli=3):
    """Cartella principale suggerita: un livello sopra la cartella del PNG
    (es. .../songpressplusplus/img/logo.png -> .../songpressplusplus).
    Se lì non ci sono file .py, sale ancora (al massimo max_livelli)."""
    cartella_png = os.path.dirname(os.path.abspath(percorso_png))
    padre = os.path.dirname(cartella_png) or cartella_png
    corrente = padre
    for _ in range(max_livelli):
        if contiene_py(corrente):
            return os.path.normpath(corrente)
        superiore = os.path.dirname(corrente)
        if superiore == corrente:
            break
        corrente = superiore
    return os.path.normpath(padre)


def carica_config():
    try:
        with open(FILE_CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def salva_config(dati):
    try:
        os.makedirs(os.path.dirname(FILE_CONFIG), exist_ok=True)
        with open(FILE_CONFIG, "w", encoding="utf-8") as f:
            json.dump(dati, f, indent=2)
    except OSError:
        pass


def leggi_testo(percorso):
    """Legge un file provando più codifiche."""
    for enc in ("utf-8", "latin-1"):
        try:
            with open(percorso, "r", encoding=enc) as f:
                return f.readlines()
        except UnicodeDecodeError:
            continue
        except OSError:
            return []
    return []


def cerca(cartella, nome_png, anche_senza_estensione, ignora_maiuscole):
    """Restituisce (lista risultati, numero file .py esaminati)."""
    termini = [nome_png]
    base = os.path.splitext(nome_png)[0]
    if anche_senza_estensione and base and base != nome_png:
        termini.append(base)
    if ignora_maiuscole:
        termini = [t.lower() for t in termini]

    risultati = []  # (percorso_relativo, numero_riga, testo_riga, termine)
    n_file = 0
    for radice, dirs, files in os.walk(cartella):
        dirs[:] = [d for d in dirs if d not in CARTELLE_ESCLUSE]
        for nome in files:
            if not nome.endswith(".py"):
                continue
            n_file += 1
            percorso = os.path.join(radice, nome)
            for i, riga in enumerate(leggi_testo(percorso), start=1):
                confronto = riga.lower() if ignora_maiuscole else riga
                for t in termini:
                    if t in confronto:
                        risultati.append((os.path.relpath(percorso, cartella),
                                          i, riga.strip(), t))
                        break
    return risultati, n_file


# ---------------------------------------------------------------------------
# Icone colorate disegnate nel codice (nessun file esterno necessario)
# ---------------------------------------------------------------------------
LATO = 16  # dimensione icone in pixel


class Pennello:
    """Griglia di pixel su cui disegnare forme semplici."""

    def __init__(self, lato=LATO):
        self.n = lato
        self.px = [[None] * lato for _ in range(lato)]

    def punto(self, x, y, c):
        if 0 <= x < self.n and 0 <= y < self.n:
            self.px[y][x] = c

    def rett(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.punto(x, y, c)

    def cerchio(self, cx, cy, r, c, r_int=None):
        """Cerchio pieno (o anello se r_int è indicato)."""
        for y in range(self.n):
            for x in range(self.n):
                d = ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) ** 0.5
                if d <= r and (r_int is None or d > r_int):
                    self.punto(x, y, c)

    def linea(self, x0, y0, x1, y1, c, spessore=1.0):
        dx, dy = x1 - x0, y1 - y0
        lung2 = dx * dx + dy * dy or 1
        for y in range(self.n):
            for x in range(self.n):
                px, py = x + 0.5, y + 0.5
                t = max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / lung2))
                qx, qy = x0 + t * dx, y0 + t * dy
                if ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5 <= spessore / 2:
                    self.punto(x, y, c)

    def immagine(self, master):
        img = tk.PhotoImage(master=master, width=self.n, height=self.n)
        righe = []
        for riga in self.px:
            righe.append("{" + " ".join(c or "#000000" for c in riga) + "}")
        img.put(" ".join(righe))
        for y, riga in enumerate(self.px):
            for x, c in enumerate(riga):
                if c is None:
                    img.transparency_set(x, y, True)
        return img


def icona_cartella():
    p = Pennello()
    p.rett(1, 3, 6, 4, "#e0a526")        # linguetta
    p.rett(1, 5, 14, 13, "#e0a526")       # retro
    p.rett(1, 7, 14, 13, "#ffcc40")       # fronte
    p.rett(1, 13, 14, 13, "#c98a10")      # bordo
    return p


def icona_immagine():
    p = Pennello()
    p.rett(1, 2, 14, 13, "#5a6b7d")       # cornice
    p.rett(2, 3, 13, 12, "#8fd3ff")       # cielo
    p.cerchio(10.5, 6, 1.8, "#ffd21f")    # sole
    p.linea(2, 12, 7, 7, "#3aa655", 2.5)  # collina
    p.linea(6, 8, 13, 12, "#2e8b47", 2.5)
    p.rett(2, 11, 13, 12, "#2e8b47")
    return p


def icona_cerca():
    p = Pennello()
    p.linea(9.5, 9.5, 14.5, 14.5, "#8b5a2b", 3)   # manico
    p.cerchio(6.5, 6.5, 5.5, "#1f6fd1")           # anello
    p.cerchio(6.5, 6.5, 3.8, "#cdeaff")           # lente
    p.punto(5, 4, "#ffffff"); p.punto(4, 5, "#ffffff")
    return p


def icona_esci():
    p = Pennello()
    p.cerchio(8, 8, 7.5, "#d93025")
    p.linea(5, 5, 11, 11, "#ffffff", 2.2)
    p.linea(11, 5, 5, 11, "#ffffff", 2.2)
    return p


def icona_licenza():
    p = Pennello()
    p.rett(2, 1, 12, 14, "#7a7a7a")        # bordo foglio
    p.rett(3, 2, 11, 13, "#ffffff")        # foglio
    for y in (4, 6, 8):
        p.rett(4, y, 10, y, "#3b7ddd")     # righe di testo
    p.cerchio(11.5, 11.5, 3.5, "#c62828")  # sigillo
    p.cerchio(11.5, 11.5, 1.5, "#ffd54f")
    return p


def icona_info():
    p = Pennello()
    p.cerchio(8, 8, 7.5, "#1f6fd1")
    p.rett(7, 3, 8, 4, "#ffffff")
    p.rett(7, 6, 8, 12, "#ffffff")
    p.rett(6, 12, 9, 12, "#ffffff")
    return p


def icona_web():
    p = Pennello()
    p.cerchio(8, 8, 7.5, "#1e88e5")
    p.cerchio(5.5, 6, 2.6, "#43a047")      # continenti
    p.cerchio(10.5, 11, 2.3, "#43a047")
    p.cerchio(11.5, 4.5, 1.3, "#43a047")
    return p


def icona_chiudi():
    p = Pennello()
    p.linea(3.5, 3.5, 12.5, 12.5, "#d93025", 3)
    p.linea(12.5, 3.5, 3.5, 12.5, "#d93025", 3)
    return p


def icona_sistema():
    p = Pennello()
    p.rett(1, 2, 14, 11, "#455a64")        # cornice monitor
    p.rett(2, 3, 13, 10, "#29b6f6")        # schermo
    p.rett(3, 4, 7, 5, "#e1f5fe")          # riflesso
    p.rett(7, 12, 8, 13, "#455a64")        # collo
    p.rett(4, 14, 11, 14, "#455a64")       # base
    return p


def icona_copia():
    p = Pennello()
    p.rett(1, 1, 9, 11, "#7a7a7a")         # foglio dietro
    p.rett(2, 2, 8, 10, "#e3f2fd")
    p.rett(6, 5, 14, 15, "#1f6fd1")        # foglio davanti
    p.rett(7, 6, 13, 14, "#ffffff")
    for y in (8, 10, 12):
        p.rett(8, y, 12, y, "#1f6fd1")
    return p


def crea_icone(master):
    return {nome: f().immagine(master) for nome, f in {
        "cartella": icona_cartella,
        "immagine": icona_immagine,
        "cerca": icona_cerca,
        "esci": icona_esci,
        "licenza": icona_licenza,
        "info": icona_info,
        "web": icona_web,
        "chiudi": icona_chiudi,
        "sistema": icona_sistema,
        "copia": icona_copia,
    }.items()}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("820x540")
        self.minsize(640, 420)
        self.protocol("WM_DELETE_WINDOW", self.esci)
        self.icone = crea_icone(self)  # riferimenti da tenere in vita

        self.config_utente = carica_config()
        tema_salvato = self.config_utente.get("tema", "sistema")
        if tema_salvato not in ("chiaro", "scuro", "sistema"):
            tema_salvato = "sistema"
        lingua_salvata = self.config_utente.get("lingua", LINGUA_PREDEFINITA)
        if lingua_salvata not in LINGUE:
            lingua_salvata = LINGUA_PREDEFINITA
        self.var_tema = tk.StringVar(value=tema_salvato)
        self.var_lingua = tk.StringVar(value=lingua_salvata)
        self.tema_attivo = "chiaro"
        self.esito = None          # None, "si" oppure "no"
        self.ultimo = None         # (nome_png, risultati, n_file) dell'ultima ricerca
        self.cercando = None       # nome del PNG mentre la ricerca è in corso
        self.menu_lista = []       # menu da ricolorare
        self.finestre_testo = []   # (Toplevel, Text) della licenza
        self.stile = ttk.Style(self)

        self.var_png = tk.StringVar()
        self.var_cartella = tk.StringVar()
        self.cartella_manuale = False  # True se l'utente ha scelto la cartella a mano
        self.var_senza_ext = tk.BooleanVar(value=True)
        self.var_maiusc = tk.BooleanVar(value=False)

        frm = ttk.Frame(self)
        frm.pack(fill="x", padx=8, pady=4)
        frm.columnconfigure(1, weight=1)

        self.lbl_png = ttk.Label(frm)
        self.lbl_png.grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_png).grid(row=0, column=1, sticky="ew", padx=4)
        self.btn_png = ttk.Button(frm, image=self.icone["immagine"], compound="left",
                                  command=self.scegli_png)
        self.btn_png.grid(row=0, column=2, sticky="ew")

        self.lbl_cartella = ttk.Label(frm)
        self.lbl_cartella.grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=self.var_cartella).grid(row=1, column=1, sticky="ew", padx=4)
        self.btn_cartella = ttk.Button(frm, image=self.icone["cartella"], compound="left",
                                       command=self.scegli_cartella)
        self.btn_cartella.grid(row=1, column=2, sticky="ew")

        opz = ttk.Frame(self)
        opz.pack(fill="x", padx=8, pady=4)
        self.chk_ext = ttk.Checkbutton(opz, variable=self.var_senza_ext)
        self.chk_ext.pack(side="left")
        self.chk_maiusc = ttk.Checkbutton(opz, variable=self.var_maiusc)
        self.chk_maiusc.pack(side="left", padx=12)
        self.btn = ttk.Button(opz, image=self.icone["cerca"],
                              compound="left", command=self.avvia_ricerca)
        self.btn.pack(side="right")

        self.lbl_esito = tk.Label(self, text="", font=("Helvetica", 16, "bold"), pady=4)
        self.lbl_esito.pack(fill="x", padx=8, pady=4)

        # Riepilogo per file
        self.lbl_file_usano = ttk.Label(self)
        self.lbl_file_usano.pack(anchor="w", padx=8)
        self.lst_file = tk.Listbox(self, height=5, relief="flat", borderwidth=0,
                                   highlightthickness=1, activestyle="none")
        self.lst_file.pack(fill="x", padx=8, pady=4)

        # Dettaglio righe
        self.lbl_dettaglio = ttk.Label(self)
        self.lbl_dettaglio.pack(anchor="w", padx=8)
        tv_frame = ttk.Frame(self)
        tv_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self.tree = ttk.Treeview(tv_frame, columns=("file", "riga", "codice"),
                                 show="headings")
        self.tree.column("file", width=220)
        self.tree.column("riga", width=50, anchor="center")
        self.tree.column("codice", width=500)
        sb = ttk.Scrollbar(tv_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.stato = ttk.Label(self, style="Stato.TLabel", anchor="w", padding=(6, 3))
        self.stato.pack(fill="x", side="bottom", before=frm)

        self.applica_lingua()
        self.applica_tema()
        self.after(10000, self.controlla_tema_sistema)

    # --- lingua ---
    def t(self, chiave, **valori):
        testo = TESTI[self.var_lingua.get()][chiave]
        return testo.format(**valori) if valori else testo

    def cambia_lingua(self):
        self.config_utente["lingua"] = self.var_lingua.get()
        salva_config(self.config_utente)
        self.applica_lingua()

    def applica_lingua(self):
        """Aggiorna tutti i testi della finestra nella lingua scelta."""
        self.title(self.t("titolo"))
        self.crea_menu()
        self.colora_menu()
        self.lbl_png.configure(text=self.t("file_png"))
        self.lbl_cartella.configure(text=self.t("cartella"))
        self.btn_png.configure(text=self.t("sfoglia"))
        self.btn_cartella.configure(text=self.t("sfoglia"))
        self.chk_ext.configure(text=self.t("senza_ext"))
        self.chk_maiusc.configure(text=self.t("maiuscole"))
        self.btn.configure(text=self.t("cerca"))
        self.lbl_file_usano.configure(text=self.t("file_usano"))
        self.lbl_dettaglio.configure(text=self.t("dettaglio"))
        self.tree.heading("file", text=self.t("col_file"))
        self.tree.heading("riga", text=self.t("col_riga"))
        self.tree.heading("codice", text=self.t("col_codice"))
        self.scrivi_risultati()

    # --- temi ---
    def cambia_tema(self):
        self.config_utente["tema"] = self.var_tema.get()
        salva_config(self.config_utente)
        self.applica_tema()

    def controlla_tema_sistema(self):
        """Se è scelto 'Sistema', segue i cambi di tema del sistema operativo."""
        if self.var_tema.get() == "sistema":
            def lavoro():
                nuovo = tema_sistema()
                if nuovo != self.tema_attivo:
                    self.after(0, self.applica_tema, nuovo)
            threading.Thread(target=lavoro, daemon=True).start()
        self.after(10000, self.controlla_tema_sistema)

    def applica_tema(self, nome=None):
        if nome is None:
            scelta = self.var_tema.get()
            nome = tema_sistema() if scelta == "sistema" else scelta
        self.tema_attivo = nome
        p = TEMI[nome]
        s = self.stile
        s.theme_use("clam")  # tema ttk che accetta colori personalizzati

        s.configure(".", background=p["bg"], foreground=p["fg"],
                    fieldbackground=p["campo"], bordercolor=p["bordo"],
                    lightcolor=p["bg"], darkcolor=p["bg"],
                    troughcolor=p["traccia"], focuscolor=p["focus"],
                    selectbackground=p["sel_bg"], selectforeground=p["sel_fg"],
                    insertcolor=p["fg"])
        s.map(".", foreground=[("disabled", p["disab_fg"])])

        s.configure("TLabel", background=p["bg"], foreground=p["fg"])
        s.configure("Stato.TLabel", background=p["stato_bg"], foreground=p["fg"])
        s.configure("TFrame", background=p["bg"])

        s.configure("TButton", background=p["btn_bg"], foreground=p["fg"],
                    bordercolor=p["bordo"], lightcolor=p["btn_bg"],
                    darkcolor=p["btn_bg"], padding=(8, 3))
        s.map("TButton",
              background=[("disabled", p["btn_bg"]), ("pressed", p["btn_premuto"]),
                          ("active", p["btn_attivo"])],
              lightcolor=[("pressed", p["btn_premuto"]), ("active", p["btn_attivo"])],
              darkcolor=[("pressed", p["btn_premuto"]), ("active", p["btn_attivo"])],
              bordercolor=[("focus", p["focus"])],
              foreground=[("disabled", p["disab_fg"])])

        s.configure("TEntry", fieldbackground=p["campo"], foreground=p["campo_fg"],
                    insertcolor=p["campo_fg"], bordercolor=p["bordo"],
                    lightcolor=p["campo"], darkcolor=p["campo"],
                    selectbackground=p["sel_bg"], selectforeground=p["sel_fg"])
        s.map("TEntry", bordercolor=[("focus", p["focus"])],
              lightcolor=[("focus", p["focus"])])

        s.configure("TCheckbutton", background=p["bg"], foreground=p["fg"],
                    indicatorbackground=p["campo"], indicatorforeground=p["campo_fg"],
                    upperbordercolor=p["bordo"], lowerbordercolor=p["bordo"])
        s.map("TCheckbutton",
              background=[("active", p["hover"])],
              indicatorbackground=[("pressed", p["btn_premuto"]),
                                   ("active", p["campo"])])

        s.configure("Treeview", background=p["campo"], fieldbackground=p["campo"],
                    foreground=p["campo_fg"], bordercolor=p["bordo"],
                    lightcolor=p["campo"], darkcolor=p["campo"])
        s.map("Treeview", background=[("selected", p["sel_bg"])],
              foreground=[("selected", p["sel_fg"])])
        s.configure("Treeview.Heading", background=p["head_bg"], foreground=p["fg"],
                    bordercolor=p["bordo"], lightcolor=p["head_bg"],
                    darkcolor=p["head_bg"])
        s.map("Treeview.Heading", background=[("active", p["head_attivo"])])

        s.configure("TScrollbar", background=p["pollice"], troughcolor=p["traccia"],
                    arrowcolor=p["fg"], bordercolor=p["traccia"],
                    lightcolor=p["pollice"], darkcolor=p["pollice"])
        s.map("TScrollbar", background=[("active", p["pollice_attivo"])],
              lightcolor=[("active", p["pollice_attivo"])],
              darkcolor=[("active", p["pollice_attivo"])])

        # Widget tk classici
        self.configure(bg=p["bg"])
        self.lst_file.configure(bg=p["campo"], fg=p["campo_fg"],
                                selectbackground=p["sel_bg"],
                                selectforeground=p["sel_fg"],
                                highlightbackground=p["bordo"],
                                highlightcolor=p["focus"])
        self.colora_esito()
        self.colora_menu()
        for win, testo in list(self.finestre_testo):
            if win.winfo_exists():
                self.colora_testo(win, testo)
            else:
                self.finestre_testo.remove((win, testo))

        # Colori per le finestre create in seguito (dialoghi di tk)
        for chiave, valore in (("*Background", p["bg"]), ("*Foreground", p["fg"]),
                               ("*Listbox.background", p["campo"]),
                               ("*Listbox.foreground", p["campo_fg"]),
                               ("*Entry.background", p["campo"]),
                               ("*Entry.foreground", p["campo_fg"]),
                               ("*selectBackground", p["sel_bg"]),
                               ("*selectForeground", p["sel_fg"]),
                               ("*insertBackground", p["fg"]),
                               ("*activeBackground", p["btn_attivo"]),
                               ("*activeForeground", p["fg"])):
            self.option_add(chiave, valore)

    def colora_menu(self):
        p = TEMI[self.tema_attivo]
        for m in self.menu_lista:
            m.configure(bg=p["menu_bg"], fg=p["fg"],
                        activebackground=p["sel_bg"], activeforeground=p["sel_fg"],
                        selectcolor=p["fg"], disabledforeground=p["disab_fg"],
                        relief="flat", activeborderwidth=0)

    def colora_esito(self):
        p = TEMI[self.tema_attivo]
        if self.esito == "si":
            self.lbl_esito.configure(bg=p["si_bg"], fg=p["esito_fg"])
        elif self.esito == "no":
            self.lbl_esito.configure(bg=p["no_bg"], fg=p["esito_fg"])
        else:
            self.lbl_esito.configure(bg=p["bg"], fg=p["fg"])

    def colora_testo(self, win, testo):
        p = TEMI[self.tema_attivo]
        win.configure(bg=p["bg"])
        testo.configure(bg=p["campo"], fg=p["campo_fg"], insertbackground=p["campo_fg"],
                        selectbackground=p["sel_bg"], selectforeground=p["sel_fg"],
                        highlightbackground=p["bordo"], highlightcolor=p["focus"],
                        highlightthickness=1, relief="flat", borderwidth=0)

    # --- menu ---
    def crea_menu(self):
        vecchia = self.menu_lista[0] if self.menu_lista else None
        barra = tk.Menu(self)

        m_file = tk.Menu(barra, tearoff=0)
        m_file.add_command(label=self.t("m_esci"), accelerator="Ctrl+Q", command=self.esci,
                           image=self.icone["esci"], compound="left")
        barra.add_cascade(label=self.t("m_file"), menu=m_file)

        m_tema = tk.Menu(barra, tearoff=0)
        for chiave, valore in (("t_chiaro", "chiaro"), ("t_scuro", "scuro"),
                               ("t_sistema", "sistema")):
            m_tema.add_radiobutton(label=self.t(chiave), value=valore,
                                   variable=self.var_tema, command=self.cambia_tema)
        barra.add_cascade(label=self.t("m_tema"), menu=m_tema)

        m_lingua = tk.Menu(barra, tearoff=0)
        for codice, nome in LINGUE.items():  # nomi sempre nella propria lingua
            m_lingua.add_radiobutton(label=nome, value=codice,
                                     variable=self.var_lingua, command=self.cambia_lingua)
        barra.add_cascade(label=self.t("m_lingua"), menu=m_lingua)

        m_aiuto = tk.Menu(barra, tearoff=0)
        m_aiuto.add_command(label=self.t("m_licenza"), command=self.mostra_licenza,
                            image=self.icone["licenza"], compound="left")
        m_aiuto.add_command(label=self.t("m_sistema"), command=self.mostra_sistema,
                            image=self.icone["sistema"], compound="left")
        m_aiuto.add_separator()
        m_aiuto.add_command(label=self.t("m_info"), command=self.mostra_info,
                            image=self.icone["info"], compound="left")
        barra.add_cascade(label="?", menu=m_aiuto)

        self.menu_lista = [barra, m_file, m_tema, m_lingua, m_aiuto]
        self.config(menu=barra)
        if vecchia is not None:
            vecchia.destroy()
        self.bind_all("<Control-q>", lambda e: self.esci())

    def esci(self):
        if messagebox.askyesno(self.t("esci_titolo"), self.t("esci_domanda"), parent=self):
            self.destroy()

    def mostra_info(self):
        messagebox.showinfo(
            self.t("info_titolo"),
            self.t("info_testo", prog=self.t("titolo"), ver=VERSIONE),
            parent=self)

    def mostra_licenza(self):
        win = tk.Toplevel(self)
        win.title(self.t("lic_titolo"))
        win.geometry("560x420")
        win.transient(self)

        testo = tk.Text(win, wrap="word", padx=10, pady=10)
        sb = ttk.Scrollbar(win, orient="vertical", command=testo.yview)
        testo.configure(yscrollcommand=sb.set)
        # Unisce le righe di ogni paragrafo: l'a capo lo decide la finestra
        paragrafi = self.t("lic_testo").strip().split("\n\n")
        corpo = [" ".join(p.split()) for p in paragrafi[1:]]
        testo.insert("1.0", "\n\n".join([paragrafi[0]] + corpo))  # intestazione intatta
        testo.config(state="disabled")

        pulsanti = ttk.Frame(win)
        pulsanti.pack(side="bottom", fill="x", padx=8, pady=8)
        ttk.Button(pulsanti, text=self.t("lic_online"), image=self.icone["web"],
                   compound="left",
                   command=lambda: webbrowser.open(URL_GPL)).pack(side="left")
        ttk.Button(pulsanti, text=self.t("chiudi"), image=self.icone["chiudi"], compound="left",
                   command=win.destroy).pack(side="right")

        sb.pack(side="right", fill="y")
        testo.pack(side="left", fill="both", expand=True)
        self.colora_testo(win, testo)
        self.finestre_testo.append((win, testo))
        win.grab_set()

    # --- info sistema ---
    def raccogli_info_sistema(self):
        """Restituisce una lista di (etichetta, valore) sul sistema in uso."""
        nd = self.t("s_nd")

        def leggi(percorso):
            try:
                with open(percorso, encoding="utf-8", errors="replace") as f:
                    return f.read().replace("\x00", "").strip()
            except OSError:
                return ""

        # Sistema operativo e distribuzione
        so = f"{platform.system()} {platform.release()}".strip() or nd
        distro = ""
        if SISTEMA == "Linux":
            for riga in leggi("/etc/os-release").splitlines():
                if riga.startswith("PRETTY_NAME="):
                    distro = riga.split("=", 1)[1].strip('"')
        elif SISTEMA == "Windows":
            ver = platform.win32_ver()
            distro = f"Windows {ver[0]} ({ver[1]}) {platform.win32_edition() or ''}".strip()
        elif SISTEMA == "Darwin":
            distro = f"macOS {platform.mac_ver()[0]}"

        # Modello del dispositivo (es. Raspberry Pi)
        dispositivo = (leggi("/proc/device-tree/model")
                       or leggi("/sys/devices/virtual/dmi/id/product_name"))

        desktop = ""
        if SISTEMA == "Linux":
            parti = [os.environ.get("XDG_CURRENT_DESKTOP", ""),
                     os.environ.get("XDG_SESSION_TYPE", "")]
            desktop = " / ".join(p for p in parti if p)

        # Schermo e scala
        try:
            scala = float(self.tk.call("tk", "scaling"))
            scala_txt = f"{scala:.2f} ({round(scala * 72)} DPI)"
        except (tk.TclError, ValueError):
            scala_txt = nd
        schermo = f"{self.winfo_screenwidth()} × {self.winfo_screenheight()} px"

        nomi_tema = {"chiaro": self.t("t_chiaro"), "scuro": self.t("t_scuro"),
                     "sistema": self.t("t_sistema")}
        tema_att = nomi_tema[self.tema_attivo]
        if self.var_tema.get() == "sistema":
            tema_att += f" ({nomi_tema['sistema']})"

        return [
            ("s_programma", f"{self.t('titolo')} {VERSIONE}"),
            ("s_programma_file", os.path.abspath(__file__)),
            ("s_os", so),
            ("s_distro", distro or nd),
            ("s_dispositivo", dispositivo or nd),
            ("s_arch", f"{platform.machine() or nd} ({platform.architecture()[0]})"),
            ("s_cpu", str(os.cpu_count() or nd)),
            ("s_desktop", desktop or nd),
            ("s_python", f"{platform.python_implementation()} "
                         f"{platform.python_version()}"),
            ("s_eseguibile", sys.executable or nd),
            ("s_tk", str(self.tk.call("info", "patchlevel"))),
            ("s_grafica", str(self.tk.call("tk", "windowingsystem"))),
            ("s_tema_ttk", self.stile.theme_use()),
            ("s_tema_sys", nomi_tema[tema_sistema()]),
            ("s_tema_att", tema_att),
            ("s_lingua", LINGUE[self.var_lingua.get()]),
            ("s_schermo", schermo),
            ("s_scala", scala_txt),
            ("s_config", FILE_CONFIG),
        ]

    def mostra_sistema(self):
        info = self.raccogli_info_sistema()
        larghezza = max(len(self.t(k)) for k, _ in info) + 2
        testo_info = "\n".join(f"{(self.t(k) + ':').ljust(larghezza)} {v}"
                               for k, v in info)

        win = tk.Toplevel(self)
        win.title(self.t("sys_titolo"))
        win.geometry("700x430")
        win.transient(self)

        pulsanti = ttk.Frame(win)
        pulsanti.pack(side="bottom", fill="x", padx=8, pady=8)
        lbl_copiato = ttk.Label(pulsanti)

        def copia():
            self.clipboard_clear()
            self.clipboard_append(testo_info)
            lbl_copiato.configure(text=self.t("sys_copiato"))
            win.after(2500, lambda: lbl_copiato.winfo_exists()
                      and lbl_copiato.configure(text=""))

        ttk.Button(pulsanti, text=self.t("sys_copia"), image=self.icone["copia"],
                   compound="left", command=copia).pack(side="left")
        lbl_copiato.pack(side="left", padx=10)
        ttk.Button(pulsanti, text=self.t("chiudi"), image=self.icone["chiudi"],
                   compound="left", command=win.destroy).pack(side="right")

        testo = tk.Text(win, wrap="none", padx=10, pady=10, font="TkFixedFont")
        sb_y = ttk.Scrollbar(win, orient="vertical", command=testo.yview)
        sb_x = ttk.Scrollbar(win, orient="horizontal", command=testo.xview)
        testo.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        testo.insert("1.0", testo_info)
        testo.config(state="disabled")
        sb_x.pack(side="bottom", fill="x")
        sb_y.pack(side="right", fill="y")
        testo.pack(side="left", fill="both", expand=True)

        self.colora_testo(win, testo)
        self.finestre_testo.append((win, testo))
        win.grab_set()

    # --- scelte file/cartella ---
    def scegli_png(self):
        p = filedialog.askopenfilename(
            title=self.t("dlg_png"),
            filetypes=[(self.t("tipo_png"), "*.png *.PNG"), (self.t("tipo_tutti"), "*.*")])
        if p:
            self.var_png.set(p)
            if not self.cartella_manuale or not self.var_cartella.get():
                self.var_cartella.set(cartella_suggerita(p))

    def scegli_cartella(self):
        d = filedialog.askdirectory(title=self.t("dlg_cartella"),
                                    initialdir=self.var_cartella.get() or None)
        if d:
            self.var_cartella.set(os.path.normpath(d))
            self.cartella_manuale = True

    # --- ricerca ---
    def avvia_ricerca(self):
        nome_png = os.path.basename(self.var_png.get().strip())
        cartella = self.var_cartella.get().strip()
        if not nome_png:
            messagebox.showwarning(self.t("attenzione"), self.t("err_png"), parent=self)
            return
        if not os.path.isdir(cartella):
            messagebox.showwarning(self.t("attenzione"), self.t("err_cartella"), parent=self)
            return

        self.btn.config(state="disabled")
        self.ultimo = None
        self.cercando = nome_png
        self.scrivi_risultati()

        def lavoro():
            ris, n = cerca(cartella, nome_png,
                           self.var_senza_ext.get(), self.var_maiusc.get())
            self.after(0, self.mostra, nome_png, ris, n)

        threading.Thread(target=lavoro, daemon=True).start()

    def mostra(self, nome_png, risultati, n_file):
        self.btn.config(state="normal")
        self.cercando = None
        self.ultimo = (nome_png, risultati, n_file)
        self.scrivi_risultati()

    def scrivi_risultati(self):
        """Scrive esito, elenco, tabella e stato nella lingua attuale."""
        selezione = [self.tree.index(i) for i in self.tree.selection()]
        self.lst_file.delete(0, "end")
        self.tree.delete(*self.tree.get_children())

        if self.ultimo is None:
            self.esito = None
            self.lbl_esito.config(text="")
            if self.cercando:
                self.stato.config(text=self.t("in_corso", nome=self.cercando))
            else:
                self.stato.config(text=self.t("pronto"))
            self.colora_esito()
            return

        nome_png, risultati, n_file = self.ultimo
        file_trovati = sorted({r[0] for r in risultati})
        if file_trovati:
            self.esito = "si"
            self.lbl_esito.config(text=self.t("esito_si", nome=nome_png,
                                              n=len(file_trovati)))
        else:
            self.esito = "no"
            self.lbl_esito.config(text=self.t("esito_no", nome=nome_png))
        self.colora_esito()

        for f in file_trovati:
            n = sum(1 for r in risultati if r[0] == f)
            parola = self.t("occorrenza") if n == 1 else self.t("occorrenze")
            self.lst_file.insert("end", f"{f}   ({n} {parola})")
        righe = [self.tree.insert("", "end", values=(f, riga, codice))
                 for f, riga, codice, _ in risultati]
        for i in selezione:
            if i < len(righe):
                self.tree.selection_add(righe[i])

        self.stato.config(text=self.t("stato_fine", n=n_file, r=len(risultati)))


if __name__ == "__main__":
    if "--verifica-contrasto" in sys.argv:
        sys.exit(0 if verifica_contrasto() else 1)
    App().mainloop()
