###############################################################
# Name:         MusicalSymbolDialog.py
# Purpose:      Dialog per inserire simboli musicali Unicode
#               nell'editor STC (UTF-8).
# Author:       Denisov21
# Created:      2026
# Copyright:    © 2026 Denisov21
# License:      GNU GPL v2
###############################################################

import os
import wx
import wx.grid
import wx.stc

from .Globals import glb   # per glb.AddPath()

_ = wx.GetTranslation


def N_(s):
    """Mark a string for extraction by xgettext without translating at import time."""
    return s


# ---------------------------------------------------------------------------
# Caricamento dinamico di tutti i font SMP dalla cartella fonts/
# ---------------------------------------------------------------------------
# Songpress++ carica automaticamente ogni file .ttf presente in
#   <installazione>/fonts/
# come font privato (wx.Font.AddPrivateFont).  I face-name registrati
# vengono raccolti in _SMP_FACES (lista ordinata) e usati da SongDecorator
# per il rendering GDI+ dei caratteri U+10000+.
#
# Ordine di priorità predefinito (il primo file trovato vince per glifo):
#   1. FreeSerif.ttf        — copertura completa Musical Symbols U+1D100-1D1FF
#   2. Bravura.ttf          — font SMuFL professionale
#   3. NotoMusic.ttf / NotoMusicRegular.ttf  — Google Noto, ampia copertura SMP
#   4. qualsiasi altro .ttf nella cartella   — caricato automaticamente
#   5. Segoe UI Symbol      — presente di sistema su Windows 10/11 (fallback)
# ---------------------------------------------------------------------------

# Lista globale dei face-name SMP disponibili, popolata da _load_fonts_dir().
# SongDecorator la legge via get_smp_faces().
_SMP_FACES: list = []
_fonts_dir_loaded: bool = False

# Font che vogliamo caricare per primi (ordine di preferenza).
_PREFERRED_ORDER = [
    "FreeSerif.ttf",
    "Bravura.ttf",
    "NotoMusic.ttf",
    "NotoMusicRegular.ttf",
]


def _load_fonts_dir() -> None:
    """Carica tutti i .ttf presenti in <package>/fonts/ come font privati wx.
    Popola _SMP_FACES con i face-name riconosciuti da wx.Font.
    Viene eseguita una sola volta per processo (guard _fonts_dir_loaded).
    """
    global _fonts_dir_loaded, _SMP_FACES
    if _fonts_dir_loaded:
        return
    _fonts_dir_loaded = True

    try:
        fonts_dir = glb.AddPath("fonts")
        if not os.path.isdir(fonts_dir):
            return

        # Costruisce la lista dei file: prima quelli preferiti (in ordine),
        # poi gli altri in ordine alfabetico.
        all_ttf = [f for f in os.listdir(fonts_dir)
                   if f.lower().endswith(".ttf")]
        preferred = [f for f in _PREFERRED_ORDER if f in all_ttf]
        others    = sorted(f for f in all_ttf if f not in _PREFERRED_ORDER)
        ordered   = preferred + others

        for filename in ordered:
            path = os.path.join(fonts_dir, filename)
            try:
                if not wx.Font.AddPrivateFont(path):
                    continue
                # Ricava il face-name chiedendo a wx di creare il font
                # con il nome del file senza estensione come primo tentativo
                stem = os.path.splitext(filename)[0]
                face = _resolve_face(stem)
                if face and face not in _SMP_FACES:
                    _SMP_FACES.append(face)
            except Exception:
                pass

        # Segoe UI Symbol è un font di sistema su Windows 10/11:
        # lo aggiungiamo in coda come fallback senza caricarlo esplicitamente.
        if "Segoe UI Symbol" not in _SMP_FACES:
            f = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                        wx.FONTWEIGHT_NORMAL, faceName="Segoe UI Symbol")
            if f.IsOk() and "segoe" in f.GetFaceName().lower():
                _SMP_FACES.append("Segoe UI Symbol")

    except Exception:
        pass


