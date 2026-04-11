###############################################################
# Name:             songpress_clenaup.py
# Purpose:     Songpress++ Cleanup Tool Rimuove nel cestino tutte le cartelle e chiavi di registro lasciate da installazioni attuali o precedenti di Songpress++.
# Author:        Denisov21
# Created:     2026-04-11
# Copyright:   Denisov21 © 2026
# License:     GNU GPL v2
##############################################################

"""
Songpress++ Cleanup Tool
Rimuove nel cestino tutte le cartelle e chiavi di registro
lasciate da installazioni attuali o precedenti di Songpress++.
"""

import os
import sys
import winreg
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Union

# Terzo elemento di ogni item: stringa per folder/subdir/shortcut/reg,
# tupla (subkey, value_name) per regval.
ItemPath = Union[str, tuple[str, str]]
CleanupItem = tuple[str, str, ItemPath, str, bool]

# --- Percorsi da controllare ---
def expand(path: str) -> str:
    return os.path.expandvars(path)

def _shell_folder(name: str, fallback_env: str) -> str:
    """Legge un percorso reale da Shell Folders (funziona anche su unità non-C:)."""
    try:
        k = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
        )
        val, _ = winreg.QueryValueEx(k, name)
        winreg.CloseKey(k)
        return val
    except Exception:
        return os.path.expandvars(fallback_env)

def _instdir_from_registry() -> str | None:
    """Legge il percorso effettivo di installazione da UninstallString nel registro."""
    try:
        k = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Songpress++",
        )
        val, _ = winreg.QueryValueEx(k, "UninstallString")
        winreg.CloseKey(k)
        uninst = val.strip('"')
        folder = str(Path(uninst).parent)
        return folder if os.path.isabs(folder) else None
    except Exception:
        return None

def _scan_all_drives() -> list[tuple[str, str]]:
    """
    Cerca la cartella Songpress++ su tutte le unità disco disponibili.
    Controlla i percorsi tipici per ogni unità (AppData, Desktop, radice unità, ecc.).
    Non fa una scansione ricorsiva completa (troppo lenta), ma copre tutti
    i pattern usati dall'installer.
    """
    import ctypes
    found: list[tuple[str, str]] = []
    seen: set[str] = set()

    # Recupera tutte le lettere di unità disponibili
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        if bitmask & (1 << i):
            drives.append(f"{letter}:")

    # Pattern da controllare su ogni unità
    # %DRIVE% viene sostituito con la lettera es. "E:"
    DRIVE_PATTERNS = [
        # Percorsi AppData-like su qualsiasi unità
        r"{drive}\Users\*\AppData\Local\Songpress++",
        r"{drive}\Users\*\AppData\Roaming\Songpress++",
        r"{drive}\Users\*\Desktop\Songpress++",
        r"{drive}\Users\*\OneDrive\Desktop\Songpress++",
        # Radice unità
        r"{drive}\Songpress++",
        r"{drive}\Program Files\Songpress++",
        r"{drive}\Program Files (x86)\Songpress++",
        r"{drive}\Apps\Songpress++",
        r"{drive}\Programmi\Songpress++",
    ]

    import glob
    for drive in drives:
        for pattern in DRIVE_PATTERNS:
            full_pattern = pattern.format(drive=drive)
            try:
                for match in glob.glob(full_pattern):
                    norm = os.path.normpath(match)
                    key  = norm.lower()
                    if key not in seen and os.path.isdir(norm):
                        seen.add(key)
                        # Determina etichetta in base al percorso
                        pl = norm.lower()
                        if "appdata\\local" in pl:
                            label = f"Installazione standard ({drive})"
                        elif "appdata\\roaming" in pl:
                            label = f"Dati utente ({drive})"
                        elif "desktop" in pl:
                            label = f"Installazione portabile – Desktop ({drive})"
                        else:
                            label = f"Cartella trovata ({drive})"
                        found.append((norm, label))
            except Exception:
                pass

    return found

