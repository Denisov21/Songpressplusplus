###############################################################
# Name:         PdfExporter.py
# Purpose:      Esportazione PDF per Songpress
# Author:       Luca Allulli (webmaster@roma21.it)
# Created:      2026
# Copyright:    Luca Allulli (https://www.skeed.it/songpress)
# License:      GNU GPL v2
###############################################################
#
# Rispetta le impostazioni di "Imposta pagina":
#   - Formato carta  (_print_data.GetPaperId())
#   - Orientamento   (_print_data.GetOrientation())
#   - Margini mm     (_margin_top/bottom/left/right)
#
# Strategia cross-platform:
#   Windows  → reportlab
#   Linux/macOS → wx.PRINT_MODE_FILE via CUPS
#
###############################################################

import sys
import os
import tempfile

import wx


# ------------------------------------------------------------------ #
#  Mappa wx.PAPER_* → dimensioni in mm (larghezza, altezza)           #
# ------------------------------------------------------------------ #

_PAPER_SIZES_MM = {
    wx.PAPER_A3:        (297, 420),
    wx.PAPER_A4:        (210, 297),
    wx.PAPER_A5:        (148, 210),
    wx.PAPER_B4:        (250, 354),
    wx.PAPER_B5:        (182, 257),
    wx.PAPER_LETTER:    (215.9, 279.4),
    wx.PAPER_LEGAL:     (215.9, 355.6),
    wx.PAPER_EXECUTIVE: (184.1, 266.7),
}
_DEFAULT_PAPER_MM = (210, 297)  # A4 fallback


def _get_pagesize_pt(frame_obj):
    """Restituisce (width_pt, height_pt) tenendo conto di formato e orientamento."""
    paper_id    = frame_obj._print_data.GetPaperId()
    orientation = frame_obj._print_data.GetOrientation()
    w_mm, h_mm  = _PAPER_SIZES_MM.get(paper_id, _DEFAULT_PAPER_MM)
    if orientation == wx.LANDSCAPE:
        w_mm, h_mm = h_mm, w_mm
    return w_mm * 72.0 / 25.4, h_mm * 72.0 / 25.4


def _get_margins_pt(frame_obj):
    """Restituisce (top, bottom, left, right) in punti PDF."""
    def mm2pt(v): return v * 72.0 / 25.4
    return (
        mm2pt(getattr(frame_obj, '_margin_top',    15)),
        mm2pt(getattr(frame_obj, '_margin_bottom', 15)),
        mm2pt(getattr(frame_obj, '_margin_left',   15)),
        mm2pt(getattr(frame_obj, '_margin_right',  15)),
    )


# ------------------------------------------------------------------ #
#  Punto di ingresso                                                   #
# ------------------------------------------------------------------ #

def export_as_pdf(frame_obj, filepath, title):
    if sys.platform == 'win32':
        _export_reportlab(frame_obj, filepath)
    else:
        _export_cups(frame_obj, filepath, title)


# ------------------------------------------------------------------ #
#  Windows — reportlab                                                 #
# ------------------------------------------------------------------ #

def _split_on_new_page(text):
    """
    Divide il testo sui comandi {new_page} o {np} (case-insensitive).
    Restituisce una lista di segmenti di testo (almeno uno).
    """
    import re
    parts = re.split(r'\{\s*(?:new_page|np)\s*\}', text, flags=re.IGNORECASE)
    result = [p for p in parts if p.strip()] or [text]
    return result


def _render_segment_to_png(frame_obj, seg_text, scale, avail_w_px, avail_h_px):
    """
    Renderizza un segmento di testo in un wx.Bitmap temporaneo.
    Ritorna il Bitmap (dimensioni naturali * scale, ma limitato all'area disponibile).
    """
    from .SongpressFrame import Renderer, SongDecorator

    decorator = (
        frame_obj.pref.decorator
        if frame_obj.pref.labelVerses
        else SongDecorator()
    )
    r = Renderer(frame_obj.pref.format, decorator, frame_obj.pref.notations)

    # Misura
    mdc = wx.MemoryDC(wx.Bitmap(1, 1))
    sw, sh = r.Render(seg_text, mdc)
    sw, sh = max(1, sw), max(1, sh)

    # Scala per adattare alla larghezza disponibile (in pixel a 96 dpi)
    fit_scale = scale
    natural_w = sw * scale
    if natural_w > avail_w_px:
        fit_scale = scale * (avail_w_px / natural_w)

    bmp_w = int(sw * fit_scale)
    bmp_h = int(sh * fit_scale)
    bmp = wx.Bitmap(max(1, bmp_w), max(1, bmp_h))
    dc = wx.MemoryDC(bmp)
    dc.SetUserScale(fit_scale, fit_scale)
    dc.SetBackground(wx.WHITE_BRUSH)
    dc.Clear()
    r2 = Renderer(frame_obj.pref.format, decorator, frame_obj.pref.notations)
    r2.Render(seg_text, dc)
    del dc
    return bmp