def _resolve_face(stem: str) -> str:
    """Dato uno stem (nome file senza .ttf), tenta di ricavare il face-name
    effettivo con cui wx conosce il font appena caricato.
    Prova prima lo stem esatto, poi alcune varianti comuni.
    """
    candidates = [stem]
    # Varianti: "NotoMusicRegular" → "Noto Music", "FreeSerif" → "FreeSerif"
    # Aggiunge uno spazio prima di ogni maiuscola interna (CamelCase → "Camel Case")
    import re
    spaced = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', stem)
    if spaced != stem:
        candidates.append(spaced)
    # Rimuove suffissi comuni ("Regular", "Bold", "Italic")
    base = re.sub(r'(?i)\s*(Regular|Bold|Italic|Light|Medium)$', '', spaced).strip()
    if base and base not in candidates:
        candidates.append(base)

    for name in candidates:
        f = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL, faceName=name)
        if f.IsOk():
            actual = f.GetFaceName()
            if actual:
                return actual
    return ""


def get_smp_faces() -> list:
    """Restituisce la lista (ordinata per preferenza) dei face-name SMP
    disponibili.  Chiamata da SongDecorator._smp_gc_font().
    """
    _load_fonts_dir()
    return _SMP_FACES


def _best_face() -> str:
    """Restituisce il nome del font migliore disponibile per i simboli SMP
    (usato dal dialog per la griglia di anteprima).
    """
    _load_fonts_dir()
    if _SMP_FACES:
        return _SMP_FACES[0]
    return ""   # font di sistema


def _make_stc(parent: wx.Window, font_face: str, font_size: int,
              readonly: bool = True) -> wx.stc.StyledTextCtrl:
    """
    Crea uno StyledTextCtrl con STC_CP_UTF8 + DirectWrite,
    esattamente come Editor.py.
    """
    stc = wx.stc.StyledTextCtrl(parent,
                                style=wx.BORDER_NONE | wx.WANTS_CHARS)
    stc.SetCodePage(wx.stc.STC_CP_UTF8)
    try:
        stc.SetTechnology(wx.stc.STC_TECHNOLOGY_DIRECTWRITE)
    except AttributeError:
        pass
    stc.SetReadOnly(readonly)
    stc.SetUseHorizontalScrollBar(False)
    stc.SetUseVerticalScrollBar(False)
    stc.SetMarginWidth(0, 0)
    stc.SetMarginWidth(1, 0)
    stc.SetMarginWidth(2, 0)
    stc.SetWrapMode(wx.stc.STC_WRAP_NONE)
    stc.SetLexer(wx.stc.STC_LEX_NULL)

    font = wx.Font(font_size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                   wx.FONTWEIGHT_NORMAL, faceName=font_face)
    stc.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, font)
    stc.StyleClearAll()

    # Sfondo bianco, nessun cursore visibile
    stc.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, wx.WHITE)
    stc.SetCaretForeground(wx.WHITE)
    stc.SetCaretWidth(0)
    stc.SetHighlightGuide(0)
    stc.SetIndentationGuides(0)

    return stc


# ---------------------------------------------------------------------------
# Tabelle dei simboli per categoria
# ---------------------------------------------------------------------------

