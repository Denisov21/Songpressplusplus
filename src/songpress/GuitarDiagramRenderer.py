###############################################################
# Name:         GuitarDiagramRenderer.py
# Purpose:      Draw guitar chord diagrams (neck/fretboard)
# Author:       Denisov21
# Created:      2026-03-12
# Copyright:    Denisov21
# License:      GNU GPL v2
###############################################################
"""
Renders one or more guitar chord diagrams defined via:

    {define: NAME base-fret N frets S1 S2 S3 S4 S5 S6}

where each Si is:
    0  = open string
    X  = muted string
    N  = fret number (1-based from base-fret)

The diagrams are drawn below the song body, laid out in a row,
exactly like KlavierRenderer draws piano-keyboard diagrams.

Public API
----------
draw_guitar_diagram_section(dc, define_list, x, y, base_font,
                            pen_scale, highlight_color) -> height_added
"""

import re
import wx

# ---------------------------------------------------------------------------
# Geometry constants (logical pixels @ 96 dpi – same reference as klavier)
# ---------------------------------------------------------------------------
STRINGS      = 6          # standard guitar
FRETS_SHOWN  = 5          # rows in the grid
CELL_W       = 12         # width of one string column
CELL_H       = 12         # height of one fret row
NUT_H        = 4          # extra height for nut bar (base-fret == 1)
DOT_R        = 4          # radius of a finger dot
LABEL_PAD    = 6          # gap between chord name and marker row
MARKER_ROW_H = 14         # fixed height of the open/mute symbol row
FRET_LABEL_W = 14         # width reserved left of grid for base-fret number
DIAGRAM_GAP  = 18         # horizontal gap between diagrams
MUTE_SIZE    = 4          # half-size of X mark for muted strings
OPEN_R       = 3          # radius of open-string circle


def _parse_define(text):
    """
    Parse a {define:} attribute string.

    Returns (name, base_fret, frets) or None on failure.
    frets is a list of 6 elements, each one of: int (1-6), 0 (open), -1 (mute).
    """
    text = text.strip()
    # Tolerate both  "define: ..."  and just the attribute value after the colon
    # The Renderer already strips the command name, so `text` starts at the name.
    # Pattern: NAME  base-fret N  frets S1 S2 S3 S4 S5 S6
    m = re.match(
        r'(\S+)\s+base-fret\s+(\d+)\s+frets\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)',
        text, re.IGNORECASE
    )
    if not m:
        return None
    name     = m.group(1)
    base_fret = int(m.group(2))
    raw = [m.group(i) for i in range(3, 9)]
    frets = []
    for r in raw:
        if r.upper() == 'X':
            frets.append(-1)
        else:
            try:
                frets.append(int(r))
            except ValueError:
                return None
    return name, base_fret, frets


def _diagram_size(dc, base_font):
    """Return (diagram_w, diagram_h) for a single chord diagram."""
    dc.SetFont(base_font)
    _, label_h = dc.GetTextExtent("A")
    grid_w = (STRINGS - 1) * CELL_W
    grid_h = FRETS_SHOWN * CELL_H
    total_w = FRET_LABEL_W + grid_w + CELL_W
    total_h = label_h + LABEL_PAD + MARKER_ROW_H + NUT_H + grid_h
    return total_w, total_h, label_h


