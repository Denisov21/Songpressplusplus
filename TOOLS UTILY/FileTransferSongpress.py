#!/usr/bin/env python3
#
# FileTransferSongpress — sostituisce un file nella cartella di installazione
# di Songpress (SongpressPlusPlus), con backup, pulizia della cache e
# gestione dei permessi di root.
#
# Copyright (C) 2026  Denisov21
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301  USA.
#

import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path


class FileTransferGUI:

    def __init__(self, root):
        self.root = root

        self.root.title("Trasferimento file Songpress")
        self.root.geometry("780x720")
        self.root.resizable(False, False)

        self.file_origine = None
        self.cartella_destinazione = Path("/usr/lib/python3/dist-packages/songpressplusplus")
        self.ricerca_in_corso = False

        # Rileva il comando per esecuzione privilegiata
        # (imposta anche self.in_snap, self.in_flatpak, self.in_sandbox)
        self.comando_privilegiato = self._rileva_comando_privilegiato()

        # Rileva se il programma è stato avviato da terminale
        # (usa self.in_sandbox impostato sopra)
        self.avviato_da_terminale = self._rileva_avvio_da_terminale()

        self.crea_interfaccia()


    def _rileva_avvio_da_terminale(self):
        """Rileva se il programma è stato avviato da un terminale reale
        (bash, zsh, konsole, gnome-terminal, ecc.) e non da un IDE come
        Thonny, IDLE, VS Code o simili.

        Risale la catena dei processi padre fino a 8 livelli.
        """

        # Salva info di debug per eventuale visualizzazione
        self.debug_catena_processi = []

        # 1. Se ci sono variabili d'ambiente di Thonny, NON è terminale
        if os.environ.get("THONNY_USER_DIR"):
            self.debug_catena_processi.append("[Env] THONNY_USER_DIR trovata")
            return False

        if os.environ.get("THONNY_FRONTEND_LOCATION"):
            self.debug_catena_processi.append("[Env] THONNY_FRONTEND_LOCATION trovata")
            return False

        # 2. Sandbox Snap/Flatpak di un IDE
        if self.in_sandbox:
            snap_name = os.environ.get("SNAP_NAME", "").lower()
            flatpak_id = os.environ.get("FLATPAK_ID", "").lower()
            ide_keywords = ["thonny", "idle", "pycharm", "code",
                            "atom", "sublime", "spyder"]
            for parola in ide_keywords:
                if parola in snap_name or parola in flatpak_id:
                    self.debug_catena_processi.append(
                        f"[Sandbox] IDE '{parola}' in snap/flatpak"
                    )
                    return False

        # Liste di nomi
        ide_names = [
            "thonny", "idle", "pycharm", "code", "atom",
            "sublime", "spyder", "geany", "eclipse", "netbeans",
            "wingide", "jupyter"
        ]

        terminal_names = [
            # Shell
            "bash", "zsh", "fish", "dash", "ksh", "tcsh",
            # Emulatori di terminale
            "konsole", "gnome-terminal", "xterm", "terminator",
            "tilix", "alacritty", "kitty", "urxvt", "rxvt",
            "xfce4-terminal", "lxterminal", "mate-terminal",
            "yakuake", "guake", "terminology", "cool-retro-term",
            "hyper", "wezterm", "foot", "qterminal", "deepin-terminal"
        ]

        # 3. Risali la catena dei processi padre (max 8 livelli)
        try:
            pid = os.getppid()

            for livello in range(8):

                try:
                    with open(f"/proc/{pid}/comm", "r", encoding="utf-8") as f:
                        nome = f.read().strip().lower()
                except Exception:
                    break

                self.debug_catena_processi.append(
                    f"Livello {livello}: PID {pid} → '{nome}'"
                )

                # Controlla IDE
                for ide in ide_names:
                    if ide in nome:
                        self.debug_catena_processi.append(
                            f"  → riconosciuto come IDE ('{ide}')"
                        )
                        return False

                # Controlla terminali (match esatto o startswith)
                for term in terminal_names:
                    if nome == term or nome.startswith(term):
                        self.debug_catena_processi.append(
                            f"  → riconosciuto come TERMINALE ('{term}')"
                        )
                        return True

                # Sale al padre successivo
                try:
                    with open(f"/proc/{pid}/status", "r", encoding="utf-8") as f:
                        prossimo_pid = None
                        for riga in f:
                            if riga.startswith("PPid:"):
                                prossimo_pid = int(riga.split()[1])
                                break

                    if prossimo_pid is None or prossimo_pid <= 1:
                        self.debug_catena_processi.append(
                            "  → raggiunto init/systemd, stop"
                        )
                        break

                    pid = prossimo_pid

                except Exception:
                    break

        except Exception as e:
            self.debug_catena_processi.append(f"[Errore] {e}")

        # 4. Fallback finale: isatty
        try:
            is_tty = sys.stdin.isatty() and sys.stdout.isatty()
            self.debug_catena_processi.append(
                f"[Fallback] stdin.isatty()={sys.stdin.isatty()}, "
                f"stdout.isatty()={sys.stdout.isatty()}"
            )
            return is_tty
        except Exception:
            return False


    def _rileva_comando_privilegiato(self):
        """Trova quale comando è disponibile per l'esecuzione con privilegi"""

        # Rileva se siamo dentro una sandbox (Snap, Flatpak)
        self.in_snap = bool(
            os.environ.get("SNAP")
            or os.environ.get("SNAP_NAME")
            or os.environ.get("SNAP_INSTANCE_NAME")
        )

        self.in_flatpak = bool(
            os.environ.get("FLATPAK_ID")
            or Path("/.flatpak-info").exists()
        )

        self.in_sandbox = self.in_snap or self.in_flatpak

        # STRATEGIA 1: Percorsi assoluti (più affidabile)
        # Prova prima pkexec (grafico), poi sudo
        percorsi_da_provare = [
            "/usr/bin/pkexec",
            "/usr/local/bin/pkexec",
            "/bin/pkexec",
            "/usr/bin/sudo",
            "/usr/local/bin/sudo",
            "/bin/sudo",
        ]

        for percorso in percorsi_da_provare:
            try:
                if Path(percorso).exists():
                    return percorso
            except Exception:
                pass

        # STRATEGIA 2: Prova a eseguire direttamente il comando
        # Se il binario è nel PATH ma Path.exists() fallisce (sandbox strane),
        # subprocess può comunque trovarlo tramite il PATH del sistema
        for comando in ["pkexec", "sudo"]:
            try:
                risultato = subprocess.run(
                    [comando, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if risultato.returncode == 0:
                    return comando
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
            except Exception:
                continue

        # STRATEGIA 3: which come ultimo fallback
        for comando in ["pkexec", "sudo"]:
            try:
                risultato = subprocess.run(
                    ["which", comando],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if risultato.returncode == 0 and risultato.stdout.strip():
                    return risultato.stdout.strip()
            except Exception:
                continue

        # STRATEGIA 4: Con PATH esplicito aggiornato
        env_pulito = os.environ.copy()
        env_pulito["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:" + env_pulito.get("PATH", "")

        for comando in ["pkexec", "sudo"]:
            try:
                risultato = subprocess.run(
                    [comando, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    env=env_pulito
                )
                if risultato.returncode == 0:
                    return comando
            except Exception:
                continue

        return None


    def _esegui_privilegiato(self, comando_args):
        """Esegue un comando con privilegi elevati usando pkexec o sudo."""

        if self.comando_privilegiato is None:

            if self.in_snap:
                messaggio = (
                    "Thonny è installato come Snap e la sua "
                    "sandbox impedisce l'uso di sudo/pkexec.\n\n"
                    "SOLUZIONE 1 (consigliata):\n"
                    "Chiudi Thonny e lancia il programma da un "
                    "terminale normale:\n\n"
                    "    python3 ~/Scaricati/FileTransferSongpress.py\n\n"
                    "SOLUZIONE 2:\n"
                    "Usa File > Genera script per creare uno "
                    "script bash da eseguire in un terminale."
                )
            elif self.in_flatpak:
                messaggio = (
                    "Thonny è installato come Flatpak e la sua "
                    "sandbox impedisce l'uso di sudo/pkexec.\n\n"
                    "SOLUZIONE 1 (consigliata):\n"
                    "Chiudi Thonny e lancia il programma da un "
                    "terminale normale:\n\n"
                    "    python3 ~/Scaricati/FileTransferSongpress.py\n\n"
                    "SOLUZIONE 2:\n"
                    "Usa File > Genera script per creare uno "
                    "script bash da eseguire in un terminale."
                )
            else:
                messaggio = (
                    "Nessun comando per privilegi elevati "
                    "disponibile sul sistema.\n\n"
                    "Verifica che pkexec sia installato:\n"
                    "    sudo apt install pkexec\n\n"
                    "Oppure usa File > Genera script per creare "
                    "uno script bash da eseguire in un terminale."
                )

            raise FileNotFoundError(messaggio)

        # PATH esteso per assicurarsi che il comando venga trovato
        env_esteso = os.environ.copy()
        env_esteso["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:" + env_esteso.get("PATH", "")

        comando_completo = [self.comando_privilegiato] + comando_args

        return subprocess.run(
            comando_completo,
            text=True,
            capture_output=True,
            env=env_esteso
        )


    # ========================================================
    # INTERFACCIA
    # ========================================================

    def crea_interfaccia(self):

        # ----------------------------------------------------
        # BARRA DEI MENU
        # ----------------------------------------------------

        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # Menu File
        menu_file = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=menu_file)
        menu_file.add_command(label="Genera script bash...", command=self.genera_script)
        menu_file.add_separator()
        menu_file.add_command(label="Esci", command=self.esci)

        # Menu ?
        menu_help = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="?", menu=menu_help)
        menu_help.add_command(label="Guida", command=self.mostra_guida)
        menu_help.add_command(label="Licenza", command=self.mostra_licenza)
        menu_help.add_separator()
        menu_help.add_command(label="Debug rilevamento...", command=self.mostra_debug)

        tk.Label(
            self.root,
            text="Trasferimento file Songpress",
            font=("Arial", 22, "bold")
        ).pack(pady=(25, 5))

        tk.Label(
            self.root,
            text="Il file manterrà il suo nome originale e verrà pulita la cache",
            font=("Arial", 12)
        ).pack(pady=(0, 10))


        # ----------------------------------------------------
        # BANNER TERMINALE (solo se lanciato da terminale)
        # ----------------------------------------------------

        if self.avviato_da_terminale:

            frame_banner = tk.Frame(
                self.root,
                bg="#d1e7dd",
                relief="solid",
                borderwidth=1
            )
            frame_banner.pack(fill="x", padx=35, pady=(0, 15))

            tk.Label(
                frame_banner,
                text="✓ PROGRAMMA AVVIATO DA TERMINALE",
                font=("Arial", 11, "bold"),
                fg="#0f5132",
                bg="#d1e7dd"
            ).pack(pady=(8, 2))

            tk.Label(
                frame_banner,
                text=(
                    "Hai accesso completo a sudo/pkexec.\n"
                    "Il trasferimento file funzionerà direttamente dalla GUI."
                ),
                font=("Arial", 9),
                fg="#0f5132",
                bg="#d1e7dd",
                justify="center"
            ).pack(pady=(0, 8))

        else:

            # Banner arancione se NON da terminale (avviso)
            frame_banner = tk.Frame(
                self.root,
                bg="#fff3cd",
                relief="solid",
                borderwidth=1
            )
            frame_banner.pack(fill="x", padx=35, pady=(0, 15))

            tk.Label(
                frame_banner,
                text="⚠ PROGRAMMA NON AVVIATO DA TERMINALE",
                font=("Arial", 11, "bold"),
                fg="#664d03",
                bg="#fff3cd"
            ).pack(pady=(8, 2))

            tk.Label(
                frame_banner,
                text=(
                    "Se il trasferimento fallisce per problemi di permessi,\n"
                    "lancia il programma da un terminale oppure usa "
                    "\"GENERA SCRIPT BASH\"."
                ),
                font=("Arial", 9),
                fg="#664d03",
                bg="#fff3cd",
                justify="center"
            ).pack(pady=(0, 8))


        # ----------------------------------------------------
        # FILE ORIGINE
        # ----------------------------------------------------

        frame_origine = tk.LabelFrame(
            self.root,
            text=" 1. File da trasferire ",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=15
        )

        frame_origine.pack(
            fill="x",
            padx=35,
            pady=5
        )

        self.origine_var = tk.StringVar(
            value="Nessun file selezionato"
        )

        tk.Label(
            frame_origine,
            textvariable=self.origine_var,
            anchor="w",
            justify="left",
            fg="#174ea6"
        ).pack(
            side="left",
            fill="x",
            expand=True
        )

        self.seleziona_file_button = tk.Button(
            frame_origine,
            text="Seleziona file...",
            command=self.seleziona_file,
            width=18
        )

        self.seleziona_file_button.pack(
            side="right"
        )


        # ----------------------------------------------------
        # DESTINAZIONE
        # ----------------------------------------------------

        frame_destinazione = tk.LabelFrame(
            self.root,
            text=" 2. Cartella di destinazione ",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=15
        )

        frame_destinazione.pack(
            fill="x",
            padx=35,
            pady=10
        )

        self.destinazione_var = tk.StringVar(
            value=str(self.cartella_destinazione)
        )

        tk.Label(
            frame_destinazione,
            textvariable=self.destinazione_var,
            anchor="w",
            justify="left",
            fg="#174ea6"
        ).pack(
            side="left",
            fill="x",
            expand=True
        )

        frame_bottoni_dest = tk.Frame(frame_destinazione)
        frame_bottoni_dest.pack(side="right", fill="x")

        self.seleziona_destinazione_button = tk.Button(
            frame_bottoni_dest,
            text="Seleziona cartella...",
            command=self.seleziona_destinazione,
            width=18
        )

        self.seleziona_destinazione_button.pack(
            side="left",
            padx=5
        )


        # ----------------------------------------------------
        # ANTEPRIMA
        # ----------------------------------------------------

        frame_anteprima = tk.LabelFrame(
            self.root,
            text=" Anteprima ",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=10
        )

        frame_anteprima.pack(
            fill="x",
            padx=35,
            pady=5
        )

        self.anteprima_var = tk.StringVar(
            value="Seleziona file"
        )

        tk.Label(
            frame_anteprima,
            textvariable=self.anteprima_var,
            anchor="w",
            justify="left",
            fg="#198754"
        ).pack(
            fill="x"
        )


        # ----------------------------------------------------
        # PULSANTI
        # ----------------------------------------------------

        frame_pulsanti = tk.Frame(self.root)
        frame_pulsanti.pack(pady=18)

        self.trasferisci_button = tk.Button(
            frame_pulsanti,
            text="TRASFERISCI FILE",
            command=self.trasferisci_file,
            bg="#198754",
            fg="white",
            activebackground="#146c43",
            activeforeground="white",
            font=("Arial", 11, "bold"),
            width=24,
            height=2
        )

        self.trasferisci_button.grid(
            row=0,
            column=0,
            padx=8
        )

        self.ripristina_button = tk.Button(
            frame_pulsanti,
            text="RIPRISTINA ORIGINALE",
            command=self.ripristina_originale,
            bg="#dc3545",
            fg="white",
            activebackground="#b02a37",
            activeforeground="white",
            font=("Arial", 11, "bold"),
            width=24,
            height=2
        )

        self.ripristina_button.grid(
            row=0,
            column=1,
            padx=8
        )

        # Pulsante GENERA SCRIPT BASH (blu)
        self.genera_script_button = tk.Button(
            frame_pulsanti,
            text="GENERA SCRIPT BASH",
            command=self.genera_script,
            bg="#0d6efd",
            fg="white",
            activebackground="#0a58ca",
            activeforeground="white",
            font=("Arial", 10, "bold"),
            width=50,
            height=1
        )

        self.genera_script_button.grid(
            row=1,
            column=0,
            columnspan=2,
            padx=8,
            pady=(10, 0)
        )


        # ----------------------------------------------------
        # STATO
        # ----------------------------------------------------

        self.stato_var = tk.StringVar(
            value="Pronto."
        )

        tk.Label(
            self.root,
            textvariable=self.stato_var,
            fg="#555555",
            font=("Arial", 10)
        ).pack(pady=(5, 5))


        # ----------------------------------------------------
        # INFORMAZIONI
        # ----------------------------------------------------

        tk.Label(
            self.root,
            text=(
                "Il nome del file non viene modificato.\n"
                "Se esiste già, viene creato automaticamente un backup con estensione .backup\n"
                "La cache Python (.pyc) verrà pulita automaticamente dopo il trasferimento."
            ),
            fg="#777777",
            font=("Arial", 9)
        ).pack()


    # ========================================================
    # SELEZIONA FILE
    # ========================================================

    def seleziona_file(self):

        file_scelto = filedialog.askopenfilename(
            title="Seleziona il file da trasferire",
            filetypes=[
                ("File Python", "*.py"),
                ("Tutti i file", "*.*")
            ]
        )

        if not file_scelto:
            return

        self.file_origine = Path(file_scelto)
        self.origine_var.set(str(self.file_origine))
        self.aggiorna_anteprima()


    # ========================================================
    # SELEZIONA DESTINAZIONE
    # ========================================================

    def seleziona_destinazione(self):

        cartella = filedialog.askdirectory(
            title="Seleziona la cartella di destinazione"
        )

        if not cartella:
            return

        self.cartella_destinazione = Path(cartella)
        self.destinazione_var.set(str(self.cartella_destinazione))
        self.aggiorna_anteprima()


    # ========================================================
    # ANTEPRIMA
    # ========================================================

    def aggiorna_anteprima(self):

        if self.file_origine is None:
            self.anteprima_var.set("Seleziona file")
            return

        destinazione = (
            self.cartella_destinazione /
            self.file_origine.name
        )

        self.anteprima_var.set(
            f"Destinazione:\n{destinazione}"
        )


    # ========================================================
    # CONTROLLA SE SERVE SUDO
    # ========================================================

    def richiede_sudo(self, percorso):

        # In ambienti sandbox (Snap) i controlli di permessi possono
        # essere inaffidabili. Se il percorso è in una zona di sistema
        # tipica, usiamo sempre sudo per sicurezza.
        percorso_str = str(percorso)
        zone_sistema = [
            "/usr/",
            "/etc/",
            "/opt/",
            "/var/",
            "/lib/",
            "/lib64/",
            "/boot/",
            "/root/"
        ]

        for zona in zone_sistema:
            if percorso_str.startswith(zona):
                return True

        try:

            if percorso.exists():
                return not os.access(
                    str(percorso),
                    os.W_OK
                )

            parent = percorso.parent

            while not parent.exists():
                parent = parent.parent

            return not os.access(
                str(parent),
                os.W_OK
            )

        except Exception:
            return True


    # ========================================================
    # COPIA CON SUDO
    # ========================================================

    def copia_sudo(self, origine, destinazione):

        try:

            risultato = self._esegui_privilegiato(
                ["cp", str(origine), str(destinazione)]
            )

            if risultato.returncode != 0:

                errore = risultato.stderr.strip()

                if not errore:
                    errore = "Errore durante la copia."

                messagebox.showerror(
                    "Errore",
                    errore
                )

                return False

            return True

        except FileNotFoundError as e:

            self._mostra_errore_comando_mancante(str(e))

            return False

        except Exception as e:

            messagebox.showerror(
                "Errore",
                str(e)
            )

            return False


    # ========================================================
    # CREA BACKUP
    # ========================================================

    def crea_backup(self, destinazione):

        # Verifica esistenza con test privilegiato per compatibilità sandbox
        try:
            risultato_test = self._esegui_privilegiato(
                ["test", "-f", str(destinazione)]
            )
            file_esiste = risultato_test.returncode == 0
        except Exception:
            file_esiste = destinazione.exists()

        if not file_esiste:
            return True

        backup = Path(
            str(destinazione) + ".backup"
        )

        risposta = messagebox.askyesno(
            "File già esistente",
            f"Il file {destinazione.name} esiste già.\n\n"
            "Prima della sostituzione verrà creato:\n\n"
            f"{backup.name}\n\n"
            "Vuoi continuare?"
        )

        if not risposta:
            return False

        try:

            if self.richiede_sudo(destinazione):

                risultato = self._esegui_privilegiato(
                    ["cp", str(destinazione), str(backup)]
                )

                if risultato.returncode != 0:

                    messagebox.showerror(
                        "Errore backup",
                        risultato.stderr.strip()
                    )

                    return False

            else:

                shutil.copy2(
                    str(destinazione),
                    str(backup)
                )

            return True

        except Exception as e:

            messagebox.showerror(
                "Errore backup",
                str(e)
            )

            return False


    # ========================================================
    # PULISCI CACHE
    # ========================================================

    def pulisci_cache(self, cartella_destinazione):
        """Pulisce i file .pyc compilati dalla cache"""

        try:

            # Elimina file .pyc con privilegi (se serve)
            try:
                self._esegui_privilegiato(
                    [
                        "find",
                        str(cartella_destinazione),
                        "-name",
                        "*.pyc",
                        "-type",
                        "f",
                        "-delete"
                    ]
                )
            except Exception:
                # Fallback: prova senza privilegi
                subprocess.run(
                    [
                        "find",
                        str(cartella_destinazione),
                        "-name",
                        "*.pyc",
                        "-type",
                        "f",
                        "-delete"
                    ],
                    capture_output=True,
                    text=True
                )

            # Tenta di eliminare __pycache__
            pycache_dir = cartella_destinazione / "__pycache__"

            # Usa sempre il comando privilegiato per __pycache__ in /usr/lib
            if str(cartella_destinazione).startswith(("/usr/", "/etc/", "/opt/")):
                try:
                    self._esegui_privilegiato(
                        ["rm", "-rf", str(pycache_dir)]
                    )
                except Exception:
                    pass
            elif pycache_dir.exists():
                shutil.rmtree(str(pycache_dir))

            return True

        except Exception as e:

            messagebox.showwarning(
                "Avviso cache",
                f"Difficoltà nel pulire la cache:\n{str(e)}\n\n"
                "Il trasferimento è comunque completato."
            )

            return False


    # ========================================================
    # TRASFERISCI FILE
    # ========================================================

    def trasferisci_file(self):

        if self.file_origine is None:

            messagebox.showwarning(
                "File mancante",
                "Seleziona il file da trasferire."
            )

            return

        if not self.file_origine.exists():

            messagebox.showerror(
                "File non trovato",
                f"Il file non esiste:\n\n"
                f"{self.file_origine}"
            )

            return

        # Nota: non controlliamo exists() sulla cartella perché in ambienti
        # sandbox (es. Thonny installato via Snap) Path.exists() può
        # restituire False anche per cartelle di sistema esistenti.
        # Se la cartella non esiste davvero, sudo cp restituirà un errore chiaro.


        destinazione = (
            self.cartella_destinazione /
            self.file_origine.name
        )


        risposta = messagebox.askyesno(
            "Conferma trasferimento",

            "Il file verrà trasferito mantenendo "
            "il nome originale.\n"
            "La cache Python verrà pulita.\n\n"

            f"Origine:\n"
            f"{self.file_origine}\n\n"

            f"Destinazione:\n"
            f"{destinazione}\n\n"

            "Continuare?"
        )

        if not risposta:
            return


        self.disabilita_pulsanti()

        try:

            # BACKUP
            if not self.crea_backup(destinazione):
                return

            # COPIA
            self.stato_var.set("Trasferimento in corso...")
            self.root.update()

            if self.richiede_sudo(destinazione):
                successo = self.copia_sudo(
                    self.file_origine,
                    destinazione
                )
            else:
                try:
                    shutil.copy2(
                        str(self.file_origine),
                        str(destinazione)
                    )
                    successo = True
                except Exception as e:
                    messagebox.showerror("Errore", str(e))
                    successo = False

            if not successo:
                return

            # PULISCI CACHE
            self.stato_var.set("Pulizia cache in corso...")
            self.root.update()
            self.pulisci_cache(self.cartella_destinazione)

            self.stato_var.set("Trasferimento completato.")

            backup = Path(str(destinazione) + ".backup")

            testo_backup = f"\n\nBackup:\n{backup}" if backup.exists() else ""

            messagebox.showinfo(
                "Completato",

                "Trasferimento completato correttamente.\n\n"
                f"File:\n{self.file_origine.name}\n\n"
                f"Destinazione:\n{destinazione}\n\n"
                "Cache Python pulita."
                f"{testo_backup}"
            )

        finally:
            self.abilita_pulsanti()


    # ========================================================
    # RIPRISTINA ORIGINALE
    # ========================================================

    def ripristina_originale(self):

        if self.file_origine is None:

            messagebox.showwarning(
                "File non selezionato",
                "Seleziona prima il file originale "
                "che vuoi ripristinare."
            )

            return

        destinazione = (
            self.cartella_destinazione /
            self.file_origine.name
        )

        backup = Path(str(destinazione) + ".backup")

        # Controllo backup con test privilegiato per compatibilità sandbox
        backup_esiste = False
        try:
            risultato_test = self._esegui_privilegiato(
                ["test", "-f", str(backup)]
            )
            backup_esiste = risultato_test.returncode == 0
        except Exception:
            backup_esiste = backup.exists()

        if not backup_esiste:

            messagebox.showerror(
                "Backup non trovato",

                "Non esiste un backup per questo file.\n\n"
                f"File:\n{destinazione}\n\n"
                f"Backup cercato:\n{backup}"
            )

            return

        risposta = messagebox.askyesno(
            "Ripristina originale",

            "Vuoi ripristinare il file originale?\n\n"
            f"Backup:\n{backup}\n\n"
            f"Verrà ripristinato in:\n{destinazione}\n\n"
            "Il file modificato attualmente presente "
            "verrà sostituito."
        )

        if not risposta:
            return

        self.disabilita_pulsanti()

        try:

            self.stato_var.set("Ripristino dell'originale...")
            self.root.update()

            if self.richiede_sudo(destinazione):

                risultato = self._esegui_privilegiato(
                    ["cp", str(backup), str(destinazione)]
                )

                if risultato.returncode != 0:
                    messagebox.showerror(
                        "Errore",
                        risultato.stderr.strip()
                    )
                    return

            else:

                shutil.copy2(
                    str(backup),
                    str(destinazione)
                )

            # Pulisci cache anche nel ripristino
            self.stato_var.set("Pulizia cache in corso...")
            self.root.update()
            self.pulisci_cache(self.cartella_destinazione)

            self.stato_var.set("Originale ripristinato.")

            messagebox.showinfo(
                "Ripristino completato",

                "Il file originale è stato "
                "ripristinato correttamente.\n\n"
                f"{destinazione}\n\n"
                "Cache Python pulita."
            )

        except Exception as e:
            messagebox.showerror(
                "Errore durante il ripristino",
                str(e)
            )

        finally:
            self.abilita_pulsanti()


    # ========================================================
    # MENU: DEBUG
    # ========================================================

    def mostra_debug(self):
        """Mostra informazioni sul rilevamento terminale/sandbox"""

        finestra = tk.Toplevel(self.root)
        finestra.title("Debug rilevamento")
        finestra.geometry("650x520")
        finestra.resizable(False, False)
        finestra.transient(self.root)

        tk.Label(
            finestra,
            text="Informazioni di debug",
            font=("Arial", 14, "bold")
        ).pack(pady=(15, 10))

        # Riepilogo stato
        stato_text = (
            f"Avviato da terminale: "
            f"{'SÌ' if self.avviato_da_terminale else 'NO'}\n"
            f"In sandbox Snap: {'SÌ' if self.in_snap else 'NO'}\n"
            f"In sandbox Flatpak: {'SÌ' if self.in_flatpak else 'NO'}\n"
            f"Comando privilegiato: {self.comando_privilegiato or 'NESSUNO'}\n"
            f"PID processo: {os.getpid()}\n"
            f"PID processo padre (PPID): {os.getppid()}"
        )

        frame_stato = tk.LabelFrame(
            finestra,
            text=" Stato attuale ",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=10
        )
        frame_stato.pack(fill="x", padx=20, pady=5)

        tk.Label(
            frame_stato,
            text=stato_text,
            justify="left",
            anchor="w",
            font=("Courier", 10)
        ).pack(fill="x")

        # Catena processi
        frame_catena = tk.LabelFrame(
            finestra,
            text=" Catena processi analizzata ",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=10
        )
        frame_catena.pack(fill="both", expand=True, padx=20, pady=5)

        scrollbar = tk.Scrollbar(frame_catena)
        scrollbar.pack(side="right", fill="y")

        text_catena = tk.Text(
            frame_catena,
            wrap="word",
            font=("Courier", 9),
            yscrollcommand=scrollbar.set,
            bg="#f8f9fa",
            padx=8,
            pady=8,
            height=10
        )
        text_catena.pack(fill="both", expand=True)
        scrollbar.config(command=text_catena.yview)

        if self.debug_catena_processi:
            contenuto = "\n".join(self.debug_catena_processi)
        else:
            contenuto = "(nessuna informazione disponibile)"

        text_catena.insert("1.0", contenuto)
        text_catena.config(state="disabled")

        # Pulsante chiudi
        tk.Button(
            finestra,
            text="Chiudi",
            command=finestra.destroy,
            width=15,
            bg="#0d6efd",
            fg="white",
            activebackground="#0a58ca",
            activeforeground="white",
            font=("Arial", 10, "bold")
        ).pack(pady=10)


    # ========================================================
    # MENU: GENERA SCRIPT
    # ========================================================

    def genera_script(self):
        """Crea uno script bash che l'utente può eseguire in un terminale"""

        if self.file_origine is None:
            messagebox.showwarning(
                "File mancante",
                "Seleziona prima il file da trasferire."
            )
            return

        destinazione = (
            self.cartella_destinazione /
            self.file_origine.name
        )

        backup = Path(str(destinazione) + ".backup")

        # Chiedi dove salvare lo script
        percorso_script = filedialog.asksaveasfilename(
            title="Salva script bash",
            defaultextension=".sh",
            initialfile=f"trasferisci_{self.file_origine.stem}.sh",
            filetypes=[
                ("Script Bash", "*.sh"),
                ("Tutti i file", "*.*")
            ]
        )

        if not percorso_script:
            return

        # Contenuto dello script
        contenuto_script = f"""#!/bin/bash
# Script generato automaticamente da FileTransferSongpress
# Trasferisce {self.file_origine.name} nella cartella di Songpress
# ATTENZIONE: eseguire con: bash "{percorso_script}"

set -e  # Ferma in caso di errore

ORIGINE="{self.file_origine}"
DESTINAZIONE="{destinazione}"
BACKUP="{backup}"
CARTELLA="{self.cartella_destinazione}"

echo "==========================================="
echo "  Trasferimento file Songpress"
echo "==========================================="
echo ""
echo "Origine:      $ORIGINE"
echo "Destinazione: $DESTINAZIONE"
echo ""

# Verifica che il file origine esista
if [ ! -f "$ORIGINE" ]; then
    echo "ERRORE: File origine non trovato: $ORIGINE"
    exit 1
fi

# Verifica che la cartella destinazione esista
if [ ! -d "$CARTELLA" ]; then
    echo "ERRORE: Cartella destinazione non trovata: $CARTELLA"
    exit 1
fi

# Backup del file esistente (se presente)
if [ -f "$DESTINAZIONE" ]; then
    echo "Creazione backup: $BACKUP"
    sudo cp "$DESTINAZIONE" "$BACKUP"
    echo "  OK"
fi

# Copia del nuovo file
echo "Copia del file..."
sudo cp "$ORIGINE" "$DESTINAZIONE"
echo "  OK"

# Pulizia cache Python
echo "Pulizia cache Python..."
sudo find "$CARTELLA" -name "*.pyc" -type f -delete 2>/dev/null || true
sudo rm -rf "$CARTELLA/__pycache__" 2>/dev/null || true
echo "  OK"

echo ""
echo "==========================================="
echo "  Trasferimento completato!"
echo "==========================================="
echo ""
echo "File trasferito: $DESTINAZIONE"
if [ -f "$BACKUP" ]; then
    echo "Backup salvato: $BACKUP"
fi
echo ""
echo "Ora puoi riavviare Songpress."
"""

        try:
            with open(percorso_script, "w", encoding="utf-8") as f:
                f.write(contenuto_script)

            # Rende lo script eseguibile
            os.chmod(percorso_script, 0o755)

            # Mostra finestra personalizzata con pulsante copia
            self._mostra_finestra_script_creato(percorso_script)

        except Exception as e:
            messagebox.showerror(
                "Errore",
                f"Impossibile creare lo script:\n\n{str(e)}"
            )


    def _mostra_errore_comando_mancante(self, messaggio):
        """Mostra finestra di errore quando sudo/pkexec non è disponibile,
        con pulsante per copiare il comando suggerito"""

        # Determina quale comando suggerire in base al contesto
        if self.in_sandbox:
            comando_da_copiare = "python3 ~/Scaricati/FileTransferSongpress.py"
            etichetta_comando = "Comando da eseguire in un terminale:"
        else:
            comando_da_copiare = "sudo apt install pkexec"
            etichetta_comando = "Comando da eseguire in un terminale:"

        finestra = tk.Toplevel(self.root)
        finestra.title("Comando non disponibile")
        finestra.geometry("560x400")
        finestra.resizable(False, False)
        finestra.transient(self.root)
        finestra.grab_set()

        # Icona di errore + titolo
        tk.Label(
            finestra,
            text="⚠ Comando non disponibile",
            font=("Arial", 13, "bold"),
            fg="#dc3545"
        ).pack(pady=(20, 10))

        # Area messaggio
        frame_messaggio = tk.Frame(finestra)
        frame_messaggio.pack(fill="both", expand=True, padx=25, pady=5)

        testo_messaggio = tk.Text(
            frame_messaggio,
            wrap="word",
            font=("Arial", 10),
            height=10,
            padx=10,
            pady=8,
            bg="#f8f9fa",
            relief="flat",
            borderwidth=1
        )
        testo_messaggio.insert("1.0", messaggio)
        testo_messaggio.config(state="disabled")
        testo_messaggio.pack(fill="both", expand=True)

        # Separatore
        tk.Frame(finestra, height=1, bg="#cccccc").pack(
            fill="x", padx=25, pady=8
        )

        # Etichetta del comando
        tk.Label(
            finestra,
            text=etichetta_comando,
            font=("Arial", 9, "bold"),
            anchor="w"
        ).pack(fill="x", padx=25)

        # Comando in campo selezionabile
        entry_comando = tk.Entry(
            finestra,
            font=("Courier", 10),
            fg="#212529",
            bg="#f8f9fa",
            relief="solid",
            borderwidth=1
        )
        entry_comando.insert(0, comando_da_copiare)
        entry_comando.config(state="readonly")
        entry_comando.pack(fill="x", padx=25, pady=6)

        # Feedback copia
        feedback_var = tk.StringVar(value="")
        tk.Label(
            finestra,
            textvariable=feedback_var,
            font=("Arial", 9, "italic"),
            fg="#198754"
        ).pack()

        def copia_comando():
            finestra.clipboard_clear()
            finestra.clipboard_append(comando_da_copiare)
            finestra.update()
            feedback_var.set("✓ Comando copiato negli appunti!")
            finestra.after(2500, lambda: feedback_var.set(""))

        # Pulsanti
        frame_pulsanti = tk.Frame(finestra)
        frame_pulsanti.pack(pady=12)

        tk.Button(
            frame_pulsanti,
            text="📋 Copia comando",
            command=copia_comando,
            bg="#0d6efd",
            fg="white",
            activebackground="#0a58ca",
            activeforeground="white",
            font=("Arial", 10, "bold"),
            width=20,
            padx=10
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            frame_pulsanti,
            text="OK",
            command=finestra.destroy,
            width=12,
            padx=10
        ).grid(row=0, column=1, padx=5)


    def _mostra_finestra_script_creato(self, percorso_script):
        """Mostra una finestra con il comando bash e un pulsante per copiarlo"""

        comando_bash = f'bash "{percorso_script}"'

        finestra = tk.Toplevel(self.root)
        finestra.title("Script creato")
        finestra.geometry("520x360")
        finestra.resizable(False, False)
        finestra.transient(self.root)
        finestra.grab_set()

        # Icona/titolo
        tk.Label(
            finestra,
            text="✓ Script bash creato correttamente",
            font=("Arial", 12, "bold"),
            fg="#198754"
        ).pack(pady=(20, 10))

        # Percorso
        frame_percorso = tk.Frame(finestra)
        frame_percorso.pack(fill="x", padx=25, pady=5)

        tk.Label(
            frame_percorso,
            text="Percorso:",
            font=("Arial", 9, "bold"),
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            frame_percorso,
            text=percorso_script,
            font=("Arial", 9),
            anchor="w",
            fg="#174ea6",
            wraplength=470,
            justify="left"
        ).pack(fill="x")

        # Separatore
        tk.Frame(finestra, height=1, bg="#cccccc").pack(
            fill="x", padx=25, pady=10
        )

        # Istruzioni
        tk.Label(
            finestra,
            text="Per eseguirlo, apri un terminale e incolla il comando:",
            font=("Arial", 9),
            anchor="w"
        ).pack(fill="x", padx=25)

        # Comando in evidenza (selezionabile)
        entry_comando = tk.Entry(
            finestra,
            font=("Courier", 10),
            fg="#212529",
            bg="#f8f9fa",
            relief="solid",
            borderwidth=1
        )
        entry_comando.insert(0, comando_bash)
        entry_comando.config(state="readonly")
        entry_comando.pack(fill="x", padx=25, pady=8)

        # Etichetta feedback copia
        feedback_var = tk.StringVar(value="")
        tk.Label(
            finestra,
            textvariable=feedback_var,
            font=("Arial", 9, "italic"),
            fg="#198754"
        ).pack()

        # Funzione per copiare negli appunti
        def copia_comando():
            finestra.clipboard_clear()
            finestra.clipboard_append(comando_bash)
            finestra.update()  # Forza il mantenimento negli appunti
            feedback_var.set("✓ Comando copiato negli appunti!")
            # Rimuove il feedback dopo 2 secondi
            finestra.after(2500, lambda: feedback_var.set(""))

        # Frame pulsanti
        frame_pulsanti = tk.Frame(finestra)
        frame_pulsanti.pack(pady=15)

        tk.Button(
            frame_pulsanti,
            text="📋 Copia comando",
            command=copia_comando,
            bg="#0d6efd",
            fg="white",
            activebackground="#0a58ca",
            activeforeground="white",
            font=("Arial", 10, "bold"),
            width=20,
            padx=10
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            frame_pulsanti,
            text="Chiudi",
            command=finestra.destroy,
            width=12,
            padx=10
        ).grid(row=0, column=1, padx=5)


    # ========================================================
    # MENU: ESCI
    # ========================================================

    def esci(self):

        risposta = messagebox.askyesno(
            "Conferma uscita",
            "Vuoi davvero uscire dal programma?"
        )

        if risposta:
            self.root.destroy()


    # ========================================================
    # MENU: GUIDA
    # ========================================================

    def mostra_guida(self):

        finestra_guida = tk.Toplevel(self.root)
        finestra_guida.title("Guida")
        finestra_guida.geometry("720x600")
        finestra_guida.resizable(False, False)
        finestra_guida.transient(self.root)

        # Titolo
        tk.Label(
            finestra_guida,
            text="Guida all'uso",
            font=("Arial", 18, "bold")
        ).pack(pady=(15, 10))

        # Area di testo scrollabile
        frame_testo = tk.Frame(finestra_guida)
        frame_testo.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        scrollbar = tk.Scrollbar(frame_testo)
        scrollbar.pack(side="right", fill="y")

        testo = tk.Text(
            frame_testo,
            wrap="word",
            font=("Arial", 10),
            yscrollcommand=scrollbar.set,
            padx=15,
            pady=15,
            bg="#f8f9fa",
            relief="flat"
        )
        testo.pack(fill="both", expand=True)
        scrollbar.config(command=testo.yview)

        # Contenuto della guida
        contenuto = (
            "A COSA SERVE\n"
            "\n"
            "Questo programma serve a sostituire un file all'interno "
            "della cartella di Songpress (installato in "
            "/usr/lib/python3/dist-packages/songpressplusplus). "
            "È utile per applicare modifiche o fix a file come "
            "Editor.py senza dover reinstallare l'intero pacchetto.\n"
            "\n"
            "\n"
            "COME USARLO — PASSO PER PASSO\n"
            "\n"
            "1. SELEZIONA IL FILE\n"
            "   Clicca su \"Seleziona file...\" nella sezione 1 e "
            "scegli il file Python modificato dal tuo computer "
            "(tipicamente dalla cartella Scaricati).\n"
            "\n"
            "2. VERIFICA LA DESTINAZIONE\n"
            "   La cartella di destinazione è già impostata su "
            "/usr/lib/python3/dist-packages/songpressplusplus. "
            "Se serve, puoi cambiarla con \"Seleziona cartella...\".\n"
            "\n"
            "3. CONTROLLA L'ANTEPRIMA\n"
            "   Nella sezione \"Anteprima\" vedrai il percorso "
            "completo dove verrà copiato il file. Il nome del file "
            "NON viene modificato: rimane identico all'originale.\n"
            "\n"
            "4. TRASFERISCI\n"
            "   Clicca sul pulsante verde \"TRASFERISCI FILE\". "
            "Il programma:\n"
            "   - Crea automaticamente un backup del file esistente "
            "(con estensione .backup)\n"
            "   - Copia il nuovo file al posto del vecchio\n"
            "   - Pulisce la cache Python (.pyc e __pycache__)\n"
            "\n"
            "5. RIAVVIA SONGPRESS\n"
            "   Chiudi Songpress se è aperto e riaprilo per "
            "vedere le modifiche.\n"
            "\n"
            "\n"
            "RIPRISTINO DEL FILE ORIGINALE\n"
            "\n"
            "Se qualcosa non funziona dopo il trasferimento, puoi "
            "sempre tornare indietro:\n"
            "\n"
            "1. Seleziona lo STESSO file che hai trasferito prima\n"
            "2. Assicurati che la destinazione sia la stessa\n"
            "3. Clicca sul pulsante rosso \"RIPRISTINA ORIGINALE\"\n"
            "\n"
            "Il programma userà il file .backup creato in precedenza "
            "per ripristinare la versione originale.\n"
            "\n"
            "\n"
            "PERMESSI DI AMMINISTRATORE\n"
            "\n"
            "La cartella di Songpress si trova in una zona di "
            "sistema (/usr/lib), quindi per modificarla servono "
            "i permessi di root. Il programma userà "
            "automaticamente pkexec (con finestra grafica per la "
            "password) oppure sudo, a seconda di cosa è "
            "disponibile sul sistema.\n"
            "\n"
            "\n"
            "SE USI THONNY INSTALLATO COME SNAP\n"
            "\n"
            "La sandbox di Snap blocca l'accesso a sudo e "
            "pkexec, quindi il trasferimento diretto NON "
            "funziona da Thonny Snap. Hai due opzioni:\n"
            "\n"
            "OPZIONE A (consigliata):\n"
            "Chiudi Thonny e lancia il programma da un "
            "terminale normale:\n"
            "    python3 ~/Scaricati/FileTransferSongpress.py\n"
            "\n"
            "OPZIONE B:\n"
            "Usa File > Genera script bash. Il programma "
            "creerà uno script .sh che potrai eseguire da "
            "un terminale con:\n"
            "    bash nome_script.sh\n"
            "\n"
            "\n"
            "IMPORTANTE\n"
            "\n"
            "- Il nome del file DEVE corrispondere a quello nella "
            "cartella di Songpress. Se trasferisci Editor.py, "
            "sostituirà l'Editor.py esistente.\n"
            "\n"
            "- Il backup viene creato con estensione .backup "
            "(es. Editor.py.backup). Non cancellarlo: serve per il "
            "ripristino.\n"
            "\n"
            "- Un aggiornamento di sistema (apt upgrade) potrebbe "
            "sovrascrivere le tue modifiche. In quel caso, "
            "ricopia il file con questo programma.\n"
            "\n"
            "- La pulizia della cache è importante: Python può "
            "usare versioni compilate vecchie (.pyc) invece del "
            "file appena copiato, e le modifiche non risulterebbero "
            "attive.\n"
            "\n"
            "\n"
            "COME LASCIARE IL PROGRAMMA\n"
            "\n"
            "Quando hai finito, chiudi la finestra normalmente "
            "oppure usa File > Esci. Non serve salvare nulla: "
            "il programma non mantiene uno stato tra un avvio "
            "e l'altro.\n"
            "\n"
            "Assicurati però di:\n"
            "- Aver verificato che Songpress si avvii correttamente "
            "dopo il trasferimento\n"
            "- Non cancellare i file .backup se pensi di dover "
            "ripristinare in futuro\n"
        )

        testo.insert("1.0", contenuto)
        testo.config(state="disabled")

        # Pulsante chiudi
        tk.Button(
            finestra_guida,
            text="Chiudi",
            command=finestra_guida.destroy,
            width=15,
            bg="#0d6efd",
            fg="white",
            activebackground="#0a58ca",
            activeforeground="white",
            font=("Arial", 10, "bold")
        ).pack(pady=15)


    # ========================================================
    # MENU: LICENZA
    # ========================================================

    def mostra_licenza(self):

        finestra_licenza = tk.Toplevel(self.root)
        finestra_licenza.title("Licenza")
        finestra_licenza.geometry("720x600")
        finestra_licenza.resizable(False, False)
        finestra_licenza.transient(self.root)

        # Titolo
        tk.Label(
            finestra_licenza,
            text="Licenza",
            font=("Arial", 18, "bold")
        ).pack(pady=(15, 10))

        # Area di testo scrollabile
        frame_testo = tk.Frame(finestra_licenza)
        frame_testo.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        scrollbar = tk.Scrollbar(frame_testo)
        scrollbar.pack(side="right", fill="y")

        testo = tk.Text(
            frame_testo,
            wrap="word",
            font=("Arial", 10),
            yscrollcommand=scrollbar.set,
            padx=15,
            pady=15,
            bg="#f8f9fa",
            relief="flat"
        )
        testo.pack(fill="both", expand=True)
        scrollbar.config(command=testo.yview)

        # Contenuto della licenza
        contenuto = (
            "FileTransferSongpress\n"
            "Copyright (C) 2026  Denisov21\n"
            "\n"
            "\n"
            "GNU GENERAL PUBLIC LICENSE, versione 2\n"
            "\n"
            "Questo programma è software libero: puoi ridistribuirlo "
            "e/o modificarlo secondo i termini della GNU General "
            "Public License come pubblicata dalla Free Software "
            "Foundation, nella versione 2 della licenza o (a tua "
            "scelta) in una versione successiva.\n"
            "\n"
            "Questo programma è distribuito nella speranza che sia "
            "utile, ma SENZA ALCUNA GARANZIA; senza neppure la "
            "garanzia implicita di COMMERCIABILITÀ o IDONEITÀ PER "
            "UN PARTICOLARE SCOPO. Vedi la GNU General Public "
            "License per maggiori dettagli.\n"
            "\n"
            "Dovresti aver ricevuto una copia della GNU General "
            "Public License insieme a questo programma. In caso "
            "contrario, vedi <https://www.gnu.org/licenses/>.\n"
            "\n"
            "\n"
            "IN BREVE (riepilogo informale, non sostituisce il testo "
            "della licenza)\n"
            "\n"
            "- Sei libero di usare, studiare, copiare e modificare "
            "questo programma.\n"
            "- Puoi ridistribuirlo, anche modificato, purché lo fai "
            "sotto la stessa licenza GPL e rendendo disponibile il "
            "codice sorgente.\n"
            "- Il programma è fornito senza alcuna garanzia.\n"
            "\n"
            "\n"
            "TESTO COMPLETO DELLA LICENZA\n"
            "\n"
            "Il testo integrale della GNU General Public License "
            "versione 2 si trova nel file COPYING distribuito insieme "
            "a questo programma, oppure online all'indirizzo:\n"
            "\n"
            "    https://www.gnu.org/licenses/old-licenses/gpl-2.0.html\n"
        )

        testo.insert("1.0", contenuto)
        testo.config(state="disabled")

        # Pulsante chiudi
        tk.Button(
            finestra_licenza,
            text="Chiudi",
            command=finestra_licenza.destroy,
            width=15,
            bg="#0d6efd",
            fg="white",
            activebackground="#0a58ca",
            activeforeground="white",
            font=("Arial", 10, "bold")
        ).pack(pady=15)


    # ========================================================
    # GESTIONE PULSANTI
    # ========================================================

    def disabilita_pulsanti(self):

        self.trasferisci_button.config(state="disabled")
        self.ripristina_button.config(state="disabled")
        self.genera_script_button.config(state="disabled")
        self.seleziona_file_button.config(state="disabled")
        self.seleziona_destinazione_button.config(state="disabled")


    def abilita_pulsanti(self):

        self.trasferisci_button.config(state="normal")
        self.ripristina_button.config(state="normal")
        self.genera_script_button.config(state="normal")
        self.seleziona_file_button.config(state="normal")
        self.seleziona_destinazione_button.config(state="normal")


# ============================================================
# AVVIO
# ============================================================

if __name__ == "__main__":

    # Se il programma è lanciato da un terminale vero (non da IDE),
    # stampa un messaggio informativo in grassetto verde.
    def _e_terminale_vero():
        try:
            if os.environ.get("THONNY_USER_DIR"):
                return False
            with open(
                f"/proc/{os.getppid()}/comm", "r", encoding="utf-8"
            ) as f:
                parent = f.read().strip().lower()
            ide_names = ["thonny", "idle", "pycharm", "code",
                         "atom", "sublime", "spyder", "geany"]
            for ide in ide_names:
                if ide in parent:
                    return False
            terminal_names = [
                "bash", "zsh", "fish", "dash", "ksh", "tcsh",
                "konsole", "gnome-terminal", "xterm", "terminator",
                "tilix", "alacritty", "kitty", "urxvt", "rxvt",
                "xfce4-terminal", "lxterminal", "mate-terminal",
                "yakuake", "guake", "terminology"
            ]
            for term in terminal_names:
                if term in parent:
                    return True
            return sys.stdin.isatty() and sys.stdout.isatty()
        except Exception:
            return False

    if _e_terminale_vero():

        print()
        print("\033[1;32m" + "=" * 60 + "\033[0m")
        print("\033[1;32m  ✓ PROGRAMMA AVVIATO DA TERMINALE\033[0m")
        print("\033[1;32m" + "=" * 60 + "\033[0m")
        print("\033[1;32m  Hai accesso completo a sudo/pkexec.\033[0m")
        print("\033[1;32m  Il trasferimento file funzionerà"
              " direttamente dalla GUI.\033[0m")
        print("\033[1;32m" + "=" * 60 + "\033[0m")
        print()

    finestra_principale = tk.Tk()
    app = FileTransferGUI(finestra_principale)
    finestra_principale.mainloop()
