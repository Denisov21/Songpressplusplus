#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tooltip test — wxGTK / wxMSW
============================
Passa il mouse sopra ogni controllo e guarda DOVE compare il tooltip.
La tecnica giusta per te = quella che mostra il tooltip sui CHECKBOX
e sui RADIOBUTTON anche quando stanno DENTRO una StaticBox
(come nel tuo PreferencesDialog).

I colori del testo si adattano al tema (chiari su tema scuro), cosi'
sono leggibili anche sui temi scuri di Linux.
"""

import locale
import platform
import sys

import wx
import wx.adv
from wx.lib.scrolledpanel import ScrolledPanel

APP_NAME = "Tooltip test"
APP_VERSION = "1.0"
APP_DESC = (
    "Piccolo strumento di diagnostica per capire DOVE compaiono i tooltip "
    "su wxWidgets, in particolare su wxGTK (Linux) rispetto a wxMSW "
    "(Windows).\n\n"
    "Mette a confronto varie tecniche per applicare un tooltip a CheckBox e "
    "RadioButton, sia \"nudi\" sia dentro una StaticBox, cosi' da individuare "
    "l'unica che funziona in modo affidabile su tutte le piattaforme e da "
    "usare poi nel PreferencesDialog di Songpress++.")
APP_COPYRIGHT = "Copyright (C) 2026 Denisov21"

GUIDE_TEXT = (
    "GUIDA\n"
    "=====\n\n"
    "Scopo\n"
    "-----\n"
    "Trovare la tecnica giusta per mostrare i tooltip su checkbox e "
    "radiobutton, soprattutto quando stanno dentro una StaticBox come nel "
    "PreferencesDialog.\n\n"
    "Come si usa\n"
    "-----------\n"
    "Passa il mouse su ogni controllo e osserva se e dove compare il "
    "tooltip. Confronta le sezioni:\n\n"
    "  1) SANITY CHECK — TextCtrl e Button: su GTK il tooltip di norma "
    "compare. Serve solo a confermare che i tooltip funzionano nel tuo "
    "ambiente.\n\n"
    "  2) IL PROBLEMA — CheckBox e RadioButton \"nudi\", come nel codice "
    "attuale.\n\n"
    "  3) WORKAROUND — Tecnica A (tooltip anche sul panel padre) e Tecnica B "
    "(controllo dentro un mini-panel dedicato).\n\n"
    "  4) DENTRO StaticBox — Tecnica E: i controlli hanno come parent la "
    "StaticBox stessa (sbsizer.GetStaticBox()), non il panel. E' il modo "
    "corretto su wxGTK.\n\n"
    "Info sistema\n"
    "------------\n"
    "Dal menu \"?\" -> \"Info sistema\" apri una finestra che mostra il "
    "sistema operativo e le caratteristiche rilevabili dall'ambiente "
    "(Python, wxPython, toolkit, schermo, lingua). Utile da allegare a una "
    "segnalazione di bug: c'e' il bottone \"Copia negli appunti\".\n\n"
    "Regola pratica\n"
    "--------------\n"
    "Nel PreferencesDialog crea SEMPRE i controlli dentro una StaticBox "
    "usando come parent sbsizer.GetStaticBox() (la StaticBox), non self o il "
    "panel. Cosi' i tooltip compaiono e nessun controllo finisce fuori "
    "posto.")

LICENSE_TEXT = (
    APP_NAME + " — diagnostica tooltip wxGTK/wxMSW\n"
    + APP_COPYRIGHT + "\n\n"
    "Questo programma e' software libero: puoi ridistribuirlo e/o "
    "modificarlo secondo i termini della GNU General Public License come "
    "pubblicata dalla Free Software Foundation, versione 2 della Licenza, o "
    "(a tua scelta) una versione successiva.\n\n"
    "Questo programma e' distribuito nella speranza che sia utile, ma SENZA "
    "ALCUNA GARANZIA; senza neppure la garanzia implicita di "
    "COMMERCIABILITA' o IDONEITA' PER UN PARTICOLARE SCOPO. Vedi la GNU "
    "General Public License per maggiori dettagli.\n\n"
    "Dovresti aver ricevuto una copia della GNU General Public License "
    "insieme a questo programma; in caso contrario, vedi "
    "<https://www.gnu.org/licenses/>.")


# ---------------------------------------------------------------- temi
# Modalita' corrente del tema: "auto" segue il sistema, "light" e "dark"
# forzano rispettivamente il tema chiaro o scuro.
_THEME_MODE = "auto"

# "Ruoli" dei widget (memorizzati nel loro Name) per ricolorarli al cambio
# tema mantenendo i colori speciali di accento e testo secondario.
ROLE_ACCENT = "themed-accent"
ROLE_MUTED = "themed-muted"

LIGHT_THEME = {
    "bg": wx.Colour(240, 240, 240),
    "fg": wx.Colour(20, 20, 20),
    "accent": wx.Colour(60, 90, 200),
    "muted": wx.Colour(110, 110, 110),
    "input_bg": wx.Colour(255, 255, 255),
    "input_fg": wx.Colour(20, 20, 20),
}
DARK_THEME = {
    "bg": wx.Colour(45, 45, 48),
    "fg": wx.Colour(230, 230, 230),
    "accent": wx.Colour(120, 165, 255),
    "muted": wx.Colour(170, 170, 170),
    "input_bg": wx.Colour(30, 30, 30),
    "input_fg": wx.Colour(230, 230, 230),
}


def set_theme_mode(mode):
    """Imposta la modalita' tema: 'auto', 'light' o 'dark'."""
    global _THEME_MODE
    if mode in ("auto", "light", "dark"):
        _THEME_MODE = mode