def _deep_scan_drive(drive: str, max_depth: int = 4) -> list[tuple[str, str]]:
    """
    Scansione ricorsiva reale su un'unità fino a max_depth livelli.
    Cerca qualsiasi cartella il cui nome sia 'Songpress++' (case-insensitive).
    Salta cartelle di sistema inaccessibili o molto profonde.
    """
    found: list[tuple[str, str]] = []
    target = "songpress++"

    # Cartelle da saltare completamente (troppo grandi o inaccessibili)
    SKIP_NAMES = {
        "windows", "system32", "syswow64", "winsxs", "$recycle.bin",
        "system volume information", "recovery", "perflogs",
        "msocache", "intel", "amd", "nvidia", "$windows.~ws",
        "node_modules", "__pycache__", ".git",
    }

    def _walk(path: str, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if not entry.is_dir(follow_symlinks=False):
                        continue
                    name_lower = entry.name.lower()
                    if name_lower == target:
                        found.append((entry.path, f"Trovata con scansione ({drive})"))
                        # Non scendere dentro la cartella trovata
                        continue
                    if name_lower in SKIP_NAMES:
                        continue
                    _walk(entry.path, depth + 1)
        except (PermissionError, OSError):
            pass

    _walk(drive + "\\", 0)
    return found


def _build_folder_list() -> list[tuple[str, str]]:
    """
    Costruisce la lista completa di cartelle da controllare:
    1. Percorso dal registro (installazione corrente)
    2. Shell Folders reali (unità corrente utente, anche non-C:)
    3. Scansione su tutte le unità
    I duplicati vengono rimossi.
    """
    seen: set[str] = set()
    result: list[tuple[str, str]] = []

    def add(path: str, label: str) -> None:
        norm = os.path.normpath(path)
        key  = norm.lower()
        if key not in seen:
            seen.add(key)
            result.append((norm, label))

    # 1. Dal registro
    reg_dir = _instdir_from_registry()
    if reg_dir:
        add(reg_dir, "Installazione (da registro)")

    # 2. Shell Folders reali
    localappdata = _shell_folder("Local AppData", "%LOCALAPPDATA%")
    appdata      = _shell_folder("AppData",       "%APPDATA%")
    desktop      = _shell_folder("Desktop",       "%USERPROFILE%\\Desktop")
    add(os.path.join(localappdata, "Songpress++"), "Installazione standard (LocalAppData)")
    add(os.path.join(desktop,      "Songpress++"), "Installazione portabile (Desktop)")
    add(os.path.join(appdata,      "Songpress++"), "Dati utente (AppData)")

    # 3. Variabili ambiente fallback
    add(expand(r"%LOCALAPPDATA%\Songpress++"), "Installazione standard (%LOCALAPPDATA%)")
    add(expand(r"%APPDATA%\Songpress++"),      "Dati utente (%APPDATA%)")
    add(expand(r"%USERPROFILE%\Desktop\Songpress++"), "Installazione portabile (%USERPROFILE%\\Desktop)")

    # 4. Scansione pattern veloci su tutte le unità (fast-path)
    for path, label in _scan_all_drives():
        add(path, label)

    return result


def _build_folder_list_deep(
    callback,
    existing: list[tuple[str, str]] | None = None,
) -> list[tuple[str, str]]:
    """
    Scansione ricorsiva reale su tutte le unità (max 4 livelli).
    Trova Songpress++ in qualunque percorso non coperto dai pattern fissi.
    Da eseguire in un thread separato per non bloccare la GUI.
    `callback(path, label)` viene chiamata per ogni nuova cartella trovata.
    """
    import ctypes

    seen: set[str] = set()
    if existing:
        for path, _ in existing:
            seen.add(os.path.normpath(path).lower())

    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        if bitmask & (1 << i):
            drives.append(f"{letter}:")

    new_items: list[tuple[str, str]] = []
    for drive in drives:
        for path, label in _deep_scan_drive(drive, max_depth=4):
            key = os.path.normpath(path).lower()
            if key not in seen:
                seen.add(key)
                new_items.append((path, label))
                callback(path, label)

    return new_items


FOLDERS = _build_folder_list()

# Chiavi di registro (HKCU) da rimuovere — allineate al NSI
REG_KEYS = [
    # Uninstall
    (r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Songpress++",          "Disinstallatore"),
    # App Paths — nome exe corretto dal NSI
    (r"Software\Microsoft\Windows\CurrentVersion\App Paths\SongPressPlusPlus.exe", "App Paths (SongPressPlusPlus.exe)"),
    # ProgID corrente
    (r"Software\Classes\SongpressPlusPlus.ChordPro", "ProgID attuale (SongpressPlusPlus.ChordPro)"),
    # ProgID legacy
    (r"Software\Classes\Songpress.ChordPro",         "ProgID legacy (Songpress.ChordPro)"),
    (r"Software\Classes\Songpress.crd",              "ProgID legacy (Songpress.crd)"),
    # Associazioni estensioni (inclusa .tab, gestita dal NSI)
    (r"Software\Classes\.crd",      "Associazione .crd"),
    (r"Software\Classes\.pro",      "Associazione .pro"),
    (r"Software\Classes\.chopro",   "Associazione .chopro"),
    (r"Software\Classes\.chordpro", "Associazione .chordpro"),
    (r"Software\Classes\.cho",      "Associazione .cho"),
    (r"Software\Classes\.tab",      "Associazione .tab"),
]

# Valori singoli di registro (HKCU) da rimuovere: (subkey, value_name, label)
# Il NSI rimuove le voci OpenWithProgids per entrambi i ProgID legacy su tutte le estensioni.
REG_VALUES = [
    # OpenWithProgids – Songpress.crd (legacy)
    (r"Software\Classes\.crd\OpenWithProgids",      "Songpress.crd",       "OpenWithProgids .crd → Songpress.crd"),
    (r"Software\Classes\.pro\OpenWithProgids",      "Songpress.crd",       "OpenWithProgids .pro → Songpress.crd"),
    (r"Software\Classes\.chopro\OpenWithProgids",   "Songpress.crd",       "OpenWithProgids .chopro → Songpress.crd"),
    (r"Software\Classes\.chordpro\OpenWithProgids", "Songpress.crd",       "OpenWithProgids .chordpro → Songpress.crd"),
    (r"Software\Classes\.cho\OpenWithProgids",      "Songpress.crd",       "OpenWithProgids .cho → Songpress.crd"),
    (r"Software\Classes\.tab\OpenWithProgids",      "Songpress.crd",       "OpenWithProgids .tab → Songpress.crd"),
    # OpenWithProgids – Songpress.ChordPro (legacy)
    (r"Software\Classes\.crd\OpenWithProgids",      "Songpress.ChordPro",  "OpenWithProgids .crd → Songpress.ChordPro"),
    (r"Software\Classes\.pro\OpenWithProgids",      "Songpress.ChordPro",  "OpenWithProgids .pro → Songpress.ChordPro"),
    (r"Software\Classes\.chopro\OpenWithProgids",   "Songpress.ChordPro",  "OpenWithProgids .chopro → Songpress.ChordPro"),
    (r"Software\Classes\.chordpro\OpenWithProgids", "Songpress.ChordPro",  "OpenWithProgids .chordpro → Songpress.ChordPro"),
    (r"Software\Classes\.cho\OpenWithProgids",      "Songpress.ChordPro",  "OpenWithProgids .cho → Songpress.ChordPro"),
    (r"Software\Classes\.tab\OpenWithProgids",      "Songpress.ChordPro",  "OpenWithProgids .tab → Songpress.ChordPro"),
]

# Shortcut da rimuovere (percorsi con variabili ambiente, risolti a runtime)
SHORTCUTS = [
    (r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Songpress++\Songpress++.lnk",
     "Collegamento Start Menu"),
    (r"%USERPROFILE%\Desktop\Songpress++.lnk",
     "Collegamento Desktop"),
]

# Sottocartelle interne all'installazione da cercare e rimuovere separatamente.
INSTALL_SUBDIRS = ["bin", "tools", "python", "cache"]

# --- Utility ---

def reg_key_exists(subkey: str) -> bool:
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey)
        winreg.CloseKey(k)
        return True
    except FileNotFoundError:
        return False

def send_to_recycle(path: str) -> bool:
    """Manda una cartella nel cestino usando SHFileOperation via ctypes."""
    import ctypes
    from ctypes import wintypes

    class SHFILEOPSTRUCT(ctypes.Structure):
        _fields_ = [
            ("hwnd",                  wintypes.HWND),
            ("wFunc",                 wintypes.UINT),
            ("pFrom",                 wintypes.LPCWSTR),
            ("pTo",                   wintypes.LPCWSTR),
            ("fFlags",                wintypes.WORD),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings",         ctypes.c_void_p),
            ("lpszProgressTitle",     wintypes.LPCWSTR),
        ]

    FO_DELETE    = 0x0003
    FOF_ALLOWUNDO        = 0x0040  # manda nel cestino
    FOF_NOCONFIRMATION   = 0x0010
    FOF_SILENT           = 0x0004

    # pFrom deve terminare con \0\0
    path_buf = path + "\0"

    op = SHFILEOPSTRUCT()
    op.hwnd   = None
    op.wFunc  = FO_DELETE
    op.pFrom  = path_buf
    op.pTo    = None
    op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT

    shell32 = ctypes.windll.shell32
    ret = shell32.SHFileOperationW(ctypes.byref(op))
    return ret == 0

def delete_reg_key_recursive(subkey: str) -> bool:
    """Elimina una chiave di registro HKCU ricorsivamente."""
    try:
        # RegDeleteTree disponibile su Vista+
        import ctypes
        advapi = ctypes.windll.advapi32
        HKEY_CURRENT_USER = 0x80000001
        ret = advapi.RegDeleteTreeW(HKEY_CURRENT_USER, subkey)
        return ret == 0
    except Exception:
        return False

def delete_reg_value(subkey: str, value_name: str) -> bool:
    """Elimina un singolo valore di registro HKCU (es. una voce OpenWithProgids)."""
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(k, value_name)
        winreg.CloseKey(k)
        return True
    except FileNotFoundError:
        return True   # già assente, consideriamo OK
    except Exception:
        return False

def reg_value_exists(subkey: str, value_name: str) -> bool:
    """Controlla se un singolo valore di registro HKCU esiste."""
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey)
        winreg.QueryValueEx(k, value_name)
        winreg.CloseKey(k)
        return True
    except Exception:
        return False

