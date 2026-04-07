###############################################################
# Name:         KlavierRenderer.py
# Purpose:      Draw piano keyboard diagrams for chords
# Author:       Denisov21
# Created:      2026-03-12
# Copyright:    Denisov21
# License:      GNU GPL v2
###############################################################


import wx
import re

try:
    from .Transpose import translateChord
    _has_transpose = True
except ImportError:
    _has_transpose = False

# Note italiane -> semitono (ordinate per lunghezza decrescente per match corretto)
_ITALIAN_NOTES = [
    ('sol#', 8), ('solb', 6), ('sol', 7),
    ('do#', 1),  ('dob', 11), ('do', 0),
    ('re#', 3),  ('reb', 1),  ('re', 2),
    ('mi#', 5),  ('mib', 3),  ('mi', 4),
    ('fa#', 6),  ('fab', 4),  ('fa', 5),
    ('la#', 10), ('lab', 8),  ('la', 9),
    ('si#', 0),  ('sib', 10), ('si', 11),
]

# Note inglesi -> semitono
_ENGLISH_NOTES = [
    ('c#', 1), ('cb', 11), ('c', 0),
    ('d#', 3), ('db', 1),  ('d', 2),
    ('e#', 5), ('eb', 3),  ('e', 4),
    ('f#', 6), ('fb', 4),  ('f', 5),
    ('g#', 8), ('gb', 6),  ('g', 7),
    ('a#', 10), ('ab', 8), ('a', 9),
    ('b#', 0), ('bb', 10), ('b', 11),
    ('h', 11),
]

# Suffissi accordo -> intervalli (ordinati per lunghezza decrescente)
_CHORD_INTERVALS = [
    ('maj7',  [0, 4, 7, 11]),
    ('maj',   [0, 4, 7]),
    ('m7b5',  [0, 3, 6, 10]),
    ('m7',    [0, 3, 7, 10]),
    ('min',   [0, 3, 7]),
    ('m',     [0, 3, 7]),
    ('dim7',  [0, 3, 6, 9]),
    ('dim',   [0, 3, 6]),
    ('aug',   [0, 4, 8]),
    ('sus4',  [0, 5, 7]),
    ('sus2',  [0, 2, 7]),
    ('7',     [0, 4, 7, 10]),
    ('5',     [0, 7]),
    ('-',     [0, 3, 7]),
    ('',      [0, 4, 7]),
]

# Tasti bianchi nell'ottava (semitoni)
_WHITE_KEYS = [0, 2, 4, 5, 7, 9, 11]
# Tasti neri: semitono -> indice spazio tra i bianchi
_BLACK_KEYS = {1: 0, 3: 1, 6: 3, 8: 4, 10: 5}


def parse_chord(chord_str):
    """
    Analizza una stringa accordo (notazione italiana o inglese).
    Restituisce (root_semitone, intervals) o None.
    """
    s = chord_str.strip()
    sl = s.lower()
    root = None
    rest = ''

    # Prova prima notazione italiana
    for note_str, semitone in _ITALIAN_NOTES:
        if sl.startswith(note_str):
            root = semitone
            rest = s[len(note_str):]
            break

    # Se non trovato prova inglese
    if root is None:
        for note_str, semitone in _ENGLISH_NOTES:
            if sl.startswith(note_str):
                root = semitone
                rest = s[len(note_str):]
                break

    if root is None:
        return None

    # Ignora il basso dopo /
    rest = rest.split('/')[0].strip()
    intervals = [0, 4, 7]  # default maggiore
    for suffix, ivs in _CHORD_INTERVALS:
        if rest.lower().startswith(suffix.lower()):
            intervals = ivs
            break

    return root, intervals


def get_chord_keys(chord_str):
    """Restituisce lista di semitoni (0-11) da evidenziare."""
    result = parse_chord(chord_str)
    if result is None:
        return None
    root, intervals = result
    return [(root + i) % 12 for i in intervals]


def _normalize_chord(chord_str, notations):
    """
    Converte l'accordo dalla notazione corrente verso l'italiano
    usando translateChord, così il parser funziona sempre.
    """
    if not _has_transpose or notations is None:
        return chord_str
    try:
        italian_notation = None
        for n in notations:
            if hasattr(n, 'id') and ('it' in n.id.lower() or 'italian' in n.id.lower()):
                italian_notation = n
                break
        if italian_notation is None:
            return chord_str
        current = notations[0] if notations else None
        if current is None:
            return chord_str
        return translateChord(chord_str, current, italian_notation)
    except Exception:
        return chord_str