def get_theme_mode():
    """Restituisce la modalita' tema corrente ('auto'/'light'/'dark')."""
    return _THEME_MODE


def _system_is_dark():
    """True se lo sfondo delle finestre di sistema e' scuro."""
    c = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
    lum = 0.299 * c.Red() + 0.587 * c.Green() + 0.114 * c.Blue()
    return lum < 128


def is_dark():
    """True se il tema EFFETTIVO attuale e' scuro (risolve 'auto')."""
    if _THEME_MODE == "dark":
        return True
    if _THEME_MODE == "light":
        return False
    return _system_is_dark()


def current_theme():
    """Il dizionario colori del tema effettivo corrente."""
    return DARK_THEME if is_dark() else LIGHT_THEME


def accent_colour():
    """Blu di accento leggibile sul tema corrente."""
    return current_theme()["accent"]


def muted_colour():
    """Grigio secondario leggibile sul tema corrente."""
    return current_theme()["muted"]


def apply_theme(win):
    """Applica il tema corrente a 'win' e ricorsivamente a tutti i figli.

    I controlli di input (TextCtrl) ricevono i colori di campo; gli altri
    ricevono sfondo/testo generici, tranne i widget con ruolo di accento o
    testo secondario, che mantengono il loro colore dedicato.
    """
    theme = current_theme()

    def _walk(w):
        name = w.GetName()
        if isinstance(w, wx.TextCtrl):
            w.SetBackgroundColour(theme["input_bg"])
            w.SetForegroundColour(theme["input_fg"])
        else:
            w.SetBackgroundColour(theme["bg"])
            if name == ROLE_ACCENT:
                w.SetForegroundColour(theme["accent"])
            elif name == ROLE_MUTED:
                w.SetForegroundColour(theme["muted"])
            else:
                w.SetForegroundColour(theme["fg"])
        for child in w.GetChildren():
            _walk(child)
        w.Refresh()

    _walk(win)