def notify_shell():
    """Notifica Windows del cambio associazioni file."""
    import ctypes
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)


# --- Fix associazioni file ---

EXTENSIONS = ["crd", "pro", "chopro", "chordpro", "cho", "tab"]
PROGID      = "SongpressPlusPlus.ChordPro"
LEGACY_PROGIDS = ["Songpress.crd", "Songpress.ChordPro"]

def _detect_instdir_candidates() -> list[tuple[str, str]]:
    """
    Restituisce una lista di (percorso_instdir, etichetta) candidati,
    cercando SongPressPlusPlus.exe su tutte le unita' disponibili.
    """
    import ctypes, glob
    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(path: str, label: str) -> None:
        norm = os.path.normpath(path)
        key  = norm.lower()
        if key not in seen and os.path.isfile(os.path.join(norm, "bin", "SongPressPlusPlus.exe")):
            seen.add(key)
            candidates.append((norm, label))

    # 1. Dal registro (piu' affidabile)
    reg_dir = _instdir_from_registry()
    if reg_dir:
        add(reg_dir, f"Da registro: {reg_dir}")

    # 2. Shell Folders reali (funziona anche su drive non-C:)
    localappdata = _shell_folder("Local AppData", "%LOCALAPPDATA%")
    add(os.path.join(localappdata, "Songpress++"), f"LocalAppData: {localappdata}\\Songpress++")

    # 3. Scansione pattern su tutti i drive
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    drives = [f"{l}:" for i, l in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ") if bitmask & (1 << i)]
    patterns = [
        r"{drive}\Users\*\AppData\Local\Songpress++",
        r"{drive}\Users\*\Desktop\Songpress++",
        r"{drive}\Users\*\OneDrive\Desktop\Songpress++",
    ]
    for drive in drives:
        for pat in patterns:
            for match in glob.glob(pat.format(drive=drive)):
                add(match, match)

    return candidates


def fix_associations(instdir: str) -> tuple[int, list[str]]:
    """
    Rimuove i ProgID legacy e reimporta le associazioni corrette
    per il percorso di installazione `instdir`.
    Restituisce (n_operazioni_ok, lista_errori).
    """
    ok = 0
    errors: list[str] = []

    exe = os.path.join(instdir, "bin", "SongPressPlusPlus.exe")
    ico = os.path.join(instdir, "songpressplusplus.ico")
    cmd = f'"{exe}" "%1"'

    # 1. Rimuovi ProgID legacy e corrente (reimpostazione pulita)
    legacy_keys = [
        r"Software\Classes\Songpress.crd",
        r"Software\Classes\Songpress.ChordPro",
        r"Software\Classes\SongpressPlusPlus.ChordPro",
    ]
    for subkey in legacy_keys:
        if reg_key_exists(subkey):
            if delete_reg_key_recursive(subkey):
                ok += 1
            else:
                errors.append(f"Impossibile eliminare HKCU\\{subkey}")
        else:
            ok += 1

    # 2. Rimuovi OpenWithProgids sporchi su tutte le estensioni
    for ext in EXTENSIONS:
        for legacy in LEGACY_PROGIDS:
            subkey = rf"Software\Classes\.{ext}\OpenWithProgids"
            if reg_value_exists(subkey, legacy):
                if delete_reg_value(subkey, legacy):
                    ok += 1
                else:
                    errors.append(f"Impossibile eliminare HKCU\\{subkey} -> {legacy}")
            else:
                ok += 1

    # 3. Scrivi ProgID corretto
    try:
        base = rf"Software\Classes\{PROGID}"
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, base)
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "ChordPro")
        winreg.CloseKey(k)

        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{base}\DefaultIcon")
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f"{ico},0")
        winreg.CloseKey(k)

        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{base}\shell")
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "open")
        winreg.CloseKey(k)

        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{base}\shell\open")
        winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, "Songpress++")
        winreg.SetValueEx(k, "Icon",    0, winreg.REG_SZ, f"{ico},0")
        winreg.CloseKey(k)

        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{base}\shell\open\command")
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(k)
        ok += 1
    except Exception as e:
        errors.append(f"Errore scrittura ProgID: {e}")

    # 4. Associa tutte le estensioni al ProgID corretto
    for ext in EXTENSIONS:
        try:
            k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\.{ext}")
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, PROGID)
            winreg.CloseKey(k)
            ok += 1
        except Exception as e:
            errors.append(f"Errore associazione .{ext}: {e}")

    notify_shell()
    return ok, errors