def _draw_one_diagram(dc, name, base_fret, frets, x, y,
                      pen_scale, base_font, highlight_color):
    """
    Draw one guitar chord diagram with top-left at (x, y).

    Vertical layout (top → bottom):
        [label_h]      chord name
        [LABEL_PAD]    gap
        [MARKER_ROW_H] open (○) / mute (X) symbols  ← own row, never overlaps name
        [NUT_H]        nut bar (only if base-fret == 1)
        [grid_h]       fret grid with finger dots

    Returns (width, height) of the drawn area.
    """
    pw = max(1, int(round(1.0 / pen_scale)))

    dc.SetFont(base_font)
    _, label_h = dc.GetTextExtent("A")

    grid_x = x + FRET_LABEL_W
    grid_w  = (STRINGS - 1) * CELL_W
    grid_h  = FRETS_SHOWN * CELL_H

    # Y positions for each zone
    name_y    = y
    marker_y  = y + label_h + LABEL_PAD          # top of marker row
    nut_y     = marker_y + MARKER_ROW_H           # top of nut / first fret line
    fret_top  = nut_y                             # adjusted below if nut drawn

    # ---- Chord name --------------------------------------------------------
    nw, _ = dc.GetTextExtent(name)
    dc.SetTextForeground(wx.BLACK)
    dc.DrawText(name, int(grid_x + (grid_w - nw) / 2), int(name_y))

    # ---- Open / mute markers (in their own dedicated row) ------------------
    marker_cy = int(marker_y + MARKER_ROW_H // 2)  # vertical centre of marker row

    for col, f in enumerate(frets):
        sx = int(grid_x + col * CELL_W)
        if f == -1:
            # Muted: draw X centred in marker row
            xc, yc = sx, marker_cy
            dc.SetPen(wx.Pen(wx.BLACK, pw + 1))
            dc.DrawLine(xc - MUTE_SIZE, yc - MUTE_SIZE, xc + MUTE_SIZE, yc + MUTE_SIZE)
            dc.DrawLine(xc - MUTE_SIZE, yc + MUTE_SIZE, xc + MUTE_SIZE, yc - MUTE_SIZE)
        elif f == 0:
            # Open: draw circle centred in marker row
            dc.SetPen(wx.Pen(wx.BLACK, pw))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.DrawCircle(sx, marker_cy, OPEN_R)

    # ---- Nut or base-fret number -------------------------------------------
    if base_fret == 1:
        nut_pen = wx.Pen(wx.BLACK, max(2, pw * 3))
        dc.SetPen(nut_pen)
        dc.DrawLine(int(grid_x), int(nut_y), int(grid_x + grid_w), int(nut_y))
        fret_top = nut_y + NUT_H
    else:
        dc.SetFont(
            wx.Font(max(6, base_font.GetPointSize() - 2),
                    wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL, False, base_font.GetFaceName())
        )
        dc.SetTextForeground(wx.BLACK)
        num_str = str(base_fret)
        nw2, nh2 = dc.GetTextExtent(num_str)
        dc.DrawText(num_str,
                    int(grid_x - FRET_LABEL_W + (FRET_LABEL_W - nw2) // 2),
                    int(fret_top + (CELL_H - nh2) // 2))
        dc.SetFont(base_font)

    # ---- Grid lines --------------------------------------------------------
    grid_pen = wx.Pen(wx.BLACK, pw)
    dc.SetPen(grid_pen)
    for row in range(FRETS_SHOWN + 1):
        fy = int(fret_top + row * CELL_H)
        dc.DrawLine(int(grid_x), fy, int(grid_x + grid_w), fy)
    for col in range(STRINGS):
        sx = int(grid_x + col * CELL_W)
        dc.DrawLine(sx, int(fret_top), sx, int(fret_top + grid_h))

    # ---- Finger dots -------------------------------------------------------
    if highlight_color is None:
        dot_color = wx.Colour(180, 30, 30)
    elif isinstance(highlight_color, wx.Colour):
        dot_color = highlight_color
    else:
        dot_color = wx.Colour(180, 30, 30)

    dc.SetBrush(wx.Brush(dot_color))
    dc.SetPen(wx.Pen(dot_color, pw))

    for col, f in enumerate(frets):
        if f <= 0:
            continue
        row = f - 1
        if row >= FRETS_SHOWN:
            continue
        sx = int(grid_x + col * CELL_W)
        fy = int(fret_top + row * CELL_H + CELL_H // 2)
        dc.DrawCircle(sx, fy, DOT_R)

    total_w = FRET_LABEL_W + grid_w
    total_h = label_h + LABEL_PAD + MARKER_ROW_H + NUT_H + grid_h
    return total_w, total_h


def draw_guitar_diagram_section(dc, define_list, x, y,
                                base_font, pen_scale,
                                highlight_color=None):
    """
    Draw all chord diagrams in define_list starting at (x, y).

    Returns the total height added (so the caller can expand the song bbox).
    """
    if not define_list:
        return 0

    parsed = []
    for attr in define_list:
        result = _parse_define(attr)
        if result is not None:
            parsed.append(result)

    if not parsed:
        return 0

    _, total_h, _ = _diagram_size(dc, base_font)
    cx = x
    for name, base_fret, frets in parsed:
        dw, dh = _draw_one_diagram(
            dc, name, base_fret, frets, cx, y,
            pen_scale, base_font, highlight_color
        )
        cx += dw + DIAGRAM_GAP

    return total_h + LABEL_PAD
