##############################################################
# Name:         PrintDialog.py
# Purpose:      Tutto il codice di stampa di Songpress++:
#               - SongpressPrintout  (wx.Printout)
#               - PrintManager       (mixin con stato e metodi di stampa)
#               - PrintOptionsDialog (dialog opzioni di stampa ottimizzato)
# Author:       Denisov21
# Created:      2026
# Copyright:    Denisov21 © 2026
#               Basato su Songpress di Luca Allulli (https://www.skeed.it/songpress)
# License:      GNU GPL v2
##############################################################
#
# USO IN SongpressFrame.py
# ────────────────────────
# 1. Aggiungere in cima al file:
#
#       from .PrintDialog import SongpressPrintout, PrintManager
#
# 2. Rimuovere da SongpressFrame.py:
#    • La classe SongpressPrintout   (righe 694-1149)
#    • Il dict  _PAPER_SIZE_MM       (righe 7243-7253)
#    • I metodi _GetPaperSizeMm      (7255-7262)
#    •          OnPageSetup          (7264-7283)
#    •          _reopen_print_options_if_pinned (7286-7316)
#    •          _ask_two_pages_per_sheet        (7318-7491)
#    •          OnPrint              (7493-7525)
#    •          OnPrintPreview       (7527-7758)
#
# 3. Aggiungere PrintManager come base aggiuntiva di SongpressFrame:
#
#       class SongpressFrame(SDIMainFrame, PrintManager):
#           def __init__(self, res):
#               PrintManager.__init__(self)
#               ...
#
##############################################################

import math
import os

import wx

from .Globals import glb
from .Renderer import Renderer, SongDecorator

_ = wx.GetTranslation

# ── Costanti ──────────────────────────────────────────────────────────────────

_GAP = 8          # margine interno dialogo (px)

_PAPER_SIZE_MM = {
    wx.PAPER_A3:        (297.0, 420.0),
    wx.PAPER_A4:        (210.0, 297.0),
    wx.PAPER_A5:        (148.0, 210.0),
    wx.PAPER_B4:        (250.0, 354.0),
    wx.PAPER_B5:        (176.0, 250.0),
    wx.PAPER_LETTER:    (215.9, 279.4),
    wx.PAPER_LEGAL:     (215.9, 355.6),
    wx.PAPER_TABLOID:   (279.4, 431.8),
    wx.PAPER_EXECUTIVE: (184.1, 266.7),
}


# ══════════════════════════════════════════════════════════════════════════════
# SongpressPrintout
# ══════════════════════════════════════════════════════════════════════════════