# Symbol table keys are in English; tab labels are translated at runtime via _tab_order().
_SYMBOLS = {
    "Notes and rests": [
        ("\U0001D157", N_("Void whole note (semibreve)")),
        ("\U0001D15C", N_("Breve")),
        ("\U0001D15D", N_("Whole note (semibreve)")),
        ("\U0001D158", N_("Half note head")),
        ("\U0001D15E", N_("Half note (open)")),
        ("\U0001D15F", N_("Quarter note")),
        ("\U0001D160", N_("Eighth note")),
        ("\U0001D161", N_("16th note")),
        ("\U0001D162", N_("32nd note")),
        ("\U0001D163", N_("64th note")),
        ("\U0001D164", N_("128th note")),
        ("\U0001D13B", N_("Whole rest")),
        ("\U0001D13C", N_("Half rest")),
        ("\U0001D13D", N_("Quarter rest")),
        ("\U0001D13E", N_("Eighth rest")),
        ("\U0001D13F", N_("16th rest")),
        ("\U0001D140", N_("32nd rest")),
        ("\U0001D141", N_("64th rest")),
        ("\U0001D142", N_("128th rest")),
    ],
    "Accidentals": [
        ("\u266F", N_("Sharp (#)")),
        ("\u266D", N_("Flat (b)")),
        ("\u266E", N_("Natural")),
        ("\U0001D12A", N_("Double sharp")),
        ("\U0001D12B", N_("Double flat")),
        ("\U0001D130", N_("Quarter-tone flat")),
        ("\U0001D131", N_("Quarter-tone sharp")),
        ("\U0001D132", N_("Three-quarter-tone flat")),
        ("\U0001D133", N_("Three-quarter-tone sharp")),
    ],
    "Dynamics": [
        ("\U0001D18F", N_("piano")),
        ("\U0001D190", N_("forte")),
        ("\U0001D191", N_("mp")),
        ("\U0001D192", N_("mf")),
        ("\U0001D193", N_("sf")),
        ("\U0001D194", N_("sfz")),
        ("\U0001D195", N_("fz")),
        ("\U0001D196", N_("fp")),
        ("\U0001D197", N_("resso")),
        ("\U0001D198", N_("senza misura")),
        ("\U0001D199", N_("Crescendo (<)")),
        ("\U0001D19A", N_("Decrescendo (>)")),
        ("\U0001D19B", N_("smorzando")),
        ("\U0001D19C", N_("rinforzando")),
    ],
    "Staff and clefs": [
        ("\U0001D11E", N_("Treble clef")),
        ("\U0001D120", N_("Baritone clef")),
        ("\U0001D121", N_("Alto clef (C)")),
        ("\U0001D122", N_("Tenor clef (C)")),
        ("\U0001D123", N_("Mezzo-soprano clef (C)")),
        ("\U0001D124", N_("Soprano clef (C)")),
        ("\U0001D11F", N_("Bass clef")),
        ("\U0001D125", N_("Percussion bass clef")),
        ("\U0001D126", N_("Percussion clef alt.")),
        ("\U0001D100", N_("Single barline")),
        ("\U0001D101", N_("Double barline")),
        ("\U0001D102", N_("Final barline")),
        ("\U0001D103", N_("Double final barline")),
        ("\U0001D104", N_("Start repeat barline")),
        ("\U0001D105", N_("End repeat barline")),
        ("\U0001D106", N_("Short barline section 1")),
        ("\U0001D107", N_("Short barline section 2")),
        ("\U0001D108", N_("Short barline segno")),
        ("\U0001D10B", N_("Segno")),
        ("\U0001D10C", N_("Coda")),
    ],
    "Ornaments and articulations": [
        ("\U0001D176", N_("Begin slur")),
        ("\U0001D177", N_("End slur")),
        ("\U0001D178", N_("Begin tie")),
        ("\U0001D179", N_("End tie")),
        ("\U0001D17A", N_("Begin phrase")),
        ("\U0001D110", N_("Fermata")),
        ("\U0001D111", N_("Short fermata")),
        ("\U0001D112", N_("Breath mark (comma)")),
        ("\U0001D113", N_("Caesura (//)")),
        ("\U0001D114", N_("Drum: snare")),
        ("\U0001D115", N_("Drum: double pedal")),
        ("\U0001D116", N_("Multiple measure rest 1")),
        ("\U0001D117", N_("Multiple measure rest 2")),
        ("\U0001D118", N_("Multiple measure rest 3")),
        ("\U0001D119", N_("Multiple measure rest 4")),
        ("\U0001D11A", N_("Multiple measure rest 5")),
    ],
    "Common (BMP)": [
        ("\u266A", N_("Musical note")),
        ("\u266B", N_("Beamed notes")),
        ("\u266C", N_("Beamed sixteenth notes")),
        ("\u2669", N_("Quarter note (black)")),
        ("\u2605", N_("Black star")),
        ("\u2606", N_("White star")),
        ("\u2020", N_("Dagger")),
        ("\u2117", N_("Sound recording copyright")),
        ("\u00B0", N_("Degree")),
        ("\u00BD", N_("Half (1/2)")),
        ("\u00BC", N_("Quarter (1/4)")),
        ("\u00BE", N_("Three quarters (3/4)")),
        ("\u2044", N_("Fraction slash")),
        ("\u00D7", N_("Multiply (x)")),
        ("\u2013", N_("En dash")),
        ("\u2014", N_("Em dash")),
        ("\u2026", N_("Ellipsis")),
    ],
}