# ---------------------------------------------------------------- info sistema
def _os_pretty_name():
    """Nome descrittivo del sistema operativo.

    Su Linux legge PRETTY_NAME da /etc/os-release (es. 'Ubuntu 24.04.1 LTS'),
    su macOS/Windows compone una stringa leggibile.
    """
    sysname = platform.system()
    if sysname == "Linux":
        try:
            data = {}
            with open("/etc/os-release", encoding="utf-8") as f:
                for line in f:
                    if "=" in line:
                        key, _, val = line.partition("=")
                        data[key.strip()] = val.strip().strip('"')
            name = data.get("PRETTY_NAME") or data.get("NAME")
            if name:
                return name
        except OSError:
            pass
        return "Linux " + platform.release()
    if sysname == "Darwin":
        ver = platform.mac_ver()[0]
        return "macOS " + ver if ver else "macOS"
    if sysname == "Windows":
        return "Windows " + platform.release()
    return sysname or "sconosciuto"


def build_system_report():
    """Costruisce un report testuale (allineato) sull'ambiente corrente.

    Richiede che l'App wx sia gia' attiva (per i dati sullo schermo).
    """
    sections = []

    def section(title, pairs):
        # tiene solo le coppie con valore non vuoto
        clean = [(k, str(v)) for k, v in pairs if v not in (None, "")]
        if clean:
            sections.append((title, clean))

    # --- Sistema operativo ---
    section("Sistema operativo", [
        ("Nome", _os_pretty_name()),
        ("Famiglia", platform.system()),
        ("Release", platform.release()),
        ("Versione", platform.version()),
        ("Architettura", platform.machine()),
        ("Nome macchina (host)", platform.node()),
    ])

    # --- Python ---
    section("Python", [
        ("Versione", platform.python_version()),
        ("Implementazione", platform.python_implementation()),
        ("Eseguibile", sys.executable),
        ("Encoding default", sys.getdefaultencoding()),
    ])

    # --- wxPython / toolkit ---
    section("wxPython / toolkit", [
        ("wxPython", wx.version()),
        ("PlatformInfo", ", ".join(wx.PlatformInfo)),
    ])

    # --- Schermo (richiede App attiva) ---
    screen = []
    try:
        w, h = wx.GetDisplaySize()
        screen.append(("Risoluzione primaria", "%d x %d px" % (w, h)))
    except Exception:
        pass
    try:
        ppi = wx.GetDisplayPPI()
        screen.append(("DPI", "%d x %d" % (ppi.width, ppi.height)))
    except Exception:
        pass
    try:
        screen.append(("Profondita' colore", "%d bit" % wx.DisplayDepth()))
    except Exception:
        pass
    try:
        screen.append(("Numero display", str(wx.Display.GetCount())))
    except Exception:
        pass
    mode_label = {"auto": "automatico", "light": "chiaro", "dark": "scuro"}
    screen.append(("Tema (modalita')", mode_label.get(get_theme_mode(), "?")))
    screen.append(("Tema effettivo", "scuro" if is_dark() else "chiaro"))
    section("Schermo", screen)

    # --- Lingua / locale ---
    lang = []
    try:
        lang.append(("Locale Python", str(locale.getlocale())))
    except Exception:
        pass
    try:
        lang.append(("Encoding preferito", locale.getpreferredencoding(False)))
    except Exception:
        pass
    try:
        name = wx.Locale.GetLanguageName(wx.Locale.GetSystemLanguage())
        if name:
            lang.append(("Lingua di sistema (wx)", name))
    except Exception:
        pass
    section("Lingua", lang)

    # --- formattazione allineata ---
    all_pairs = [p for _, pairs in sections for p in pairs]
    width = max((len(k) for k, _ in all_pairs), default=0)
    lines = []
    for title, pairs in sections:
        lines.append(title)
        lines.append("-" * len(title))
        for key, val in pairs:
            lines.append("  " + key.ljust(width) + "  " + val)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------- dialog testo
