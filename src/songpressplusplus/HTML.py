###############################################################
# Name:             HTML.py
# Purpose:     Export song to HTML
# Author:         Luca Allulli (webmaster@roma21.it)
# Modified by:  Denisov21
# Created:     2010-05-05
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
###############################################################

import base64
import os
import re
import traceback
from xml.sax.saxutils import escape as _xml_escape

import wx

from .Renderer import *
from .SongDecorator import SongDecorator
from .Globals import glb as _glb
from .KlavierRenderer import draw_klavier_section, start_note_to_semitone
from .GuitarDiagramRenderer import (
    draw_guitar_diagram_section, _parse_define,
    STRINGS, CELL_W, FRET_LABEL_W, DIAGRAM_GAP, DOT_R)


class _SvgDC(object):
    """Mini wx.DC che registra le chiamate di disegno come elementi SVG.

    Implementa solo i metodi usati da KlavierRenderer e GuitarDiagramRenderer
    (le tastiere e i diagrammi chitarra). Si usa questo al posto di
    wx.SVGFileDC perche' non passa da un file temporaneo, non dipende dal
    backend grafico e accetta anche la penna/pennello nulli (wx.NullPen) che
    KlavierRenderer imposta prima del titolo di sezione.

    Le coordinate sono pixel logici con y verso il basso, come per un DC wx;
    le misure del testo vengono da un wx.MemoryDC (stessa metrica dell'anteprima).
    """

    def __init__(self):
        self.parts = []
        self._mdc = wx.MemoryDC(wx.Bitmap(1, 1))
        try:
            self._ppi = float(self._mdc.GetPPI()[1]) or 96.0
        except Exception:
            self._ppi = 96.0
        self._font = wx.NORMAL_FONT
        self._pen = None
        self._brush = None
        self._tcol = wx.BLACK

    # -- stato -----------------------------------------------------------
    def SetFont(self, font):
        if font is not None and font.IsOk():
            self._font = font
            self._mdc.SetFont(font)

    def GetFont(self):
        return self._font

    def SetPen(self, pen):
        self._pen = pen

    def SetBrush(self, brush):
        self._brush = brush

    def SetTextForeground(self, colour):
        self._tcol = colour

    def SetBackgroundMode(self, mode):
        pass

    def GetUserScale(self):
        return 1.0, 1.0

    def SetUserScale(self, sx, sy):
        pass

    def DrawBitmap(self, *args, **kwargs):
        pass   # le sezioni vettoriali non usano bitmap (arrow_bitmap=False)

    # -- misure ----------------------------------------------------------
    def GetTextExtent(self, text):
        w, h = self._mdc.GetTextExtent(text)
        return w, h

    def GetFullTextExtent(self, text):
        return self._mdc.GetFullTextExtent(text)

    # -- disegno ---------------------------------------------------------
    @staticmethod
    def _hex(col):
        return '#%02x%02x%02x' % (col.Red(), col.Green(), col.Blue())

    @staticmethod
    def _num(v):
        return ('%.2f' % v).rstrip('0').rstrip('.')

    def _attrs(self):
        """Attributi SVG (stroke/fill) da penna e pennello correnti, piu'
        lo spessore del tratto (0 se non c'e' bordo)."""
        pen, br = self._pen, self._brush
        stroke = bool(pen is not None and pen.IsOk()
                      and pen.GetStyle() != wx.PENSTYLE_TRANSPARENT)
        fill = bool(br is not None and br.IsOk()
                    and br.GetStyle() != wx.BRUSHSTYLE_TRANSPARENT)
        a = []
        pw = 0
        if stroke:
            pw = max(1, pen.GetWidth())
            a.append('stroke="%s" stroke-width="%s"'
                     % (self._hex(pen.GetColour()), self._num(pw)))
            if pen.GetStyle() in (wx.PENSTYLE_DOT, wx.PENSTYLE_SHORT_DASH):
                a.append('stroke-dasharray="%s %s"'
                         % (self._num(pw), self._num(2 * pw)))
        else:
            a.append('stroke="none"')
        if fill:
            a.append('fill="%s"' % self._hex(br.GetColour()))
        else:
            a.append('fill="none"')
        return ' '.join(a), stroke, fill, pw

    def DrawLine(self, x1, y1, x2, y2):
        attrs, stroke, _fill, pw = self._attrs()
        if not stroke:
            return
        # Linee di spessore dispari sul centro del pixel: restano nitide
        o = 0.5 if int(round(pw)) % 2 == 1 else 0
        self.parts.append(
            '<line x1="%s" y1="%s" x2="%s" y2="%s" %s shape-rendering="crispEdges"/>'
            % (self._num(x1 + o), self._num(y1 + o),
               self._num(x2 + o), self._num(y2 + o), attrs))

    def DrawRectangle(self, x, y, w, h):
        attrs, stroke, fill, pw = self._attrs()
        if not (stroke or fill):
            return
        if stroke:
            # Come in wx il bordo sta dentro (x..x+w-1): si rientra di mezzo tratto
            x, y, w, h = x + pw / 2.0, y + pw / 2.0, w - pw, h - pw
        self.parts.append(
            '<rect x="%s" y="%s" width="%s" height="%s" %s shape-rendering="crispEdges"/>'
            % (self._num(x), self._num(y), self._num(max(0, w)),
               self._num(max(0, h)), attrs))

    def DrawCircle(self, x, y, r):
        attrs, stroke, fill, _pw = self._attrs()
        if stroke or fill:
            self.parts.append('<circle cx="%s" cy="%s" r="%s" %s/>'
                              % (self._num(x + 0.5), self._num(y + 0.5),
                                 self._num(r), attrs))

    def DrawPolygon(self, points, *args, **kwargs):
        attrs, stroke, fill, _pw = self._attrs()
        if (stroke or fill) and points:
            pts = ' '.join('%s,%s' % (self._num(p[0]), self._num(p[1]))
                           for p in points)
            self.parts.append('<polygon points="%s" %s/>' % (pts, attrs))

    def DrawText(self, text, x, y):
        if not text:
            return
        f = self._font
        _w, h, desc, _lead = self._mdc.GetFullTextExtent(text)
        baseline = y + (h - desc)       # (x, y) = angolo alto-sinistro del testo
        face = (f.GetFaceName() or '').replace('"', '').replace("'", '')
        fam = ("'%s', " % face if face else '') + 'Helvetica, Arial, sans-serif'
        try:
            bold = f.GetNumericWeight() >= 600
        except Exception:
            bold = f.GetWeight() == wx.FONTWEIGHT_BOLD
        italic = f.GetStyle() in (wx.FONTSTYLE_ITALIC, wx.FONTSTYLE_SLANT)
        size = max(1.0, f.GetPointSize() * self._ppi / 72.0)
        self.parts.append(
            '<text x="%s" y="%s" font-family="%s" font-size="%s"%s%s fill="%s" '
            'xml:space="preserve">%s</text>'
            % (self._num(x), self._num(baseline), _xml_escape(fam),
               self._num(size),
               ' font-weight="bold"' if bold else '',
               ' font-style="italic"' if italic else '',
               self._hex(self._tcol), _xml_escape(text)))