def _export_reportlab(frame_obj, filepath):
    """
    Genera PDF multipagina tramite reportlab rispettando:
    - formato carta, orientamento, margini
    - interruzioni di pagina esplicite {new_page} / {np}
    Ogni segmento diviso da {new_page} viene renderizzato su una pagina PDF separata.
    """
    try:
        from reportlab.pdfgen import canvas as rl_canvas
    except ImportError:
        wx.MessageBox(
            "La libreria 'reportlab' non è installata.\n"
            "Eseguire: pip install reportlab",
            "Libreria mancante",
            wx.OK | wx.ICON_ERROR,
            frame_obj.frame,
        )
        return

    SCALE = 3  # ~216 dpi per una buona qualità

    page_w, page_h = _get_pagesize_pt(frame_obj)
    mt, mb, ml, mr = _get_margins_pt(frame_obj)
    avail_w_pt = page_w - ml - mr
    avail_h_pt = page_h - mt - mb

    # Area disponibile in pixel a 96 dpi (per misurare il rendering wx)
    PT_TO_PX = 96.0 / 72.0
    avail_w_px = int(avail_w_pt * PT_TO_PX * SCALE)
    avail_h_px = int(avail_h_pt * PT_TO_PX * SCALE)

    full_text = frame_obj.text.GetText()
    segments  = _split_on_new_page(full_text)

    tmp_files = []
    try:
        c = rl_canvas.Canvas(filepath, pagesize=(page_w, page_h))

        for seg_idx, seg_text in enumerate(segments):
            bmp = _render_segment_to_png(
                frame_obj, seg_text, SCALE, avail_w_px, avail_h_px
            )
            img = bmp.ConvertToImage()

            tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            tmp.close()
            img.SaveFile(tmp.name, wx.BITMAP_TYPE_PNG)
            tmp_files.append(tmp.name)

            # Dimensioni immagine in punti (SCALE * 96 dpi → 72 pt)
            px_to_pt = 72.0 / (SCALE * 96.0)
            draw_w = bmp.GetWidth()  * px_to_pt
            draw_h = bmp.GetHeight() * px_to_pt

            # Adatta all'area disponibile mantenendo le proporzioni
            scale_fit = min(avail_w_pt / draw_w, avail_h_pt / draw_h, 1.0)
            final_w = draw_w * scale_fit
            final_h = draw_h * scale_fit

            # Centrato orizzontalmente, allineato in alto entro i margini
            x = ml + (avail_w_pt - final_w) / 2.0
            y = mb + avail_h_pt - final_h  # reportlab: y=0 è in basso

            if seg_idx > 0:
                c.showPage()

            c.drawImage(tmp.name, x, y, width=final_w, height=final_h)

        c.save()

        wx.MessageBox(
            "PDF esportato con successo:\n%s" % filepath,
            "Esportazione PDF",
            wx.OK | wx.ICON_INFORMATION,
            frame_obj.frame,
        )
    finally:
        for f in tmp_files:
            try:
                os.unlink(f)
            except OSError:
                pass


# ------------------------------------------------------------------ #
#  Linux / macOS — CUPS                                               #
# ------------------------------------------------------------------ #

def _export_cups(frame_obj, filepath, title):
    """Genera PDF tramite wx.PRINT_MODE_FILE (CUPS), rispettando le impostazioni di pagina."""
    from .SongpressFrame import SongpressPrintout

    pd = wx.PrintData()
    pd.SetPaperId(frame_obj._print_data.GetPaperId())
    pd.SetOrientation(frame_obj._print_data.GetOrientation())
    pd.SetPrintMode(wx.PRINT_MODE_FILE)
    pd.SetFilename(filepath)

    pdd      = wx.PrintDialogData(pd)
    printer  = wx.Printer(pdd)
    printout = SongpressPrintout(
        frame_obj, title,
        two_pages_per_sheet=frame_obj._two_pages_per_sheet,
    )

    if not printer.Print(frame_obj.frame, printout, False):
        if printer.GetLastError() == wx.PRINTER_ERROR:
            wx.MessageBox(
                "Errore durante l'esportazione PDF.\n"
                "Verifica che CUPS sia installato e configurato.",
                "Errore esportazione PDF",
                wx.OK | wx.ICON_ERROR,
                frame_obj.frame,
            )
    else:
        wx.MessageBox(
            "PDF esportato con successo:\n%s" % filepath,
            "Esportazione PDF",
            wx.OK | wx.ICON_INFORMATION,
            frame_obj.frame,
        )
    printout.Destroy()
