#!/usr/bin/env python3
###############################################################
# Name:        trasferire_file_gui.py
# Purpose:     Interfaccia grafica per trasferire (con backup)
#              nel pacchetto Songpress++ di sistema.
# Author:      Denisov21
# License:     GNU GPL v2
###############################################################
#
# Chiede quale file trasferire e in quale cartella del pacchetto,
# poi: backup datato → copia → proprietario root:root + permessi 644.
# Se il file è un .py, rimuove anche il bytecode e lo ricompila.
#
# Privilegi: se non sei root usa pkexec (prompt grafico su KDE) oppure
# sudo. Puoi anche lanciare l'intera GUI con sudo/pkexec.
#
# Avvio:  python3 trasferire_file_gui.py
#
###############################################################

import ast
import datetime as _dt
import glob
import hashlib
import os
import platform
import py_compile
import re
import shlex
import shutil
import subprocess
import sys
import sysconfig

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

PKG_NAMES = ("songpressplusplus", "songpress")

# Suffisso backup: <nomefile>.bak-YYYYMMDD-HHMMSS
_BAK_RE = re.compile(r"\.bak-\d{8}-\d{6}$")


def original_name_from_backup(backup_path):
    """Nome del file originale ricavato dal nome di un backup datato."""
    return _BAK_RE.sub("", os.path.basename(backup_path))

IS_WINDOWS = os.name == "nt"
IS_MAC     = sys.platform == "darwin"
IS_LINUX   = sys.platform.startswith("linux")


# ── Rilevamento sistema operativo ──────────────────────────────────────────────

def _linux_distro():
    """Nome della distribuzione da /etc/os-release, se disponibile."""
    try:
        info = {}
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, _, v = line.partition("=")
                    info[k.strip()] = v.strip().strip('"')
        return info.get("PRETTY_NAME") or info.get("NAME") or "Linux"
    except Exception:
        return "Linux"


def detect_os():
    """Restituisce (family, label) dove family ∈ {'windows','macos','linux','unix'}."""
    if IS_WINDOWS:
        rel = platform.release()          # es. "10", "11"
        ver = platform.version()          # build
        label = f"Windows {rel}".strip()
        if ver:
            label += f" (build {ver})"
        return "windows", label
    if IS_MAC:
        return "macos", f"macOS {platform.mac_ver()[0] or platform.release()}".strip()
    if IS_LINUX:
        return "linux", f"{_linux_distro()} — {platform.machine()}"
    return "unix", f"{platform.system() or 'Unix'} {platform.release()}".strip()


def os_icon(family, label=""):
    """Icona per la famiglia di OS. Riconosce anche alcune distro Linux dal nome."""
    if family == "linux":
        # Considera solo il nome della distro (prima di ' — <arch>'),
        # così 'aarch64' non fa scattare per errore 'arch'.
        name = label.split(" — ", 1)[0].lower()
        distro_icons = (
            ("raspbian", "🍓"),
            ("raspberry", "🍓"),
            ("ubuntu", "🟠"),
            ("debian", "🌀"),
            ("linux mint", "🌿"),
            ("fedora", "🎩"),
            ("manjaro", "🥭"),
            ("arch", "🏹"),
            ("opensuse", "🦎"),
            ("suse", "🦎"),
        )
        for key, ic in distro_icons:
            if key in name:
                return ic
        return "🐧"
    return {
        "windows": "🪟",
        "macos": "🍎",
        "unix": "🖥️",
    }.get(family, "💻")


# ── Rilevamento cartelle candidate ─────────────────────────────────────────────

def candidate_base_dirs():
    bases = []
    for key in ("purelib", "platlib"):
        try:
            p = sysconfig.get_paths().get(key)
            if p:
                bases.append(p)
        except Exception:
            pass
    bases += [
        "/usr/lib/python3/dist-packages",
        "/usr/local/lib/python3/dist-packages",
    ]
    bases += [p for p in sys.path if p.endswith(("dist-packages", "site-packages"))]
    seen, out = set(), []
    for b in bases:
        if b and b not in seen and os.path.isdir(b):
            seen.add(b)
            out.append(b)
    return out