class HtmlExporter(object):
    def __init__(self, sf):
        object.__init__(self)
        self.sf = sf
        self.out = ""
        # Tastiere ({taste:}/{fingering:}) e diagrammi chitarra ({define:}):
        # vengono disegnati come SVG vettoriale incorporato nella pagina.
        # Gli attributi hanno gli stessi nomi di SongDecorator, cosi' Renderer
        # (che imposta .notation) e SongpressFrame li gestiscono uguale.
        self.showKlavier = True
        self.showGuitarDiagrams = True
        self.notation = None
        self.klavierHighlightColor = None
        self.fingerNumColor = None
        self.klavierStartNote = 0
        # Larghezza (px) entro cui le tastiere vanno a capo
        self.diagramsWidth = 800
        # Battiti sopra gli accordi ({beats_time:}): stessi nomi e default di
        # SongDecorator; SongpressFrame li imposta dalle preferenze.
        self.showDurationBeats = True
        self.durationBeatsColourHex = '#6464C8'
        self.durationBeatsSizePct = 60
        self.durationBeatsBold = False
        self.durationBeatsAlign = 'right'     # 'left' | 'center' | 'right'
        self.durationBeatsMode = 'number'     # 'number' | 'dots' | 'both'
        # Icona del tempo ({tempo_s:}, {tempo_c:}...): Renderer le imposta a ogni
        # Render (dimensione in px, colore wx.Colour o None = colore originale).
        self.tempoIconSize = None
        self.tempoIconColour = None
        # Etichette di strofe/ritornelli (come l'anteprima, se attive)
        self.showLabels = False
        self.chorusLabel = ''

    # ── Battiti e icone del tempo ───────────────────────────────────────
    def _BeatsHtml(self, beats):
        """HTML del numero e/o dei puntini dei battiti da mettere sopra un
        accordo (stessa logica di SongDecorator._DrawBeatsApex)."""
        if not beats or beats < 1 or not self.showDurationBeats:
            return ''
        col = self.durationBeatsColourHex or '#6464C8'
        align = self.durationBeatsAlign if self.durationBeatsAlign in (
            'left', 'center', 'right') else 'right'
        style = 'color:%s;font-size:%d%%;font-weight:%s;text-align:%s' % (
            col, int(self.durationBeatsSizePct or 60),
            'bold' if self.durationBeatsBold else 'normal', align)
        mode = self.durationBeatsMode
        html = ''
        if mode in ('dots', 'both'):
            dots = ''.join(
                '<span style="display:inline-block;width:.4em;height:.4em;'
                'border-radius:50%%;background:%s;margin:0 .1em"></span>' % col
                for _i in range(int(beats)))
            html += '<span class="beats" style="%s">%s</span>' % (style, dots)
        if mode in ('number', 'both'):
            html += '<span class="beats" style="%s">%d</span>' % (style, beats)
        return html

    def _TempoIconHtml(self, t):
        """<img> con l'icona del tempo (nota musicale) se il testo `t` ne ha
        una, altrimenti ''. Usa gli stessi file di SongDecorator: prima l'SVG
        (vettoriale, con il colore scelto), altrimenti il PNG."""
        for flag, svg_name, png_name in SongDecorator._TEMPO_ICONS:
            if not getattr(t, flag, False):
                continue
            size = int(self.tempoIconSize) if self.tempoIconSize else 0
            height = ('%dpx' % size) if size else '1.3em'
            style = 'height:%s;vertical-align:middle;margin-right:2px' % height
            try:
                path = _glb.AddPath('img/vector/%s.svg' % svg_name)
                if os.path.isfile(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        svg = f.read()
                    col = self.tempoIconColour
                    if col is not None and col.IsOk():
                        svg = re.sub(r'fill\s*=\s*"(?!none)[^"]*"',
                                     'fill="#%02x%02x%02x"' % (
                                         col.Red(), col.Green(), col.Blue()),
                                     svg, flags=re.IGNORECASE)
                    uri = 'data:image/svg+xml;base64,' + base64.b64encode(
                        svg.encode('utf-8')).decode('ascii')
                    return '<img alt="" src="%s" style="%s">' % (uri, style)
                png = _glb.AddPath(png_name.replace('img/', 'img/32/', 1))
                if not os.path.isfile(png):
                    png = _glb.AddPath(png_name)
                with open(png, 'rb') as f:
                    uri = 'data:image/png;base64,' + base64.b64encode(
                        f.read()).decode('ascii')
                return '<img alt="" src="%s" style="%s">' % (uri, style)
            except Exception:
                return ''
        return ''

    def _VectorSection(self, draw):
        """Esegue draw(dc, x, y) -> (altezza, larghezza_usata) su un _SvgDC e
        restituisce l'elemento <svg> (testo) pronto da incorporare nell'HTML.

        L'SVG contiene linee, rettangoli e testo veri (niente bitmap): nitido
        a qualunque zoom e in stampa."""
        pad = 2
        dc = _SvgDC()
        h, used_w = draw(dc, pad, pad)
        w = max(1, int(used_w) + 2 * pad)   # margine a sinistra e a destra
        h = max(1, int(h) + 2 * pad)
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
                'viewBox="0 0 %d %d">%s</svg>' % (w, h, w, h, ''.join(dc.parts)))

    def _SectionHtml(self, css_class, draw):
        """<div> con l'SVG della sezione. Se il disegno fallisce l'esportazione
        prosegue: al posto della sezione resta un commento HTML con il motivo
        (si legge aprendo il file come testo)."""
        try:
            return '<div class="diagrams %s">%s</div>' % (
                css_class, self._VectorSection(draw))
        except Exception:
            err = traceback.format_exc().replace('--', '- -')
            return '<!-- Songpress: sezione "%s" non disegnata:\n%s-->' % (
                css_class, err)

    def _DiagramsHtml(self, song):
        """SVG vettoriali di tastiere e diagrammi chitarra del brano."""
        parts = []
        font = song.format.wxFont
        klavier_list = getattr(song, 'klavier_list', None)
        if self.showKlavier and klavier_list:
            def draw_klavier(dc, x, y):
                return draw_klavier_section(
                    dc, klavier_list, x, y, font, 1.0, self.notation,
                    self.klavierHighlightColor,
                    finger_num_color=self.fingerNumColor,
                    content_w=self.diagramsWidth,
                    start_note=start_note_to_semitone(self.klavierStartNote),
                    arrow_bitmap=False)   # frecce vettoriali, non bitmap
            parts.append(self._SectionHtml('klavier', draw_klavier))
        define_list = getattr(song, 'define_list', None)
        if self.showGuitarDiagrams and define_list:
            # Larghezza reale: i diagrammi stanno su una sola riga
            n = sum(1 for d in define_list if _parse_define(d))
            guitar_w = (n * (FRET_LABEL_W + (STRINGS - 1) * CELL_W)
                        + max(0, n - 1) * DIAGRAM_GAP + DOT_R)

            def draw_guitar(dc, x, y):
                h = draw_guitar_diagram_section(
                    dc, define_list, x, y, font, 1.0,
                    self.klavierHighlightColor)
                return h, guitar_w
            parts.append(self._SectionHtml('guitar', draw_guitar))
        return ''.join(parts)

    def _FaviconHtml(self):
        """<link rel="icon"> con img/favicon.ico incorporato (data URI), cosi' la
        pagina resta un file unico. Dall'.ico si tengono solo le immagini
        piccole (16/32/48 px) per non appesantire l'HTML."""
        import struct
        data = None
        for name in ('img/favicon.ico', 'img/songpress.ico', 'img/songpress++.ico'):
            try:
                path = _glb.AddPath(name)
                if path and os.path.isfile(path):
                    with open(path, 'rb') as f:
                        data = f.read()
                    break
            except Exception:
                traceback.print_exc()
        if not data:
            return ''
        try:
            count = struct.unpack('<H', data[4:6])[0]
            entries = []
            for i in range(count):
                w, h, c, r, pl, bpp, size, off = struct.unpack(
                    '<BBBBHHII', data[6 + 16 * i:22 + 16 * i])
                if (w or 256) <= 48:
                    entries.append((w, h, c, r, pl, bpp, data[off:off + size]))
            if entries:
                head = struct.pack('<HHH', 0, 1, len(entries))
                offset = 6 + 16 * len(entries)
                dirs, blobs = b'', b''
                for w, h, c, r, pl, bpp, blob in entries:
                    dirs += struct.pack('<BBBBHHII', w, h, c, r, pl, bpp,
                                        len(blob), offset + len(blobs))
                    blobs += blob
                data = head + dirs + blobs
        except Exception:
            traceback.print_exc()
        uri = 'data:image/x-icon;base64,' + base64.b64encode(data).decode('ascii')
        return '    <link rel="icon" type="image/x-icon" href="%s" />' % uri

    def _BlockLabel(self, block):
        """Testo dell'etichetta di strofa/ritornello, con le stesse regole di
        StandardVerseNumbers ('' = nessuna etichetta)."""
        if not self.showLabels or block.type == SongBlock.title:
            return ''
        if len(block.boxes) == 0:
            return ''
        label = getattr(block, 'label', None)
        if block.type == SongBlock.verse:
            # Nessuna etichetta se il blocco non ha testo visibile
            visible = False
            for line in block.boxes:
                for t in line.boxes:
                    tx = (getattr(t, 'text', '') or '').strip()
                    if t.type != SongText.comment and tx and not tx.startswith('#'):
                        visible = True
            if not visible:
                return ''
            if label is not None:
                return label
            n = getattr(block, 'verseLabelNumber', None)
            return '' if n is None else str(n)
        if label is not None:
            return label
        return self.chorusLabel or ''

    def Draw(self, song, dc):
        classes = {
            SongBlock.title: 'titleblock',
            SongBlock.chorus: 'chorus',
            SongBlock.verse: 'verse',
        }

        template = """<!DOCTYPE html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>%(title)s</title>
%(favicon)s
    <style>
        body {
            font-family: "%(face)s";
        }
        div.chorus, div.verse, div.titleblock {
            margin-bottom: 1.5em;
        }
        div.chorus {
            font-weight: bold;
        }
        .lcell {
            flex: 0 0 auto;
            min-width: %(labw)s;
            padding-right: 0.6em;
            box-sizing: content-box;
            align-self: flex-end;
            line-height: 1.4;
        }
        .text.notext {
            display: block;
            height: 0;
            line-height: 0;
            overflow: hidden;
        }
        .blabel {
            display: inline-block;
            box-sizing: border-box;
            min-width: 1.4em;
            padding: 0 0.3em;
            text-align: center;
            font-weight: normal;
            line-height: 1.3;
            background: #c8c8c8;
            color: #000;
            border: 1px solid #000;
            white-space: nowrap;
        }
        .blabel.ghost {
            visibility: hidden;
        }
        .blabel.lab-chorus {
            background: #000;
            color: #fff;
        }
        .title {
            font-weight: bold;
            text-decoration: underline;
        }
        .subtitle {
            font-weight: normal;
            font-style: italic;
            font-size: 0.95em;
        }
        .line {
            display: flex;
            flex-direction: row;
            flex-wrap: nowrap;
            align-items: flex-end;
            line-height: 1.4;
        }
        .pair {
            display: inline-flex;
            flex-direction: column;
            align-items: flex-start;
        }
        .chord {
            font-style: italic;
            font-size: small;
            font-weight: normal;
            white-space: pre;
            min-height: 1em;
        }
        .text {
            white-space: pre;
        }
        .cb {
            display: inline-flex;
            flex-direction: column;
            font-size: small;
        }
        .beats {
            display: block;
            font-style: normal;
            line-height: 1.1;
            white-space: pre;
        }
        .diagrams {
            margin-top: 1.5em;
        }
        .diagrams svg {
            display: block;
            max-width: 100%%;
            height: auto;
        }
    </style>
</head>
<body>
    %(body)s
</body>
</html>"""

        out = ""
        # Titolo della pagina: i soli {title:} (SongText.title) del PRIMO blocco
        # titolo che ne contiene. Sottotitoli, commenti ({comment_box:}...) e testo
        # semplice dei blocchi titolo successivi non lo devono sovrascrivere.
        title = None
        _title_open = False      # stiamo leggendo i {title:} del blocco corrente
        _title_done = False      # il titolo e' completo: non cambia piu'
        _title_fallback = None   # primo testo semplice, se non c'e' nessun {title:}

        # Colonna delle etichette: larghezza comune a tutti i blocchi, cosi' il
        # testo di "Intro" e delle strofe parte alla stessa distanza.
        _maxlen = max([len(self._BlockLabel(b)) for b in song.boxes] + [1])
        labw = '%dch' % (_maxlen + 2)

        for block in song.boxes:
            lab = self._BlockLabel(block)
            b = '<div class="%s%s">' % (classes[block.type], ' labeled' if lab else '')
            _title_open = False
            _label_html = ''
            if lab:
                _label_html = '<span class="blabel %s">%s</span>' % (
                    'lab-chorus' if block.type == SongBlock.chorus else 'lab-verse',
                    _xml_escape(lab))
            # Come in anteprima: l'etichetta sta sulla prima riga che contiene
            # davvero del testo o degli accordi (salta righe vuote iniziali).
            _label_idx = 0
            for _i, _l in enumerate(block.boxes):
                if any((getattr(_t, 'text', '') or '').strip() for _t in _l.boxes):
                    _label_idx = _i
                    break
            _line_no = -1

            for line in block.boxes:
                _line_no += 1
                pairs = []
                current_pair = [None, "", 0]    # [accordo, testo, battiti]

                for t in line.boxes:
                    if t.type == SongText.title:
                        current_pair[1] += '<span class="title">%s</span>' % t.text
                        if block.type == SongBlock.title and not _title_done:
                            if not _title_open:
                                title = t.text
                                _title_open = True
                            else:
                                title += t.text
                    elif t.type == SongText.subtitle:
                        current_pair[1] += '<span class="subtitle">%s%s</span>' % (
                            self._TempoIconHtml(t), t.text)
                    elif t.type == SongText.chord:
                        pairs.append(current_pair)
                        current_pair = [t.text, "", getattr(t, 'duration_beats', 0) or 0]
                    else:
                        current_pair[1] += t.text
                        if (block.type == SongBlock.title
                                and _title_fallback is None and t.text.strip()):
                            _title_fallback = t.text.strip()

                pairs.append(current_pair)

                line_html = '<div class="line">'
                if lab:
                    line_html += '<div class="lcell">%s</div>' % (
                        _label_html if _line_no == _label_idx
                        else _label_html.replace('class="blabel', 'class="blabel ghost', 1))
                no_text = not any(re.sub(r'<[^>]*>', '', tx or '').strip()
                                  for _c, tx, _b in pairs)
                for chord, text, beats in pairs:
                    chord_html = chord if chord is not None else ""
                    chord_span = '<span class="chord">%s</span>' % (
                        chord_html or "&#8203;")
                    beats_html = self._BeatsHtml(beats) if chord else ''
                    if beats_html:
                        # numero/puntini sopra l'accordo, allineati alla sua larghezza
                        chord_span = '<span class="cb">%s%s</span>' % (
                            beats_html, chord_span)
                    if no_text:
                        # riga di soli accordi: il testo (solo spazi) tiene la
                        # distanza tra gli accordi ma non occupa altezza
                        line_html += (
                            '<div class="pair">%s'
                            '<span class="text notext">%s</span>'
                            '</div>'
                        ) % (chord_span, text or "")
                    else:
                        line_html += (
                            '<div class="pair">%s'
                            '<span class="text">%s</span>'
                            '</div>'
                        ) % (chord_span, text or "&#8203;")
                line_html += "</div>"
                b += line_html

            b += "</div>"
            out += b
            if _title_open:
                _title_done = True   # primo blocco con {title:} chiuso

        if title is None:
            title = _title_fallback or "Songpress"

        # Tastiere e diagrammi chitarra in fondo al brano (come in anteprima).
        # Con una selezione (brano non intero) non si disegnano, come in PostDrawSong.
        if getattr(song, 'drawWholeSong', True):
            out += self._DiagramsHtml(song)

        self.out = template % {
            'title': title,
            'body': out,
            'face': self.sf.face,
            'labw': labw,
            'favicon': self._FaviconHtml(),
        }
        return 0, 0

    def getHtml(self):
        return self.out


class TabExporter(object):
    def __init__(self, sf):
        object.__init__(self)
        self.sf = sf
        self.out = ""

    def Draw(self, song, dc):
        # dc is a dummy parameter
        out = []
        for block in song.boxes:
            for line in block.boxes:
                tc = ""
                tt = ""
                spaces = 0
                for t in line.boxes:
                    if t.type == SongText.chord:
                        if spaces >= 0:
                            tc += " " * spaces
                        else:
                            tt += " " * -spaces
                        tc += t.text
                        spaces = -len(t.text)
                    else:
                        tt += t.text
                        spaces += len(t.text)
                if tc != "":
                    out.append(tc)
                out.append(tt)
            out.append("\n")
        self.out = "\n".join(out).strip()
        return 0, 0

    def getTab(self):
        return self.out