class FixAssocDialog(tk.Toplevel):
    """Dialog per ripristinare le associazioni file di Songpress++."""

    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("Ripristina associazioni file")
        self.resizable(False, False)
        self.grab_set()
        self._build_ui()
        self._detect()

    def _build_ui(self):
        pad = {"padx": 14, "pady": 5}

        tk.Label(self, text="Ripristina associazioni file",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=5)
        tk.Label(self,
                 text="Questa funzione rimuove i ProgID legacy e reimporta le\n"
                      "associazioni corrette per .crd .pro .chopro .chordpro .cho .tab.",
                 font=("Segoe UI", 9), justify="left").pack(anchor="w", padx=14, pady=(0, 8))

        tk.Label(self, text="Percorso installazione Songpress++:",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14)

        sel_frame = tk.Frame(self)
        sel_frame.pack(fill="x", padx=14, pady=(2, 0))

        self.path_var = tk.StringVar()
        self.combo = ttk.Combobox(sel_frame, textvariable=self.path_var,
                                  width=58, state="readonly")
        self.combo.pack(side="left")

        tk.Button(sel_frame, text="Sfoglia...",
                  command=self._browse).pack(side="left", padx=(6, 0))

        tk.Label(self,
                 text="Se il percorso non compare nell'elenco, premi Sfoglia e seleziona\n"
                      "la cartella Songpress++ (quella che contiene la sottocartella bin\\).",
                 font=("Segoe UI", 8), fg="#666", justify="left").pack(
            anchor="w", padx=14, pady=(2, 10))

        self.status_var = tk.StringVar(value="Rilevamento installazioni in corso...")
        tk.Label(self, textvariable=self.status_var, anchor="w",
                 font=("Segoe UI", 8), fg="#555").pack(fill="x", padx=14, pady=(0, 8))

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=14, pady=(0, 12))
        self.btn_fix = tk.Button(
            btn_frame, text="Ripristina associazioni",
            command=self._apply,
            bg="#28a745", fg="white",
            font=("Segoe UI", 10, "bold"), width=26, state="disabled",
        )
        self.btn_fix.pack(side="left")
        tk.Button(btn_frame, text="Annulla", command=self.destroy,
                  width=10).pack(side="right")

    def _detect(self):
        candidates = _detect_instdir_candidates()
        if candidates:
            values = [path for path, _ in candidates]
            self.combo["values"] = values
            self.combo.current(0)
            self.status_var.set(
                f"{len(candidates)} installazione/i rilevata/e — seleziona quella corretta."
            )
            self.btn_fix.config(state="normal")
        else:
            self.combo["values"] = []
            self.status_var.set(
                "Nessuna installazione rilevata automaticamente. Usa Sfoglia."
            )

    def _browse(self):
        path = filedialog.askdirectory(
            title="Seleziona la cartella Songpress++ (quella con la sottocartella bin\\)",
            mustexist=True,
        )
        if not path:
            return
        path = os.path.normpath(path)
        exe = os.path.join(path, "bin", "SongPressPlusPlus.exe")
        if not os.path.isfile(exe):
            messagebox.showwarning(
                "Percorso non valido",
                f"Non ho trovato bin\\SongPressPlusPlus.exe in:\n{path}\n\n"
                "Seleziona la cartella principale di Songpress++ "
                "(quella che contiene la sottocartella bin\\).",
                parent=self,
            )
            return
        current = list(self.combo["values"])
        if path not in current:
            current.insert(0, path)
            self.combo["values"] = current
        self.path_var.set(path)
        self.combo.config(state="readonly")
        self.btn_fix.config(state="normal")
        self.status_var.set(f"Percorso selezionato manualmente: {path}")

    def _apply(self):
        instdir = self.path_var.get().strip()
        if not instdir:
            messagebox.showwarning("Nessun percorso", "Seleziona prima il percorso di installazione.", parent=self)
            return
        exe = os.path.join(instdir, "bin", "SongPressPlusPlus.exe")
        if not os.path.isfile(exe):
            messagebox.showerror(
                "Percorso non valido",
                f"bin\\SongPressPlusPlus.exe non trovato in:\n{instdir}",
                parent=self,
            )
            return

        ok, errors = fix_associations(instdir)
        if errors:
            messagebox.showwarning(
                "Completato con errori",
                f"{ok} operazioni riuscite.\n\nErrori:\n" + "\n".join(errors),
                parent=self,
            )
        else:
            messagebox.showinfo(
                "Associazioni ripristinate",
                f"Associazioni file ripristinate con successo ({ok} operazioni).\n\n"
                f"Percorso exe:\n{exe}\n\n"
                "Se le icone dei file non si aggiornano subito, riavvia Esplora risorse.",
                parent=self,
            )
        self.destroy()