class SongpressPrintout(wx.Printout):
    """
    Printout per Songpress++.

    Supporta interruzioni di pagina esplicite tramite il comando {new_page}:
    il testo viene suddiviso in segmenti, ognuno stampato su una o più pagine.
    All'interno di ciascun segmento il contenuto scorre automaticamente se
    supera l'altezza della pagina.
    """

    _SCREEN_PPI = 96

    def __init__(self, frame_obj, title="Song", two_pages_per_sheet=False,
                 font_scale=100, force_full=False):
        wx.Printout.__init__(self, title)
        self.frame_obj          = frame_obj
        self.two_pages_per_sheet = two_pages_per_sheet
        self._font_scale        = font_scale / 100.0
        # force_full=True → ignora la selezione e stampa sempre l'intero documento
        self._force_full        = force_full
        self._page_offsets      = None   # list of (segment_idx, y_offset_px)
        self._segments          = None   # list of text strings (split on {new_page})
        self._scale_x           = None
        self._scale_y           = None
        self._margin_du         = None
        self._usable_w_du       = None
        self._song_info         = None   # (full_song, line_start, line_end)
        self._col_h_px          = 0      # altezza colonna testo in px schermo (0 = illimitata)
        self._seg_verse_start   = {}     # seg_idx -> (verseCount, labelCount, chorusCount)
        self._col_w_du          = None
        self._gap_du            = None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _mm_to_du(self, mm, ppi):
        return int(mm * ppi / 25.4)

    @staticmethod
    def _split_on_new_page(text):
        """
        Divide il testo su comandi {new_page} / {np} (case-insensitive).
        Le righe commentate con '#' vengono ignorate.
        Restituisce una lista di segmenti (almeno uno).
        """
        import re
        cmd_pat     = re.compile(r'\{\s*(?:new_page|np)\s*\}', re.IGNORECASE)
        comment_pat = re.compile(r'^\s*#')

        split_positions = []
        offset = 0
        for line in text.splitlines(keepends=True):
            if not comment_pat.match(line):
                for m in cmd_pat.finditer(line):
                    split_positions.append((offset + m.start(), offset + m.end()))
            offset += len(line)

        if not split_positions:
            return [text]

        parts = []
        prev = 0
        for start, end in split_positions:
            parts.append(text[prev:start])
            prev = end
        parts.append(text[prev:])

        return [p for p in parts if p.strip()] or [text]

    def _make_renderer(self):
        decorator = (
            self.frame_obj.pref.decorator
            if self.frame_obj.pref.labelVerses
            else SongDecorator()
        )
        r = Renderer(
            self.frame_obj.pref.format,
            decorator,
            self.frame_obj.pref.notations,
        )
        r.tempoDisplay    = getattr(self.frame_obj.pref, 'tempoDisplay',    0)
        r.timeDisplay     = getattr(self.frame_obj.pref, 'timeDisplay',     True)
        r.keyDisplay      = getattr(self.frame_obj.pref, 'keyDisplay',      True)
        r.tempoIconSize   = getattr(self.frame_obj.pref, 'tempoIconSize',   24)
        r.gridDisplayMode = getattr(self.frame_obj.pref, 'gridDisplayMode', 'pipe')
        r.gridDefaultLabel = getattr(self.frame_obj.pref, 'gridDefaultLabel', None)
        r.gridSizeDir     = getattr(self.frame_obj.pref, 'gridSizeDir',     'both')
        r.columns         = getattr(self.frame_obj, '_columns_per_page', 1)
        r.columnHeight    = getattr(self, '_col_h_px', 0)
        return r

    def _ensure_layout(self, dc):
        if self._page_offsets is not None:
            return

        pw, ph   = self.GetPageSizePixels()
        ppi_x, ppi_y = dc.GetPPI()

        ml = self._mm_to_du(self.frame_obj._margin_left,   ppi_x)
        mr = self._mm_to_du(self.frame_obj._margin_right,  ppi_x)
        mt = self._mm_to_du(self.frame_obj._margin_top,    ppi_y)
        mb = self._mm_to_du(self.frame_obj._margin_bottom, ppi_y)
        self._margin_du = (ml, mt, mr, mb)

        columns_per_page = getattr(self.frame_obj, '_columns_per_page', 1)

        if self.two_pages_per_sheet:
            gap      = self._mm_to_du(5, ppi_x)
            col_w    = (pw - ml - mr - gap) // 2
            usable_w = col_w
            usable_h = ph - mt - mb
            self._col_w_du = col_w
            self._gap_du   = gap
        else:
            usable_w = pw - ml - mr
            usable_h = ph - mt - mb

        if columns_per_page >= 2:
            col_gap_du      = self._mm_to_du(8, ppi_x)
            text_col_w      = (usable_w - col_gap_du) // 2
            self._col_h_px  = usable_h / (ppi_y / self._SCREEN_PPI)
            usable_w_for_scale = text_col_w
        else:
            self._col_h_px      = 0
            usable_w_for_scale  = usable_w

        self._usable_w_du = usable_w
        self._scale_x     = ppi_x / self._SCREEN_PPI * self._font_scale
        self._scale_y     = ppi_y / self._SCREEN_PPI * self._font_scale

        start, end  = self.frame_obj.text.GetSelection()
        # Se force_full è attivo, oppure non c'è selezione → stampa intero documento
        full_song   = self._force_full or (start == end)
        line_start  = self.frame_obj.text.LineFromPosition(start)
        line_end    = self.frame_obj.text.LineFromPosition(end)
        full_text   = self.frame_obj._strip_hash_commands(self.frame_obj.text.GetText())
        self._song_info = (full_song, line_start, line_end)

        if full_song:
            self._segments = self._split_on_new_page(full_text)
        else:
            self._segments = [full_text]

        mdc = wx.MemoryDC(wx.Bitmap(1, 1))
        self._page_offsets = []

        verse_count = label_count = chorus_count = 0
        for seg_idx, seg_text in enumerate(self._segments):
            r = self._make_renderer()
            r.initialVerseCount  = verse_count
            r.initialLabelCount  = label_count
            r.initialChorusCount = chorus_count
            self._seg_verse_start[seg_idx] = (verse_count, label_count, chorus_count)
            if full_song:
                sw, sh = r.Render(seg_text, mdc)
            else:
                sw, sh = r.Render(full_text, mdc, line_start, line_end)
            sw, sh = max(1, sw), max(1, sh)
            verse_count  = r.song.verseCount
            label_count  = r.song.labelCount
            chorus_count = r.song.chorusCount

            natural_w = sw * self._scale_x
            if natural_w > usable_w_for_scale:
                fit = usable_w_for_scale / natural_w
                self._scale_x = min(self._scale_x, self._scale_x * fit)
                self._scale_y = min(self._scale_y, self._scale_y * fit)

        # ── fit_to_page / shrink_to_fit ───────────────────────────────
        mdc2 = wx.MemoryDC(wx.Bitmap(1, 1))

        for seg_idx, seg_text in enumerate(self._segments):
            r = self._make_renderer()
            vc, lc, cc = self._seg_verse_start.get(seg_idx, (0, 0, 0))
            r.initialVerseCount  = vc
            r.initialLabelCount  = lc
            r.initialChorusCount = cc
            if full_song:
                sw, sh = r.Render(seg_text, mdc2)
            else:
                sw, sh = r.Render(full_text, mdc2, line_start, line_end)

        # Usa sh / scale_y come altezza totale del testo in device units
        total_h_px = sh

        if getattr(self.frame_obj, '_fit_to_page', False):
            if total_h_px * self._scale_y > usable_h:
                f = usable_h / (total_h_px * self._scale_y)
                self._scale_x *= f
                self._scale_y *= f

        if getattr(self.frame_obj, '_shrink_to_fit', False):
            min_margin_mm  = float(getattr(self.frame_obj, '_min_margin_shrink', 5))
            min_margin_du  = self._mm_to_du(min_margin_mm, ppi_y)
            reducible_du   = min(mt, mb) - min_margin_du

            r_check = self._make_renderer()
            vc, lc, cc = self._seg_verse_start.get(0, (0, 0, 0))
            r_check.initialVerseCount  = vc
            r_check.initialLabelCount  = lc
            r_check.initialChorusCount = cc
            _, sh_check = r_check.Render(
                self._segments[0] if full_song else full_text, mdc2
            )
            row_h = max(1, sh_check // max(1, sum(
                1 for ln in (self._segments[0] if full_song else full_text).splitlines() if ln.strip()
            )))

            px_per_page = usable_h / self._scale_y

            def _best_ppp(ppp):
                n = max(1, int(math.floor(ppp / row_h)))
                return n * row_h

            def _apply_margins(red_du):
                new_usable = usable_h + red_du
                new_ppp    = new_usable / self._scale_y
                return new_usable, _best_ppp(new_ppp)

            ideal_ppp = _best_ppp(px_per_page)
            gap       = px_per_page - ideal_ppp

            if gap > 0:
                gap_du = gap * self._scale_y
                if gap_du <= reducible_du:
                    usable_h, px_per_page = _apply_margins(gap_du)
                    px_per_page = _best_ppp(px_per_page)
                else:
                    if reducible_du > 0:
                        usable_h, px_per_page = _apply_margins(reducible_du)
                        ideal_ppp = _best_ppp(px_per_page)
                        gap       = px_per_page - ideal_ppp
                        gap_du    = gap * self._scale_y

                    if gap > 0:
                        n_rows_now  = max(1, int(math.floor(px_per_page / row_h)))
                        target_ppp  = n_rows_now * row_h
                        f           = usable_h / (self._scale_y * target_ppp)
                        if f < 1.0:
                            self._scale_x  *= f
                            self._scale_y  *= f
                            px_per_page     = usable_h / self._scale_y
                            px_per_page     = _best_ppp(px_per_page)

        # ── calcolo definitivo degli offsets di pagina ─────────────────
        px_per_page = usable_h / self._scale_y

        mdc3 = wx.MemoryDC(wx.Bitmap(1, 1))
        for seg_idx, seg_text in enumerate(self._segments):
            r = self._make_renderer()
            vc, lc, cc = self._seg_verse_start.get(seg_idx, (0, 0, 0))
            r.initialVerseCount  = vc
            r.initialLabelCount  = lc
            r.initialChorusCount = cc
            if full_song:
                sw, sh = r.Render(seg_text, mdc3)
            else:
                sw, sh = r.Render(full_text, mdc3, line_start, line_end)
            sw, sh = max(1, sw), max(1, sh)

            if getattr(self.frame_obj, '_remove_blank_pages', False) and sh <= 2:
                continue

            y = 0.0
            while y < sh:
                self._page_offsets.append((seg_idx, y))
                y += px_per_page

        if not self._page_offsets:
            self._page_offsets = [(0, 0.0)]

        # Rimuovi ultima pagina quasi vuota
        if getattr(self.frame_obj, '_remove_blank_pages', False) and len(self._page_offsets) > 1:
            last_seg_idx, last_y = self._page_offsets[-1]
            r_check = self._make_renderer()
            vc, lc, cc = self._seg_verse_start.get(last_seg_idx, (0, 0, 0))
            r_check.initialVerseCount  = vc
            r_check.initialLabelCount  = lc
            r_check.initialChorusCount = cc
            _, sh_last = r_check.Render(self._segments[last_seg_idx], mdc3)
            remaining  = sh_last - last_y
            threshold  = getattr(self.frame_obj, '_blank_page_threshold', 5) / 100.0
            if remaining < px_per_page * threshold:
                self._page_offsets.pop()

    # ── wx.Printout interface ─────────────────────────────────────────────────

    def _n_sheets(self):
        if self._page_offsets is None:
            dc = self.GetDC()
            if dc and dc.IsOk():
                self._ensure_layout(dc)
        n_logical = len(self._page_offsets) if self._page_offsets else 1
        if self.two_pages_per_sheet:
            return max(1, math.ceil(n_logical / 2))
        return max(1, n_logical)

    def GetPageInfo(self):
        n = self._n_sheets()
        return 1, n, 1, n

    def HasPage(self, page):
        return 1 <= page <= self._n_sheets()

    def OnPreparePrinting(self):
        dc = self.GetDC()
        if dc:
            self._ensure_layout(dc)

    def _render_logical_page(self, dc, logical_page_idx, origin_x, origin_y):
        if logical_page_idx >= len(self._page_offsets):
            return

        seg_idx, y_offset_px = self._page_offsets[logical_page_idx]
        ml, mt, mr, mb       = self._margin_du
        usable_h_du          = self.GetPageSizePixels()[1] - mt - mb
        full_song, line_start, line_end = self._song_info

        if full_song:
            seg_text = self._segments[seg_idx]
        else:
            seg_text = self.frame_obj._strip_hash_commands(self.frame_obj.text.GetText())

        dc.SetClippingRegion(origin_x, origin_y, self._usable_w_du, usable_h_du)
        dc.SetDeviceOrigin(origin_x, origin_y - int(y_offset_px * self._scale_y))
        dc.SetUserScale(self._scale_x, self._scale_y)

        r = self._make_renderer()
        vc, lc, cc = self._seg_verse_start.get(seg_idx, (0, 0, 0))
        r.initialVerseCount  = vc
        r.initialLabelCount  = lc
        r.initialChorusCount = cc
        if full_song:
            r.Render(seg_text, dc)
        else:
            r.Render(seg_text, dc, line_start, line_end)

        dc.SetUserScale(1.0, 1.0)
        dc.SetDeviceOrigin(0, 0)
        dc.DestroyClippingRegion()

    def OnPrintPage(self, page):
        dc = self.GetDC()
        self._ensure_layout(dc)

        ml, mt, mr, mb = self._margin_du
        pw, ph         = self.GetPageSizePixels()

        if self.two_pages_per_sheet:
            left_idx  = (page - 1) * 2
            right_idx = left_idx + 1
            n_logical = len(self._page_offsets)
            no_mirror = getattr(self.frame_obj, '_no_mirror_right', False)
            if right_idx >= n_logical:
                right_idx = None if no_mirror else left_idx

            left_x   = ml
            right_x  = ml + self._col_w_du + self._gap_du
            center_x = ml + self._col_w_du + self._gap_du // 2

            dc.SetPen(wx.Pen(wx.Colour(180, 180, 180), 1, wx.PENSTYLE_DOT))
            dc.DrawLine(center_x, mt, center_x, ph - mb)
            dc.SetPen(wx.NullPen)

            self._render_logical_page(dc, left_idx,  left_x,  mt)
            if right_idx is not None:
                self._render_logical_page(dc, right_idx, right_x, mt)
        else:
            page_idx = page - 1
            if page_idx >= len(self._page_offsets):
                return False
            self._render_logical_page(dc, page_idx, ml, mt)

        return True


