# -*- coding: utf-8 -*-
"""Chord direction arrow helpers.

In .crd files the arrow is an ASCII suffix inside the brackets:
    [DO^]  -> up      [DOv] -> down
(typed U+2191 / U+2193 are also accepted).
"""
import re

_ARROW_RE = re.compile(r'^(?P<name>.*\S)\s*(?P<a>[\^↑v↓])$')
_MAP = {'^': 'up', '↑': 'up', 'v': 'down', '↓': 'down'}
_GLYPH = {'up': u'↑', 'down': u'↓', '': u''}
SUFFIX = {'up': '^', 'down': 'v', '': ''}


def split_arrow(chord):
    """'DO^' -> ('DO', 'up'); 'DOv' -> ('DO', 'down'); 'DO' -> ('DO', '')."""
    m = _ARROW_RE.match(chord.strip())
    if not m:
        return chord, ''
    return m.group('name'), _MAP[m.group('a')]


def arrow_glyph(arrow):
    return _GLYPH.get(arrow, u'')


# Icona vettoriale (da navigation_3d28ulblt0hj.svg, viewBox 512x512): punta di
# freccia con tacca alla base. Definita verso l'ALTO e specchiata in y per
# ottenere la versione verso il BASSO (ARROW_DOWN_POLY).
_UP_POLY = [(256, 114.6), (396.5, 397.4), (256, 313.6), (115.5, 397.4)]
_YSUM = 114.6 + 397.4
ARROW_DOWN_POLY = [(x, _YSUM - y) for x, y in _UP_POLY]
_xs = [p[0] for p in ARROW_DOWN_POLY]
_ys = [p[1] for p in ARROW_DOWN_POLY]
ARROW_BBOX = (min(_xs), min(_ys), max(_xs), max(_ys))
ARROW_ASPECT = (ARROW_BBOX[2] - ARROW_BBOX[0]) / (ARROW_BBOX[3] - ARROW_BBOX[1])


def arrow_points(arrow, x0, top, w, h):
    """Punti (float) della sagoma scalata nel rettangolo (x0, top, w, h)."""
    bx0, by0, bx1, by1 = ARROW_BBOX
    sx = w / (bx1 - bx0)
    sy = h / (by1 - by0)
    pts = []
    for px, py in ARROW_DOWN_POLY:
        fx = (px - bx0) * sx
        fy = (py - by0) * sy
        if arrow == 'up':
            fy = h - fy
        pts.append((x0 + fx, top + fy))
    return pts


# ---------------------------------------------------------------------------
# Rasterizzazione nitida a QUALSIASI dimensione/zoom: si disegna a risoluzione
# DEVICE (pixel reali) con super-campionamento 8x e riduzione LANCZOS, cosi'
# i bordi restano lisci e le proporzioni fedeli all'SVG a ogni scala.
# ---------------------------------------------------------------------------
_SS = 8
_icon_cache = {}


def render_icon(arrow, w, h, rgb):
    """Ritorna (w, h, rgb_bytes, alpha_bytes) oppure None se Pillow manca."""
    key = (arrow, w, h, rgb)
    hit = _icon_cache.get(key)
    if hit is not None:
        return hit
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return None
    W, H = w * _SS, h * _SS
    m = Image.new('L', (W, H), 0)
    pts = arrow_points('down', 0, 0, W, H)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    if arrow == 'up':
        m = m.transpose(Image.FLIP_TOP_BOTTOM)
    m = m.resize((w, h), Image.LANCZOS)
    res = (w, h, bytes(bytearray(list(rgb) * (w * h))), m.tobytes())
    if len(_icon_cache) > 64:
        _icon_cache.clear()
    _icon_cache[key] = res
    return res