# --- GUI ---

class CleanupApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Songpress++ — Pulizia installazione")
        self.resizable(False, False)
        self._build_ui()
        self._scan()

    def _build_ui(self):
        # Titolo
        tk.Label(self, text="Songpress++ Cleanup Tool",
                 font=("Segoe UI", 13, "bold")).pack(padx=12, pady=6, anchor="w")
        tk.Label(self, text="Seleziona gli elementi da eliminare e premi Elimina. "
                            "Le cartelle vanno nel cestino, le chiavi registro vengono eliminate definitivamente.",
                 font=("Segoe UI", 9), wraplength=700, justify="left").pack(padx=12, pady=(0, 8), anchor="w")

        # Frame lista
        frame = tk.Frame(self)
        frame.pack(padx=12, fill="both", expand=True)

        # Scrollbar
        sb = tk.Scrollbar(frame)
        sb.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            frame,
            columns=("tipo", "percorso", "stato"),
            show="headings",
            yscrollcommand=sb.set,
            selectmode="none",
            height=16,
        )
        sb.config(command=self.tree.yview)

        self.tree.heading("tipo",    text="Tipo")
        self.tree.heading("percorso", text="Percorso / Chiave registro")
        self.tree.heading("stato",   text="Stato")

        self.tree.column("tipo",     width=160, anchor="w")
        self.tree.column("percorso", width=460, anchor="w")
        self.tree.column("stato",    width=100, anchor="center")

        self.tree.pack(fill="both", expand=True)

        # Colori righe
        self.tree.tag_configure("presente",  background="#fff3cd")  # giallo
        self.tree.tag_configure("assente",   background="#f8f9fa")  # grigio chiaro
        self.tree.tag_configure("check_on",  background="#d4edda")  # verde chiaro
        self.tree.tag_configure("reg",       foreground="#555555")

        # Checkbox simulata: click su riga toglie/mette spunta
        self.tree.bind("<ButtonRelease-1>", self._on_click)
        self.checked = set()  # iid degli elementi selezionati

        # Bottoni
        btn_frame = tk.Frame(self)
        btn_frame.pack(padx=12, pady=10, fill="x")

        tk.Button(btn_frame, text="Seleziona tutto",   command=self._select_all,
                  width=18).pack(side="left", padx=(0, 6))
        tk.Button(btn_frame, text="Deseleziona tutto", command=self._deselect_all,
                  width=18).pack(side="left", padx=(0, 6))
        tk.Button(btn_frame, text="📂  Aggiungi cartella...", command=self._add_custom_folder,
                  width=22).pack(side="left")
        tk.Button(btn_frame, text="🔗  Ripristina associazioni...",
                  command=lambda: FixAssocDialog(self),
                  bg="#9acd32", fg="black",
                  font=("Segoe UI", 9, "bold"),
                  width=26).pack(side="left", padx=(6, 0))

        self.btn_delete = tk.Button(
            btn_frame, text="🗑  Elimina selezionati",
            command=self._delete, bg="#dc3545", fg="white",
            font=("Segoe UI", 10, "bold"), width=22,
        )
        self.btn_delete.pack(side="right")

        tk.Button(btn_frame, text="Chiudi", command=self.destroy,
                  width=10).pack(side="right", padx=(0, 8))

        # Status bar
        self.status_var = tk.StringVar(value="Scansione in corso...")
        tk.Label(self, textvariable=self.status_var, anchor="w",
                 font=("Segoe UI", 8), fg="#666").pack(
            fill="x", padx=12, pady=(0, 6))

    def _scan(self):
        import threading

        self.items: list[CleanupItem] = []
        self._sep_iid: str | None = None   # iid del separatore (inserito dopo i folder)
        self._deep_running = False
        self.status_var.set("Scansione rapida in corso...")
        self.update()

        # ── 1. Scansione rapida (registro + pattern fissi) ──────────────────
        folders = _build_folder_list()

        for path, label in folders:
            exists = os.path.isdir(path)
            iid = self.tree.insert(
                "", "end",
                values=("📁 Cartella", path, "✔ Trovata" if exists else "— Assente"),
                tags=("presente" if exists else "assente",),
            )
            self.items.append((iid, "folder", path, label, exists))
            if exists:
                self.checked.add(iid)

        # Separatore visivo (lo ricordiamo per inserire prima di esso i nuovi folder)
        self._sep_iid = self.tree.insert("", "end", values=("", "", ""), tags=("assente",))

        # ── Shortcut ─────────────────────────────────────────────────────────
        for env_path, label in SHORTCUTS:
            path = os.path.expandvars(env_path)
            exists = os.path.isfile(path)
            iid = self.tree.insert(
                "", "end",
                values=("🔗 Collegamento", path, "✔ Trovato" if exists else "— Assente"),
                tags=("presente" if exists else "assente",),
            )
            self.items.append((iid, "shortcut", path, label, exists))
            if exists:
                self.checked.add(iid)

        # ── Sottocartelle interne ─────────────────────────────────────────────
        # Vengono cercate dentro ogni cartella di installazione trovata.
        _seen_subdirs: set[str] = set()
        for _iid, kind, inst_path, _lbl, inst_exists in list(self.items):
            if kind != "folder" or not inst_exists:
                continue
            assert isinstance(inst_path, str)
            for sub in INSTALL_SUBDIRS:
                full = os.path.normpath(os.path.join(inst_path, sub))
                key  = full.lower()
                if key in _seen_subdirs:
                    continue
                _seen_subdirs.add(key)
                exists = os.path.isdir(full)
                iid = self.tree.insert(
                    "", "end",
                    values=("📂 Sottocartella", full, "✔ Trovata" if exists else "— Assente"),
                    tags=("presente" if exists else "assente",),
                )
                self.items.append((iid, "subdir", full, f"Sottocartella {sub}", exists))
                if exists:
                    self.checked.add(iid)

        # ── Chiavi registro ───────────────────────────────────────────────────
        for subkey, label in REG_KEYS:
            exists = reg_key_exists(subkey)
            iid = self.tree.insert(
                "", "end",
                values=("🔑 Registro", f"HKCU\\{subkey}", "✔ Trovata" if exists else "— Assente"),
                tags=("presente" if exists else "assente", "reg"),
            )
            self.items.append((iid, "reg", subkey, label, exists))
            if exists:
                self.checked.add(iid)

        # ── Valori registro (OpenWithProgids) ─────────────────────────────────
        for subkey, value_name, label in REG_VALUES:
            exists = reg_value_exists(subkey, value_name)
            display = f"HKCU\\{subkey} → {value_name}"
            iid = self.tree.insert(
                "", "end",
                values=("📋 Valore reg.", display, "✔ Trovato" if exists else "— Assente"),
                tags=("presente" if exists else "assente", "reg"),
            )
            self.items.append((iid, "regval", (subkey, value_name), label, exists))
            if exists:
                self.checked.add(iid)

        self._refresh_checks()
        n_fast = sum(1 for *_, exists in self.items if exists)
        self.status_var.set(
            f"Scansione rapida: {n_fast} trovati — scansione profonda in corso..."
        )

        # ── 2. Scansione profonda in thread ─────────────────────────────────
        self._deep_running = True

        def _deep_worker():
            existing: list[tuple[str, str]] = [
                (p, l)
                for iid, kind, p, l, _ in self.items
                if kind == "folder" and isinstance(p, str)
            ]
            _build_folder_list_deep(
                callback=self._on_deep_found,
                existing=existing,
            )
            # Segnala fine al thread principale tramite after()
            self.after(0, self._on_deep_done)

        t = threading.Thread(target=_deep_worker, daemon=True)
        t.start()

    def _on_deep_found(self, path: str, label: str):
        """Callback dal thread di scansione profonda: aggiunge una riga alla lista."""
        exists = os.path.isdir(path)

        def _insert():
            assert self._sep_iid is not None
            iid = self.tree.insert(
                "", self.tree.index(self._sep_iid),  # prima del separatore
                values=("📁 Cartella", path, "✔ Trovata" if exists else "— Assente"),
                tags=("presente" if exists else "assente",),
            )
            self.items.append((iid, "folder", path, label, exists))
            if exists:
                self.checked.add(iid)
                self._refresh_checks()
            n = sum(1 for *_, e in self.items if e)
            self.status_var.set(
                f"Scansione profonda in corso... {n} trovati finora — {path}"
            )

        self.after(0, _insert)

    def _on_deep_done(self):
        """Chiamata dal thread principale quando la scansione profonda è finita."""
        self._deep_running = False
        n = sum(1 for *_, exists in self.items if exists)
        self.status_var.set(f"Scansione completata — {n} elemento/i trovati.")

    def _on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region not in ("cell", "heading"):
            return
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        # Solo righe con elementi presenti
        item_data = next((x for x in self.items if x[0] == iid), None)
        if not item_data or not item_data[4]:
            return
        if iid in self.checked:
            self.checked.discard(iid)
        else:
            self.checked.add(iid)
        self._refresh_checks()

    def _refresh_checks(self):
        for iid, kind, _path, _label, exists in self.items:
            if not exists:
                continue
            selected = iid in self.checked
            vals = self.tree.item(iid, "values")
            check = "☑" if selected else "☐"
            tipo = vals[0]
            # Rimuovi eventuale spunta precedente dal tipo
            tipo_clean = tipo.lstrip("☑☐ ")
            self.tree.item(iid, values=(
                f"{check} {tipo_clean}", vals[1], vals[2]
            ), tags=("check_on" if selected else "presente",
                     "reg" if kind in ("reg", "regval") else ""))

    def _add_custom_folder(self):
        """Apre un dialogo per aggiungere manualmente una cartella alla lista."""
        path = filedialog.askdirectory(
            title="Seleziona cartella Songpress++ da aggiungere",
            mustexist=True,
        )
        if not path:
            return
        # Normalizza il separatore (filedialog restituisce slash su Windows)
        path = os.path.normpath(path)
        # Controlla se è già in lista
        existing_paths = {os.path.normpath(p).lower() for _, _, p, _, _ in self.items
                         if isinstance(p, str)}
        if path.lower() in existing_paths:
            messagebox.showinfo(
                "Già presente",
                f"La cartella è già nella lista:\n{path}",
            )
            return
        # Inserisce nella lista prima del separatore (se esiste), altrimenti in fondo
        exists = os.path.isdir(path)
        insert_pos: int = self.tree.index(self._sep_iid) if self._sep_iid is not None else self.tree.index("end")
        iid = self.tree.insert(
            "", insert_pos,
            values=("📁 Cartella", path, "✔ Trovata" if exists else "— Assente"),
            tags=("presente" if exists else "assente",),
        )
        self.items.append((iid, "folder", path, "Aggiunta manualmente", exists))
        if exists:
            self.checked.add(iid)
            self._refresh_checks()
            # Aggiunge anche le sottocartelle interne (bin, tools, python, cache)
            _seen_subdirs: set[str] = {
                os.path.normpath(p).lower()
                for _, kind, p, _, _ in self.items
                if kind == "subdir" and isinstance(p, str)
            }
            for sub in INSTALL_SUBDIRS:
                full = os.path.normpath(os.path.join(path, sub))
                key  = full.lower()
                if key in _seen_subdirs:
                    continue
                sub_exists = os.path.isdir(full)
                sub_iid = self.tree.insert(
                    "", "end",
                    values=("📂 Sottocartella", full, "✔ Trovata" if sub_exists else "— Assente"),
                    tags=("presente" if sub_exists else "assente",),
                )
                self.items.append((sub_iid, "subdir", full, f"Sottocartella {sub}", sub_exists))
                if sub_exists:
                    self.checked.add(sub_iid)
            self._refresh_checks()
            n = sum(1 for *_, e in self.items if e)
            self.status_var.set(f"Cartella aggiunta manualmente — {n} elemento/i trovati.")
        else:
            messagebox.showwarning(
                "Cartella non trovata",
                f"La cartella selezionata non esiste:\n{path}\n\n"
                "È stata aggiunta alla lista come assente.",
            )

    def _select_all(self):
        for iid, *_, exists in self.items:
            if exists:
                self.checked.add(iid)
        self._refresh_checks()

    def _deselect_all(self):
        self.checked.clear()
        self._refresh_checks()

    def _delete(self):
        if getattr(self, "_deep_running", False):
            messagebox.showinfo(
                "Scansione in corso",
                "La scansione profonda è ancora in esecuzione.\n"
                "Attendere il completamento prima di eliminare.",
            )
            return
        to_delete = [x for x in self.items if x[0] in self.checked and x[4]]
        if not to_delete:
            messagebox.showinfo("Nessuna selezione", "Nessun elemento selezionato.")
            return

        folders   = [x for x in to_delete if x[1] == "folder"]
        subdirs   = [x for x in to_delete if x[1] == "subdir"]
        shortcuts = [x for x in to_delete if x[1] == "shortcut"]
        regs      = [x for x in to_delete if x[1] == "reg"]
        regvals   = [x for x in to_delete if x[1] == "regval"]

        summary = ""
        if folders:
            summary += "Cartelle installazione (cestino):\n"
            summary += "\n".join(f"  📁 {x[2]}" for x in folders) + "\n\n"
        if subdirs:
            summary += "Sottocartelle (cestino):\n"
            summary += "\n".join(f"  📂 {x[2]}" for x in subdirs) + "\n\n"
        if shortcuts:
            summary += "Collegamenti (cestino):\n"
            summary += "\n".join(f"  🔗 {x[2]}" for x in shortcuts) + "\n\n"
        if regs:
            summary += "Chiavi registro (eliminate):\n"
            summary += "\n".join(f"  🔑 HKCU\\{x[2]}" for x in regs) + "\n\n"
        if regvals:
            summary += "Valori registro (eliminati):\n"
            summary += "\n".join(f"  📋 {x[3]}" for x in regvals) + "\n\n"

        if not messagebox.askyesno(
            "Conferma eliminazione",
            f"Verranno eliminati {len(to_delete)} elementi:\n\n{summary.strip()}\n\n"
            "Cartelle e collegamenti → cestino.\n"
            "Chiavi e valori registro → eliminati definitivamente.\n\n"
            "Continuare?",
            icon="warning",
        ):
            return

        errors = []
        ok_count = 0

        for iid, kind, path, _label, _ in to_delete:
            if kind in ("folder", "subdir"):
                assert isinstance(path, str)
                if os.path.isdir(path):
                    ok = send_to_recycle(path)
                    if ok:
                        ok_count += 1
                    else:
                        errors.append(f"Impossibile spostare nel cestino: {path}")
                else:
                    ok_count += 1  # già sparita
            elif kind == "shortcut":
                assert isinstance(path, str)
                if os.path.isfile(path):
                    ok = send_to_recycle(path)
                    if ok:
                        ok_count += 1
                    else:
                        errors.append(f"Impossibile spostare nel cestino: {path}")
                else:
                    ok_count += 1
            elif kind == "reg":
                assert isinstance(path, str)
                if reg_key_exists(path):
                    ok = delete_reg_key_recursive(path)
                    if ok:
                        ok_count += 1
                    else:
                        errors.append(f"Impossibile eliminare chiave: HKCU\\{path}")
                else:
                    ok_count += 1
            elif kind == "regval":
                assert isinstance(path, tuple)
                subkey, value_name = path
                if reg_value_exists(subkey, value_name):
                    ok = delete_reg_value(subkey, value_name)
                    if ok:
                        ok_count += 1
                    else:
                        errors.append(f"Impossibile eliminare valore: HKCU\\{subkey} → {value_name}")
                else:
                    ok_count += 1

        notify_shell()

        if errors:
            messagebox.showwarning(
                "Completato con errori",
                f"{ok_count} elemento/i eliminati.\n\nErrori:\n" + "\n".join(errors),
            )
        else:
            messagebox.showinfo(
                "Completato",
                f"✔ {ok_count} elemento/i eliminati con successo.",
            )

        # Aggiorna la vista
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.checked.clear()
        self.items.clear()
        self._scan()


if __name__ == "__main__":
    if sys.platform != "win32":
        print("Questo script funziona solo su Windows.")
        sys.exit(1)
    app = CleanupApp()
    app.mainloop()