def find_via_dpkg():
    if not shutil.which("dpkg"):
        return []
    found = []
    for name in PKG_NAMES:
        try:
            r = subprocess.run(["dpkg", "-L", name],
                               capture_output=True, text=True, check=False)
            if r.returncode != 0:
                continue
            for line in r.stdout.splitlines():
                in_pkgs = ("dist-packages" in line or "site-packages" in line)
                if not in_pkgs:
                    continue
                # cartella del modulo installato (…/dist-packages/<pkg>)
                if os.path.isdir(line) and os.path.basename(line) == name:
                    found.append(line)
                # oppure la cartella che contiene i file del pacchetto
                elif os.path.isfile(line):
                    d = os.path.dirname(line)
                    if os.path.isdir(d):
                        found.append(d)
        except Exception:
            pass
    return found


def detect_targets():
    cands = []
    for base in candidate_base_dirs():
        for name in PKG_NAMES:
            d = os.path.join(base, name)
            if os.path.isdir(d):
                cands.append(d)
    cands += find_via_dpkg()
    seen, out = set(), []
    for d in cands:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def validate_source(path):
    """Verifica che il file esista. Se è un .py, ne controlla anche la sintassi."""
    if not path or not os.path.isfile(path):
        return False, "file inesistente"
    if not path.endswith(".py"):
        return True, "file presente"
    try:
        with open(path, "r", encoding="utf-8") as f:
            ast.parse(f.read())
        return True, "Python valido"
    except SyntaxError as e:
        return False, f"errore di sintassi: {e}"
    except Exception as e:
        return False, f"lettura fallita: {e}"


def file_sha256(path):
    """SHA-256 di un file, o None se illeggibile."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def human_size(n):
    """Dimensione in byte → stringa leggibile (es. '12.3 KiB')."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "?"
    for unit in ("B", "KiB", "MiB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GiB"


def file_info(path):
    """Stringa 'dimensione, modificato il ...' per un file, o '' se assente."""
    try:
        st = os.stat(path)
        when = _dt.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
        return f"{human_size(st.st_size)}, modificato il {when}"
    except Exception:
        return ""


# ── Elevazione privilegi ───────────────────────────────────────────────────────

def _is_windows_admin():
    """True se il processo ha privilegi di amministratore su Windows."""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def relaunch_as_admin():
    """Rilancia la GUI con privilegi di amministratore (Windows)."""
    try:
        import ctypes
        params = " ".join(f'"{a}"' for a in sys.argv)
        rc = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1)
        return rc > 32  # >32 = successo
    except Exception:
        return False


def privilege_runner():
    """Restituisce (mode, prefix_list).
    Unix: mode in {'root','pkexec','sudo','none'}.
    Windows: mode in {'admin','user'} (prefix sempre vuoto: si opera in-process)."""
    if IS_WINDOWS:
        return ("admin" if _is_windows_admin() else "user"), []
    # os.geteuid esiste solo su Unix
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        return "root", []
    if shutil.which("pkexec"):
        return "pkexec", ["pkexec"]
    if shutil.which("sudo"):
        # sudo -n fallisce senza terminale; usiamo askpass se disponibile
        if os.environ.get("SUDO_ASKPASS"):
            return "sudo", ["sudo", "-A"]
        return "sudo", ["sudo"]
    return "none", []


# ── Operazioni native (in-process): usate su Windows e quando già root/admin ────

def native_install(src, dest_dir, do_backup=True):
    """Esegue backup → copia → permessi → pulizia bytecode → ricompilazione,
    direttamente in Python. Solleva un'eccezione in caso di errore."""
    dest_file = os.path.join(dest_dir, os.path.basename(src))
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{dest_file}.bak-{stamp}"
    log = []
    if do_backup and os.path.isfile(dest_file):
        shutil.copy2(dest_file, backup)
        log.append(f"backup creato: {backup}")
    shutil.copy2(src, dest_file)
    log.append(f"copiato in: {dest_file}")
    # Proprietario/permessi hanno senso solo su Unix
    if not IS_WINDOWS:
        try:
            os.chmod(dest_file, 0o644)
            _chown = getattr(os, "chown", None)
            if _chown and hasattr(os, "geteuid") and os.geteuid() == 0:
                _chown(dest_file, 0, 0)  # root:root
        except Exception as e:
            log.append(f"! impossibile impostare permessi/proprietario: {e}")
    _clean_and_compile(dest_dir, dest_file, log)
    return backup, log


