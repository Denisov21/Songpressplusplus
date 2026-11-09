# coding: utf-8
"""Misura la dimensione dell'installazione di Songpress++ (per AddSize nei .nsi).

Chiede l'unita' di installazione (es. E:), trova la cartella di Songpress++,
somma i byte di tutti i file e mostra:
  - il totale e il dettaglio per sottocartella;
  - il valore in KB da scrivere in `AddSize` (con un piccolo margine);
  - un pulsante per copiare la riga completa, es.
    `AddSize 272349   ; spazio stimato: ~266 MB (uv + Python + pacchetti)`;
  - un pulsante per aggiornare `AddSize` (e la stima ~MB nel commento) nei
    file .nsi scelti (mantiene BOM UTF-8 e fine riga).

Solo libreria standard (tkinter). Pensato per Windows.

Copyright (c) 2026 Denisov21
License: GNU GPL v2 (SPDX-License-Identifier: GPL-2.0-only)
"""

import os
import re
import string
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_FOLDER = "Songpress++"
MARGIN = 1.05                      # +5% di margine sul valore suggerito

APP_TITLE = "Songpress++ - Misura installazione"
GPL2_URL = "https://www.gnu.org/licenses/old-licenses/gpl-2.0.html"
SONGPRESS_URL = "https://github.com/Denisov21/Songpressplusplus"
GUIDE_TEXT = """Guida rapida

Serve a ricavare il valore di AddSize per i file .nsi (spazio mostrato
dal wizard dell'installer).

1. Prepara l'installazione da misurare
   Installa Songpress++ su una macchina pulita: disinstalla ogni versione
   precedente (scegliendo di NON conservare la cartella Songpress), poi
   installa normalmente con l'installer. Usa l'installer della stessa
   architettura dei .nsi che vuoi aggiornare (x64 oppure x86).

2. Scegli l'unità
   Seleziona l'unità dove hai installato (es. E:). Il programma propone la
   cartella di Songpress++; se è diversa, usa "Sfoglia…" per sceglierla.

3. Premi "Misura"
   Viene sommata la dimensione in byte di tutti i file. Il dettaglio per
   sottocartella (bin, tools, python, Songpress…) e il totale compaiono
   nell'elenco. L'AddSize suggerito è il totale in KB con +5% di margine.

4. Usa il risultato
   - "Copia AddSize": copia solo il numero (es. 272349).
   - "Copia riga AddSize": copia la riga completa per il .nsi, es.
     AddSize 272349   ; spazio stimato: ~266 MB (uv + Python + pacchetti)
   - "Aggiorna .nsi…": scegli i file .nsi e aggiorna la riga AddSize
     (numero e stima ~MB nel commento). BOM UTF-8 e fine riga restano
     invariati.

Note
  - Misura x64 e x86 separatamente: le dimensioni possono differire.
  - Conta i byte dei file, non la "Dimensione su disco" di Esplora file
    (che è più alta perché conta i cluster interi).
  - Ricompila l'installer dopo aver cambiato AddSize.
"""
CREDITS_TEXT = f"""{APP_TITLE}

Strumento per misurare lo spazio occupato da un'installazione di
Songpress++ e ricavare il valore di AddSize per gli script NSIS.

Copyright (c) 2026 Denis Renzi

Crediti
  - Songpress: Luca Allulli - Skeed (http://www.skeed.it/songpress)
  - Songpress++ (fork): Denisov21
    {SONGPRESS_URL}

Licenza
  Questo programma è software libero: puoi ridistribuirlo e/o
  modificarlo secondo i termini della GNU General Public License,
  versione 2, come pubblicata dalla Free Software Foundation.

  Questo programma è distribuito nella speranza che sia utile, ma
  SENZA ALCUNA GARANZIA; senza neppure la garanzia implicita di
  COMMERCIABILITÀ o di IDONEITÀ PER UNO SCOPO PARTICOLARE. Vedi la
  GNU General Public License per ulteriori dettagli.

  Testo completo della licenza:
  {GPL2_URL}
"""


def list_drives():
    """Lettere di unita' presenti (A:..Z:)."""
    drives = []
    for letter in string.ascii_uppercase:
        root = f"{letter}:\\"
        if os.path.exists(root):
            drives.append(f"{letter}:")
    return drives


def guess_install_dir(drive):
    """Cartella di Songpress++ piu' probabile sull'unita' scelta."""
    user = os.environ.get("USERNAME", "")
    candidates = [
        os.path.join(drive + "\\", "Users", user, "AppData", "Local", APP_FOLDER),
        os.path.join(drive + "\\", APP_FOLDER),
        os.path.join(drive + "\\", "Program Files", APP_FOLDER),
    ]
    for c in candidates:
        if os.path.isdir(os.path.join(c, "bin")) or os.path.isdir(os.path.join(c, "tools")):
            return c
    for c in candidates:
        if os.path.isdir(c):
            return c
    return candidates[0]