# N_() marks strings for extraction without translating at definition time.
# _() translates at call time (after wx locale is loaded).
def N_(s):
    return s


def _tab_order():
    """Returns tab names translated at runtime."""
    return [
        _("Notes and rests"),
        _("Accidentals"),
        _("Dynamics"),
        _("Staff and clefs"),
        _("Ornaments and articulations"),
        _("Common (BMP)"),
    ]


# Internal key order (English, matches _SYMBOLS keys)
_TAB_KEYS = [
    "Notes and rests",
    "Accidentals",
    "Dynamics",
    "Staff and clefs",
    "Ornaments and articulations",
    "Common (BMP)",
]

_COLS      = 8
_CELL_SIZE = 48
_FONT_SIZE = 20


# ---------------------------------------------------------------------------
# Pannello-griglia custom: ogni cella è un mini-STC con DirectWrite
# ---------------------------------------------------------------------------

class _SymbolGrid(wx.Panel):
    """
    Griglia di simboli Unicode renderizzati ognuno in un
    StyledTextCtrl readonly con STC_CP_UTF8 + DirectWrite,
    come fa Editor.py.
    """

    def __init__(self, parent: wx.Window, symbols: list,
                 font_face: str, font_size: int):
        self._symbols   = symbols
        self._font_face = font_face
        self._font_size = font_size
        self._selected  = -1          # indice del simbolo selezionato
        self._cells: list[wx.stc.StyledTextCtrl] = []

        cols = _COLS
        rows = max(1, (len(symbols) + cols - 1) // cols)

        super().__init__(parent)

        sizer = wx.GridSizer(rows=rows, cols=cols, vgap=2, hgap=2)

        for idx in range(rows * cols):
            cell = _make_stc(self, font_face, font_size, readonly=True)
            cell.SetMinSize(wx.Size(_CELL_SIZE, _CELL_SIZE))

            if idx < len(symbols):
                char, label = symbols[idx]
                cell.SetReadOnly(False)
                cell.SetText(char)
                cell.SetReadOnly(True)
                cp  = ord(char)
                tip = f"{_(label)}  (U+{cp:04X})"
                cell.SetToolTip(tip)
                # Centra il testo verticalmente con un po' di margine
                cell.SetMarginLeft(0)
                # click su questa cella
                cell.Bind(wx.EVT_LEFT_DOWN,
                          lambda e, i=idx: self._on_cell_click(i))
                cell.Bind(wx.EVT_LEFT_DCLICK,
                          lambda e, i=idx: self._on_cell_dclick(i))
            else:
                cell.SetReadOnly(True)

            self._cells.append(cell)
            sizer.Add(cell, 0, wx.EXPAND)

        self.SetSizer(sizer)
        self.Layout()

        # Callback chiamato dalla finestra padre
        self.on_select:  "Callable[[int], None] | None" = None
        self.on_dclick:  "Callable[[int], None] | None" = None

    # ── stile bordo selezione ──────────────────────────────────────────────

    def _highlight(self, idx: int, selected: bool) -> None:
        if 0 <= idx < len(self._cells):
            cell = self._cells[idx]
            bg = wx.Colour(200, 220, 255) if selected else wx.WHITE
            cell.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, bg)
            cell.StyleClearAll()
            # Riapplica font dopo StyleClearAll
            font = wx.Font(self._font_size, wx.FONTFAMILY_DEFAULT,
                           wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,
                           faceName=self._font_face)
            cell.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, font)
            cell.SetCaretWidth(0)
            cell.Refresh()

    def SelectIndex(self, idx: int) -> None:
        if self._selected >= 0:
            self._highlight(self._selected, False)
        self._selected = idx
        if idx >= 0:
            self._highlight(idx, True)

    def _on_cell_click(self, idx: int) -> None:
        self.SelectIndex(idx)
        if self.on_select:
            self.on_select(idx)

    def _on_cell_dclick(self, idx: int) -> None:
        self.SelectIndex(idx)
        if self.on_dclick:
            self.on_dclick(idx)


