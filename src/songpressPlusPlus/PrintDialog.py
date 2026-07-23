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

# ── Rilevamento duplex dal driver di sistema ───────────────────────────────────

def _get_duplex_mode(print_data):
    """
    Restituisce la modalità duplex reale della stampante selezionata.

    Strategia (Windows):
      1. Prova win32print per leggere il DEVMODE del driver nativo → fonte più
         affidabile, riflette le impostazioni del pannello del driver (es. Brother).
      2. Fallback: wx.PrintData.GetDuplex() → utile se wx ha impostato il duplex
         esplicitamente (es. dall'utente tramite PrintDialog di wx).

    Su macOS / Linux restituisce direttamente il valore wx.

    Valori restituiti (costanti wx):
      wx.DUPLEX_SIMPLEX     – stampa su un solo lato
      wx.DUPLEX_HORIZONTAL  – fronte/retro, rilegatura lato corto
      wx.DUPLEX_VERTICAL    – fronte/retro, rilegatura lato lungo
    """
    # ── Tentativo win32print (solo Windows) ───────────────────────────────
    if wx.Platform == '__WXMSW__':
        try:
            import win32print

            # Nome stampante: preferisce quello in print_data, altrimenti default
            printer_name = print_data.GetPrinterName().strip()
            if not printer_name:
                printer_name = win32print.GetDefaultPrinter()

            # Apre la stampante in sola lettura
            hprinter = win32print.OpenPrinter(printer_name)
            try:
                # Livello 2 → struttura PRINTER_INFO_2 con DEVMODE
                info = win32print.GetPrinter(hprinter, 2)
            finally:
                win32print.ClosePrinter(hprinter)

            devmode = info.get('pDevMode')
            if devmode is not None:
                # dmDuplex: 1 = simplex, 2 = vertical (long-edge), 3 = horizontal (short-edge)
                dm_duplex = getattr(devmode, 'Duplex', 1)
                if dm_duplex == 2:
                    return wx.DUPLEX_VERTICAL       # rilegatura lato lungo  (caso più comune)
                elif dm_duplex == 3:
                    return wx.DUPLEX_HORIZONTAL     # rilegatura lato corto
                else:
                    return wx.DUPLEX_SIMPLEX
        except Exception:
            pass  # win32print non disponibile o errore → fallback sotto

    # ── Fallback: valore wx.PrintData ─────────────────────────────────────
    return print_data.GetDuplex()


def _get_color_mode(print_data):
    """
    Restituisce la modalità colore reale della stampante selezionata.

    Strategia (Windows):
      1. Prova win32print per leggere il DEVMODE del driver nativo → fonte più
         affidabile, riflette le impostazioni del pannello del driver (es. Brother).
      2. Fallback: wx.PrintData.GetColour() → True se colore, False se B/N.

    Su macOS / Linux restituisce direttamente il valore wx.

    Valori restituiti:
      "color"   – stampa a colori
      "mono"    – stampa in bianco e nero / scala di grigi
      "unknown" – impossibile determinare la modalità
    """
    # ── Tentativo win32print (solo Windows) ───────────────────────────────
    if wx.Platform == '__WXMSW__':
        try:
            import win32print

            printer_name = print_data.GetPrinterName().strip()
            if not printer_name:
                printer_name = win32print.GetDefaultPrinter()

            hprinter = win32print.OpenPrinter(printer_name)
            try:
                info = win32print.GetPrinter(hprinter, 2)
            finally:
                win32print.ClosePrinter(hprinter)

            devmode = info.get('pDevMode')
            if devmode is not None:
                # dmColor: 1 = DMCOLOR_MONOCHROME, 2 = DMCOLOR_COLOR
                dm_color = getattr(devmode, 'Color', None)
                if dm_color == 2:
                    return "color"
                elif dm_color == 1:
                    return "mono"
                # dm_color None o valore imprevisto → fallback wx sotto
        except Exception:
            pass

    # ── Fallback: wx.PrintData.GetColour() ────────────────────────────────
    try:
        return "color" if print_data.GetColour() else "mono"
    except Exception:
        return "unknown"


def _get_orientation(print_data):
    """
    Restituisce l'orientamento reale della stampante selezionata.

    Strategia (Windows):
      1. Prova win32print per leggere dmOrientation dal DEVMODE del driver.
      2. Fallback: wx.PrintData.GetOrientation().

    Su macOS / Linux restituisce direttamente il valore wx.

    Valori restituiti (costanti wx):
      wx.PORTRAIT   – orientamento verticale
      wx.LANDSCAPE  – orientamento orizzontale
    """
    if wx.Platform == '__WXMSW__':
        try:
            import win32print

            printer_name = print_data.GetPrinterName().strip()
            if not printer_name:
                printer_name = win32print.GetDefaultPrinter()

            hprinter = win32print.OpenPrinter(printer_name)
            try:
                info = win32print.GetPrinter(hprinter, 2)
            finally:
                win32print.ClosePrinter(hprinter)

            devmode = info.get('pDevMode')
            if devmode is not None:
                # dmOrientation: 1 = PORTRAIT, 2 = LANDSCAPE
                orient = getattr(devmode, 'Orientation', None)
                if orient == 2:
                    return wx.LANDSCAPE
                elif orient == 1:
                    return wx.PORTRAIT
        except Exception:
            pass

    return print_data.GetOrientation()