def native_restore(backup_file, dest_dir):
    dest_file = os.path.join(dest_dir, original_name_from_backup(backup_file))
    log = []
    shutil.copy2(backup_file, dest_file)
    log.append(f"ripristinato in: {dest_file}")
    if not IS_WINDOWS:
        try:
            os.chmod(dest_file, 0o644)
            _chown = getattr(os, "chown", None)
            if _chown and hasattr(os, "geteuid") and os.geteuid() == 0:
                _chown(dest_file, 0, 0)
        except Exception as e:
            log.append(f"! impossibile impostare permessi/proprietario: {e}")
    _clean_and_compile(dest_dir, dest_file, log)
    return log


def _clean_and_compile(dest_dir, dest_file, log):
    if not dest_file.endswith(".py"):
        return  # bytecode/ricompilazione hanno senso solo per i .py
    stem = os.path.splitext(os.path.basename(dest_file))[0]
    for pyc in glob.glob(os.path.join(dest_dir, "__pycache__", f"{stem}.*.pyc")):
        try:
            os.remove(pyc)
        except OSError:
            pass
    py_compile.compile(dest_file, doraise=True)
    log.append("ricompilato (py_compile).")


def build_shell_command(src, dest_dir, do_backup=True):
    fname = os.path.basename(src)
    dest_file = os.path.join(dest_dir, fname)
    stem = os.path.splitext(fname)[0]
    cache_glob = os.path.join(dest_dir, "__pycache__", f"{stem}.*.pyc")
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{dest_file}.bak-{stamp}"
    parts = []
    if do_backup:
        # backup solo se il file esiste già
        parts.append(f"[ -f {shlex.quote(dest_file)} ] && "
                     f"cp -a {shlex.quote(dest_file)} {shlex.quote(backup)} || true")
    parts.append(f"cp {shlex.quote(src)} {shlex.quote(dest_file)}")
    parts.append(f"chown root:root {shlex.quote(dest_file)}")
    parts.append(f"chmod 644 {shlex.quote(dest_file)}")
    if fname.endswith(".py"):
        parts.append(f"rm -f {cache_glob}")
        parts.append(f"{shlex.quote(sys.executable)} -m py_compile {shlex.quote(dest_file)}")
    return " && ".join(parts), backup


def build_restore_command(backup_file, dest_dir):
    fname = original_name_from_backup(backup_file)
    dest_file = os.path.join(dest_dir, fname)
    stem = os.path.splitext(fname)[0]
    cache_glob = os.path.join(dest_dir, "__pycache__", f"{stem}.*.pyc")
    parts = [
        f"cp {shlex.quote(backup_file)} {shlex.quote(dest_file)}",
        f"chown root:root {shlex.quote(dest_file)}",
        f"chmod 644 {shlex.quote(dest_file)}",
    ]
    if fname.endswith(".py"):
        parts.append(f"rm -f {cache_glob}")
        parts.append(f"{shlex.quote(sys.executable)} -m py_compile {shlex.quote(dest_file)}")
    return " && ".join(parts)


# ── Applicazione GUI ───────────────────────────────────────────────────────────