class TextDialog(wx.Dialog):
    """Finestra con testo scorrevole di sola lettura (per Guida e Licenza)."""

    def __init__(self, parent, title, text):
        super().__init__(parent, title=title, size=wx.Size(560, 460),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        v = wx.BoxSizer(wx.VERTICAL)
        txt = wx.TextCtrl(self, value=text,
                          style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        v.Add(txt, 1, wx.EXPAND | wx.ALL, 8)
        btns = self.CreateButtonSizer(wx.OK)
        if btns:
            v.Add(btns, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.SetSizer(v)
        txt.SetInsertionPoint(0)
        apply_theme(self)


# ---------------------------------------------------------------- dialog info sistema
class SystemInfoDialog(wx.Dialog):
    """Finestra 'Info sistema': SO e caratteristiche dell'ambiente."""

    def __init__(self, parent):
        super().__init__(parent, title="Info sistema",
                         size=wx.Size(620, 520),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self._report = build_system_report()

        v = wx.BoxSizer(wx.VERTICAL)

        txt = wx.TextCtrl(
            self, value=self._report,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.HSCROLL)
        mono = wx.Font(wx.FontInfo(10).Family(wx.FONTFAMILY_TELETYPE))
        txt.SetFont(mono)
        v.Add(txt, 1, wx.EXPAND | wx.ALL, 8)

        h = wx.BoxSizer(wx.HORIZONTAL)
        copy_btn = wx.Button(self, label="Copia negli appunti")
        copy_btn.Bind(wx.EVT_BUTTON, self.on_copy)
        h.Add(copy_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        h.AddStretchSpacer()
        btns = self.CreateButtonSizer(wx.OK)
        if btns:
            h.Add(btns, 0, wx.ALIGN_CENTER_VERTICAL)
        v.Add(h, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.SetSizer(v)
        txt.SetInsertionPoint(0)
        apply_theme(self)

    def on_copy(self, _evt):
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(self._report))
            wx.TheClipboard.Close()


# ---------------------------------------------------------------- helpers
def heading(parent, sizer, text):
    sizer.AddSpacer(14)
    st = wx.StaticText(parent, label=text)
    f = st.GetFont()
    f.SetWeight(wx.FONTWEIGHT_BOLD)
    st.SetFont(f)
    sizer.Add(st, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
    sizer.Add(wx.StaticLine(parent), 0,
              wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 4)


def row(parent, sizer, control, note):
    hs = wx.BoxSizer(wx.HORIZONTAL)
    hs.Add(control, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
    lbl = wx.StaticText(parent, label=note)
    lbl.SetName(ROLE_MUTED)
    lbl.SetForegroundColour(muted_colour())
    hs.Add(lbl, 1, wx.ALIGN_CENTER_VERTICAL)
    sizer.Add(hs, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)


# ---------------------------------------------------------------- frame
class TooltipTestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Tooltip test — wxGTK / wxMSW",
                         size=wx.Size(760, 640))

        self._build_menubar()

        panel = ScrolledPanel(self)
        panel.SetupScrolling(scroll_x=False, scroll_y=True)
        v = wx.BoxSizer(wx.VERTICAL)

        plat = wx.StaticText(
            panel, label="platform = " + ", ".join(wx.PlatformInfo))
        plat.SetName(ROLE_ACCENT)
        plat.SetForegroundColour(accent_colour())
        v.Add(plat, 0, wx.ALL, 8)

        intro = wx.StaticText(
            panel,
            label=("Passa il mouse su ogni controllo: guarda dove compare "
                   "il tooltip.\n"
                   "La tecnica giusta per te = quella che mostra il tooltip "
                   "sui CHECKBOX dentro la StaticBox."))
        v.Add(intro, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # ---- 1) SANITY CHECK --------------------------------------------
        heading(panel, v, "1) SANITY CHECK — questi su GTK di norma funzionano")

        tc = wx.TextCtrl(panel, value="TextCtrl", size=wx.Size(120, -1))
        tc.SetToolTip("Tooltip sul TextCtrl  ->  [ATTESO: OK]")
        row(panel, v, tc, "TextCtrl, tooltip sul controllo  ->  [ATTESO: OK]")

        btn = wx.Button(panel, label="Button")
        btn.SetToolTip("Tooltip sul Button  ->  [ATTESO: OK]")
        row(panel, v, btn, "Button, tooltip sul controllo  ->  [ATTESO: OK]")

        # ---- 2) IL PROBLEMA ---------------------------------------------
        heading(panel, v, "2) IL PROBLEMA — come nel tuo codice ora")

        cb_bare = wx.CheckBox(panel, label="CheckBox nudo")
        cb_bare.SetToolTip("Tooltip sul CheckBox nudo  ->  [come ora]")
        row(panel, v, cb_bare,
            "CheckBox figlio del panel, tooltip sul checkbox  ->  [come ora]")

        rb_bare = wx.RadioButton(panel, label="RadioButton nudo",
                                 style=wx.RB_GROUP)
        rb_bare.SetToolTip("Tooltip sul RadioButton nudo  ->  [come ora]")
        row(panel, v, rb_bare,
            "RadioButton, tooltip sul radio  ->  [come ora]")

        # ---- 3) WORKAROUND fuori dalla StaticBox ------------------------
        heading(panel, v, "3) WORKAROUND — quale funziona da te?")

        cb_a = wx.CheckBox(panel, label="CheckBox — TECNICA A")
        cb_a.SetToolTip("Tooltip A (checkbox + panel padre)")
        row(panel, v, cb_a, "TECNICA A: tooltip su checkbox + panel padre")

        mini = wx.Panel(panel)
        mini_s = wx.BoxSizer(wx.HORIZONTAL)
        cb_b = wx.CheckBox(mini, label="CheckBox — TECNICA B")
        mini_s.Add(cb_b, 0, wx.ALL, 0)
        mini.SetSizer(mini_s)
        mini.SetToolTip("Tooltip B (sul mini-panel che avvolge il checkbox)")
        cb_b.SetToolTip("Tooltip B (sul checkbox)")
        row(panel, v, mini,
            "TECNICA B: checkbox in mini-panel dedicato, tooltip sul panel")

        # ---- 4) DENTRO StaticBox — come il tuo PreferencesDialog --------
        heading(panel, v, "4) DENTRO StaticBox — come il tuo PreferencesDialog")

        sb = wx.StaticBox(panel, label="StaticBox")
        sbs = wx.StaticBoxSizer(sb, wx.VERTICAL)
        box = sbs.GetStaticBox()   # * FIX CHIAVE: parent = StaticBox

        cb_e = wx.CheckBox(box, label="CheckBox — TECNICA E (parent = StaticBox)")
        cb_e.SetToolTip("Tooltip E: parent = StaticBox  ->  [ATTESO: OK]")
        sbs.Add(cb_e, 0, wx.ALL, 6)

        rb_e1 = wx.RadioButton(box, label="Radio A (E)", style=wx.RB_GROUP)
        rb_e1.SetToolTip("Tooltip Radio A (parent = StaticBox)")
        sbs.Add(rb_e1, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        rb_e2 = wx.RadioButton(box, label="Radio B (E)")
        rb_e2.SetToolTip("Tooltip Radio B (parent = StaticBox)")
        sbs.Add(rb_e2, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        v.Add(sbs, 0, wx.EXPAND | wx.ALL, 8)

        conclusion = wx.StaticText(
            panel,
            label=("Regola pratica per il tuo PreferencesDialog: crea SEMPRE i "
                   "controlli dentro una StaticBox con\n"
                   "parent = sbsizer.GetStaticBox() (la StaticBox), non con "
                   "parent = self/panel. Cosi' i tooltip compaiono\n"
                   "e non ci sono piu' controlli fuori posto su wxGTK."))
        v.Add(conclusion, 0, wx.ALL, 8)
        v.AddSpacer(12)

        panel.SetSizer(v)
        self.CentreOnScreen()
        apply_theme(self)

    # ---- menu -----------------------------------------------------------
    def _build_menubar(self):
        mb = wx.MenuBar()

        file_menu = wx.Menu()
        file_menu.Append(wx.ID_EXIT, "&Esci\tCtrl+Q", "Chiudi il programma")
        mb.Append(file_menu, "&File")

        view_menu = wx.Menu()
        self.mi_theme_auto = view_menu.AppendRadioItem(
            wx.ID_ANY, "Tema &automatico (sistema)",
            "Segui il tema chiaro/scuro del sistema")
        self.mi_theme_light = view_menu.AppendRadioItem(
            wx.ID_ANY, "Tema &chiaro", "Forza il tema chiaro")
        self.mi_theme_dark = view_menu.AppendRadioItem(
            wx.ID_ANY, "Tema &scuro", "Forza il tema scuro")
        mb.Append(view_menu, "&Visualizza")

        # spunta la voce corrispondente alla modalita' attuale
        {"auto": self.mi_theme_auto,
         "light": self.mi_theme_light,
         "dark": self.mi_theme_dark}[get_theme_mode()].Check(True)

        help_menu = wx.Menu()
        item_guide = help_menu.Append(wx.ID_HELP, "&Guida", "Come si usa")
        item_lic = help_menu.Append(wx.ID_ANY, "&Licenza",
                                    "Licenza GNU GPL")
        item_sys = help_menu.Append(wx.ID_ANY, "&Info sistema",
                                    "Sistema operativo e ambiente")
        help_menu.AppendSeparator()
        item_about = help_menu.Append(wx.ID_ABOUT,
                                      "&Descrizione del programma",
                                      "Informazioni sul programma")
        mb.Append(help_menu, "&?")

        self.SetMenuBar(mb)

        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_theme_auto, self.mi_theme_auto)
        self.Bind(wx.EVT_MENU, self.on_theme_light, self.mi_theme_light)
        self.Bind(wx.EVT_MENU, self.on_theme_dark, self.mi_theme_dark)
        self.Bind(wx.EVT_MENU, self.on_guide, item_guide)
        self.Bind(wx.EVT_MENU, self.on_license, item_lic)
        self.Bind(wx.EVT_MENU, self.on_sysinfo, item_sys)
        self.Bind(wx.EVT_MENU, self.on_about, item_about)

    def on_exit(self, _evt):
        self.Close()

    def _set_theme(self, mode):
        set_theme_mode(mode)
        apply_theme(self)

    def on_theme_auto(self, _evt):
        self._set_theme("auto")

    def on_theme_light(self, _evt):
        self._set_theme("light")

    def on_theme_dark(self, _evt):
        self._set_theme("dark")

    def on_guide(self, _evt):
        with TextDialog(self, "Guida", GUIDE_TEXT) as dlg:
            dlg.ShowModal()

    def on_license(self, _evt):
        with TextDialog(self, "Licenza — GNU GPL v2", LICENSE_TEXT) as dlg:
            dlg.ShowModal()

    def on_sysinfo(self, _evt):
        with SystemInfoDialog(self) as dlg:
            dlg.ShowModal()

    def on_about(self, _evt):
        info = wx.adv.AboutDialogInfo()
        info.SetName(APP_NAME)
        info.SetVersion(APP_VERSION)
        env = ("\n\nAmbiente rilevato:\n"
               "  SO: " + _os_pretty_name() + "\n"
               "  Python: " + platform.python_version() + "\n"
               "  wxPython: " + wx.version())
        info.SetDescription(APP_DESC + env)
        info.SetCopyright(APP_COPYRIGHT)
        info.SetLicence(LICENSE_TEXT)
        wx.adv.AboutBox(info, self)


class App(wx.App):
    def OnInit(self):
        TooltipTestFrame().Show()
        return True


if __name__ == "__main__":
    App(False).MainLoop()