def _make_orientation_bitmap(landscape: bool, field_h: int) -> wx.Bitmap:
    """
    Disegna e restituisce un wx.Bitmap che raffigura un foglio A4 stilizzato.

    Portrait:  rettangolo verticale  (proporzione ~√2)
    Landscape: rettangolo orizzontale (stesse dimensioni, ruotato 90°)

    Il bitmap viene disegnato su sfondo trasparente tramite wx.GraphicsContext
    in modo da adattarsi a qualsiasi colore della status bar.

    Parametri
    ----------
    landscape : bool
        True → foglio orizzontale, False → foglio verticale.
    field_h : int
        Altezza in pixel del campo della status bar; l'icona viene
        dimensionata per occuparne circa il 75 %.
    """
    # ── dimensioni icona ──────────────────────────────────────────────────
    icon_h = max(10, int(field_h * 0.75))
    # proporzione A4 ≈ 1 : √2  →  corto = icon_h / √2
    short = max(6, int(icon_h / 1.4142))

    if landscape:
        bmp_w, bmp_h = icon_h, short          # larghezza > altezza
        rect_w, rect_h = icon_h - 2, short - 2
    else:
        bmp_w, bmp_h = short, icon_h          # altezza > larghezza
        rect_w, rect_h = short - 2, icon_h - 2

    bmp = wx.Bitmap(bmp_w, bmp_h, 32)

    # ── disegno tramite GraphicsContext (anti-alias + trasparenza) ────────
    mdc = wx.MemoryDC(bmp)
    gc  = wx.GraphicsContext.Create(mdc)

    # sfondo trasparente
    gc.SetBrush(wx.TRANSPARENT_BRUSH)
    gc.SetPen(wx.TRANSPARENT_PEN)
    gc.DrawRectangle(0, 0, bmp_w, bmp_h)

    # colori
    if landscape:
        fill   = wx.Colour(180, 210, 255)   # azzurro chiaro
        border = wx.Colour( 20, 100, 180)   # blu
    else:
        fill   = wx.Colour(220, 220, 220)   # grigio chiaro
        border = wx.Colour( 80,  80,  80)   # grigio scuro

    gc.SetBrush(wx.Brush(fill))
    gc.SetPen(wx.Pen(border, 1))
    gc.DrawRectangle(1, 1, rect_w, rect_h)

    # angolo ripiegato (dog-ear) in alto a destra — proporzione ~20 % del lato corto
    ear = max(3, int(min(rect_w, rect_h) * 0.22))
    x0  = 1 + rect_w - ear          # x inizio taglio
    y0  = 1                          # y in cima

    # ridisegna solo il corpo del foglio senza l'angolo
    gc.SetBrush(wx.Brush(fill))
    gc.SetPen(wx.Pen(border, 1))
    path = gc.CreatePath()
    path.MoveToPoint(1,            y0)
    path.AddLineToPoint(x0,        y0)
    path.AddLineToPoint(x0 + ear,  y0 + ear)
    path.AddLineToPoint(x0 + ear,  y0 + rect_h)
    path.AddLineToPoint(1,         y0 + rect_h)
    path.CloseSubpath()
    gc.DrawPath(path)

    # triangolino dell'angolo ripiegato (colore leggermente più scuro)
    fold_colour = wx.Colour(
        max(0, fill.Red()   - 40),
        max(0, fill.Green() - 40),
        max(0, fill.Blue()  - 40),
    )
    gc.SetBrush(wx.Brush(fold_colour))
    gc.SetPen(wx.Pen(border, 1))
    fold = gc.CreatePath()
    fold.MoveToPoint(x0,       y0)
    fold.AddLineToPoint(x0 + ear, y0 + ear)
    fold.AddLineToPoint(x0,       y0 + ear)
    fold.CloseSubpath()
    gc.DrawPath(fold)

    mdc.SelectObject(wx.NullBitmap)
    return bmp