def draw_keyboard(dc, x, y, w, h, chord_name, highlighted_keys, label_font=None, highlight_color=None):
    """
    Disegna una tastiera di un'ottava su dc.
    highlighted_keys: lista di semitoni (0-11) da evidenziare.
    highlight_color: wx.Colour per i tasti evidenziati (default rosso).
    """
    if highlight_color is None:
        highlight_color = wx.Colour(210, 60, 60)

    white_w = w // 7
    black_w = max(4, int(white_w * 0.55))
    black_h = int(h * 0.62)
    kbd_w = white_w * 7

    # Sfondo e bordo esterno
    dc.SetBrush(wx.WHITE_BRUSH)
    dc.SetPen(wx.Pen(wx.Colour(80, 80, 80), 1))
    dc.DrawRectangle(x, y, kbd_w, h)

    # Tasti bianchi
    for i, semi in enumerate(_WHITE_KEYS):
        kx = x + i * white_w
        if semi in highlighted_keys:
            dc.SetBrush(wx.Brush(highlight_color))
        else:
            dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetPen(wx.Pen(wx.Colour(80, 80, 80), 1))
        dc.DrawRectangle(kx, y, white_w, h)

    # Tasti neri (sopra)
    for semi, gap_idx in _BLACK_KEYS.items():
        kx = x + gap_idx * white_w + white_w - black_w // 2
        if semi in highlighted_keys:
            dc.SetBrush(wx.Brush(highlight_color))
        else:
            dc.SetBrush(wx.BLACK_BRUSH)
        dc.SetPen(wx.Pen(wx.Colour(40, 40, 40), 1))
        dc.DrawRectangle(kx, y, black_w, black_h)

    # Etichetta accordo sopra
    if label_font:
        dc.SetFont(label_font)
    lw, lh = dc.GetTextExtent(chord_name)
    tx = x + (kbd_w - lw) // 2
    ty = y - lh - 3
    dc.SetTextForeground(wx.BLACK)
    dc.DrawText(chord_name, tx, ty)


def draw_klavier_section(dc, klavier_list, start_x, start_y, base_font, pen_scale=1.0, notations=None, highlight_color=None):
    """
    Disegna tutte le tastiere in klavier_list in fondo alla canzone.
    Restituisce l'altezza totale occupata.
    """
    if not klavier_list:
        return 0

    white_w = 16
    kbd_w = white_w * 7
    kbd_h = 44
    padding_x = 22
    padding_y = 14
    label_h = 18
    row_h = label_h + kbd_h + padding_y

    label_font = wx.Font(
        max(7, int(base_font.GetPointSize() * 0.85)),
        wx.FONTFAMILY_DEFAULT,
        wx.FONTSTYLE_NORMAL,
        wx.FONTWEIGHT_BOLD,
        False,
        base_font.GetFaceName()
    )

    # Linea separatrice
    sep_y = start_y + 10
    dc.SetPen(wx.Pen(wx.Colour(180, 180, 180), max(1, round(1 / pen_scale)), wx.PENSTYLE_DOT))
    dc.DrawLine(start_x, sep_y, start_x + 500, sep_y)

    # Titolo sezione
    title_font = wx.Font(
        max(7, int(base_font.GetPointSize() * 0.8)),
        wx.FONTFAMILY_DEFAULT,
        wx.FONTSTYLE_ITALIC,
        wx.FONTWEIGHT_NORMAL,
        False,
        base_font.GetFaceName()
    )
    dc.SetFont(title_font)
    dc.SetPen(wx.NullPen)
    dc.SetTextForeground(wx.Colour(110, 110, 110))
    dc.DrawText("Accordi", start_x, sep_y + 4)
    dc.SetTextForeground(wx.BLACK)

    cur_x = start_x
    cur_y = sep_y + 26
    max_x = start_x + 560

    for chord_name in klavier_list:
        normalized = _normalize_chord(chord_name, notations)
        keys = get_chord_keys(normalized)
        if keys is None:
            keys = get_chord_keys(chord_name)  # fallback
        if keys is None:
            continue
        if cur_x + kbd_w > max_x:
            cur_x = start_x
            cur_y += row_h

        draw_keyboard(dc, cur_x, cur_y + label_h, kbd_w, kbd_h, chord_name, keys, label_font, highlight_color)
        cur_x += kbd_w + padding_x

    total_h = (cur_y + row_h) - start_y + 10
    return total_h
