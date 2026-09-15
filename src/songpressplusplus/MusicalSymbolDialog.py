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

# Patch Debian/GTK - visibilita' delle frecce "+"/"-" degli SpinCtrl.
# Su wxGTK (Debian/KDE) i due pulsanti freccia sono piu' larghi che su Windows:
# una larghezza (min)size calibrata su MSW li taglia, lasciando visibile solo
# un trattino. Su piattaforme non-MSW aggiungiamo un margine di larghezza.
# (Stesso valore usato da _spin_size() in SongpressFrame.py.)
_SPIN_EXTRA_WIDTH = 0 if wx.Platform == '__WXMSW__' else 46


def N_(s):
    """Mark a string for extraction by xgettext without translating at import time."""
    return s


# ---------------------------------------------------------------------------
# Caricamento dinamico di tutti i font SMP dalla cartella fonts/
# ---------------------------------------------------------------------------
# Songpress++ carica automaticamente ogni file .ttf presente in
#   <installazione>/templates/fonts/
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
    """Carica tutti i .ttf presenti in <package>/templates/fonts/ come font privati wx.
    Popola _SMP_FACES con i face-name riconosciuti da wx.Font.
    Viene eseguita una sola volta per processo (guard _fonts_dir_loaded).
    """
    global _fonts_dir_loaded, _SMP_FACES
    if _fonts_dir_loaded:
        return
    _fonts_dir_loaded = True

    try:
        fonts_dir = glb.AddPath("templates/fonts")
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
        ("\U0001D15C", N_("Breve (double whole note)")),
        ("\U0001D15D", N_("Whole note (semibreve)")),
        ("\U0001D15E", N_("Half note (minim)")),
        ("\U0001D15F", N_("Quarter note (crotchet)")),
        ("\U0001D160", N_("Eighth note (quaver)")),
        ("\U0001D161", N_("16th note")),
        ("\U0001D162", N_("32nd note")),
        ("\U0001D163", N_("64th note")),
        ("\U0001D164", N_("128th note")),
        ("\U0001D157", N_("Void notehead")),
        ("\U0001D158", N_("Black notehead")),
        ("\U0001D13A", N_("Multi-measure rest")),
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
        ("\u266F", N_("Sharp")),
        ("\u266D", N_("Flat")),
        ("\u266E", N_("Natural")),
        ("\U0001D12A", N_("Double sharp")),
        ("\U0001D12B", N_("Double flat")),
        ("\U0001D132", N_("Quarter-tone sharp")),
        ("\U0001D133", N_("Quarter-tone flat")),
        ("\U0001D130", N_("Sharp raised (microtonal)")),
        ("\U0001D131", N_("Sharp lowered (microtonal)")),
        ("\U0001D12C", N_("Flat raised (microtonal)")),
        ("\U0001D12D", N_("Flat lowered (microtonal)")),
        ("\U0001D12E", N_("Natural raised (microtonal)")),
        ("\U0001D12F", N_("Natural lowered (microtonal)")),
    ],
    # Le dinamiche composte (pp, mf, sfz, ...) sono stringhe multi-codepoint
    # ottenute concatenando i glifi atomici p/m/f/s/z: è il modo standard in cui
    # Unicode/SMuFL rappresenta le dinamiche, e il renderer SMP le disegna in fila.
    "Dynamics": [
        ("\U0001D18F", N_("piano (p)")),
        ("\U0001D190", N_("mezzo (m)")),
        ("\U0001D191", N_("forte (f)")),
        ("\U0001D18F\U0001D18F", N_("pianissimo (pp)")),
        ("\U0001D191\U0001D191", N_("fortissimo (ff)")),
        ("\U0001D190\U0001D18F", N_("mezzo-piano (mp)")),
        ("\U0001D190\U0001D191", N_("mezzo-forte (mf)")),
        ("\U0001D18D\U0001D191", N_("sforzando (sf)")),
        ("\U0001D18D\U0001D191\U0001D18E", N_("sforzato (sfz)")),
        ("\U0001D191\U0001D18F", N_("forte-piano (fp)")),
        ("\U0001D191\U0001D18E", N_("forzando (fz)")),
        ("\U0001D18C", N_("rinforzando (rf)")),
        ("\U0001D18D", N_("subito (s)")),
        ("\U0001D18E", N_("z")),
        ("\U0001D192", N_("Crescendo (hairpin)")),
        ("\U0001D193", N_("Decrescendo (hairpin)")),
    ],
    "Staff and clefs": [
        ("\U0001D11E", N_("Treble clef (G)")),
        ("\U0001D11F", N_("Treble clef 8va alta")),
        ("\U0001D120", N_("Treble clef 8va bassa")),
        ("\U0001D122", N_("Bass clef (F)")),
        ("\U0001D123", N_("Bass clef 8va alta")),
        ("\U0001D124", N_("Bass clef 8va bassa")),
        ("\U0001D121", N_("C clef (alto/tenor)")),
        ("\U0001D125", N_("Drum clef 1")),
        ("\U0001D126", N_("Drum clef 2")),
        ("\U0001D114", N_("Brace")),
        ("\U0001D115", N_("Bracket")),
        ("\U0001D11A", N_("Five-line staff")),
        ("\U0001D100", N_("Single barline")),
        ("\U0001D101", N_("Double barline")),
        ("\U0001D102", N_("Final barline")),
        ("\U0001D103", N_("Reverse final barline")),
        ("\U0001D104", N_("Dashed barline")),
        ("\U0001D105", N_("Short barline")),
        ("\U0001D106", N_("Left (start) repeat")),
        ("\U0001D107", N_("Right (end) repeat")),
        ("\U0001D108", N_("Repeat dots")),
        ("\U0001D109", N_("Dal segno")),
        ("\U0001D10A", N_("Da capo")),
        ("\U0001D10B", N_("Segno")),
        ("\U0001D10C", N_("Coda")),
    ],
    "Ornaments and articulations": [
        ("\U0001D110", N_("Fermata")),
        ("\U0001D111", N_("Fermata below")),
        ("\U0001D112", N_("Breath mark")),
        ("\U0001D113", N_("Caesura")),
        ("\U0001D196", N_("Trill (tr)")),
        ("\U0001D197", N_("Turn")),
        ("\U0001D198", N_("Inverted turn")),
        ("\U0001D199", N_("Turn slash")),
        ("\U0001D19A", N_("Turn up")),
        ("\U0001D194", N_("Grace note (slash)")),
        ("\U0001D195", N_("Grace note (no slash)")),
        ("\U0001D175", N_("Begin tie")),
        ("\U0001D176", N_("End tie")),
        ("\U0001D177", N_("Begin slur")),
        ("\U0001D178", N_("End slur")),
        ("\U0001D179", N_("Begin phrase")),
        ("\U0001D17A", N_("End phrase")),
    ],
    "Common (BMP)": [
        ("\u266A", N_("Eighth note")),
        ("\u266B", N_("Beamed eighth notes")),
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

# _() translates at call time (after wx locale is loaded).


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
                cp  = ord(char[0]) if char else 0
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



def _plane_tag(char: str) -> str:
    """Ritorna 'SMP' se il simbolo contiene almeno un codepoint > U+FFFF
    (Supplementary Multilingual Plane, dove cade il blocco Musical Symbols
    U+1D100-1D1FF), altrimenti 'BMP' (Basic Multilingual Plane).

    Serve a segnalare all'utente quali simboli richiedono il rendering
    speciale via font a copertura SMP (FreeSerif) — gli stessi che
    SongDecorator disegna con il percorso GDI+/bitmap.
    """
    if not char:
        return "BMP"
    return "SMP" if any(ord(c) > 0xFFFF for c in char) else "BMP"


def _symbol_info(label: str, char: str) -> str:
    """Descrizione uniforme di un simbolo: nome tradotto, codepoint e piano
    Unicode (BMP/SMP). Usata sia per la riga di descrizione della selezione
    sia per i tooltip, così l'informazione è identica ovunque."""
    cp = ord(char[0]) if char else 0
    return f"{_(label)}  (U+{cp:04X})  [{_plane_tag(char)}]"


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



# ---------------------------------------------------------------------------
# Dialog principale (versione completa con parametri di personalizzazione)
# ---------------------------------------------------------------------------

class MusicalSymbolDialog(wx.Dialog):
    """Dialog modale per scegliere e inserire un simbolo musicale Unicode."""

    # ── Persistenza del colore del simbolo ──────────────────────────────────
    # Lo storage vive QUI (non più in Preferences): il dialog legge/scrive il
    # colore direttamente nella config globale (wx.Config.Get()), sotto la
    # stessa sezione usata per le altre impostazioni del simbolo musicale.
    _COLOUR_CFG_PATH = '/MusicalSymbol'
    _COLOUR_CFG_KEY  = 'colourHex'
    _COLOUR_DEFAULT  = '#000000'

    @classmethod
    def _read_stored_colour(cls) -> str:
        try:
            cfg = wx.Config.Get()
            old = cfg.GetPath()
            cfg.SetPath(cls._COLOUR_CFG_PATH)
            h = cfg.Read(cls._COLOUR_CFG_KEY)
            cfg.SetPath(old if old else '/')
            return h if h else cls._COLOUR_DEFAULT
        except Exception:
            return cls._COLOUR_DEFAULT

    @classmethod
    def _write_stored_colour(cls, hex_str: str) -> None:
        try:
            cfg = wx.Config.Get()
            old = cfg.GetPath()
            cfg.SetPath(cls._COLOUR_CFG_PATH)
            cfg.Write(cls._COLOUR_CFG_KEY, hex_str or cls._COLOUR_DEFAULT)
            cfg.SetPath(old if old else '/')
            cfg.Flush()
        except Exception:
            pass

    def __init__(self, parent, scale_enabled: bool = False, font_size: int = 24,
                 insert_verse: bool = False, on_valign_change=None,
                 symbol_colour: str = None):
        super().__init__(
            parent,
            title=_("Musical Symbols"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        self._selected = None
        self._on_valign_change = on_valign_change   # callback: rinfresca l'anteprima
        self._preview_font = _make_symbol_font(_FONT_SIZE)
        self._init_scale_enabled = scale_enabled
        self._init_font_size = max(6, min(font_size, 144))
        self._init_insert_verse = insert_verse
        # Colore iniziale: se non passato esplicitamente, lo legge dallo storage
        # interno del dialog (config globale).
        if symbol_colour is None:
            symbol_colour = self._read_stored_colour()
        self._init_symbol_colour = symbol_colour or self._COLOUR_DEFAULT

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
        # Anteprima nel colore configurato per il simbolo.
        try:
            _ph = (self._init_symbol_colour or '').strip().lstrip('#')
            if len(_ph) == 6:
                self._preview.SetForegroundColour(
                    wx.Colour(int(_ph[0:2], 16), int(_ph[2:4], 16), int(_ph[4:6], 16))
                )
        except Exception:
            pass
        info_row.Add(self._preview, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)

        self._desc = wx.StaticText(self, label="")
        info_row.Add(self._desc, 1, wx.ALIGN_CENTER_VERTICAL)

        outer.Add(info_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # ── Riga dimensione ────────────────────────────────────────────────
        size_row = wx.BoxSizer(wx.HORIZONTAL)
        self._chk_scale = wx.CheckBox(self, label=_("Custom size (pt):"))
        self._chk_scale.SetToolTip(
            _("When enabled, inserted musical symbols are wrapped with\n"
              "{textsize:N}...{textsize:} to apply the chosen point size.")
        )
        self._chk_scale.SetValue(self._init_scale_enabled)
        self._spin_size = wx.SpinCtrl(
            self, value=str(self._init_font_size),
            min=6, max=144, initial=self._init_font_size,
            style=wx.SP_ARROW_KEYS,
        )
        self._spin_size.SetMinSize(wx.Size(60 + _SPIN_EXTRA_WIDTH, -1))
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

        # ── Riga colore del simbolo ────────────────────────────────────────
        # Spostata qui dalla finestra Opzioni: il colore si sceglie al momento
        # dell'inserimento. Vale sia su Windows sia su Linux, a schermo e in
        # stampa, ed è applicato via {textcolour:...} (indipendente da {textsize}).
        colour_row = wx.BoxSizer(wx.HORIZONTAL)
        self._lbl_colour = wx.StaticText(self, label=_("Symbol colour:"))
        self._txt_colour = wx.TextCtrl(
            self, value=self._init_symbol_colour, size=wx.Size(80, -1)
        )
        self._btn_colour = wx.Button(self, label=_("Pick…"), size=wx.Size(60, -1))
        self._swatch_colour = wx.Panel(
            self, size=wx.Size(24, 24), style=wx.BORDER_SIMPLE
        )
        self._swatch_colour.SetBackgroundColour(
            self._hex_to_colour(self._init_symbol_colour)
        )
        self._txt_colour.SetToolTip(
            _("Colour applied to the inserted symbol.\n"
              "Works on both Windows and Linux, on screen and in print.")
        )
        colour_row.Add(self._lbl_colour,    0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        colour_row.Add(self._txt_colour,    0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        colour_row.Add(self._btn_colour,    0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        colour_row.Add(self._swatch_colour, 0, wx.ALIGN_CENTER_VERTICAL)
        outer.Add(colour_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self._btn_colour.Bind(wx.EVT_BUTTON, self._on_pick_colour)
        self._txt_colour.Bind(wx.EVT_TEXT, self._on_colour_text)

        # ── Nota informativa dimensione ────────────────────────────────────
        note_row = wx.BoxSizer(wx.HORIZONTAL)
        _info_icon = wx.StaticText(self, label=u"\u2139")   # ℹ
        _icon_font = _info_icon.GetFont()
        _icon_font.SetPointSize(_icon_font.GetPointSize() + 1)
        _icon_font.SetWeight(wx.FONTWEIGHT_BOLD)
        _info_icon.SetFont(_icon_font)
        _info_icon.SetForegroundColour(wx.Colour(0, 100, 180))
        note_row.Add(_info_icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        _note_lbl = wx.StaticText(
            self,
            label=_("Rendering may vary depending on the available font")
        )
        _note_font = _note_lbl.GetFont()
        _note_font.SetPointSize(max(_note_font.GetPointSize() - 1, 7))
        _note_font.SetStyle(wx.FONTSTYLE_ITALIC)
        _note_lbl.SetFont(_note_font)
        _note_lbl.SetForegroundColour(wx.Colour(90, 90, 90))
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

    # ── Colore del simbolo ─────────────────────────────────────────────────
    @staticmethod
    def _hex_to_colour(hex_str):
        try:
            h = (hex_str or "").strip().lstrip('#')
            if len(h) == 6:
                return wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except Exception:
            pass
        return wx.Colour(0, 0, 0)

    @staticmethod
    def _colour_to_hex(colour):
        if not colour.IsOk():
            return '#000000'
        return '#{:02X}{:02X}{:02X}'.format(colour.Red(), colour.Green(), colour.Blue())

    def _apply_colour_to_widgets(self, hex_str):
        """Aggiorna quadratino di anteprima e colore dell'anteprima del glifo."""
        c = self._hex_to_colour(hex_str)
        self._swatch_colour.SetBackgroundColour(c)
        self._swatch_colour.Refresh()
        self._preview.SetForegroundColour(c)
        self._preview.Refresh()

    def _on_colour_text(self, evt):
        self._apply_colour_to_widgets(self._txt_colour.GetValue())
        evt.Skip()

    def _on_pick_colour(self, evt):
        data = wx.ColourData()
        data.SetColour(self._hex_to_colour(self._txt_colour.GetValue()))
        data.SetChooseFull(True)
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            chosen = dlg.GetColourData().GetColour()
            self._txt_colour.SetValue(self._colour_to_hex(chosen))
            self._apply_colour_to_widgets(self._colour_to_hex(chosen))
        dlg.Destroy()

    def GetSymbolColour(self) -> str:
        """Restituisce il colore corrente (hex sanificato, es. '#RRGGBB')."""
        c = self._hex_to_colour(self._txt_colour.GetValue())
        return self._colour_to_hex(c)

    def EndModal(self, retCode):
        # Alla conferma (pulsante Inserisci o doppio clic → ID_OK) il dialog
        # salva da sé il colore scelto nel proprio storage, così la scelta
        # persiste tra sessioni senza passare da Preferences.
        if retCode == wx.ID_OK:
            self._write_stored_colour(self.GetSymbolColour())
        return super().EndModal(retCode)

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
            self._desc.SetLabel(_symbol_info(label, char))
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
                char, label = symbols[idx]
                grid.SetToolTip(_symbol_info(label, char))
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
            con colore            → {textcolour:#FF0000}♩{textcolour}
            con entrambe          → {start_verse}{textsize:24}♩{textsize}{end_verse}
        """
        sym = self._selected or ""
        if not sym:
            return ""
        # Applica colore del simbolo: direttiva a sé, indipendente da {textsize}.
        # Riusa la direttiva {textcolour:...}...{textcolour} già gestita dal
        # parser (SongFormat/SongBoxes) e onorata dal renderer su tutti i
        # percorsi (GraphicsContext su Windows/macOS, bitmap su Linux e stampa).
        # Si emette solo se è stato scelto un colore diverso dal nero di default,
        # così l'inserimento resta pulito quando il colore non serve.
        col = self.GetSymbolColour().strip()
        if col and col.upper() != "#000000":
            sym = f"{{textcolour:{col}}}{sym}{{textcolour}}"
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