def _open_driver_settings(print_data, parent_hwnd=None):
    """
    Apre il pannello impostazioni del driver di stampa (DocumentProperties).

    Su Windows prova in ordine:
      1. win32print (pywin32) — usa DEVMODEType allocato correttamente
      2. ctypes puro su winspool.drv — sempre disponibile su Windows
    Su altre piattaforme (o se entrambi falliscono) mostra wx.PageSetupDialog.

    Restituisce il wx.PrintData aggiornato (o quello originale se annullato).
    """

    def _apply_devmode_to_printdata(dm, pd):
        """Copia i campi rilevanti dal DEVMODE (pywin32 object) in wx.PrintData."""
        orient = getattr(dm, 'Orientation', None)
        if orient == 2:
            pd.SetOrientation(wx.LANDSCAPE)
        elif orient == 1:
            pd.SetOrientation(wx.PORTRAIT)

        duplex = getattr(dm, 'Duplex', None)
        if duplex == 2:
            pd.SetDuplex(wx.DUPLEX_VERTICAL)
        elif duplex == 3:
            pd.SetDuplex(wx.DUPLEX_HORIZONTAL)
        elif duplex == 1:
            pd.SetDuplex(wx.DUPLEX_SIMPLEX)

        color = getattr(dm, 'Color', None)
        if color == 2:
            pd.SetColour(True)
        elif color == 1:
            pd.SetColour(False)

        copies = getattr(dm, 'Copies', None)
        if copies is not None and copies > 0:
            pd.SetNoCopies(copies)

        paper = getattr(dm, 'PaperSize', None)
        if paper is not None and paper > 0:
            try:
                pd.SetPaperId(paper)
            except Exception:
                pass

    if wx.Platform == '__WXMSW__':

        # ── Tentativo 1: pywin32 (win32print + pywintypes.DEVMODEType) ─────
        try:
            import win32print
            import win32con
            import pywintypes

            printer_name = print_data.GetPrinterName().strip()
            if not printer_name:
                printer_name = win32print.GetDefaultPrinter()

            hprinter = win32print.OpenPrinter(printer_name)
            try:
                # Prima chiamata: ottieni la dimensione totale del DEVMODE
                # (None, None, 0 → sola query della dimensione)
                dm_size = win32print.DocumentProperties(
                    parent_hwnd or 0, hprinter, printer_name, None, None, 0
                )
                if dm_size <= 0:
                    raise RuntimeError(f"DocumentProperties size query: {dm_size}")

                # Calcola dmDriverExtra = dimensione totale − dimensione fissa
                dm_fixed = pywintypes.DEVMODEType().Size
                driver_extra = max(0, dm_size - dm_fixed)

                # Alloca un DEVMODE con la driverExtra corretta e leggi
                # le impostazioni correnti dal driver (DM_OUT_BUFFER)
                dm = pywintypes.DEVMODEType(driver_extra)
                win32print.DocumentProperties(
                    parent_hwnd or 0, hprinter, printer_name,
                    dm, dm, win32con.DM_OUT_BUFFER
                )

                # Mostra il pannello del driver con DM_IN_PROMPT
                result = win32print.DocumentProperties(
                    parent_hwnd or 0, hprinter, printer_name,
                    dm, dm,
                    win32con.DM_IN_BUFFER | win32con.DM_OUT_BUFFER | win32con.DM_IN_PROMPT,
                )

                # IDOK = 1
                if result == 1:
                    _apply_devmode_to_printdata(dm, print_data)

            finally:
                win32print.ClosePrinter(hprinter)

            return print_data

        except Exception:
            pass  # win32print non disponibile o errore → tentativo 2

        # ── Tentativo 2: ctypes puro su winspool.drv ───────────────────────
        try:
            import ctypes
            import ctypes.wintypes as wt

            DM_IN_BUFFER  = 8
            DM_OUT_BUFFER = 2
            DM_IN_PROMPT  = 4

            # Offset nella struttura DEVMODEW (Unicode, Windows ≥ 2000)
            _OFF_ORIENTATION = 44
            _OFF_PAPERSIZE   = 46
            _OFF_COPIES      = 78
            _OFF_COLOR       = 96
            _OFF_DUPLEX      = 100

            def _short(buf, off):
                return ctypes.c_short.from_buffer_copy(buf[off:off + 2]).value

            winspool = ctypes.WinDLL('winspool.drv', use_last_error=True)

            printer_name = print_data.GetPrinterName().strip()
            if not printer_name:
                buf_size = wt.DWORD(0)
                winspool.GetDefaultPrinterW(None, ctypes.byref(buf_size))
                buf = ctypes.create_unicode_buffer(buf_size.value)
                winspool.GetDefaultPrinterW(buf, ctypes.byref(buf_size))
                printer_name = buf.value

            if not printer_name:
                raise RuntimeError("Nessuna stampante predefinita trovata")

            hprinter = wt.HANDLE()
            if not winspool.OpenPrinterW(printer_name, ctypes.byref(hprinter), None):
                raise ctypes.WinError(ctypes.get_last_error())

            try:
                # Query dimensione
                dm_size = winspool.DocumentPropertiesW(
                    parent_hwnd or 0, hprinter, printer_name, None, None, 0
                )
                if dm_size <= 0:
                    raise RuntimeError(f"DocumentProperties size query: {dm_size}")

                # Leggi impostazioni correnti
                dm_buf = ctypes.create_string_buffer(dm_size)
                ret = winspool.DocumentPropertiesW(
                    parent_hwnd or 0, hprinter, printer_name,
                    dm_buf, None, DM_OUT_BUFFER
                )
                if ret != 1:
                    raise RuntimeError(f"DocumentProperties DM_OUT_BUFFER: {ret}")

                # Mostra dialogo driver
                dm_out = ctypes.create_string_buffer(dm_size)
                ret = winspool.DocumentPropertiesW(
                    parent_hwnd or 0, hprinter, printer_name,
                    dm_out, dm_buf,
                    DM_IN_BUFFER | DM_OUT_BUFFER | DM_IN_PROMPT,
                )

                if ret == 1:
                    orient  = _short(dm_out, _OFF_ORIENTATION)
                    paper   = _short(dm_out, _OFF_PAPERSIZE)
                    copies  = _short(dm_out, _OFF_COPIES)
                    color   = _short(dm_out, _OFF_COLOR)
                    duplex  = _short(dm_out, _OFF_DUPLEX)

                    if orient == 2:
                        print_data.SetOrientation(wx.LANDSCAPE)
                    elif orient == 1:
                        print_data.SetOrientation(wx.PORTRAIT)
                    if paper > 0:
                        try:
                            print_data.SetPaperId(paper)
                        except Exception:
                            pass
                    if copies > 0:
                        print_data.SetNoCopies(copies)
                    if color == 2:
                        print_data.SetColour(True)
                    elif color == 1:
                        print_data.SetColour(False)
                    if duplex == 2:
                        print_data.SetDuplex(wx.DUPLEX_VERTICAL)
                    elif duplex == 3:
                        print_data.SetDuplex(wx.DUPLEX_HORIZONTAL)
                    elif duplex == 1:
                        print_data.SetDuplex(wx.DUPLEX_SIMPLEX)

            finally:
                winspool.ClosePrinter(hprinter)

            return print_data

        except Exception:
            pass  # ctypes fallito → fallback wx

    # ── Fallback: wx.PageSetupDialog (non-Windows o entrambi i tentativi falliti)
    # SetSetupDialog() è stato rimosso in wxPython 4.x (Phoenix).
    pdd = wx.PageSetupDialogData(print_data)
    dlg = wx.PageSetupDialog(None, pdd)
    try:
        if dlg.ShowModal() == wx.ID_OK:
            print_data = wx.PrintData(dlg.GetPageSetupData().GetPrintData())
    finally:
        dlg.Destroy()
    return print_data


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
        self._song_info         = None   # (full_song, sel_text)
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
        if hasattr(self.frame_obj, '_getTempoIconColour'):
            r.tempoIconColour = self.frame_obj._getTempoIconColour()
        r.gridDisplayMode = getattr(self.frame_obj.pref, 'gridDisplayMode', 'pipe')
        r.gridDefaultLabel = getattr(self.frame_obj.pref, 'gridDefaultLabel', None)
        r.gridSizeDir     = getattr(self.frame_obj.pref, 'gridSizeDir',     'both')
        r.columns         = getattr(self.frame_obj, '_columns_per_page', 1)
        r.columnHeight    = getattr(self, '_col_h_px', 0)
        # Imposta la directory del documento per risolvere i percorsi relativi
        # delle immagini ({image: intro.png} → cerca nella stessa cartella del .crd)
        import os as _os
        doc_path = getattr(self.frame_obj, 'document', None)
        r._document_dir = _os.path.dirname(doc_path) if doc_path else ''
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
        full_text   = self.frame_obj._strip_hash_commands(self.frame_obj.text.GetText())

        if full_song:
            sel_text = full_text
        else:
            # Estrae direttamente il testo selezionato (come fa _get_display_text),
            # così i comandi {start_of_grid}, {start_chorus}, ecc. presenti nella
            # selezione vengono inclusi senza dipendere dal filtraggio per numero di riga.
            raw_sel  = self.frame_obj.text.GetTextRange(start, end)
            sel_text = self.frame_obj._strip_hash_commands(raw_sel)

        self._song_info = (full_song, sel_text)

        if full_song:
            self._segments = self._split_on_new_page(full_text)
        else:
            self._segments = [sel_text]

        mdc = wx.MemoryDC(wx.Bitmap(1, 1))
        self._page_offsets = []

        verse_count = label_count = chorus_count = 0
        for seg_idx, seg_text in enumerate(self._segments):
            r = self._make_renderer()
            r.initialVerseCount  = verse_count
            r.initialLabelCount  = label_count
            r.initialChorusCount = chorus_count
            self._seg_verse_start[seg_idx] = (verse_count, label_count, chorus_count)
            sw, sh = r.Render(seg_text, mdc)
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
        #
        # Approccio diretto: rendiamo tutti i segmenti su un DC temporaneo
        # con la scala corrente, misuriamo l'altezza reale di ciascuno, e
        # ricaviamo il fattore di scala / la riduzione di margine necessari
        # senza approssimazioni su row_h.
        #
        # Grandezze usate in questo blocco:
        #   px_per_page  = altezza utile in pixel-schermo (unità del Renderer)
        #                = usable_h [device units] / self._scale_y
        #   seg_h_px[]   = altezze reali di ciascun segmento in pixel-schermo
        #   overflow_px  = quanto sporge l'ultimo segmento oltre la sua pagina
        #                  (sempre nell'ultima pagina di quel segmento)
        # ─────────────────────────────────────────────────────────────────────

        mdc2 = wx.MemoryDC(wx.Bitmap(1, 1))

        # Renderizza una volta sola tutti i segmenti e memorizza le altezze.
        seg_h_px = []
        for seg_idx, seg_text in enumerate(self._segments):
            r = self._make_renderer()
            vc, lc, cc = self._seg_verse_start.get(seg_idx, (0, 0, 0))
            r.initialVerseCount  = vc
            r.initialLabelCount  = lc
            r.initialChorusCount = cc
            _, sh = r.Render(seg_text, mdc2)
            seg_h_px.append(max(1, sh))

        total_h_px = sum(seg_h_px)

        if getattr(self.frame_obj, '_fit_to_page', False):
            # Scala font in riduzione se il contenuto eccede la pagina (no ingrandimento).
            if total_h_px * self._scale_y > usable_h:
                f = usable_h / (total_h_px * self._scale_y)
                self._scale_x *= f
                self._scale_y *= f
                # Aggiorna le altezze scalate (non i px, che sono invarianti
                # rispetto al renderer, ma serviranno corretti sotto).
                # Non serve: seg_h_px rimane in px-schermo; scale è cambiata.

        if getattr(self.frame_obj, '_shrink_to_fit', False):
            # ── Parametri di margine riducibile ───────────────────────────
            min_margin_mm = float(getattr(self.frame_obj, '_min_margin_shrink', 5))
            min_margin_du = self._mm_to_du(min_margin_mm, ppi_y)

            # Quanto possiamo togliere da top e bottom rispettando il minimo.
            # Calcolato separatamente per i due margini per distribuire
            # correttamente anche quando mt ≠ mb.
            red_top_max = max(0, mt - min_margin_du)
            red_bot_max = max(0, mb - min_margin_du)
            reducible_du = red_top_max + red_bot_max   # totale disponibile

            # ── Calcolo overflow per ogni segmento ────────────────────────
            # Per ciascun segmento, l'overflow è la parte che sporge
            # nell'ultima pagina oltre un multiplo intero di px_per_page.
            # Se overflow == 0 il segmento chiude esatto: non serve shrink.
            # Prendiamo il worst-case su tutti i segmenti.

            px_per_page = usable_h / self._scale_y   # in px-schermo

            def _overflow_px(h_px, ppp):
                """Pixel che debordano nell'ultima pagina di un segmento."""
                if ppp <= 0:
                    return 0.0
                remainder = math.fmod(h_px, ppp)
                # fmod restituisce 0.0 se h_px è multiplo esatto di ppp
                return remainder

            # Overflow massimo tra tutti i segmenti (in px-schermo).
            max_overflow_px = max(
                _overflow_px(h, px_per_page) for h in seg_h_px
            )

            if max_overflow_px > 0:
                # ── Fase 1: proviamo a recuperare l'overflow riducendo i margini ──
                #
                # Quanti device-units aggiuntivi ci servono in altezza utile
                # per far rientrare max_overflow_px nella pagina?
                # Convertiamo l'overflow da px-schermo a device-units:
                #   needed_du = max_overflow_px * self._scale_y
                needed_du = max_overflow_px * self._scale_y

                if needed_du <= reducible_du:
                    # I margini bastano: li riduciamo proporzionalmente.
                    # Distribuiamo needed_du tra top e bottom in proporzione
                    # alla loro riducibilità, così rispettiamo entrambi i minimi.
                    if reducible_du > 0:
                        ratio       = needed_du / reducible_du
                        red_top_du  = int(math.ceil(red_top_max * ratio))
                        red_bot_du  = int(math.floor(red_bot_max * ratio))
                    else:
                        red_top_du = red_bot_du = 0

                    mt -= red_top_du
                    mb -= red_bot_du
                    usable_h += red_top_du + red_bot_du
                    self._margin_du = (ml, mt, mr, mb)

                else:
                    # ── Fase 2: margini non bastano → riduciamo anche il font ──
                    #
                    # Prima sfruttiamo tutto il margine disponibile…
                    mt       -= red_top_max
                    mb       -= red_bot_max
                    usable_h += reducible_du
                    self._margin_du = (ml, mt, mr, mb)

                    # …poi calcoliamo il fattore di scala per far rientrare
                    # l'overflow residuo nella pagina aggiornata.
                    #
                    # Per ogni segmento vogliamo:
                    #   h_px * scale_y_new  ≡   0  (mod usable_h_new)
                    # ovvero che h_px * scale_y_new sia un multiplo di usable_h_new.
                    # La condizione necessaria e sufficiente è che per il segmento
                    # più "scomodo" il numero di pagine che occupa con la nuova
                    # scala sia un intero.
                    #
                    # Approccio: cerchiamo il fattore f < 1 tale che, per ogni
                    # segmento, ceil(h_px * f * scale_y / usable_h) * usable_h
                    # sia >= h_px * f * scale_y  (ovvero nessun overflow).
                    # La soluzione conservativa più semplice e stabile:
                    # scaliamo in modo che l'overflow peggiore diventi 0,
                    # ovvero che ogni segmento occupi un numero intero di pagine.
                    #
                    # Per il segmento con overflow residuo:
                    #   n_pages = ceil(h_px * scale_y / usable_h)
                    #   target  = n_pages * usable_h          [in du]
                    #   f       = target / (h_px * scale_y)   [≥ 1 se già ok, ≤ 1 se va ridotto]
                    # Prendiamo il minimo f tra tutti i segmenti (quello che
                    # richiede la riduzione maggiore).

                    f_min = 1.0
                    for h_px in seg_h_px:
                        h_du = h_px * self._scale_y
                        n_pages = max(1, math.ceil(h_du / usable_h))
                        target_du = n_pages * usable_h
                        if h_du > target_du:
                            # non dovrebbe mai accadere per costruzione di ceil,
                            # ma per robustezza:
                            f_candidate = target_du / h_du
                        elif h_du > 0:
                            # Vogliamo f tale che h_px * scale_y * f <= target_du
                            # con n_pages invariato (non vogliamo aggiungere pagine).
                            # f_candidate = target_du / h_du  ← sarebbe ≥ 1, non utile.
                            # Invece cerchiamo n_pages - 1 pagine se l'overflow
                            # è ciò che causa il problema:
                            overflow_du = math.fmod(h_du, usable_h)
                            if overflow_du > 0:
                                # Riduciamo fino a far sparire l'overflow:
                                # (h_du - overflow_du) = (n_pages-1)*usable_h
                                # f = (n_pages-1)*usable_h / h_du
                                f_candidate = ((n_pages - 1) * usable_h) / h_du
                                f_candidate = max(0.5, f_candidate)  # floor di sicurezza
                            else:
                                f_candidate = 1.0
                        else:
                            f_candidate = 1.0

                        f_min = min(f_min, f_candidate)

                    if f_min < 1.0:
                        self._scale_x *= f_min
                        self._scale_y *= f_min

        # ── calcolo definitivo degli offsets di pagina ─────────────────
        px_per_page = usable_h / self._scale_y

        mdc3 = wx.MemoryDC(wx.Bitmap(1, 1))
        for seg_idx, seg_text in enumerate(self._segments):
            r = self._make_renderer()
            vc, lc, cc = self._seg_verse_start.get(seg_idx, (0, 0, 0))
            r.initialVerseCount  = vc
            r.initialLabelCount  = lc
            r.initialChorusCount = cc
            sw, sh = r.Render(seg_text, mdc3)
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
        # Il layout deve essere già stato fatto da OnPreparePrinting (che ha un DC
        # garantito). Se per qualsiasi motivo non è ancora pronto, restituiamo 1
        # come fallback sicuro anziché tentare di ottenere un DC fuori contesto.
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
        full_song, _ = self._song_info  # sel_text già incluso in self._segments

        seg_text = self._segments[seg_idx]

        dc.SetClippingRegion(
            origin_x, origin_y,
            self._col_w_du if self.two_pages_per_sheet else self._usable_w_du,
            usable_h_du,
        )
        dc.SetDeviceOrigin(origin_x, origin_y - int(y_offset_px * self._scale_y))
        dc.SetUserScale(self._scale_x, self._scale_y)

        r = self._make_renderer()
        vc, lc, cc = self._seg_verse_start.get(seg_idx, (0, 0, 0))
        r.initialVerseCount  = vc
        r.initialLabelCount  = lc
        r.initialChorusCount = cc
        r.Render(seg_text, dc)

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
        box_pages = wx.StaticBoxSizer(
            wx.StaticBox(dlg, label=_("Pages per sheet")), wx.HORIZONTAL
        )
        self.rb_page1 = wx.ToggleButton(dlg, label=_("1 page"))
        self.rb_page2 = wx.ToggleButton(dlg, label=_("2 pages"))
        self.rb_page1.SetValue(not owner._two_pages_per_sheet)
        self.rb_page2.SetValue(owner._two_pages_per_sheet)
        box_pages.Add(self.rb_page1, 1, wx.EXPAND | wx.ALL, _GAP)
        box_pages.Add(self.rb_page2, 1, wx.EXPAND | wx.ALL, _GAP)
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

        self.cb_fit = wx.CheckBox(dlg, label=_("Shrink if exceeds page"))
        self.cb_fit.SetValue(owner._fit_to_page)
        self.cb_fit.SetToolTip(_("Reduce the content only if it exceeds the page size (no upscaling)"))
        box_resize.Add(self.cb_fit, 0, wx.ALL, _GAP)

        # cb_shrink + nota secondaria
        shrink_panel = wx.Panel(dlg)
        shrink_vsz   = wx.BoxSizer(wx.VERTICAL)
        self.cb_shrink = wx.CheckBox(
            shrink_panel, label=_("Shrink to fit current page")
        )
        self.cb_shrink.SetValue(owner._shrink_to_fit)
        self.cb_shrink.SetToolTip(_("Reduce the content only if it exceeds the page size, to avoid bottom clipping"))
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
            size=(90, -1),
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
        self.cb_no_mirror.SetToolTip(_("In 2-pages mode, print only on the left half and leave the right half blank (no mirroring)"))
        self.cb_no_mirror.Enable(owner._two_pages_per_sheet)
        box_adv.Add(self.cb_no_mirror, 0, wx.ALL, _GAP)

        self.cb_remove_blank = wx.CheckBox(dlg, label=_("Remove blank pages"))
        self.cb_remove_blank.SetValue(owner._remove_blank_pages)
        self.cb_remove_blank.SetToolTip(_("Skip pages that are empty or contain only whitespace, based on the threshold below"))
        box_adv.Add(self.cb_remove_blank, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, _GAP)

        row2 = wx.BoxSizer(wx.HORIZONTAL)
        self.lbl_blank_threshold = wx.StaticText(dlg, label=_("Blank page threshold (%):"))
        self.spin_blank_threshold = wx.SpinCtrl(
            dlg, min=1, max=95,
            value=str(getattr(owner, '_blank_page_threshold', 5)),
            size=(90, -1),
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
            size=(90, -1),
        )
        box_scale.Add(lbl_scale, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, _GAP)
        box_scale.Add(self.spin_font_scale, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, _GAP)
        outer.Add(box_scale, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, _GAP)

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
        self.rb_page1.Bind(wx.EVT_TOGGLEBUTTON, self._on_page1)
        self.rb_page2.Bind(wx.EVT_TOGGLEBUTTON, self._on_page2)
        self.rb_col1.Bind(wx.EVT_TOGGLEBUTTON, self._on_col1)
        self.rb_col2.Bind(wx.EVT_TOGGLEBUTTON, self._on_col2)
        self.cb_shrink.Bind(wx.EVT_CHECKBOX, self._on_shrink_changed)
        self.cb_remove_blank.Bind(wx.EVT_CHECKBOX, self._on_remove_blank_changed)
        self.btn_pin.Bind(wx.EVT_BUTTON, self._on_pin)
        self.btn_ok.Bind(wx.EVT_BUTTON, self._on_ok)

    # ── Handler eventi ────────────────────────────────────────────────────────

    def _on_page1(self, evt):
        self.rb_page1.SetValue(True)
        self.rb_page2.SetValue(False)
        self.cb_no_mirror.Enable(False)

    def _on_page2(self, evt):
        self.rb_page2.SetValue(True)
        self.rb_page1.SetValue(False)
        self.cb_no_mirror.Enable(True)

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
        o._two_pages_per_sheet  = self.rb_page2.GetValue()
        o._columns_per_page     = 2 if self.rb_col2.GetValue() else 1
        o._fit_to_page          = self.cb_fit.GetValue()
        o._shrink_to_fit        = self.cb_shrink.GetValue()
        o._min_margin_shrink    = self.spin_min_margin.GetValue()
        o._no_mirror_right      = self.cb_no_mirror.GetValue()
        o._remove_blank_pages   = self.cb_remove_blank.GetValue()
        o._blank_page_threshold = self.spin_blank_threshold.GetValue()
        o._print_font_scale     = self.spin_font_scale.GetValue()
        # Persistenza immediata (la scala non viene salvata)
        try:
            o._SavePageMargins()
        except Exception:
            pass
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

        self._preview_frame = None

    # ── Persist ───────────────────────────────────────────────────────────────

    def _SavePageMargins(self):
        """Salva margini, formato carta, orientamento e TUTTE le opzioni di stampa.

        NOTA: ``_print_font_scale`` (Scala %) non viene mai salvato:
        deve ripartire sempre da 100 ad ogni avvio.
        """
        try:
            self.config.SetPath('/PageSetup')
            self.config.Write('margin_top',           str(self._margin_top))
            self.config.Write('margin_bottom',        str(self._margin_bottom))
            self.config.Write('margin_left',          str(self._margin_left))
            self.config.Write('margin_right',         str(self._margin_right))
            self.config.Write('paper_id',             str(self._print_data.GetPaperId()))
            self.config.Write('orientation',          str(self._print_data.GetOrientation()))
            self.config.Write('shrink_to_fit',        '1' if self._shrink_to_fit else '0')
            self.config.Write('min_margin_shrink',    str(self._min_margin_shrink))
            # ── Opzioni del dialog «Opzioni di stampa» ────────────────────
            self.config.Write('two_pages_per_sheet',  '1' if self._two_pages_per_sheet else '0')
            self.config.Write('columns_per_page',     str(self._columns_per_page))
            self.config.Write('fit_to_page',          '1' if self._fit_to_page else '0')
            self.config.Write('no_mirror_right',      '1' if self._no_mirror_right else '0')
            self.config.Write('remove_blank_pages',   '1' if self._remove_blank_pages else '0')
            self.config.Write('blank_page_threshold', str(self._blank_page_threshold))
            self.config.Write('print_options_pinned', '1' if self._print_options_pinned else '0')
            # Scala volutamente NON salvata (reset a 100 ad ogni riapertura).
            self.config.DeleteEntry('print_font_scale', False)
            self.config.Flush()
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

            # ── Opzioni del dialog «Opzioni di stampa» ────────────────────
            def _rb(key, current):
                v = self.config.Read(key)
                return (v == '1') if v else current

            def _ri(key, current, lo=None, hi=None):
                v = self.config.Read(key)
                if not v:
                    return current
                try:
                    n = int(v)
                except ValueError:
                    return current
                if lo is not None and n < lo:
                    return current
                if hi is not None and n > hi:
                    return current
                return n

            self._two_pages_per_sheet  = _rb('two_pages_per_sheet',  self._two_pages_per_sheet)
            self._columns_per_page     = _ri('columns_per_page',     self._columns_per_page, 1, 2)
            self._fit_to_page          = _rb('fit_to_page',          self._fit_to_page)
            self._no_mirror_right      = _rb('no_mirror_right',      self._no_mirror_right)
            self._remove_blank_pages   = _rb('remove_blank_pages',   self._remove_blank_pages)
            self._blank_page_threshold = _ri('blank_page_threshold', self._blank_page_threshold, 1, 95)
            self._print_options_pinned = _rb('print_options_pinned', self._print_options_pinned)

            # La scala non è persistente: sempre 100% all'avvio.
            self._print_font_scale = 100
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

        Se c'è una selezione attiva nell'editor, stampa solo quella;
        altrimenti stampa l'intero documento (gestito da _ensure_layout).
        """
        if title is None:
            title = _("Print")
        return SongpressPrintout(
            self, title,
            two_pages_per_sheet=self._two_pages_per_sheet,
            font_scale=getattr(self, '_print_font_scale', 100),
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
        if not success:
            if printer.GetLastError() == wx.PRINTER_ERROR:
                wx.MessageBox(
                    _("An error occurred while printing.\nPlease check your printer settings."),
                    _("Print error"),
                    wx.OK | wx.ICON_ERROR,
                    self.frame,
                )
            # In caso di fallimento wx non prende ownership: distruggiamo noi
            printout.Destroy()
        # In caso di successo wx prende ownership del printout: non chiamare Destroy()

    def OnPrintPreview(self, evt):
        """Mostra l'anteprima di stampa del brano."""
        self.previewCanvas.Refresh(self._get_display_text())
        base_title = os.path.splitext(os.path.basename(self.document))[0] \
                     if self.document else _("Print")
        start, end = self.text.GetSelection()
        has_sel    = (start != end)
        if has_sel:
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

        _always_on_top = getattr(getattr(self, 'pref', None), 'printPreviewAlwaysOnTop', False)
        _pf_style = wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP if _always_on_top else wx.DEFAULT_FRAME_STYLE
        pf = wx.PreviewFrame(preview, self.frame, _("Print preview"),
                             style=_pf_style)
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
            # ATTENZIONE: wx.Window.FindWindowById è di fatto una ricerca
            # GLOBALE (parent=None): con più PreviewFrame in vita — succede
            # quando la preview viene ricreata dopo «OK» in Opzioni di stampa,
            # perché la vecchia finestra è solo in attesa di distruzione —
            # restituisce i bottoni della barra VECCHIA. Cerchiamo quindi
            # esplicitamente solo fra i figli di questa control bar.
            def _find_child_by_id(parent, wid):
                if wid is None:
                    return None
                for ch in parent.GetChildren():
                    if ch.GetId() == wid:
                        return ch
                return None

            _preview_print_id = getattr(wx, 'ID_PREVIEW_PRINT', wx.ID_PRINT)
            btn_print = _find_child_by_id(ctrl_bar, _preview_print_id)
            if btn_print is None:
                btn_print = _find_child_by_id(ctrl_bar, wx.ID_PRINT)
            if btn_print is not None:
                btn_print.SetLabel(_("Print..."))

            # Registro dei percorsi icona dei bottoni personalizzati:
            # verranno ridimensionati tutti alla stessa misura più avanti.
            _custom_icon_paths = {}

            # Icona per il bottone «Stampa» nativo della preview bar
            if btn_print is not None:
                _print_icon_path = glb.AddPath('img/print_icon.png')
                if os.path.isfile(_print_icon_path):
                    _custom_icon_paths[btn_print] = _print_icon_path
                    img = wx.Image(_print_icon_path, wx.BITMAP_TYPE_PNG)
                    btn_print.SetBitmap(wx.Bitmap(img))
                    btn_print.SetBitmapPosition(wx.LEFT)

            # Icone per i bottoni nativi di zoom (- e +) della preview bar,
            # e per le frecce verdi native Precedente/Successiva/
            # Prima/Ultima pagina. Sono tutti wx.BitmapButton SENZA
            # etichetta testuale: vanno identificati tramite gli ID nativi
            # assegnati da wxWidgets alla control bar, non per label.
            _minus_icon_path      = glb.AddPath('img/minus.png')
            _plus_icon_path       = glb.AddPath('img/plus.png')
            _prev_icon_path       = glb.AddPath('img/left.png')
            _next_icon_path       = glb.AddPath('img/right.png')
            _first_icon_path      = glb.AddPath('img/first_page.png')
            _last_icon_path       = glb.AddPath('img/last_page.png')

            _zoom_in_id  = getattr(wx, 'ID_PREVIEW_ZOOM_IN', 9)
            _zoom_out_id = getattr(wx, 'ID_PREVIEW_ZOOM_OUT', 10)
            _prev_id     = getattr(wx, 'ID_PREVIEW_PREVIOUS', 3)
            _next_id     = getattr(wx, 'ID_PREVIEW_NEXT', 2)
            _first_id    = getattr(wx, 'ID_PREVIEW_FIRST', 6)
            _last_id     = getattr(wx, 'ID_PREVIEW_LAST', 7)

            _nav_icon_by_id = {
                _zoom_out_id: _minus_icon_path,
                _zoom_in_id:  _plus_icon_path,
                _prev_id:     _prev_icon_path,
                _next_id:     _next_icon_path,
                _first_id:    _first_icon_path,
                _last_id:     _last_icon_path,
            }

            def _iter_descendants(win):
                for ch in win.GetChildren():
                    yield ch
                    yield from _iter_descendants(ch)

            for child in _iter_descendants(ctrl_bar):
                if not isinstance(child, wx.AnyButton):
                    continue
                _icon_path = _nav_icon_by_id.get(child.GetId())
                if _icon_path and os.path.isfile(_icon_path):
                    _custom_icon_paths[child] = _icon_path
                    img = wx.Image(_icon_path, wx.BITMAP_TYPE_PNG)
                    child.SetBitmap(wx.Bitmap(img))
                    child.SetBitmapPosition(wx.LEFT)

            # Bottone «Impostazioni driver»
            btn_driver = wx.Button(ctrl_bar, wx.ID_ANY, _("Driver settings..."))
            _driver_icon_path = glb.AddPath('img/option_printer.png')
            if os.path.isfile(_driver_icon_path):
                _custom_icon_paths[btn_driver] = _driver_icon_path
                img = wx.Image(_driver_icon_path, wx.BITMAP_TYPE_PNG)
                btn_driver.SetBitmap(wx.Bitmap(img))
                btn_driver.SetBitmapPosition(wx.LEFT)
            else:
                # Icona di fallback: stampante dal catalogo wxArtProvider
                bmp = wx.ArtProvider.GetBitmap(wx.ART_PRINT, wx.ART_BUTTON, wx.Size(16, 16))
                if bmp.IsOk():
                    btn_driver.SetBitmap(bmp)
                    btn_driver.SetBitmapPosition(wx.LEFT)

            def on_driver_settings(e):
                hwnd = None
                if wx.Platform == '__WXMSW__':
                    try:
                        hwnd = pf.GetHandle()
                    except Exception:
                        hwnd = None
                orient_before = self._print_data.GetOrientation()
                try:
                    self._print_data = _open_driver_settings(self._print_data, parent_hwnd=hwnd)
                except Exception as exc:
                    wx.MessageBox(
                        _("Impossibile aprire le impostazioni del driver:\n{err}").format(err=exc),
                        _("Errore"), wx.OK | wx.ICON_ERROR, pf
                    )
                    return
                orient_after  = self._print_data.GetOrientation()
                # Aggiorna la status bar (duplex/colore/orientamento possono essere cambiati)
                try:
                    _sb._refresh_labels()
                except Exception:
                    pass
                # Se l'orientamento è cambiato la preview mostra ancora il foglio
                # nel verso sbagliato: bisogna ricrearla con i nuovi dati di stampa.
                if orient_after != orient_before:
                    pf.Close()
                    wx.CallAfter(self.OnPrintPreview, None)

            btn_driver.Bind(wx.EVT_BUTTON, on_driver_settings)

            # Bottone «Opzioni di stampa»
            btn_options = wx.Button(ctrl_bar, wx.ID_ANY, _("Print options..."))
            _icon_path  = glb.AddPath('img/print_icon2.png')
            if os.path.isfile(_icon_path):
                _custom_icon_paths[btn_options] = _icon_path
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
                _custom_icon_paths[btn_page_setup] = _page_icon_path
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
            _close_icon_path = glb.AddPath('img/close_print_dialog.png')
            if os.path.isfile(_close_icon_path):
                _custom_icon_paths[btn_close] = _close_icon_path
                img = wx.Image(_close_icon_path, wx.BITMAP_TYPE_PNG)
                btn_close.SetBitmap(wx.Bitmap(img))
                btn_close.SetBitmapPosition(wx.LEFT)
            btn_close.Bind(wx.EVT_BUTTON, lambda e: pf.Close())

            # Rimuove il bottone «Chiudi» nativo della preview control bar
            # (altrimenti compare doppio, senza icona, accanto al nostro).
            # Si cercano TUTTI i candidati fra i figli di *questa* barra:
            # per id wx.ID_PREVIEW_CLOSE/wx.ID_CANCEL oppure per etichetta.
            _close_ids = set()
            for _n in ('ID_PREVIEW_CLOSE', 'ID_CANCEL', 'ID_CLOSE'):
                _v = getattr(wx, _n, None)
                if _v is not None:
                    _close_ids.add(_v)
            _close_labels = {'Close', 'Chiudi', _('Close')}

            _natives = []
            for child in ctrl_bar.GetChildren():
                if child is btn_close or not isinstance(child, wx.Button):
                    continue
                if child.GetId() in _close_ids or child.GetLabel().strip() in _close_labels:
                    _natives.append(child)

            _cb_sizer = ctrl_bar.GetSizer()
            for _native_close in _natives:
                try:
                    if _cb_sizer:
                        _cb_sizer.Detach(_native_close)
                    _native_close.Hide()
                    # Distruzione differita: eliminarlo subito dentro la
                    # costruzione della barra può lasciare il sizer incoerente.
                    wx.CallAfter(_native_close.Destroy)
                except Exception:
                    pass

            # Inserisce i bottoni personalizzati nella toolbar
            # (le etichette duplex/colore sono nella status bar in basso)
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
                sizer.Insert(ins + 1, btn_driver,     0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
                sizer.Insert(ins + 2, btn_options,    0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
                sizer.Insert(ins + 3, btn_close,      0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)

            # Uniforma altezza dei bottoni personalizzati a quella dei
            # bottoni nativi della preview bar (quelli di sinistra).
            def _native_ref_height():
                # Prova prima il bottone «Print» nativo, poi qualunque
                # altro bottone nativo diverso dai nostri custom.
                _custom = (btn_page_setup, btn_driver, btn_options, btn_close)
                ref = btn_print
                if ref is not None and ref not in _custom:
                    h = ref.GetBestSize().height
                    if h > 4:
                        return h
                for child in ctrl_bar.GetChildren():
                    if isinstance(child, wx.Button) and child not in _custom:
                        h = child.GetBestSize().height
                        if h > 4:
                            return h
                return btn_options.GetBestSize().height

            ref_h = _native_ref_height()

            # Ridimensiona tutte le icone dei bottoni custom alla stessa
            # misura, ricavata dall'altezza dei bottoni nativi (con un
            # margine per il bordo del bottone). Rilegge sempre dal file
            # sorgente per non accumulare perdite di qualità.
            _icon_cache = {}

            def _apply_uniform_icons(btn_h):
                icon_sz = int(btn_h) - 8
                if icon_sz < 8:
                    icon_sz = 8
                if icon_sz > 24:
                    icon_sz = 24
                if _icon_cache.get('sz') == icon_sz:
                    return
                _icon_cache['sz'] = icon_sz
                for _b, _p in _custom_icon_paths.items():
                    try:
                        im = wx.Image(_p, wx.BITMAP_TYPE_PNG)
                        if im.GetWidth() != icon_sz or im.GetHeight() != icon_sz:
                            im = im.Scale(icon_sz, icon_sz, wx.IMAGE_QUALITY_HIGH)
                        _b.SetBitmap(wx.Bitmap(im))
                        _b.SetBitmapPosition(wx.LEFT)
                    except Exception:
                        pass

            _apply_uniform_icons(ref_h)
            for btn in (btn_page_setup, btn_driver, btn_options, btn_close):
                btn.SetMinSize(wx.Size(btn.GetBestSize().width, ref_h))
            ctrl_bar.Layout()

            def _equalize_heights():
                try:
                    h = _native_ref_height()
                    if h < 4:
                        return
                    _apply_uniform_icons(h)
                    for btn in (btn_page_setup, btn_driver, btn_options, btn_close):
                        bw = btn.GetBestSize().width
                        btn.SetMinSize(wx.Size(bw, h))
                        btn.SetSize(wx.Size(bw, h))
                    ctrl_bar.Layout()
                except Exception:
                    pass
            wx.CallAfter(_equalize_heights)

        pf.Show()

        # ── Barra di stato personalizzata (fronte/retro + colore) ─────────────
        # wx.StatusBar nativa non supporta testo colorato per campo su Windows,
        # quindi usiamo un wx.Panel agganciato come StatusBar owner-draw.
        class _ColoredStatusBar(wx.StatusBar):
            """
            Status bar con testo colorato per i campi 1, 2 e icona nel campo 3.

            Campo 0 → testo nativo wxWidgets ("Pagina N di M").
            Campo 1 → stato fronte/retro.
            Campo 2 → modalità colore.
            Campo 3 → icona orientamento foglio (wx.StaticBitmap disegnata a codice).

            Se live_poll=True un wx.Timer interroga il driver ogni _POLL_MS ms
            così le etichette si aggiornano in tempo reale anche mentre il
            pannello del driver è aperto.
            Se live_poll=False la lettura avviene una sola volta all'apertura
            e rimane fissa fino alla chiusura della preview.
            """

            _POLL_MS = 1500   # intervallo di polling in millisecondi

            # ── dizionari statici ──────────────────────────────────────────
            _DUPLEX_LABELS = {
                wx.DUPLEX_SIMPLEX:    (lambda: _("Duplex: off (simplex)"),           wx.Colour(160, 160, 160)),
                wx.DUPLEX_HORIZONTAL: (lambda: _("Duplex: ON — short-edge binding"), wx.Colour( 20, 140,  60)),
                wx.DUPLEX_VERTICAL:   (lambda: _("Duplex: ON — long-edge binding"),  wx.Colour( 20, 140,  60)),
            }
            _COLOR_LABELS = {
                "color":   (lambda: _("Color: color print"),   wx.Colour(  0, 100, 200)),
                "mono":    (lambda: _("Color: black & white"), wx.Colour( 80,  80,  80)),
                "unknown": (lambda: _("Color: unknown"),       wx.Colour(180,  80,   0)),
            }

            def __init__(self, parent, print_data_ref, live_poll=True):
                super().__init__(parent, style=wx.STB_DEFAULT_STYLE)
                # print_data_ref: callable → wx.PrintData corrente
                self._get_pd   = print_data_ref
                self._live     = live_poll

                # Campo 3: larghezza fissa per l'icona (bitmap + padding)
                self.SetFieldsCount(4)
                self.SetStatusWidths([-1, -2, -2, 44])

                # Campo 1: fronte/retro
                self._lbl_duplex = wx.StaticText(self, wx.ID_ANY, "")
                _f1 = self._lbl_duplex.GetFont()
                _f1.SetWeight(wx.FONTWEIGHT_BOLD)
                self._lbl_duplex.SetFont(_f1)

                # Campo 2: colore
                self._lbl_color = wx.StaticText(self, wx.ID_ANY, "")
                _f2 = self._lbl_color.GetFont()
                _f2.SetWeight(wx.FONTWEIGHT_BOLD)
                self._lbl_color.SetFont(_f2)

                # Campo 3: icona orientamento — placeholder, bitmap creata al primo reposition
                self._bmp_orient = _make_orientation_bitmap(False, 20)
                self._lbl_orient = wx.StaticBitmap(self, wx.ID_ANY, self._bmp_orient)
                self._last_orient = None   # None → forza primo aggiornamento

                # Stato precedente per evitare refresh inutili
                self._last_duplex = None
                self._last_color  = None

                # Prima lettura sempre immediata
                self._refresh_labels()

                # Timer: avviato solo se live_poll è attivo
                self._timer = wx.Timer(self)
                self.Bind(wx.EVT_TIMER, self._on_timer, self._timer)
                if self._live:
                    self._timer.Start(self._POLL_MS)

                self.Bind(wx.EVT_SIZE, self._on_size)
                wx.CallAfter(self._reposition)

            # ── aggiornamento etichette ────────────────────────────────────

            def _resolve_duplex(self):
                """Restituisce (text, colour) per lo stato duplex corrente."""
                try:
                    mode = _get_duplex_mode(self._get_pd())
                except Exception:
                    mode = wx.DUPLEX_SIMPLEX
                entry = self._DUPLEX_LABELS.get(mode)
                if entry:
                    text_fn, colour = entry
                    return text_fn(), colour
                return _("Duplex: unknown (mode {})".format(mode)), wx.Colour(180, 80, 0)

            def _resolve_color(self):
                """Restituisce (text, colour) per la modalità colore corrente."""
                try:
                    mode = _get_color_mode(self._get_pd())
                except Exception:
                    mode = "unknown"
                entry = self._COLOR_LABELS.get(mode)
                if entry:
                    text_fn, colour = entry
                    return text_fn(), colour
                return _("Color: unknown"), wx.Colour(180, 80, 0)

            def _resolve_orient(self):
                """Restituisce il bool landscape per l'orientamento corrente."""
                try:
                    orient = _get_orientation(self._get_pd())
                except Exception:
                    orient = wx.PORTRAIT
                return orient == wx.LANDSCAPE

            def _refresh_labels(self):
                """Interroga il driver e aggiorna le etichette se cambiate."""
                changed = False

                d_text, d_colour = self._resolve_duplex()
                if d_text != self._last_duplex:
                    self._last_duplex = d_text
                    self._lbl_duplex.SetLabel(d_text)
                    self._lbl_duplex.SetForegroundColour(d_colour)
                    changed = True

                c_text, c_colour = self._resolve_color()
                if c_text != self._last_color:
                    self._last_color = c_text
                    self._lbl_color.SetLabel(c_text)
                    self._lbl_color.SetForegroundColour(c_colour)
                    changed = True

                landscape = self._resolve_orient()
                if landscape != self._last_orient:
                    self._last_orient = landscape
                    # Ricostruisce il bitmap con l'altezza attuale del campo
                    try:
                        field_h = self.GetFieldRect(3).height
                    except Exception:
                        field_h = 20
                    self._bmp_orient = _make_orientation_bitmap(landscape, field_h)
                    self._lbl_orient.SetBitmap(self._bmp_orient)
                    changed = True

                if changed:
                    wx.CallAfter(self._reposition)

            def _on_timer(self, evt):
                self._refresh_labels()

            # ── layout ────────────────────────────────────────────────────

            def _reposition(self):
                try:
                    r1 = self.GetFieldRect(1)
                    r2 = self.GetFieldRect(2)
                    r3 = self.GetFieldRect(3)
                    pad = 4
                    for lbl, r in ((self._lbl_duplex, r1), (self._lbl_color, r2)):
                        _, h = lbl.GetBestSize()
                        y = r.y + max(0, (r.height - h) // 2)
                        lbl.SetPosition(wx.Point(r.x + pad, y))
                        lbl.SetSize(wx.Size(r.width - pad * 2, h))
                    # Campo 3: icona centrata nel campo
                    bw, bh = self._lbl_orient.GetBestSize()
                    ix = r3.x + max(0, (r3.width  - bw) // 2)
                    iy = r3.y + max(0, (r3.height - bh) // 2)
                    self._lbl_orient.SetPosition(wx.Point(ix, iy))
                except Exception:
                    pass

            def _on_size(self, evt):
                evt.Skip()
                wx.CallAfter(self._reposition)

            def stop_timer(self):
                """Ferma il polling; chiamato alla chiusura della preview."""
                try:
                    if self._timer.IsRunning():
                        self._timer.Stop()
                except Exception:
                    pass

        _live_poll = getattr(self, 'pref', None)
        _live_poll = getattr(_live_poll, 'liveDriverPoll', True) if _live_poll else True
        _sb = _ColoredStatusBar(pf, lambda: self._print_data, live_poll=_live_poll)
        pf.SetStatusBar(_sb)

        # Al chiusura della preview: ferma il timer di polling e ripristina il canvas
        def _on_preview_close(e):
            e.Skip()
            _sb.stop_timer()
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