class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.grid(sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.src_var  = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.dry_var  = tk.BooleanVar(value=False)

        row = 0
        ttk.Label(self, text="File da trasferire:"
                  ).grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1
        self.src_entry = ttk.Entry(self, textvariable=self.src_var)
        self.src_entry.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(2, 8))
        ttk.Button(self, text="📂 Sfoglia…", command=self.browse_src
                   ).grid(row=row, column=2, sticky="e", padx=(6, 0), pady=(2, 8))
        row += 1

        ttk.Label(self, text="Cartella del pacchetto (destinazione):"
                  ).grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1
        targets = detect_targets()
        self.dest_combo = ttk.Combobox(self, textvariable=self.dest_var,
                                       values=targets, state="normal")
        if targets:
            self.dest_combo.current(0)
        self.dest_combo.grid(row=row, column=0, sticky="ew", pady=(2, 8))
        dest_btns = ttk.Frame(self)
        dest_btns.grid(row=row, column=1, columnspan=2, sticky="e", padx=(6, 0), pady=(2, 8))
        ttk.Button(dest_btns, text="🔄 Aggiorna", command=self.refresh_targets
                   ).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(dest_btns, text="📂 Sfoglia…", command=self.browse_dest
                   ).grid(row=0, column=1)
        row += 1

        opts = ttk.Frame(self)
        opts.grid(row=row, column=0, columnspan=3, sticky="w")
        ttk.Checkbutton(opts, text="Simula (dry-run): non scrive nulla",
                        variable=self.dry_var).grid(row=0, column=0, sticky="w")
        row += 1

        btns = ttk.Frame(self)
        btns.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(8, 6))
        btns.columnconfigure(3, weight=1)
        self.verify_btn = ttk.Button(btns, text="🔍 Verifica", command=self.on_verify)
        self.verify_btn.grid(row=0, column=0, padx=(0, 6))
        self.install_btn = ttk.Button(btns, text="📤 Trasferire", command=self.on_install)
        self.install_btn.grid(row=0, column=1, padx=(0, 6))
        self.restore_btn = ttk.Button(btns, text="♻️ Ripristina backup…",
                                      command=self.on_restore)
        self.restore_btn.grid(row=0, column=2, padx=(0, 6))
        ttk.Button(btns, text="🚪 Esci", command=master.destroy
                   ).grid(row=0, column=4, sticky="e")
        row += 1

        logbar = ttk.Frame(self)
        logbar.grid(row=row, column=0, columnspan=3, sticky="ew")
        logbar.columnconfigure(0, weight=1)
        ttk.Label(logbar, text="Registro:").grid(row=0, column=0, sticky="w")
        ttk.Button(logbar, text="🧹 Pulisci", command=self.clear_log
                   ).grid(row=0, column=1, padx=(6, 0))
        ttk.Button(logbar, text="📋 Copia", command=self.copy_log
                   ).grid(row=0, column=2, padx=(6, 0))
        ttk.Button(logbar, text="💾 Salva…", command=self.save_log
                   ).grid(row=0, column=3, padx=(6, 0))
        row += 1
        self.log = scrolledtext.ScrolledText(self, height=12, wrap="word")
        self.log.grid(row=row, column=0, columnspan=3, sticky="nsew")
        self.rowconfigure(row, weight=1)
        self.log.tag_config("ok",    foreground="#1a7f37")
        self.log.tag_config("err",   foreground="#c01c28")
        self.log.tag_config("warn",  foreground="#b06000")
        self.log.tag_config("cmd",   foreground="#606060")
        self.log.configure(state="disabled")

        os_family, os_label = detect_os()
        self._log(f"Sistema operativo: {os_icon(os_family, os_label)} {os_label}")
        mode, _ = privilege_runner()
        self._log(f"Privilegi: {self._priv_desc(mode)}")
        if not detect_targets():
            self._log("! Nessuna cartella del pacchetto rilevata: indicala con «Sfoglia…».")

        # Verifica in tempo reale (con debounce) mentre si modifica sorgente/destinazione
        self._verify_after_id = None
        self.src_var.trace_add("write", self._schedule_verify)
        self.dest_var.trace_add("write", self._schedule_verify)
        # Invio nei campi = Verifica immediata
        self.src_entry.bind("<Return>", lambda e: self.on_verify())
        self.dest_combo.bind("<Return>", lambda e: self.on_verify())

        self.on_verify()

    # ── helper UI ──
    def _priv_desc(self, mode):
        return {
            "root":   "già root (scrittura diretta).",
            "pkexec": "verrà chiesta la password admin (pkexec).",
            "sudo":   "verrà usato sudo.",
            "none":   "NESSUN metodo di elevazione trovato: lancia la GUI con sudo/pkexec.",
            "admin":  "amministratore (scrittura diretta).",
            "user":   "utente normale: se la destinazione è protetta serviranno i "
                      "privilegi di amministratore.",
        }.get(mode, mode)

    def _log(self, msg, tag=None):
        # Deduce il colore dal prefisso se non specificato
        if tag is None:
            first = msg.lstrip()[:1]
            tag = {"✓": "ok", "✗": "err", "!": "warn", "→": "cmd"}.get(first)
        stamp = _dt.datetime.now().strftime("%H:%M:%S")
        self.log.configure(state="normal")
        self.log.insert("end", f"[{stamp}] ", "cmd")
        self.log.insert("end", msg + "\n", tag or "")
        self.log.see("end")
        self.log.configure(state="disabled")
        self.update_idletasks()

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def copy_log(self):
        text = self.log.get("1.0", "end").rstrip()
        self.clipboard_clear()
        self.clipboard_append(text)
        self._log("✓ Registro copiato negli appunti.")

    def save_log(self):
        p = filedialog.asksaveasfilename(
            title="Salva registro",
            defaultextension=".txt",
            initialfile="trasferire_log.txt",
            filetypes=[("Testo", "*.txt"), ("Tutti i file", "*.*")])
        if not p:
            return
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write(self.log.get("1.0", "end"))
            self._log(f"✓ Registro salvato in: {p}")
        except Exception as e:
            self._log(f"✗ Impossibile salvare il registro: {e}")

    def refresh_targets(self):
        targets = detect_targets()
        current = self.dest_var.get()
        self.dest_combo.configure(values=targets)
        if targets:
            if current not in targets:
                self.dest_combo.current(0)
            self._log(f"✓ Rilevate {len(targets)} cartella/e del pacchetto.")
        else:
            self._log("! Nessuna cartella del pacchetto rilevata: indicala con «Sfoglia…».")

    def _schedule_verify(self, *args):  # pylint: disable=unused-argument
        # Debounce: rimanda la verifica di 300 ms dall'ultima digitazione
        if self._verify_after_id is not None:
            try:
                self.after_cancel(self._verify_after_id)
            except Exception:
                pass
        self._verify_after_id = self.after(300, self.on_verify)

    def _set_busy(self, busy):
        state = "disabled" if busy else "normal"
        for b in (self.verify_btn, self.install_btn, self.restore_btn):
            b.configure(state=state)
        self.master["cursor"] = "watch" if busy else ""
        self.update_idletasks()

    def browse_src(self):
        start = os.path.dirname(self.src_var.get()) or os.path.expanduser("~")
        p = filedialog.askopenfilename(
            title="Scegli il file da trasferire",
            initialdir=start,
            filetypes=[("Tutti i file", "*.*"), ("Python", "*.py")])
        if p:
            self.src_var.set(p)
            self.on_verify()

    def browse_dest(self):
        start = self.dest_var.get() or "/usr/lib/python3/dist-packages"
        p = filedialog.askdirectory(title="Scegli la cartella del pacchetto",
                                    initialdir=start if os.path.isdir(start) else "/usr/lib")
        if p:
            self.dest_var.set(p)
            self.on_verify()

    # ── azioni ──
    def on_verify(self):
        self._verify_after_id = None
        src = os.path.expanduser(self.src_var.get().strip())
        dest = os.path.expanduser(self.dest_var.get().strip())
        ok_src, why = validate_source(src)
        self._log(("✓ Sorgente OK — " if ok_src else "✗ Sorgente NON valido — ") + why)
        if ok_src:
            info = file_info(src)
            if info:
                self._log(f"  {os.path.basename(src)}: {info}")
        if dest:
            if not os.path.isdir(dest):
                self._log(f"✗ Cartella inesistente: {dest}")
            elif ok_src:
                fname = os.path.basename(src)
                existing = os.path.join(dest, fname)
                if os.path.isfile(existing):
                    self._log(f"✓ Destinazione contiene già {fname}: {existing}")
                    info = file_info(existing)
                    if info:
                        self._log(f"  esistente: {info}")
                    # Confronto contenuti sorgente ↔ destinazione
                    h_src = file_sha256(src)
                    h_dst = file_sha256(existing)
                    if h_src and h_dst:
                        if h_src == h_dst:
                            self._log("✓ Sorgente e destinazione sono IDENTICI "
                                      "(già aggiornato: trasferimento non necessario).")
                        else:
                            self._log("! Sorgente e destinazione DIFFERISCONO "
                                      "(il trasferimento aggiornerà il file).")
                else:
                    self._log(f"• La cartella non contiene ancora {fname}: {dest}")

    def _run_privileged(self, shell_cmd):
        mode, prefix = privilege_runner()
        if mode == "none":
            messagebox.showerror(
                "Privilegi mancanti",
                "Non trovo pkexec né sudo.\nRilancia la GUI con:\n"
                "  pkexec python3 trasferire_file_gui.py")
            return False
        if mode == "root":
            argv = ["sh", "-c", shell_cmd]
        else:
            argv = prefix + ["sh", "-c", shell_cmd]
        self._log("→ " + " ".join(shlex.quote(a) for a in argv))
        try:
            r = subprocess.run(argv, capture_output=True, text=True)
        except Exception as e:
            self._log(f"✗ Esecuzione fallita: {e}")
            return False
        if r.stdout.strip():
            self._log(r.stdout.strip())
        if r.stderr.strip():
            self._log(r.stderr.strip())
        if r.returncode != 0:
            self._log(f"✗ Comando terminato con codice {r.returncode}.")
            return False
        return True

    def on_install(self):
        src = os.path.expanduser(self.src_var.get().strip())
        dest = os.path.expanduser(self.dest_var.get().strip())

        ok_src, why = validate_source(src)
        if not ok_src:
            messagebox.showerror("Sorgente non valido",
                                 f"Il file da trasferire non è valido:\n{why}")
            return
        if not os.path.isdir(dest):
            messagebox.showerror("Destinazione non valida",
                                 f"La cartella non esiste:\n{dest}")
            return

        fname = os.path.basename(src)
        dest_file = os.path.join(dest, fname)
        if not os.path.isfile(dest_file):
            if not messagebox.askyesno(
                    "Conferma",
                    f"Nella destinazione non c'è già un {fname}.\n"
                    f"Sei sicuro che «{dest}» sia la cartella corretta?\n\nProcedo comunque?"):
                return

        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        prospect_backup = f"{dest_file}.bak-{stamp}"

        if self.dry_var.get():
            self._log("── DRY-RUN: operazioni che verrebbero eseguite ──")
            if os.path.isfile(dest_file):
                self._log(f"backup: {prospect_backup}")
            self._log(f"copia: {src} → {dest_file}")
            if not IS_WINDOWS:
                self._log("permessi 644 + proprietario root:root (se root)")
            self._log("rimozione bytecode + ricompilazione (py_compile)")
            self._log("── nessuna modifica effettuata ──")
            return

        if not messagebox.askyesno(
                "Conferma trasferimento",
                f"Trasferisco:\n  {src}\n→\n  {dest_file}\n\n"
                f"Verrà creato un backup datato. Procedo?"):
            return

        self._log("── Trasferimento ──")
        self._set_busy(True)
        try:
            if IS_WINDOWS:
                self._install_native(src, dest)
            else:
                cmd, backup = build_shell_command(src, dest, do_backup=True)
                if self._run_privileged(cmd):
                    self._log("✓ Trasferimento completato.")
                    self._log(f"Backup (se il file esisteva): {backup}")
                    self._log("Chiudi e riavvia Songpress++ per applicare.")
                    messagebox.showinfo(
                        "Fatto",
                        "Trasferimento completato.\nRiavvia Songpress++ per applicare.\n\n"
                        "Nota: un futuro «apt upgrade» del pacchetto sovrascriverà il file.")
                else:
                    messagebox.showerror("Errore",
                                         "Trasferimento non riuscito. Vedi il registro.")
        finally:
            self._set_busy(False)

    # ── esecuzione nativa (Windows) ──
    def _install_native(self, src, dest):
        try:
            backup, log = native_install(src, dest, do_backup=True)
        except PermissionError:
            self._offer_admin_relaunch()
            return
        except Exception as e:
            self._log(f"✗ Trasferimento fallito: {e}")
            messagebox.showerror("Errore",
                                 f"Trasferimento non riuscito:\n{e}")
            return
        for line in log:
            self._log(line)
        self._log("✓ Trasferimento completato.")
        self._log(f"Backup (se il file esisteva): {backup}")
        messagebox.showinfo(
            "Fatto",
            "Trasferimento completato.\nRiavvia Songpress++ per applicare.")

    def _offer_admin_relaunch(self):
        self._log("✗ Permesso negato: la destinazione è protetta.")
        if messagebox.askyesno(
                "Privilegi insufficienti",
                "La cartella di destinazione richiede privilegi di amministratore.\n\n"
                "Vuoi rilanciare l'applicazione come amministratore?"):
            if relaunch_as_admin():
                self.master.destroy()
                sys.exit(0)
            else:
                messagebox.showerror(
                    "Errore",
                    "Impossibile rilanciare come amministratore.\n"
                    "Riavvia manualmente il programma con «Esegui come amministratore».")

    def on_restore(self):
        dest = os.path.expanduser(self.dest_var.get().strip())
        if not os.path.isdir(dest):
            messagebox.showerror("Destinazione non valida",
                                 f"La cartella non esiste:\n{dest}")
            return
        backups = sorted(glob.glob(os.path.join(dest, "*.bak-*")))
        if not backups:
            messagebox.showinfo("Nessun backup",
                                "Non ho trovato backup in questa cartella.")
            return
        self._log(f"Trovati {len(backups)} backup in {dest}.")
        chosen = filedialog.askopenfilename(
            title="Scegli il backup da ripristinare",
            initialdir=dest,
            initialfile=os.path.basename(backups[-1]),
            filetypes=[("Backup datati", "*.bak-*"),
                       ("Tutti i file", "*.*")])
        if not chosen:
            return
        target = os.path.join(dest, original_name_from_backup(chosen))
        if self.dry_var.get():
            self._log(f"── DRY-RUN ripristino da {chosen} ──")
            if IS_WINDOWS:
                self._log(f"copia: {chosen} → {target}")
                if target.endswith(".py"):
                    self._log("rimozione bytecode + ricompilazione (py_compile)")
            else:
                self._log(build_restore_command(chosen, dest))
            return
        if not messagebox.askyesno("Conferma ripristino",
                                   f"Ripristino:\n  {chosen}\n→\n  "
                                   f"{target}\n\nProcedo?"):
            return
        self._log("── Ripristino ──")
        self._set_busy(True)
        try:
            if IS_WINDOWS:
                try:
                    log = native_restore(chosen, dest)
                except PermissionError:
                    self._offer_admin_relaunch()
                    return
                except Exception as e:
                    self._log(f"✗ Ripristino fallito: {e}")
                    messagebox.showerror("Errore", f"Ripristino non riuscito:\n{e}")
                    return
                for line in log:
                    self._log(line)
                self._log("✓ Ripristino completato.")
                messagebox.showinfo("Fatto", "Ripristino completato.\nRiavvia Songpress++.")
            elif self._run_privileged(build_restore_command(chosen, dest)):
                self._log("✓ Ripristino completato.")
                messagebox.showinfo("Fatto", "Ripristino completato.\nRiavvia Songpress++.")
            else:
                messagebox.showerror("Errore", "Ripristino non riuscito. Vedi il registro.")
        finally:
            self._set_busy(False)


def main():
    root = tk.Tk()
    root.title("Trasferisci file — Songpress++")
    root.minsize(640, 480)
    try:
        ttk.Style().theme_use("clam")
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