# ══════════════════════════════════════════════════════════════════════════════
# PrintOptionsDialog  (dialog grafica ottimizzata)
# ══════════════════════════════════════════════════════════════════════════════

class PrintOptionsDialog:
    """
    Dialog «Opzioni di stampa» con grafica a sezioni (wx.StaticBoxSizer).

    Invocato da PrintManager._ask_two_pages_per_sheet(); riceve il frame
    come ``owner`` per poter leggere e scrivere i parametri di stampa.
    """

    def __init__(self, owner, parent=None, on_apply=None, _dlg_ref=None):
        self.owner    = owner
        self.on_apply = on_apply

        dialog_parent = parent if parent is not None else owner.frame

        self.dlg = wx.Dialog(
            dialog_parent,
            title=_("Print options"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP,
        )
        if _dlg_ref is not None:
            _dlg_ref[0] = self.dlg

        self._build_ui()
        self._bind_events()

        self.dlg.SetSizerAndFit(self._outer)
        self.dlg.CentreOnParent()

    # ── Costruzione UI ────────────────────────────────────────────────────────

    def _build_ui(self):
        owner = self.owner
        dlg   = self.dlg
        self._outer = outer = wx.BoxSizer(wx.VERTICAL)

        # ── Sezione Pagine ────────────────────────────────────────────
        box_pages = wx.StaticBoxSizer(wx.StaticBox(dlg, label=_("Pages")), wx.VERTICAL)
        self.cb = wx.CheckBox(dlg, label=_("Print 2 pages per sheet"))
        self.cb.SetValue(owner._two_pages_per_sheet)
        box_pages.Add(self.cb, 0, wx.ALL, _GAP)
        outer.Add(box_pages, 0, wx.EXPAND | wx.ALL, _GAP)

        # ── Sezione Colonne ───────────────────────────────────────────
        box_cols = wx.StaticBoxSizer(
            wx.StaticBox(dlg, label=_("Columns per page")), wx.HORIZONTAL
        )
        self.rb_col1 = wx.ToggleButton(dlg, label=_("1 column"))
        self.rb_col2 = wx.ToggleButton(dlg, label=_("2 columns"))
        self.rb_col1.SetValue(owner._columns_per_page == 1)
        self.rb_col2.SetValue(owner._columns_per_page == 2)
        box_cols.Add(self.rb_col1, 1, wx.EXPAND | wx.ALL, _GAP)
        box_cols.Add(self.rb_col2, 1, wx.EXPAND | wx.ALL, _GAP)
        outer.Add(box_cols, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, _GAP)

        # ── Sezione Ridimensionamento ──────────────────────────────────
        box_resize = wx.StaticBoxSizer(
            wx.StaticBox(dlg, label=_("Scaling")), wx.VERTICAL
        )

        self.cb_fit = wx.CheckBox(dlg, label=_("Fit to page"))
        self.cb_fit.SetValue(owner._fit_to_page)
        box_resize.Add(self.cb_fit, 0, wx.ALL, _GAP)

        # cb_shrink + nota secondaria
        shrink_panel = wx.Panel(dlg)
        shrink_vsz   = wx.BoxSizer(wx.VERTICAL)
        self.cb_shrink = wx.CheckBox(
            shrink_panel, label=_("Shrink to fit current page")
        )
        self.cb_shrink.SetValue(owner._shrink_to_fit)
        note = wx.StaticText(shrink_panel, label=_("(prevent bottom clipping)"))
        note.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
        nf = note.GetFont()
        nf.SetPointSize(max(7, nf.GetPointSize() - 1))
        note.SetFont(nf)
        shrink_vsz.Add(self.cb_shrink, 0)
        shrink_vsz.Add(note, 0, wx.LEFT, 20)
        shrink_panel.SetSizer(shrink_vsz)
        box_resize.Add(shrink_panel, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, _GAP)

        # Spin margine minimo
        row1 = wx.BoxSizer(wx.HORIZONTAL)
        self.lbl_min_margin = wx.StaticText(
            dlg, label=_("Min margin for auto-shrink (mm):")
        )
        self.spin_min_margin = wx.SpinCtrl(
            dlg, min=0, max=50,
            value=str(getattr(owner, '_min_margin_shrink', 5)),
            size=(60, -1),
        )
        row1.Add(self.lbl_min_margin, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        row1.Add(self.spin_min_margin, 0, wx.ALIGN_CENTER_VERTICAL)
        box_resize.Add(row1, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, _GAP)

        self.lbl_min_margin.Enable(owner._shrink_to_fit)
        self.spin_min_margin.Enable(owner._shrink_to_fit)

        outer.Add(box_resize, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, _GAP)

        # ── Sezione Opzioni avanzate ───────────────────────────────────
        box_adv = wx.StaticBoxSizer(
            wx.StaticBox(dlg, label=_("Advanced options")), wx.VERTICAL
        )

        self.cb_no_mirror = wx.CheckBox(
            dlg, label=_("Do not replicate (leave right half blank)")
        )
        self.cb_no_mirror.SetValue(owner._no_mirror_right)
        self.cb_no_mirror.Enable(owner._two_pages_per_sheet)
        box_adv.Add(self.cb_no_mirror, 0, wx.ALL, _GAP)

        self.cb_remove_blank = wx.CheckBox(dlg, label=_("Remove blank pages"))
        self.cb_remove_blank.SetValue(owner._remove_blank_pages)
        box_adv.Add(self.cb_remove_blank, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, _GAP)

        row2 = wx.BoxSizer(wx.HORIZONTAL)
        self.lbl_blank_threshold = wx.StaticText(dlg, label=_("Blank page threshold (%):"))
        self.spin_blank_threshold = wx.SpinCtrl(
            dlg, min=1, max=95,
            value=str(getattr(owner, '_blank_page_threshold', 5)),
            size=(60, -1),
        )
        row2.Add(self.lbl_blank_threshold, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        row2.Add(self.spin_blank_threshold, 0, wx.ALIGN_CENTER_VERTICAL)
        box_adv.Add(row2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, _GAP)

        self.lbl_blank_threshold.Enable(owner._remove_blank_pages)
        self.spin_blank_threshold.Enable(owner._remove_blank_pages)

        outer.Add(box_adv, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, _GAP)

        # ── Sezione Scala ──────────────────────────────────────────────
        box_scale = wx.StaticBoxSizer(
            wx.StaticBox(dlg, label=_("Scale")), wx.HORIZONTAL
        )
        lbl_scale = wx.StaticText(dlg, label=_("Scale (%):"))
        self.spin_font_scale = wx.SpinCtrl(
            dlg, min=50, max=200,
            value=str(getattr(owner, '_print_font_scale', 100)),
            size=(70, -1),
        )
        box_scale.Add(lbl_scale, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, _GAP)
        box_scale.Add(self.spin_font_scale, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, _GAP)
        outer.Add(box_scale, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, _GAP)

        # ── Sezione Ambito di stampa ───────────────────────────────────
        # Rileva se c'è una selezione attiva nell'editor
        start, end = owner.text.GetSelection()
        self._has_selection = (start != end)

        box_scope = wx.StaticBoxSizer(
            wx.StaticBox(dlg, label=_("Print scope")), wx.VERTICAL
        )
        current_scope = getattr(owner, '_print_scope', 'auto')

        self.rb_scope_full = wx.RadioButton(
            dlg, label=_("Entire document"), style=wx.RB_GROUP
        )
        self.rb_scope_sel  = wx.RadioButton(
            dlg, label=_("Selection only")
        )

        # Stato iniziale
        if self._has_selection and current_scope == 'selection':
            self.rb_scope_sel.SetValue(True)
            self.rb_scope_full.SetValue(False)
        else:
            self.rb_scope_full.SetValue(True)
            self.rb_scope_sel.SetValue(False)

        # Disabilita "Selezione" se non c'è testo selezionato
        self.rb_scope_sel.Enable(self._has_selection)

        # Nota descrittiva (pattern identico a MusicalSymbolDialog)
        if self._has_selection:
            scope_note_text = _("A text selection is active in the editor.")
        else:
            scope_note_text = _("No active selection — printing entire document.")

        _scope_note_row = wx.BoxSizer(wx.HORIZONTAL)
        _scope_info_icon = wx.StaticText(dlg, label=u"\u2139")   # ℹ
        _icon_font = _scope_info_icon.GetFont()
        _icon_font.SetPointSize(_icon_font.GetPointSize() + 1)
        _icon_font.SetWeight(wx.FONTWEIGHT_BOLD)
        _scope_info_icon.SetFont(_icon_font)
        _scope_info_icon.SetForegroundColour(wx.Colour(0, 100, 180))
        _scope_note_row.Add(_scope_info_icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        self._scope_note = wx.StaticText(dlg, label=scope_note_text)
        _note_font = self._scope_note.GetFont()
        _note_font.SetPointSize(max(_note_font.GetPointSize() - 1, 7))
        _note_font.SetStyle(wx.FONTSTYLE_ITALIC)
        self._scope_note.SetFont(_note_font)
        self._scope_note.SetForegroundColour(wx.Colour(90, 90, 90))
        _scope_note_row.Add(self._scope_note, 0, wx.ALIGN_CENTER_VERTICAL)

        box_scope.Add(self.rb_scope_full, 0, wx.ALL, _GAP)
        box_scope.Add(self.rb_scope_sel,  0, wx.LEFT | wx.RIGHT | wx.BOTTOM, _GAP)
        box_scope.Add(_scope_note_row,    0, wx.LEFT | wx.BOTTOM, _GAP + 2)
        outer.Add(box_scope, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, _GAP)

        # ── Bottoni ────────────────────────────────────────────────────
        PIN_OFF = u"📌"
        PIN_ON  = u"📍"
        self._pinned = [getattr(owner, '_print_options_pinned', False)]

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_pin = wx.Button(
            dlg, wx.ID_ANY,
            PIN_ON if self._pinned[0] else PIN_OFF,
            size=(32, -1),
        )
        self.btn_pin.SetToolTip(_("Keep this dialog open after applying"))
        self.btn_ok     = wx.Button(dlg, wx.ID_OK,     _("OK"))
        self.btn_cancel = wx.Button(dlg, wx.ID_CANCEL, _("Cancel"))
        self.btn_ok.SetDefault()

        btn_sizer.Add(self.btn_pin,    0, wx.RIGHT, 4)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(self.btn_ok,     0, wx.RIGHT, 4)
        btn_sizer.Add(self.btn_cancel, 0)
        outer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, _GAP)

    # ── Bind ──────────────────────────────────────────────────────────────────

    def _bind_events(self):
        self.rb_col1.Bind(wx.EVT_TOGGLEBUTTON, self._on_col1)
        self.rb_col2.Bind(wx.EVT_TOGGLEBUTTON, self._on_col2)
        self.cb_shrink.Bind(wx.EVT_CHECKBOX, self._on_shrink_changed)
        self.cb_remove_blank.Bind(wx.EVT_CHECKBOX, self._on_remove_blank_changed)
        self.cb.Bind(wx.EVT_CHECKBOX, self._on_two_pages_changed)
        self.rb_scope_full.Bind(wx.EVT_RADIOBUTTON, self._on_scope_changed)
        self.rb_scope_sel.Bind(wx.EVT_RADIOBUTTON, self._on_scope_changed)
        self.btn_pin.Bind(wx.EVT_BUTTON, self._on_pin)
        self.btn_ok.Bind(wx.EVT_BUTTON, self._on_ok)

    # ── Handler eventi ────────────────────────────────────────────────────────

    def _on_col1(self, evt):
        self.rb_col1.SetValue(True)
        self.rb_col2.SetValue(False)

    def _on_col2(self, evt):
        self.rb_col2.SetValue(True)
        self.rb_col1.SetValue(False)

    def _on_shrink_changed(self, evt):
        enabled = self.cb_shrink.GetValue()
        self.lbl_min_margin.Enable(enabled)
        self.spin_min_margin.Enable(enabled)
        evt.Skip()

    def _on_remove_blank_changed(self, evt):
        enabled = self.cb_remove_blank.GetValue()
        self.lbl_blank_threshold.Enable(enabled)
        self.spin_blank_threshold.Enable(enabled)
        evt.Skip()

    def _on_two_pages_changed(self, evt):
        self.cb_no_mirror.Enable(self.cb.GetValue())
        evt.Skip()

    def _on_scope_changed(self, evt):
        evt.Skip()  # aggiornamento in _apply_options al momento dell'OK

    def _on_pin(self, evt):
        PIN_OFF = u"📌"
        PIN_ON  = u"📍"
        self._pinned[0] = not self._pinned[0]
        self.owner._print_options_pinned = self._pinned[0]
        self.btn_pin.SetLabel(PIN_ON if self._pinned[0] else PIN_OFF)

    def _on_ok(self, evt):
        self._apply_options()
        if not self._pinned[0]:
            self.dlg.EndModal(wx.ID_OK)

    # ── Logica ────────────────────────────────────────────────────────────────

    def _apply_options(self):
        o = self.owner
        o._two_pages_per_sheet  = self.cb.GetValue()
        o._columns_per_page     = 2 if self.rb_col2.GetValue() else 1
        o._fit_to_page          = self.cb_fit.GetValue()
        o._shrink_to_fit        = self.cb_shrink.GetValue()
        o._min_margin_shrink    = self.spin_min_margin.GetValue()
        o._no_mirror_right      = self.cb_no_mirror.GetValue()
        o._remove_blank_pages   = self.cb_remove_blank.GetValue()
        o._blank_page_threshold = self.spin_blank_threshold.GetValue()
        o._print_font_scale     = self.spin_font_scale.GetValue()
        # Ambito di stampa
        if self._has_selection and self.rb_scope_sel.GetValue():
            o._print_scope = 'selection'
        else:
            o._print_scope = 'full'
        if self.on_apply is not None:
            self.on_apply()

    def show(self):
        """Mostra il dialog in modo modale. Restituisce True se confermato."""
        result = self.dlg.ShowModal()
        self.dlg.Destroy()
        return result == wx.ID_OK


# ══════════════════════════════════════════════════════════════════════════════
# PrintManager  (mixin da aggiungere a SongpressFrame)
# ══════════════════════════════════════════════════════════════════════════════

class PrintManager:
    """
    Mixin che raccoglie tutto lo stato e i metodi legati alla stampa.

    Aggiungere come base di SongpressFrame e chiamare PrintManager.__init__(self)
    nel costruttore di SongpressFrame, PRIMA di _LoadPageMargins().
    """

    # ── Dizionario formato carta ───────────────────────────────────────────────

    _PAPER_SIZE_MM = _PAPER_SIZE_MM

    # ── Init ──────────────────────────────────────────────────────────────────

    def __init__(self):
        self._print_data = wx.PrintData()
        self._print_data.SetPaperId(wx.PAPER_A4)
        self._print_data.SetOrientation(wx.PORTRAIT)

        # Margini in mm
        self._margin_top    = 15
        self._margin_bottom = 15
        self._margin_left   = 15
        self._margin_right  = 15

        # Opzioni di stampa
        self._two_pages_per_sheet  = False
        self._columns_per_page     = 1
        self._fit_to_page          = False
        self._no_mirror_right      = False
        self._remove_blank_pages   = False
        self._blank_page_threshold = 5
        self._shrink_to_fit        = False
        self._min_margin_shrink    = 5
        self._print_font_scale     = 100
        self._print_options_pinned = False
        # 'auto'       = comportamento originale: selezione se attiva, altrimenti tutto
        # 'selection'  = stampa solo la selezione corrente
        # 'full'       = stampa sempre l'intero documento
        self._print_scope          = 'auto'

        self._preview_frame = None

    # ── Persist ───────────────────────────────────────────────────────────────

    def _SavePageMargins(self):
        """Salva margini, formato carta, orientamento e opzioni di riduzione."""
        try:
            self.config.SetPath('/PageSetup')
            self.config.Write('margin_top',        str(self._margin_top))
            self.config.Write('margin_bottom',     str(self._margin_bottom))
            self.config.Write('margin_left',       str(self._margin_left))
            self.config.Write('margin_right',      str(self._margin_right))
            self.config.Write('paper_id',          str(self._print_data.GetPaperId()))
            self.config.Write('orientation',       str(self._print_data.GetOrientation()))
            self.config.Write('shrink_to_fit',     '1' if self._shrink_to_fit else '0')
            self.config.Write('min_margin_shrink', str(self._min_margin_shrink))
        except Exception:
            pass

    def _LoadPageMargins(self):
        """Ripristina margini, formato carta, orientamento e opzioni di riduzione."""
        try:
            self.config.SetPath('/PageSetup')
            top         = self.config.Read('margin_top')
            bottom      = self.config.Read('margin_bottom')
            left        = self.config.Read('margin_left')
            right       = self.config.Read('margin_right')
            if top:    self._margin_top    = int(top)
            if bottom: self._margin_bottom = int(bottom)
            if left:   self._margin_left   = int(left)
            if right:  self._margin_right  = int(right)
            paper_id    = self.config.Read('paper_id')
            if paper_id:
                self._print_data.SetPaperId(int(paper_id))
            orientation = self.config.Read('orientation')
            if orientation:
                self._print_data.SetOrientation(int(orientation))
            shrink      = self.config.Read('shrink_to_fit')
            if shrink:
                self._shrink_to_fit = (shrink == '1')
            min_m       = self.config.Read('min_margin_shrink')
            if min_m:
                self._min_margin_shrink = int(min_m)
        except Exception:
            pass

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _GetPaperSizeMm(self):
        """Restituisce (w_mm, h_mm) del foglio tenendo conto dell'orientamento."""
        pid  = self._print_data.GetPaperId()
        w, h = self._PAPER_SIZE_MM.get(pid, (210.0, 297.0))
        if self._print_data.GetOrientation() == wx.LANDSCAPE:
            w, h = h, w
        return w, h

    def _make_printout(self, title=None):
        """Crea e restituisce un SongpressPrintout configurato.

        Tiene conto di _print_scope:
          'full'      → forza stampa intero documento (ignora selezione)
          'selection' → stampa solo la selezione (comportamento naturale se c'è selezione)
          'auto'      → lascia decidere a SongpressPrintout in base alla selezione attiva
        """
        if title is None:
            title = _("Print")
        scope = getattr(self, '_print_scope', 'auto')
        # force_full=True solo quando esplicitamente richiesto 'full'
        # (in 'auto' e 'selection' il comportamento è gestito da _ensure_layout
        #  tramite GetSelection())
        force_full = (scope == 'full')
        return SongpressPrintout(
            self, title,
            two_pages_per_sheet=self._two_pages_per_sheet,
            font_scale=getattr(self, '_print_font_scale', 100),
            force_full=force_full,
        )

    # ── Azioni ────────────────────────────────────────────────────────────────

    def OnPageSetup(self, evt):
        """Apre il dialog di impostazione pagina (formato, orientamento, margini)."""
        data = wx.PageSetupDialogData(self._print_data)
        data.SetMarginTopLeft(wx.Point(self._margin_left, self._margin_top))
        data.SetMarginBottomRight(wx.Point(self._margin_right, self._margin_bottom))
        dlg = wx.PageSetupDialog(self.frame, data)
        if dlg.ShowModal() == wx.ID_OK:
            result = dlg.GetPageSetupData()
            self._print_data    = wx.PrintData(result.GetPrintData())
            tl                  = result.GetMarginTopLeft()
            br                  = result.GetMarginBottomRight()
            self._margin_left   = tl.x
            self._margin_top    = tl.y
            self._margin_right  = br.x
            self._margin_bottom = br.y
            w_mm, h_mm = self._GetPaperSizeMm()
            self.previewCanvas.SetPageSizeMm(w_mm, h_mm)
            self.previewCanvas.SetPageMarginsMm(self._margin_top, self._margin_bottom)
        dlg.Destroy()

    def _reopen_print_options_if_pinned(self):
        """Riapre il dialog opzioni di stampa se il pin era attivo.
        Chiamato da wx.CallLater dopo che OnPrintPreview ha creato il nuovo pf."""
        if not getattr(self, '_print_options_pinned', False):
            return
        pf = getattr(self, '_preview_frame', None)
        if pf is None or not pf.IsShown():
            return

        _dlg_ref = [None]

        def _do_apply():
            self.previewCanvas.SetColumns(self._columns_per_page)
            self.previewCanvas.Refresh(self._get_display_text())
            if self._print_options_pinned and _dlg_ref[0] is not None:
                dlg = _dlg_ref[0]
                dlg.EndModal(wx.ID_OK)

                def _deferred_reopen():
                    pf.Close()
                    self.OnPrintPreview(None)
                    wx.CallAfter(
                        wx.CallLater, 50,
                        lambda: self._reopen_print_options_if_pinned()
                    )
                wx.CallAfter(_deferred_reopen)
            else:
                pf.Close()
                wx.CallAfter(self.OnPrintPreview, None)

        self._ask_two_pages_per_sheet(parent=pf, on_apply=_do_apply, _dlg_ref=_dlg_ref)

    def _ask_two_pages_per_sheet(self, parent=None, on_apply=None, _dlg_ref=None):
        """
        Mostra il dialog «Opzioni di stampa» (grafica ottimizzata).

        Args:
            parent:   finestra padre (default: self.frame)
            on_apply: callable invocato dopo il salvataggio delle opzioni
            _dlg_ref: lista [None] popolata con l'istanza wx.Dialog
        """
        dlg_wrapper = PrintOptionsDialog(
            owner=self,
            parent=parent,
            on_apply=on_apply,
            _dlg_ref=_dlg_ref,
        )
        return dlg_wrapper.show()

    def OnPrint(self, evt):
        """Stampa il brano esattamente come mostrato nell'anteprima."""
        if getattr(self.pref, 'showPrintPreview', True):
            self.OnPrintPreview(evt)
            return

        pdd = wx.PrintDialogData(self._print_data)
        dlg = wx.PrintDialog(self.frame, pdd)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        self._print_data = wx.PrintData(dlg.GetPrintDialogData().GetPrintData())
        dlg.Destroy()

        pdd2    = wx.PrintDialogData(self._print_data)
        printer = wx.Printer(pdd2)
        title   = os.path.splitext(os.path.basename(self.document))[0] \
                  if self.document else _("Print")
        printout = self._make_printout(title)
        success  = printer.Print(self.frame, printout, False)
        if not success and printer.GetLastError() == wx.PRINTER_ERROR:
            wx.MessageBox(
                _("An error occurred while printing.\nPlease check your printer settings."),
                _("Print error"),
                wx.OK | wx.ICON_ERROR,
                self.frame,
            )
        printout.Destroy()

    def OnPrintPreview(self, evt):
        """Mostra l'anteprima di stampa del brano."""
        self.previewCanvas.Refresh(self._get_display_text())
        base_title = os.path.splitext(os.path.basename(self.document))[0] \
                     if self.document else _("Print")
        scope = getattr(self, '_print_scope', 'auto')
        start, end = self.text.GetSelection()
        has_sel    = (start != end)
        if scope == 'selection' and has_sel:
            title = u"{} — {}".format(base_title, _("Selection"))
        else:
            title = base_title

        printout1 = self._make_printout(title)
        printout2 = self._make_printout(title)
        preview   = wx.PrintPreview(printout1, printout2, self._print_data)

        if not preview.IsOk():
            wx.MessageBox(
                _("Unable to create print preview.\nPlease check your printer settings."),
                _("Print preview error"),
                wx.OK | wx.ICON_ERROR,
                self.frame,
            )
            return

        pf = wx.PreviewFrame(preview, self.frame, _("Print preview"))
        pf.Initialize()
        self._preview_frame = pf

        # ── Personalizzazione toolbar di anteprima ─────────────────────
        ctrl_bar = None
        get_cb   = getattr(pf, 'GetControlBar', None)
        if get_cb is not None:
            ctrl_bar = get_cb()
        if ctrl_bar is None:
            for child in pf.GetChildren():
                if isinstance(child, wx.PreviewControlBar):
                    ctrl_bar = child
                    break

        if ctrl_bar is not None:
            # Rinomina bottoni nativi seguendo la locale attiva
            _label_map = {
                "Print":    _("Print..."),
                "Print...": _("Print..."),
                "Next":     _("Next page"),
                "Prev":     _("Previous page"),
                "Previous": _("Previous page"),
                "First":    _("First page"),
                "Last":     _("Last page"),
                "Close":    _("Close"),
            }
            for child in ctrl_bar.GetChildren():
                if isinstance(child, wx.Button):
                    lbl = child.GetLabel().strip()
                    if lbl in _label_map:
                        child.SetLabel(_label_map[lbl])
            btn_print = ctrl_bar.FindWindowById(wx.ID_PRINT)
            if btn_print is not None:
                btn_print.SetLabel(_("Print..."))

            # Bottone «Opzioni di stampa»
            btn_options = wx.Button(ctrl_bar, wx.ID_ANY, _("Print options..."))
            _icon_path  = glb.AddPath('img/productivity-expert-icon.png')
            if os.path.isfile(_icon_path):
                img = wx.Image(_icon_path, wx.BITMAP_TYPE_PNG)
                btn_options.SetBitmap(wx.Bitmap(img))
                btn_options.SetBitmapPosition(wx.LEFT)

            def on_print_options(e):
                _dlg_ref = [None]

                def _do_apply():
                    self.previewCanvas.SetColumns(self._columns_per_page)
                    self.previewCanvas.Refresh(self._get_display_text())
                    if self._print_options_pinned and _dlg_ref[0] is not None:
                        _dlg_ref[0].EndModal(wx.ID_OK)

                        def _deferred_reopen():
                            pf.Close()
                            self.OnPrintPreview(None)
                            wx.CallAfter(
                                wx.CallLater, 50,
                                lambda: self._reopen_print_options_if_pinned()
                            )
                        wx.CallAfter(_deferred_reopen)
                    else:
                        pf.Close()
                        wx.CallAfter(self.OnPrintPreview, None)

                self._ask_two_pages_per_sheet(
                    parent=pf, on_apply=_do_apply, _dlg_ref=_dlg_ref
                )

            btn_options.Bind(wx.EVT_BUTTON, on_print_options)

            # Bottone «Impostazione pagina»
            btn_page_setup  = wx.Button(ctrl_bar, wx.ID_ANY, _("Page setup..."))
            _page_icon_path = glb.AddPath('img/file-black-icon.png')
            if os.path.isfile(_page_icon_path):
                img = wx.Image(_page_icon_path, wx.BITMAP_TYPE_PNG)
                btn_page_setup.SetBitmap(wx.Bitmap(img))
                btn_page_setup.SetBitmapPosition(wx.LEFT)

            def on_page_setup_preview(e):
                data = wx.PageSetupDialogData(self._print_data)
                data.SetMarginTopLeft(wx.Point(self._margin_left, self._margin_top))
                data.SetMarginBottomRight(wx.Point(self._margin_right, self._margin_bottom))
                dlg = wx.PageSetupDialog(pf, data)
                if dlg.ShowModal() == wx.ID_OK:
                    result = dlg.GetPageSetupData()
                    self._print_data    = wx.PrintData(result.GetPrintData())
                    tl                  = result.GetMarginTopLeft()
                    br                  = result.GetMarginBottomRight()
                    self._margin_left   = tl.x
                    self._margin_top    = tl.y
                    self._margin_right  = br.x
                    self._margin_bottom = br.y
                    dlg.Destroy()
                    pf.Close()
                    wx.CallAfter(self.OnPrintPreview, None)
                else:
                    dlg.Destroy()

            btn_page_setup.Bind(wx.EVT_BUTTON, on_page_setup_preview)

            # Bottone «Chiudi»
            btn_close = wx.Button(ctrl_bar, wx.ID_ANY, _("Close"))
            btn_close.Bind(wx.EVT_BUTTON, lambda e: pf.Close())

            # Nasconde il bottone Close nativo
            native_close = ctrl_bar.FindWindowById(wx.ID_CLOSE)
            if native_close is not None:
                native_close.Hide()
            else:
                for child in ctrl_bar.GetChildren():
                    if isinstance(child, wx.AnyButton) and \
                            child.GetLabel().strip() in ('Close', _('Close')):
                        child.Hide()
                        break

            # Inserisce i bottoni personalizzati nella toolbar
            sizer = ctrl_bar.GetSizer()
            if sizer:
                spacer_idx = None
                for i in range(sizer.GetItemCount() - 1, -1, -1):
                    item = sizer.GetItem(i)
                    if item.IsSpacer() and item.GetProportion() > 0:
                        spacer_idx = i
                        break
                ins = (spacer_idx + 1) if spacer_idx is not None else sizer.GetItemCount()
                sizer.Insert(ins,     btn_page_setup, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
                sizer.Insert(ins + 1, btn_options,    0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
                sizer.Insert(ins + 2, btn_close,      0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)

            # Uniforma altezza bottoni
            ref_h = btn_options.GetBestSize().height
            for btn in (btn_page_setup, btn_close):
                btn.SetMinSize(wx.Size(btn.GetBestSize().width, ref_h))
            ctrl_bar.Layout()

            def _equalize_heights():
                try:
                    h = btn_options.GetSize().height
                    if h < 4:
                        return
                    for btn in (btn_page_setup, btn_close):
                        bw = btn.GetSize().width
                        btn.SetMinSize(wx.Size(bw, h))
                        btn.SetSize(wx.Size(bw, h))
                    ctrl_bar.Layout()
                except Exception:
                    pass
            wx.CallAfter(_equalize_heights)

        pf.Show()

        # Al chiusura della preview ripristina il canvas al testo intero
        def _on_preview_close(e):
            e.Skip()
            wx.CallAfter(
                self.previewCanvas.Refresh,
                self._strip_hash_commands(self.text.GetText()),
            )
        pf.Bind(wx.EVT_CLOSE, _on_preview_close)

        # Dimensiona la finestra di anteprima al 90% dell'area di lavoro
        display_idx = wx.Display.GetFromWindow(self.frame)
        if display_idx == wx.NOT_FOUND:
            display_idx = 0
        display     = wx.Display(display_idx)
        client_area = display.GetClientArea()
        preview_w   = min(int(client_area.width  * 0.90), client_area.width)
        preview_h   = min(int(client_area.height * 0.90), client_area.height)
        pf.SetSize(wx.Size(preview_w, preview_h))
        pf.CentreOnScreen()