# ---------------------------------------------------------------------------
# Dialog principale
# ---------------------------------------------------------------------------

class MusicalSymbolDialog(wx.Dialog):
    """Dialog modale per scegliere e inserire un simbolo musicale Unicode."""

    def __init__(self, parent):
        super().__init__(
            parent,
            title=_("Musical Symbols"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        self._selected: str | None = None
        self._font_face = _best_face()
        self._grids: dict[str, _SymbolGrid] = {}

        self._build_ui()
        self.SetMinSize(wx.Size(520, 460))
        self.Fit()
        self.CentreOnParent()

    # ── costruzione UI ─────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = wx.BoxSizer(wx.VERTICAL)

        self._nb = wx.Notebook(self)

        for key, label in zip(_TAB_KEYS, _tab_order()):
            symbols = _SYMBOLS.get(key, [])
            panel   = wx.Panel(self._nb)
            sg      = _SymbolGrid(panel, symbols,
                                  self._font_face, _FONT_SIZE)
            sg.on_select = self._on_grid_select
            sg.on_dclick = self._on_grid_dclick
            self._grids[key] = sg

            sz = wx.BoxSizer(wx.VERTICAL)
            sz.Add(sg, 1, wx.EXPAND | wx.ALL, 4)
            panel.SetSizer(sz)
            self._nb.AddPage(panel, label)

        outer.Add(self._nb, 1, wx.EXPAND | wx.ALL, 6)

        # ── Riga preview + descrizione ─────────────────────────────────────
        info_row = wx.BoxSizer(wx.HORIZONTAL)

        # STC per la preview grande — stesso approccio di Editor.py
        self._preview_stc = _make_stc(self, self._font_face, 36, readonly=True)
        self._preview_stc.SetMinSize(wx.Size(60, 60))
        info_row.Add(self._preview_stc, 0,
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)

        self._desc = wx.StaticText(self, label="")
        info_row.Add(self._desc, 1, wx.ALIGN_CENTER_VERTICAL)

        outer.Add(info_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # ── Pulsanti ───────────────────────────────────────────────────────
        btn_sizer = wx.StdDialogButtonSizer()
        self._btn_insert = wx.Button(self, wx.ID_OK, _("Insert"))
        self._btn_insert.SetDefault()
        self._btn_insert.Disable()
        btn_cancel = wx.Button(self, wx.ID_CANCEL, _("Close"))
        btn_sizer.AddButton(self._btn_insert)
        btn_sizer.AddButton(btn_cancel)
        btn_sizer.Realize()
        outer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 6)

        self.SetSizer(outer)

    # ── eventi dalla griglia ───────────────────────────────────────────────

    def _current_grid(self) -> "_SymbolGrid | None":
        key = _TAB_KEYS[self._nb.GetSelection()]
        return self._grids.get(key)

    def _current_symbols(self) -> list:
        key = _TAB_KEYS[self._nb.GetSelection()]
        return _SYMBOLS.get(key, [])

    def _on_grid_select(self, idx: int) -> None:
        symbols = self._current_symbols()
        if 0 <= idx < len(symbols):
            char, label = symbols[idx]
            self._selected = char
            # Aggiorna preview STC
            self._preview_stc.SetReadOnly(False)
            self._preview_stc.SetText(char)
            self._preview_stc.SetReadOnly(True)
            cp = ord(char)
            self._desc.SetLabel(f"{_(label)}  (U+{cp:04X})")
            self._btn_insert.Enable()
        else:
            self._selected = None
            self._preview_stc.SetReadOnly(False)
            self._preview_stc.SetText("")
            self._preview_stc.SetReadOnly(True)
            self._desc.SetLabel("")
            self._btn_insert.Disable()

    def _on_grid_dclick(self, idx: int) -> None:
        symbols = self._current_symbols()
        if 0 <= idx < len(symbols):
            self._selected = symbols[idx][0]
            self.EndModal(wx.ID_OK)

    # ── API pubblica ───────────────────────────────────────────────────────

    def GetSymbol(self) -> str:
        return self._selected or ""


def _make_symbol_font(point_size: int) -> wx.Font:
    """Restituisce un wx.Font adatto a visualizzare simboli musicali SMP.
    Usa la lista dinamica _SMP_FACES (popolata da _load_fonts_dir);
    fallback al font di sistema se nessun candidato è disponibile.
    """
    _load_fonts_dir()
    for face in _SMP_FACES:
        f = wx.Font(point_size, wx.FONTFAMILY_DEFAULT,
                    wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,
                    faceName=face)
        if f.IsOk():
            return f
    # Nessun font SMP disponibile: usa il font di sistema
    return wx.Font(point_size, wx.FONTFAMILY_DEFAULT,
                   wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)


# Dimensione della griglia
_COLS = 8
_CELL_SIZE = 48
_FONT_SIZE  = 20


class MusicalSymbolDialog(wx.Dialog):
    """Dialog modale per scegliere e inserire un simbolo musicale Unicode."""

    def __init__(self, parent, scale_enabled: bool = False, font_size: int = 24,
                 insert_verse: bool = False):
        super().__init__(
            parent,
            title=_("Musical Symbols"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        self._selected = None
        self._preview_font = _make_symbol_font(_FONT_SIZE)
        self._init_scale_enabled = scale_enabled
        self._init_font_size = max(6, min(font_size, 144))
        self._init_insert_verse = insert_verse

        self._build_ui()
        self.SetMinSize(wx.Size(620, 400))
        self.SetSize(wx.Size(620, 400))
        self.Fit()
        self.CentreOnParent()

    def _build_ui(self):
        outer = wx.BoxSizer(wx.VERTICAL)

        self._nb = wx.Notebook(self)
        self._grids = {}

        for key, label in zip(_TAB_KEYS, _tab_order()):
            symbols = _SYMBOLS.get(key, [])
            panel   = wx.Panel(self._nb)
            grid    = self._make_grid(panel, symbols)
            self._grids[key] = grid
            sz = wx.BoxSizer(wx.VERTICAL)
            sz.Add(grid, 1, wx.EXPAND | wx.ALL, 4)
            panel.SetSizer(sz)
            self._nb.AddPage(panel, label)

        outer.Add(self._nb, 1, wx.EXPAND | wx.ALL, 6)

        info_row = wx.BoxSizer(wx.HORIZONTAL)

        self._preview = wx.StaticText(
            self, label="", style=wx.ALIGN_CENTRE_HORIZONTAL | wx.ST_NO_AUTORESIZE
        )
        self._preview.SetFont(_make_symbol_font(36))
        self._preview.SetMinSize(wx.Size(56, 56))
        info_row.Add(self._preview, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)

        self._desc = wx.StaticText(self, label="")
        info_row.Add(self._desc, 1, wx.ALIGN_CENTER_VERTICAL)

        outer.Add(info_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # ── Riga dimensione ────────────────────────────────────────────────
        size_row = wx.BoxSizer(wx.HORIZONTAL)
        self._chk_scale = wx.CheckBox(self, label=_("Custom size (pt):"))
        self._chk_scale.SetValue(self._init_scale_enabled)
        self._spin_size = wx.SpinCtrl(
            self, value=str(self._init_font_size),
            min=6, max=144, initial=self._init_font_size,
            style=wx.SP_ARROW_KEYS,
        )
        self._spin_size.SetMinSize(wx.Size(60, -1))
        self._spin_size.Enable(self._init_scale_enabled)
        size_row.Add(self._chk_scale, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        size_row.Add(self._spin_size, 0, wx.ALIGN_CENTER_VERTICAL)
        outer.Add(size_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self._chk_scale.Bind(wx.EVT_CHECKBOX, self._on_chk_scale)

        # ── Checkbox: inserisci nuova strofa numerata ──────────────────────
        self._chk_verse = wx.CheckBox(
            self, label=_("Wrap symbol in a verse block (not counted)")
        )
        self._chk_verse.SetToolTip(
            _("When enabled, the symbol is wrapped inside {start_verse}...{end_verse}\n"
              "so it appears as a verse block without being counted in the verse numbering.\n"
              "Example: {start_verse}{textsize:24}\u266a{textsize}{end_verse}")
        )
        self._chk_verse.SetValue(self._init_insert_verse)
        outer.Add(self._chk_verse, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # ── Nota informativa dimensione ────────────────────────────────────
        note_row = wx.BoxSizer(wx.HORIZONTAL)
        _info_path = glb.AddPath("img/info.png")
        try:
            _info_bmp = wx.Bitmap(_info_path, wx.BITMAP_TYPE_PNG)
            if _info_bmp.IsOk():
                _info_icon = wx.StaticBitmap(self, bitmap=_info_bmp)
                note_row.Add(_info_icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        except Exception:
            pass
        _note_lbl = wx.StaticText(
            self,
            label=_("Note: not all symbols can be resized!")
        )
        _note_font = _note_lbl.GetFont()
        _note_font.SetStyle(wx.FONTSTYLE_ITALIC)
        _note_lbl.SetFont(_note_font)
        note_row.Add(_note_lbl, 0, wx.ALIGN_CENTER_VERTICAL)
        outer.Add(note_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        # ──────────────────────────────────────────────────────────────────

        btn_sizer = wx.StdDialogButtonSizer()
        self._btn_insert = wx.Button(self, wx.ID_OK, _("Insert"))
        self._btn_insert.SetDefault()
        self._btn_insert.Disable()
        btn_cancel = wx.Button(self, wx.ID_CANCEL, _("Close"))
        btn_sizer.AddButton(self._btn_insert)
        btn_sizer.AddButton(btn_cancel)
        btn_sizer.Realize()
        outer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 6)

        self.SetSizer(outer)

        for grid in self._grids.values():
            grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self._on_dclick)

    def _on_chk_scale(self, evt):
        self._spin_size.Enable(self._chk_scale.GetValue())

    def _make_grid(self, parent, symbols):
        rows = max(1, (len(symbols) + _COLS - 1) // _COLS)

        grid = wx.grid.Grid(parent)
        grid.CreateGrid(rows, _COLS)
        grid.EnableEditing(False)
        grid.DisableDragGridSize()
        grid.SetSelectionMode(wx.grid.Grid.GridSelectCells)

        grid.SetRowLabelSize(0)
        grid.SetColLabelSize(0)

        for c in range(_COLS):
            grid.SetColSize(c, _CELL_SIZE)
        for r in range(rows):
            grid.SetRowSize(r, _CELL_SIZE)

        for idx, (char, label) in enumerate(symbols):
            r, c = divmod(idx, _COLS)
            grid.SetCellValue(r, c, char)
            grid.SetCellFont(r, c, self._preview_font)
            grid.SetCellAlignment(r, c, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
            grid.SetReadOnly(r, c, True)

        total = rows * _COLS
        for idx in range(len(symbols), total):
            r, c = divmod(idx, _COLS)
            grid.SetReadOnly(r, c, True)

        grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, self._on_select)
        grid.Bind(wx.EVT_MOTION, lambda evt, g=grid, s=symbols: self._on_motion(evt, g, s))

        return grid

    def _current_symbols(self):
        key = _TAB_KEYS[self._nb.GetSelection()]
        return _SYMBOLS.get(key, [])

    def _on_select(self, evt):
        r, c = evt.GetRow(), evt.GetCol()
        symbols = self._current_symbols()
        idx = r * _COLS + c
        if 0 <= idx < len(symbols):
            char, label = symbols[idx]
            self._selected = char
            self._preview.SetLabel(char)
            cp = ord(char)
            self._desc.SetLabel(f"{_(label)}  (U+{cp:04X})")
            self._btn_insert.Enable()
        else:
            self._selected = None
            self._preview.SetLabel("")
            self._desc.SetLabel("")
            self._btn_insert.Disable()
        evt.Skip()

    def _on_motion(self, evt, grid, symbols):
        x, y = evt.GetPosition()
        col = grid.XToCol(x)
        row = grid.YToRow(y)
        if row >= 0 and col >= 0:
            idx = row * _COLS + col
            if 0 <= idx < len(symbols):
                _, label = symbols[idx]
                cp = ord(symbols[idx][0])
                tip = f"{_(label)}  (U+{cp:04X})"
                grid.SetToolTip(tip)
                evt.Skip()
                return
        grid.SetToolTip("")
        evt.Skip()

    def _on_dclick(self, evt):
        r, c = evt.GetRow(), evt.GetCol()
        symbols = self._current_symbols()
        idx = r * _COLS + c
        if 0 <= idx < len(symbols):
            self._selected = symbols[idx][0]
            self.EndModal(wx.ID_OK)
        evt.Skip()

    def GetSymbol(self) -> str:
        """Restituisce il testo da inserire nell'editor.

        - Se 'Dimensione personalizzata' è attiva: wrappa con {textsize:N}...{textsize}
        - Se 'Wrappa in blocco strofa' è attiva: wrappa con {start_verse}...{end_verse}
        Le due opzioni sono combinabili.

        Esempi:
            solo simbolo          → ♩
            con dimensione        → {textsize:24}♩{textsize}
            con strofa            → {start_verse}♩{end_verse}
            con entrambe          → {start_verse}{textsize:24}♩{textsize}{end_verse}
        """
        sym = self._selected or ""
        if not sym:
            return ""
        # Applica dimensione
        if self._chk_scale.GetValue():
            pt = self._spin_size.GetValue()
            sym = f"{{textsize:{pt}}}{sym}{{textsize}}"
        # Applica wrap strofa
        if self._chk_verse.GetValue():
            sym = f"{{start_verse}}{sym}{{end_verse}}"
        return sym

    def GetScaleEnabled(self) -> bool:
        """Restituisce True se la checkbox 'Dimensione personalizzata' è attiva."""
        return self._chk_scale.GetValue()

    def GetFontSize(self) -> int:
        """Restituisce il valore corrente dello spinctrl dimensione (pt)."""
        return self._spin_size.GetValue()

    def GetInsertVerse(self) -> bool:
        """Restituisce True se la checkbox 'Inserisci strofa numerata' è attiva."""
        return self._chk_verse.GetValue()