def folder_size(path):
    """Somma dei byte dei file sotto path (i link simbolici non sono seguiti)."""
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                fp = os.path.join(root, name)
                if not os.path.islink(fp):
                    total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def measure(path):
    """Ritorna (totale_byte, [(nome, byte), ...]) con il dettaglio per cartella."""
    parts = []
    loose = 0
    with os.scandir(path) as it:
        for e in it:
            try:
                if e.is_dir(follow_symlinks=False):
                    parts.append((e.name, folder_size(e.path)))
                elif e.is_file(follow_symlinks=False):
                    loose += e.stat().st_size
            except OSError:
                pass
    if loose:
        parts.append(("(file nella radice)", loose))
    parts.sort(key=lambda x: -x[1])
    return sum(b for _n, b in parts), parts


def addsize_line(kb):
    """Riga `AddSize` completa, nel formato usato nei .nsi (valori calcolati)."""
    return f"AddSize {kb}   ; spazio stimato: ~{round(kb / 1024)} MB (uv + Python + pacchetti)"


def update_addsize(nsi_path, kb):
    """Sostituisce il numero di `AddSize` nel .nsi, mantenendo BOM e fine riga.

    Aggiorna anche la stima nel commento (`~NNN MB`) se presente sulla stessa riga.
    Ritorna True se la riga e' stata trovata e modificata.
    """
    raw = open(nsi_path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw[3:].decode("utf-8") if bom else raw.decode("utf-8")
    mb = round(kb / 1024)
    new_text, n = re.subn(r"(?m)^(\s*AddSize\s+)\d+([^\r\n]*)",
                          lambda m: f"{m.group(1)}{kb}" + re.sub(r"~\d+ MB", f"~{mb} MB", m.group(2)),
                          text, count=1)
    if n == 0:
        return False
    out = new_text.encode("utf-8")
    if bom:
        out = b"\xef\xbb\xbf" + out
    open(nsi_path, "wb").write(out)
    return True


def fmt_mb(b):
    return f"{b / 1024 / 1024:,.1f} MB"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("620x520")
        self.minsize(560, 460)
        self.suggested_kb = None
        self._build_menu()
        self._build()
        self._on_drive_change()

    def _build_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Esci", accelerator="Ctrl+Q", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Guida rapida", accelerator="F1", command=self._show_guide)
        help_menu.add_separator()
        help_menu.add_command(label="Crediti", command=self._show_credits)
        menubar.add_cascade(label="?", menu=help_menu)
        self.config(menu=menubar)
        self.bind_all("<Control-q>", lambda _e: self.destroy())
        self.bind_all("<F1>", lambda _e: self._show_guide())

    def _text_dialog(self, title, text, height, license_btn=False):
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.transient(self)
        dlg.resizable(False, False)
        txt = tk.Text(dlg, width=72, height=height, wrap="word", relief="flat", padx=12, pady=10)
        txt.insert("1.0", text)
        txt.config(state="disabled")
        txt.pack(fill="both", expand=True)
        row = ttk.Frame(dlg)
        row.pack(fill="x", padx=10, pady=(0, 10))
        if license_btn:
            ttk.Button(row, text="Licenza GNU GPL v2…", command=lambda: webbrowser.open(GPL2_URL)).pack(side="left")
        ttk.Button(row, text="Chiudi", command=dlg.destroy).pack(side="right")
        dlg.bind("<Escape>", lambda _e: dlg.destroy())
        dlg.grab_set()
        dlg.focus_set()

    def _show_guide(self):
        self._text_dialog("Guida rapida", GUIDE_TEXT, height=30)

    def _show_credits(self):
        self._text_dialog("Crediti", CREDITS_TEXT, height=22, license_btn=True)

    def _build(self):
        pad = {"padx": 10, "pady": 4}

        top = ttk.LabelFrame(self, text="Unità di installazione")
        top.pack(fill="x", **pad)

        row = ttk.Frame(top)
        row.pack(fill="x", padx=8, pady=6)
        ttk.Label(row, text="Unità:").pack(side="left")
        drives = list_drives()
        self.drive_var = tk.StringVar(value=("E:" if "E:" in drives else (drives[0] if drives else "C:")))
        self.drive_cb = ttk.Combobox(row, textvariable=self.drive_var, values=drives, width=6, state="readonly")
        self.drive_cb.pack(side="left", padx=(6, 12))
        self.drive_cb.bind("<<ComboboxSelected>>", lambda _e: self._on_drive_change())

        ttk.Label(top, text="Cartella di Songpress++:").pack(anchor="w", padx=8)
        row2 = ttk.Frame(top)
        row2.pack(fill="x", padx=8, pady=(2, 8))
        self.path_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.path_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row2, text="Sfoglia…", command=self._browse).pack(side="left", padx=(6, 0))

        self.measure_btn = ttk.Button(self, text="Misura", command=self._start)
        self.measure_btn.pack(**pad)

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", **pad)

        res = ttk.LabelFrame(self, text="Dettaglio")
        res.pack(fill="both", expand=True, **pad)
        self.tree = ttk.Treeview(res, columns=("size",), show="tree headings", height=8)
        self.tree.heading("#0", text="Cartella")
        self.tree.heading("size", text="Dimensione")
        self.tree.column("size", width=120, anchor="e")
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        self.total_var = tk.StringVar(value="Totale: —")
        self.addsize_var = tk.StringVar(value="AddSize suggerito: —")
        ttk.Label(self, textvariable=self.total_var, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12)
        ttk.Label(self, textvariable=self.addsize_var, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12)

        btns = ttk.Frame(self)
        btns.pack(fill="x", **pad)
        self.copy_btn = ttk.Button(btns, text="Copia AddSize", command=self._copy, state="disabled")
        self.copy_btn.pack(side="left")
        self.copyline_btn = ttk.Button(btns, text="Copia riga AddSize", command=self._copy_line, state="disabled")
        self.copyline_btn.pack(side="left", padx=6)
        self.nsi_btn = ttk.Button(btns, text="Aggiorna .nsi…", command=self._update_nsi, state="disabled")
        self.nsi_btn.pack(side="left", padx=6)

    def _on_drive_change(self):
        self.path_var.set(guess_install_dir(self.drive_var.get()))

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.path_var.get() or None,
                                    title="Cartella di installazione di Songpress++")
        if d:
            self.path_var.set(os.path.normpath(d))
            drive = os.path.splitdrive(self.path_var.get())[0]
            if drive:
                self.drive_var.set(drive.upper())

    def _start(self):
        path = self.path_var.get().strip()
        if not os.path.isdir(path):
            messagebox.showerror("Cartella non trovata", f"La cartella non esiste:\n{path}")
            return
        self.measure_btn.config(state="disabled")
        self.copy_btn.config(state="disabled")
        self.copyline_btn.config(state="disabled")
        self.nsi_btn.config(state="disabled")
        self.tree.delete(*self.tree.get_children())
        self.total_var.set("Totale: calcolo in corso…")
        self.addsize_var.set("AddSize suggerito: —")
        self.progress.start(12)
        threading.Thread(target=self._worker, args=(path,), daemon=True).start()

    def _worker(self, path):
        try:
            result = measure(path)
            self.after(0, self._done, result, None)
        except Exception as e:      # pylint: disable=broad-except
            self.after(0, self._done, None, e)

    def _done(self, result, err):
        self.progress.stop()
        self.measure_btn.config(state="normal")
        if err is not None:
            self.total_var.set("Totale: errore")
            messagebox.showerror("Errore", str(err))
            return
        total, parts = result
        for name, b in parts:
            self.tree.insert("", "end", text=name, values=(fmt_mb(b),))
        kb = total / 1024
        self.suggested_kb = int(kb * MARGIN)
        self.total_var.set(f"Totale: {total:,} byte  =  {kb:,.0f} KB  ({fmt_mb(total)})")
        self.addsize_var.set(f"AddSize suggerito (+{round((MARGIN - 1) * 100)}%): {self.suggested_kb}")
        if total == 0:
            messagebox.showwarning("Cartella vuota", "Nessun file trovato: controlla la cartella scelta.")
            return
        self.copy_btn.config(state="normal")
        self.copyline_btn.config(state="normal")
        self.nsi_btn.config(state="normal")

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(str(self.suggested_kb))
        messagebox.showinfo("Copiato", f"Valore {self.suggested_kb} copiato negli appunti.")

    def _copy_line(self):
        line = addsize_line(self.suggested_kb)
        self.clipboard_clear()
        self.clipboard_append(line)
        messagebox.showinfo("Copiato", f"Riga copiata negli appunti:\n\n{line}")

    def _update_nsi(self):
        files = filedialog.askopenfilenames(
            title="Scegli i file .nsi da aggiornare (stessa architettura dell'installazione misurata)",
            filetypes=[("Script NSIS", "*.nsi"), ("Tutti i file", "*.*")])
        if not files:
            return
        names = "\n".join(os.path.basename(f) for f in files)
        if not messagebox.askyesno("Conferma",
                                   f"Impostare AddSize = {self.suggested_kb} in:\n\n{names}\n\n"
                                   "(BOM UTF-8 e fine riga vengono mantenuti;\n"
                                   "se presente, viene aggiornata anche la stima ~MB nel commento)"):
            return
        ok, ko = [], []
        for f in files:
            try:
                (ok if update_addsize(f, self.suggested_kb) else ko).append(os.path.basename(f))
            except OSError as e:
                ko.append(f"{os.path.basename(f)} ({e})")
        msg = ""
        if ok:
            msg += "Aggiornati:\n" + "\n".join(ok)
        if ko:
            msg += ("\n\n" if msg else "") + "Riga AddSize non trovata / errore:\n" + "\n".join(ko)
        messagebox.showinfo("Risultato", msg)


if __name__ == "__main__":
    App().mainloop()
