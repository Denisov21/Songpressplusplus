###############################################################
# Name:         PdfExporter.py
# Purpose:      Esportazione PDF per Songpress
# Author:       Denisov21
# Created:      2026
# Copyright: © 2026 Denisov21
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
import subprocess
import tempfile

import wx

# Testo del brano come vero testo vettoriale (selezionabile, nitido a ogni
# zoom). Se un brano usa qualcosa che non si sa disegnare cosi' (font non
# trovato, filigrana, caratteri mancanti nel font...) l'esportazione ripiega
# da sola sul bitmap. Mettere False per tornare sempre al bitmap.
PDF_VECTOR_TEXT = True


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

def _has_reportlab():
    """True se la libreria reportlab e' importabile."""
    try:
        import reportlab  # noqa: F401
        return True
    except ImportError:
        return False


def open_pdf(filepath):
    """Apre il PDF con l'applicazione predefinita del sistema (Win/Linux/macOS)."""
    try:
        if sys.platform == 'win32':
            os.startfile(filepath)  # type: ignore[attr-defined]
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', filepath])
        else:
            subprocess.Popen(['xdg-open', filepath])
    except Exception as e:
        wx.MessageBox(
            "Impossibile aprire il PDF automaticamente:\n%s\n\n"
            "Il file e' comunque stato creato in:\n%s" % (e, filepath),
            "Apertura PDF",
            wx.OK | wx.ICON_WARNING,
        )


def _notify_success_and_maybe_open(frame_obj, filepath, offer_open):
    """Mostra l'esito dell'esportazione e, se l'utente lascia spuntata la
    casella "Apri il PDF ora", apre il file con l'applicazione predefinita.

    Usa wx.RichMessageDialog, che espone nativamente una checkbox sul dialog
    ed e' disponibile su tutte le piattaforme. Se per qualche motivo non fosse
    disponibile, ripiega su un normale messaggio informativo (senza apertura).
    """
    parent = getattr(frame_obj, 'frame', None)
    msg = "PDF esportato con successo:\n%s" % filepath
    title = "Esportazione PDF"

    if offer_open and hasattr(wx, 'RichMessageDialog'):
        dlg = wx.RichMessageDialog(parent, msg, title,
                                   wx.OK | wx.ICON_INFORMATION)
        dlg.ShowCheckBox("Apri il PDF ora", checked=True)
        dlg.ShowModal()
        want_open = dlg.IsCheckBoxChecked()
        dlg.Destroy()
        if want_open:
            open_pdf(filepath)
    else:
        wx.MessageBox(msg, title, wx.OK | wx.ICON_INFORMATION, parent)


def ask_h_alignment(frame_obj):
    """Chiede la posizione orizzontale del brano (A sinistra / Al centro).

    Mostra due radio button, preselezionati sul valore corrente di
    `_print_h_center` (lo stesso della voce "Posizione" in Opzioni di stampa) e,
    se l'utente conferma, lo aggiorna e lo salva. Ritorna False se annullato.
    Va chiamata prima di export_as_pdf().
    """
    _ = wx.GetTranslation
    parent = getattr(frame_obj, 'frame', None)
    dlg = wx.Dialog(parent, title=_("Position:").rstrip(':'),
                    style=wx.DEFAULT_DIALOG_STYLE)
    center = bool(getattr(frame_obj, '_print_h_center', False))

    box = wx.StaticBoxSizer(wx.VERTICAL, dlg, _("Position:").rstrip(':'))
    rb_left = wx.RadioButton(dlg, label=_("Left"), style=wx.RB_GROUP)
    rb_center = wx.RadioButton(dlg, label=_("Center"))
    rb_left.SetValue(not center)
    rb_center.SetValue(center)
    box.Add(rb_left, 0, wx.ALL, 6)
    box.Add(rb_center, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

    top = wx.BoxSizer(wx.VERTICAL)
    top.Add(box, 0, wx.EXPAND | wx.ALL, 10)
    top.Add(dlg.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL),
            0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
    dlg.SetSizerAndFit(top)
    dlg.CentreOnParent()
    rb_left.SetFocus()

    ok = dlg.ShowModal() == wx.ID_OK
    new_center = rb_center.GetValue()
    dlg.Destroy()
    if not ok:
        return False
    frame_obj._print_h_center = bool(new_center)
    try:
        frame_obj._SavePageMargins()     # stessa chiave di Opzioni di stampa
    except Exception:
        pass
    return True


def export_as_pdf(frame_obj, filepath, title, offer_open=True):
    """Esporta il brano in PDF.

    reportlab e' il metodo primario su TUTTE le piattaforme: e' Python puro,
    non dipende dal backend di stampa nativo e produce lo stesso output
    ovunque. Su Linux/macOS il vecchio percorso CUPS (wx.PRINT_MODE_FILE) non
    e' affidabile su wxGTK: segnala "successo" ma spesso NON crea il file.
    Per questo lo usiamo solo come ripiego, e solo se reportlab non c'e'.

    Se offer_open e' True e l'esportazione riesce, il messaggio di esito
    mostra una casella "Apri il PDF ora" (spuntata di default): lasciandola
    spuntata il PDF viene aperto con l'applicazione predefinita del sistema.
    """
    if _has_reportlab():
        ok = _export_reportlab(frame_obj, filepath)
    elif sys.platform == 'win32':
        # Nessuna alternativa: _export_reportlab mostrera' il messaggio
        # "installare reportlab".
        ok = _export_reportlab(frame_obj, filepath)
    else:
        ok = _export_cups(frame_obj, filepath, title)

    if ok:
        _notify_success_and_maybe_open(frame_obj, filepath, offer_open)
    return ok


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


# ------------------------------------------------------------------ #
#  Disegno VETTORIALE di tastiere e diagrammi chitarra                #
# ------------------------------------------------------------------ #
#
# Tastiere ({taste:}/{fingering:}) e diagrammi chitarra ({define:}) vengono
# disegnati direttamente nel PDF come linee, rettangoli e testo: restano nitidi
# a qualunque zoom e in stampa. (Il testo del brano e' vettoriale a sua volta,
# vedi _SongDC piu' sotto, salvo ripiego sul bitmap di _render_segment_to_png.) Per riusare KlavierRenderer e
# GuitarDiagramRenderer (che disegnano su un wx.DC) senza duplicarne la
# geometria, _VectorDC e' un piccolo "DC" che traduce le chiamate di disegno
# in operazioni di un canvas reportlab.

_PX_TO_PT = 0.75   # 1 pixel logico (96 dpi) = 0.75 pt: scala "naturale" del brano


def _rl_font_name(font):
    """Nome del font base PDF piu' vicino al wx.Font (Helvetica/Times/Courier)."""
    face = (font.GetFaceName() or '').lower()
    if 'courier' in face or 'mono' in face or 'consolas' in face:
        fam = 'Courier'
    elif 'times' in face or 'serif' in face and 'sans' not in face:
        fam = 'Times'
    else:
        fam = 'Helvetica'
    try:
        bold = font.GetNumericWeight() >= 600
    except Exception:
        bold = font.GetWeight() == wx.FONTWEIGHT_BOLD
    italic = font.GetStyle() in (wx.FONTSTYLE_ITALIC, wx.FONTSTYLE_SLANT)
    if fam == 'Times':
        return {(0, 0): 'Times-Roman', (1, 0): 'Times-Bold',
                (0, 1): 'Times-Italic', (1, 1): 'Times-BoldItalic'}[(bold, italic)]
    suffix = {(0, 0): '', (1, 0): '-Bold', (0, 1): '-Oblique',
              (1, 1): '-BoldOblique'}[(bold, italic)]
    return fam + suffix


class _VectorDC(object):
    """Mini wx.DC che disegna su un canvas reportlab in vettoriale.

    Implementa solo i metodi usati da KlavierRenderer e GuitarDiagramRenderer.
    Le coordinate sono pixel logici con y verso il basso e origine in alto a
    sinistra della sezione; (ox, oy) e' quel punto sulla pagina PDF (in pt, y
    verso l'alto) e k i punti per pixel logico. Con canvas=None non disegna
    nulla ma risponde alle misure: serve a calcolare l'ingombro della sezione.
    """

    def __init__(self, canvas, ox=0.0, oy=0.0, k=_PX_TO_PT):
        self.c = canvas
        self.ox, self.oy, self.k = ox, oy, k
        self._mdc = wx.MemoryDC(wx.Bitmap(1, 1))   # solo per le metriche del font
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
    def _size_px(self):
        """Corpo del font in pixel logici."""
        return max(1.0, self._font.GetPointSize() * self._ppi / 72.0)

    def _text_width(self, text):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        return stringWidth(self._clean(text), _rl_font_name(self._font),
                           self._size_px())

    @staticmethod
    def _clean(text):
        # I font base PDF coprono solo Latin-1/WinAnsi
        return text.encode('cp1252', 'replace').decode('cp1252')

    def GetTextExtent(self, text):
        _w, h = self._mdc.GetTextExtent(text)
        return int(round(self._text_width(text))), h

    def GetFullTextExtent(self, text):
        _w, h, desc, lead = self._mdc.GetFullTextExtent(text)
        return int(round(self._text_width(text))), h, desc, lead

    # -- disegno ---------------------------------------------------------
    @staticmethod
    def _rgb(col):
        if not hasattr(col, 'Red'):          # stringa "#RRGGBB", nome, tupla
            col = wx.Colour(col)
        return col.Red() / 255.0, col.Green() / 255.0, col.Blue() / 255.0

    def _style(self):
        """(stroke, fill) in base a penna e pennello correnti; imposta i
        colori e lo spessore/tratteggio sul canvas."""
        pen, br = self._pen, self._brush
        stroke = bool(pen is not None and pen.IsOk()
                      and pen.GetStyle() != wx.PENSTYLE_TRANSPARENT)
        fill = bool(br is not None and br.IsOk()
                    and br.GetStyle() != wx.BRUSHSTYLE_TRANSPARENT)
        c, k = self.c, self.k
        if stroke:
            c.setStrokeColorRGB(*self._rgb(pen.GetColour()))
            w = max(0.25, pen.GetWidth() * k)
            c.setLineWidth(w)
            if pen.GetStyle() in (wx.PENSTYLE_DOT, wx.PENSTYLE_SHORT_DASH):
                c.setDash([w, 2 * w])
            else:
                c.setDash([])
        if fill:
            c.setFillColorRGB(*self._rgb(br.GetColour()))
        return stroke, fill

    def _x(self, x):
        return self.ox + x * self.k

    def _y(self, y):
        return self.oy - y * self.k

    def DrawLine(self, x1, y1, x2, y2):
        if self.c is None:
            return
        stroke, _fill = self._style()
        if stroke:
            self.c.line(self._x(x1), self._y(y1), self._x(x2), self._y(y2))

    def DrawRectangle(self, x, y, w, h):
        if self.c is None:
            return
        stroke, fill = self._style()
        if stroke or fill:
            self.c.rect(self._x(x), self._y(y + h), w * self.k, h * self.k,
                        stroke=int(stroke), fill=int(fill))

    def DrawCircle(self, x, y, r):
        if self.c is None:
            return
        stroke, fill = self._style()
        if stroke or fill:
            self.c.circle(self._x(x), self._y(y), r * self.k,
                          stroke=int(stroke), fill=int(fill))

    def DrawPolygon(self, points, *args, **kwargs):
        if self.c is None or not points:
            return
        stroke, fill = self._style()
        if not (stroke or fill):
            return
        path = self.c.beginPath()
        for i, pt in enumerate(points):
            px, py = self._x(pt[0]), self._y(pt[1])
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        path.close()
        self.c.drawPath(path, stroke=int(stroke), fill=int(fill))

    def DrawText(self, text, x, y):
        if self.c is None or not text:
            return
        _w, h, desc, _lead = self._mdc.GetFullTextExtent(text)
        baseline = y + (h - desc)      # (x, y) = angolo alto-sinistro del testo
        self.c.setFillColorRGB(*self._rgb(self._tcol))
        self.c.setFont(_rl_font_name(self._font), self._size_px() * self.k)
        self.c.drawString(self._x(x), self._y(baseline), self._clean(text))


def _call_or_none(obj, name):
    f = getattr(obj, name, None)
    try:
        return f() if callable(f) else None
    except Exception:
        return None


def _prepare_vector_sections(frame_obj, info, content_w_logical):
    """Prepara le sezioni vettoriali (tastiere, diagrammi chitarra) di una
    pagina. Restituisce una lista di (disegna, altezza, larghezza) in pixel
    logici, dove disegna(dc, x, y) disegna la sezione su un _VectorDC (o sul DC
    di misura). La larghezza e' quella realmente occupata (0 se non nota)."""
    from .KlavierRenderer import draw_klavier_section
    from .GuitarDiagramRenderer import draw_guitar_diagram_section

    font = info.get('font')
    klavier = info.get('klavier') or []
    define = info.get('define') or []
    if font is None or not (klavier or define):
        return []
    notations = getattr(frame_obj.pref, 'notations', None)
    hl = _call_or_none(frame_obj, '_getKlavierHighlightColour')
    fingers = _call_or_none(frame_obj, '_getFingerNumColour')

    sections = []
    measure = _VectorDC(None)
    if klavier:
        def draw_klavier(dc, x, y):
            return draw_klavier_section(
                dc, klavier, x, y, font, 1.0, notations, hl,
                finger_num_color=fingers, content_w=content_w_logical,
                arrow_bitmap=False)          # frecce vettoriali
        _kh, _kw = draw_klavier(measure, 0, 0)
        sections.append((draw_klavier, _kh, _kw))
    if define:
        def draw_guitar(dc, x, y):
            return draw_guitar_diagram_section(dc, define, x, y, font, 1.0, hl)
        sections.append((draw_guitar, draw_guitar(measure, 0, 0), 0))
    return sections


# ------------------------------------------------------------------ #
#  Testo del brano VETTORIALE                                         #
# ------------------------------------------------------------------ #
#
# SongDecorator disegna il brano su un wx.DC. Per averlo come testo vero nel
# PDF si fa girare lo STESSO decorator, con la stessa scala e le stesse misure
# di prima, su _SongDC: un DC "registratore" che le misure (GetTextExtent...)
# le fa chiedere a un vero wx.MemoryDC (cosi' le posizioni di accordi e sillabe
# restano identiche al bitmap) e invece di colorare pixel traduce le chiamate
# di disegno in operazioni reportlab. I font vengono cercati sul sistema e
# incorporati nel PDF (TrueType); se qualcosa non si puo' rendere in vettoriale
# si solleva _VectorUnsupported e l'esportazione usa il bitmap.

class _VectorUnsupported(Exception):
    """Il brano usa qualcosa che il disegno vettoriale non sa rendere."""


_FONT_CACHE = {}      # (faccia, grassetto, corsivo) -> (nome reportlab, TTFont)


def _font_bold_italic(font):
    try:
        bold = font.GetNumericWeight() >= 600
    except Exception:
        bold = font.GetWeight() == wx.FONTWEIGHT_BOLD
    italic = font.GetStyle() in (wx.FONTSTYLE_ITALIC, wx.FONTSTYLE_SLANT)
    return bool(bold), bool(italic)


def _find_font_windows(face, bold, italic):
    """(percorso, indice) del file del font cercando nel registro di Windows."""
    try:
        import winreg
    except ImportError:
        return None
    want = face.strip().lower()
    if bold and italic:
        sfx = (' bold italic', ' bold oblique')
    elif bold:
        sfx = (' bold',)
    elif italic:
        sfx = (' italic', ' oblique')
    else:
        sfx = ('', ' regular')
    wanted = set(want + s for s in sfx)
    sub = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
    sysdir = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
    userdir = os.path.join(os.environ.get('LOCALAPPDATA', ''),
                           'Microsoft', 'Windows', 'Fonts')
    for hive, base in ((winreg.HKEY_LOCAL_MACHINE, sysdir),
                       (winreg.HKEY_CURRENT_USER, userdir)):
        try:
            key = winreg.OpenKey(hive, sub)
        except OSError:
            continue
        with key:
            i = 0
            while True:
                try:
                    name, value, _t = winreg.EnumValue(key, i)
                except OSError:
                    break
                i += 1
                # "Arial Bold (TrueType)"; i .ttc: "Cambria & Cambria Math (TrueType)"
                label = name.rsplit(' (', 1)[0].strip().lower()
                for idx, part in enumerate(label.split(' & ')):
                    if part.strip() not in wanted:
                        continue
                    path = value if os.path.isabs(value) else os.path.join(base, value)
                    if path.lower().endswith(('.ttf', '.ttc')) and os.path.isfile(path):
                        return path, idx
    return None


# Font "liberi" con le STESSE metriche di quelli proprietari: su Linux fontconfig
# risponde con questi quando si chiede Arial, Times New Roman, ecc. Anche lo
# schermo (pango) e la misura del layout usano lo stesso sostituto, quindi nel
# PDF sono interscambiabili. Chiave: nome richiesto; valore: famiglie accettate.
_METRIC_ALIASES = {
    'arial':           ('liberation sans', 'arimo', 'nimbus sans', 'helvetica'),
    'helvetica':       ('liberation sans', 'arimo', 'nimbus sans'),
    'times new roman': ('liberation serif', 'tinos', 'nimbus roman'),
    'times':           ('liberation serif', 'tinos', 'nimbus roman'),
    'courier new':     ('liberation mono', 'cousine', 'nimbus mono ps',
                        'nimbus mono'),
    'courier':         ('liberation mono', 'cousine', 'nimbus mono ps',
                        'nimbus mono'),
    'calibri':         ('carlito',),
    'cambria':         ('caladea',),
    'georgia':         ('gelasio',),
}


def _fc_match(pattern):
    """(percorso, [famiglie minuscole], indice) di `fc-match pattern`, o None."""
    import shutil
    if not shutil.which('fc-match'):
        return None
    try:
        out = subprocess.run(
            ['fc-match', '-f', '%{file}\t%{family}\t%{index}', pattern],
            capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return None
    parts = out.split('\t')
    if len(parts) < 3:
        return None
    return (parts[0], [f.strip().lower() for f in parts[1].split(',')],
            parts[2].strip())


def _ttf_result(path, idx):
    """(percorso, indice) se `path` e' un TrueType leggibile da reportlab."""
    if not path or not path.lower().endswith(('.ttf', '.ttc')):
        return None
    if not os.path.isfile(path):
        return None
    try:
        return path, int(idx) & 0xFFFF
    except ValueError:
        return path, 0


def _find_font_fontconfig(face, bold, italic):
    """(percorso, indice) tramite fontconfig (Linux e, se c'e', macOS)."""
    style = (':bold' if bold else '') + (':italic' if italic else '')
    want = face.strip().lower()

    # 1) Il font che fontconfig sceglie per `face`. Su Linux e' lo STESSO che
    #    usa pango per misurare il brano, quindi (se e' un TrueType) si accetta
    #    anche un sostituto (Arial -> Liberation Sans, ecc.): le metriche
    #    coincidono con quelle del layout.
    m = _fc_match(face + style)
    if m is not None:
        path, fams, idx = m
        same = want in fams or any(
            f in _METRIC_ALIASES.get(want, ()) for f in fams)
        if same or sys.platform.startswith('linux'):
            r = _ttf_result(path, idx)
            if r:
                return r

    # 2) Il primo risultato non e' utilizzabile (tipicamente Nimbus Sans in
    #    formato .otf/.pfb, che reportlab non legge): si prova ogni sostituto
    #    con le stesse metriche (Liberation Sans, Arimo...), accettandolo solo
    #    se fontconfig risponde proprio con quella famiglia.
    for alias in _METRIC_ALIASES.get(want, ()):
        m = _fc_match(alias + style)
        if m is not None and alias in m[1]:
            r = _ttf_result(m[0], m[2])
            if r:
                return r
    return None


# File dei font "liberi" metrici: stem in ordine Regular, Bold, Italic, BoldItalic
_LINUX_FONT_FILES = {
    'liberation sans': ('LiberationSans-Regular', 'LiberationSans-Bold',
                        'LiberationSans-Italic', 'LiberationSans-BoldItalic'),
    'arimo':           ('Arimo-Regular', 'Arimo-Bold',
                        'Arimo-Italic', 'Arimo-BoldItalic'),
    'liberation serif': ('LiberationSerif-Regular', 'LiberationSerif-Bold',
                         'LiberationSerif-Italic', 'LiberationSerif-BoldItalic'),
    'tinos':           ('Tinos-Regular', 'Tinos-Bold',
                        'Tinos-Italic', 'Tinos-BoldItalic'),
    'liberation mono': ('LiberationMono-Regular', 'LiberationMono-Bold',
                        'LiberationMono-Italic', 'LiberationMono-BoldItalic'),
    'cousine':         ('Cousine-Regular', 'Cousine-Bold',
                        'Cousine-Italic', 'Cousine-BoldItalic'),
}


def _find_font_linux_files(face, bold, italic):
    """(percorso, 0) cercando a mano i file dei sostituti metrici (Liberation,
    Arimo...) nelle cartelle dei font di Linux. Ripiego quando fontconfig non
    e' disponibile o risponde con un formato che reportlab non legge."""
    if not sys.platform.startswith('linux'):
        return None
    want = face.strip().lower()
    families = [want] + list(_METRIC_ALIASES.get(want, ()))
    stems = {}
    for fam in families:
        names = _LINUX_FONT_FILES.get(fam)
        if names:
            stems[names[(1 if bold else 0) + (2 if italic else 0)].lower()
                  + '.ttf'] = fam
    if not stems:
        return None
    roots = ('/usr/share/fonts', '/usr/local/share/fonts',
             '/usr/share/X11/fonts',
             os.path.expanduser('~/.fonts'),
             os.path.expanduser('~/.local/share/fonts'))
    for root in roots:
        for dirpath, _dirs, files in os.walk(root):
            for fn in files:
                if fn.lower() in stems:
                    return os.path.join(dirpath, fn), 0
    return None


def _find_font_dirs(face, bold, italic):
    """(percorso, 0) cercando "<Faccia> [Bold] [Italic].ttf" nelle cartelle
    dei font di macOS (ripiego quando manca fontconfig)."""
    style = (' Bold' if bold else '') + (' Italic' if italic else '')
    wanted = (face.strip() + style + '.ttf').lower()
    for d in ('/Library/Fonts', '/System/Library/Fonts/Supplemental',
              '/System/Library/Fonts', os.path.expanduser('~/Library/Fonts')):
        try:
            for fn in os.listdir(d):
                if fn.lower() == wanted:
                    return os.path.join(d, fn), 0
        except OSError:
            continue
    return None


def _get_rl_font(font):
    """(nome_reportlab, TTFont) del wx.Font, registrandolo in reportlab.
    Solleva _VectorUnsupported se il file del font non si trova."""
    face = (font.GetFaceName() or '').strip()
    bold, italic = _font_bold_italic(font)
    key = (face.lower(), bold, italic)
    if key not in _FONT_CACHE:
        result = None
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            found = None
            if face:
                for finder in (_find_font_windows, _find_font_fontconfig,
                               _find_font_linux_files, _find_font_dirs):
                    found = finder(face, bold, italic)
                    if found:
                        break
            if found:
                name = 'SPP%d' % len(_FONT_CACHE)
                tt = TTFont(name, found[0], subfontIndex=found[1])
                pdfmetrics.registerFont(tt)
                result = (name, tt)
        except Exception:
            result = None
        _FONT_CACHE[key] = result
    if _FONT_CACHE[key] is None:
        why = ''
        if sys.platform.startswith('linux'):
            m = _fc_match(face + (':bold' if bold else '') +
                          (':italic' if italic else ''))
            why = ' [fc-match: %s]' % (m[0] if m else 'non disponibile')
        raise _VectorUnsupported('font "%s"%s%s non trovato%s' % (
            face, ' bold' if bold else '', ' italic' if italic else '', why))
    return _FONT_CACHE[key]


def _font_em_px(font, ppi):
    """Corpo del font in pixel DEVICE a scala 1 (come lo disegna il DC)."""
    try:
        h = font.GetPixelSize().GetHeight()
        if h and h > 0:
            return float(h)
    except Exception:
        pass
    return max(1.0, font.GetPointSize() * ppi / 72.0)


def _bitmap_reader(bmp, use_mask=True, crop=None):
    """wx.Bitmap -> ImageReader di reportlab (con trasparenza, se c'e')."""
    from PIL import Image
    from reportlab.lib.utils import ImageReader
    img = bmp.ConvertToImage()
    w, h = img.GetWidth(), img.GetHeight()
    im = Image.frombytes('RGB', (w, h), bytes(img.GetData()))
    if img.HasAlpha():
        im.putalpha(Image.frombytes('L', (w, h), bytes(img.GetAlpha())))
    elif use_mask and img.HasMask():
        key = (img.GetMaskRed(), img.GetMaskGreen(), img.GetMaskBlue())
        alpha = Image.new('L', (w, h), 255)
        alpha.putdata([0 if p == key else 255 for p in im.getdata()])
        im.putalpha(alpha)
    if crop:
        im = im.crop(crop)
    return ImageReader(im)


class _SongDC(object):
    """DC "registratore": misura come un wx.MemoryDC, disegna su reportlab.

    Le coordinate che riceve sono quelle logiche del decorator; qui si
    convertono in pixel DEVICE (x * UserScale) e si emettono sul canvas, che
    l'esportatore ha gia' predisposto con origine in alto a sinistra del brano
    e scala "punti per pixel device". L'asse y del canvas va verso l'alto,
    quindi le y si emettono cambiate di segno. Con canvas=None non emette nulla
    ma controlla comunque font e chiamate: serve per una prova a secco.
    """

    # Metodi di disegno che il decorator non usa e che non si sanno tradurre
    _NO = frozenset(['Blit', 'GradientFillLinear', 'GradientFillConcentric',
                     'FloodFill', 'CrossHair', 'SetClippingRegion',
                     'SetDeviceClippingRegion', 'SetLogicalFunction'])

    def __init__(self, canvas, pt_per_dev):
        self.c = canvas
        self._k = pt_per_dev or 1.0
        self._m = wx.MemoryDC(wx.Bitmap(1, 1))      # solo per misure e font
        try:
            self._ppi = float(self._m.GetPPI()[1]) or 96.0
        except Exception:
            self._ppi = 96.0
        self._sx = self._sy = 1.0
        self._font = None
        self._pen = None
        self._brush = None
        self._tcol = wx.BLACK
        self._tbg = wx.WHITE
        self._bgmode = None
        self.unsupported = None

    # -- stato e misure (inoltrati al DC vero) ----------------------------
    def _fail(self, what):
        self.unsupported = self.unsupported or what
        raise _VectorUnsupported(what)

    def __getattr__(self, name):
        # Solo per cio' che non e' definito qui: GetTextExtent, GetPPI...
        if name.startswith('_'):
            raise AttributeError(name)     # evita ricorsioni prima dell'__init__
        if name.startswith('Draw') or name in self._NO:
            def _no(*_a, **_k):
                self._fail('DC.%s' % name)
            return _no
        return getattr(self._m, name)

    def SetUserScale(self, sx, sy):
        self._sx, self._sy = float(sx), float(sy)
        self._m.SetUserScale(sx, sy)

    def GetUserScale(self):
        return self._sx, self._sy

    def SetFont(self, font):
        if font is not None and font.IsOk():
            self._font = font
            self._m.SetFont(font)

    def GetFont(self):
        return self._font if self._font is not None else self._m.GetFont()

    def SetPen(self, pen):
        self._pen = pen

    def SetBrush(self, brush):
        self._brush = brush

    @staticmethod
    def _colour(c):
        """wx.Colour da un colore qualsiasi: il decorator passa anche stringhe
        ("#RRGGBB", nomi) o tuple, che il DC vero accetta."""
        if c is None or hasattr(c, 'Red'):
            return c
        return wx.Colour(c)

    def SetTextForeground(self, colour):
        self._tcol = self._colour(colour)
        self._m.SetTextForeground(self._tcol)

    def GetTextForeground(self):
        return self._tcol

    def SetTextBackground(self, colour):
        self._tbg = self._colour(colour)

    def SetBackgroundMode(self, mode):
        self._bgmode = mode

    def SetBackground(self, brush):
        pass

    def Clear(self):
        pass        # la pagina PDF e' gia' bianca

    # -- primitive --------------------------------------------------------
    @staticmethod
    def _rgb(col):
        if not hasattr(col, 'Red'):          # stringa "#RRGGBB", nome, tupla
            col = wx.Colour(col)
        return col.Red() / 255.0, col.Green() / 255.0, col.Blue() / 255.0

    def _style(self):
        """(stroke, fill) secondo penna e pennello correnti; imposta colori,
        spessore, tratteggio e terminali sul canvas."""
        pen, br = self._pen, self._brush
        stroke = bool(pen is not None and pen.IsOk()
                      and pen.GetStyle() != wx.PENSTYLE_TRANSPARENT)
        fill = bool(br is not None and br.IsOk()
                    and br.GetStyle() != wx.BRUSHSTYLE_TRANSPARENT)
        c = self.c
        if stroke:
            c.setStrokeColorRGB(*self._rgb(pen.GetColour()))
            w = max(0.25 / self._k, pen.GetWidth() * self._sx)
            c.setLineWidth(w)
            st = pen.GetStyle()
            if st in (wx.PENSTYLE_DOT, wx.PENSTYLE_SHORT_DASH):
                c.setDash([w, 2 * w])
            elif st in (getattr(wx, 'PENSTYLE_LONG_DASH', None),
                        getattr(wx, 'PENSTYLE_DOT_DASH', None)):
                c.setDash([4 * w, 2 * w])
            else:
                c.setDash([])
            try:
                c.setLineCap({wx.CAP_BUTT: 0, wx.CAP_ROUND: 1,
                              wx.CAP_PROJECTING: 2}.get(pen.GetCap(), 1))
                c.setLineJoin({wx.JOIN_MITER: 0, wx.JOIN_ROUND: 1,
                               wx.JOIN_BEVEL: 2}.get(pen.GetJoin(), 1))
            except Exception:
                pass
        if fill:
            c.setFillColorRGB(*self._rgb(br.GetColour()))
        return stroke, fill

    def _pt(self, x, y):
        return x * self._sx, -(y * self._sy)

    @staticmethod
    def _xy(args):
        """(x, y) da DrawX(x, y, ...) o DrawX(wx.Point, ...)"""
        if hasattr(args[0], 'x'):
            return args[0].x, args[0].y, args[1:]
        return args[0], args[1], args[2:]

    def DrawLine(self, x1, y1, x2, y2):
        if self.c is None:
            return
        stroke, _fill = self._style()
        if stroke:
            ax, ay = self._pt(x1, y1)
            bx, by = self._pt(x2, y2)
            self.c.line(ax, ay, bx, by)

    def DrawRectangle(self, *args):
        if self.c is None:
            return
        if len(args) == 1:                      # wx.Rect
            r = args[0]
            x, y, w, h = r.x, r.y, r.width, r.height
        else:
            x, y, w, h = args[:4]
        stroke, fill = self._style()
        if stroke or fill:
            px, py = self._pt(x, y + h)
            self.c.rect(px, py, w * self._sx, h * self._sy,
                        stroke=int(stroke), fill=int(fill))

    def DrawCircle(self, *args):
        if self.c is None:
            return
        x, y, rest = self._xy(args)
        stroke, fill = self._style()
        if stroke or fill:
            px, py = self._pt(x, y)
            self.c.circle(px, py, rest[0] * self._sx,
                          stroke=int(stroke), fill=int(fill))

    def DrawPolygon(self, points, xoffset=0, yoffset=0, *args, **kwargs):
        if self.c is None or not points:
            return
        stroke, fill = self._style()
        if not (stroke or fill):
            return
        path = self.c.beginPath()
        for i, pt in enumerate(points):
            px, py = self._pt(pt[0] + xoffset, pt[1] + yoffset)
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        path.close()
        self.c.drawPath(path, stroke=int(stroke), fill=int(fill))

    def _place_image(self, reader, x, y, w, h):
        """Immagine con angolo alto-sinistro in (x, y) logici, grande w x h
        logici."""
        px, py = self._pt(x, y + h)
        self.c.drawImage(reader, px, py, width=w * self._sx, height=h * self._sy,
                         mask='auto')

    def DrawBitmap(self, bmp, *args):
        x, y, rest = self._xy(args)
        use_mask = bool(rest[0]) if rest else False
        # La conversione si fa anche nella prova a secco (canvas None), cosi'
        # un problema con le bitmap emerge prima di scrivere sulla pagina.
        try:
            reader = _bitmap_reader(bmp, use_mask)
        except Exception as e:
            self._fail('bitmap: %s' % e)
        if self.c is None:
            return
        # la bitmap occupa i suoi pixel in unita' logiche (il DC la scala)
        self._place_image(reader, x, y, bmp.GetWidth(), bmp.GetHeight())

    def StretchBlit(self, xdest, ydest, dstWidth, dstHeight, source,
                    xsrc, ysrc, srcWidth, srcHeight, *args, **kwargs):
        """Usato dal decorator per i simboli Unicode oltre il piano base:
        `source` e' un wx.MemoryDC con la bitmap del glifo."""
        try:
            sel = source.GetSelectedBitmap()
            if sel is None or not sel.IsOk():
                raise ValueError('nessuna bitmap selezionata')
            # GetSelectedBitmap() restituisce il membro del DC, che SelectObject
            # (NullBitmap) svuota: se ne tiene una copia (condivide i pixel).
            # Una bitmap selezionata in un DC non si puo' convertire, quindi la
            # si libera il tempo della conversione e poi la si rimette (il
            # decorator la deseleziona comunque subito dopo).
            keep = wx.Bitmap(sel)
            source.SelectObject(wx.NullBitmap)
            try:
                reader = _bitmap_reader(
                    keep, False,
                    (xsrc, ysrc, xsrc + srcWidth, ysrc + srcHeight))
            finally:
                source.SelectObject(keep)
        except Exception as e:
            self._fail('StretchBlit: %s' % e)
        if self.c is None:
            return
        self._place_image(reader, xdest, ydest, dstWidth, dstHeight)

    def DrawText(self, text, x, y):
        """(x, y) e' l'angolo alto-sinistro del testo; la riga di base si
        ricava dalle metriche misurate dal DC vero."""
        if not text:
            return
        font = self.GetFont()
        name, tt = _get_rl_font(font)
        cmap = tt.face.charToGlyph
        # Spazi e caratteri invisibili assenti nel font (tabulazioni, spazi
        # tipografici, zero-width...): GDI non disegna nulla, mentre reportlab
        # disegnerebbe il quadratino .notdef. Gli spazi diventano spazi
        # normali (la larghezza totale e' poi riallineata a quella misurata),
        # gli invisibili spariscono; qualunque altro carattere mancante
        # obbliga al ripiego sul bitmap.
        import unicodedata
        drawn = []
        for ch in text:
            if ord(ch) in cmap:
                drawn.append(ch)
            elif ch.isspace():
                drawn.append(' ')
            elif unicodedata.category(ch) in ('Cf', 'Cc'):
                continue
            else:
                self._fail('carattere U+%04X assente nel font' % ord(ch))
        if self.c is None:
            return
        shown = ''.join(drawn)
        from reportlab.pdfbase.pdfmetrics import stringWidth
        w_log, h_log, desc_log, _lead = self._m.GetFullTextExtent(text)
        sx, sy = self._sx, self._sy
        em = _font_em_px(font, self._ppi) * sy
        x_dev = x * sx
        base = -((y + h_log - desc_log) * sy)           # riga di base (y su)
        target = w_log * sx                            # larghezza misurata
        rgb = self._rgb(self._tcol)

        # sfondo del testo (solo se non e' il bianco della pagina)
        if (self._bgmode == wx.SOLID and self._tbg is not None
                and self._tbg.IsOk()
                and (self._tbg.Red(), self._tbg.Green(), self._tbg.Blue())
                != (255, 255, 255)):
            self.c.setFillColorRGB(*self._rgb(self._tbg))
            self.c.rect(x_dev, -((y + h_log) * sy), target, h_log * sy,
                        stroke=0, fill=1)

        t = self.c.beginText()
        t.setFont(name, em)
        t.setFillColorRGB(*rgb)
        n = len(shown)
        if n > 1 and target > 0:
            # GDI e reportlab possono arrotondare diversamente le larghezze dei
            # singoli glifi: si distribuisce la differenza cosi' che ogni run
            # finisca esattamente dove l'ha misurato il layout (gli accordi
            # restano sopra la sillaba giusta).
            cs = (target - stringWidth(shown, name, em)) / (n - 1)
            lim = 0.3 * em
            t.setCharSpace(max(-lim, min(lim, cs)))
        t.setTextOrigin(x_dev, base)
        t.textOut(shown)
        self.c.drawText(t)

        try:
            underlined = font.GetUnderlined()
        except Exception:
            underlined = False
        if underlined:
            self.c.setStrokeColorRGB(*rgb)
            self.c.setLineWidth(max(0.25 / self._k, em * 0.06))
            self.c.setDash([])
            uy = base - em * 0.12
            self.c.line(x_dev, uy, x_dev + target, uy)


def _make_decorator(frame_obj):
    """Crea un decorator fresco per ogni pass di rendering."""
    from .SongDecorator import SongDecorator
    if frame_obj.pref.labelVerses:
        # Crea una copia indipendente del decorator per non alterare lo stato globale
        import copy
        return copy.copy(frame_obj.pref.decorator)
    return SongDecorator()


def _measure_segment(frame_obj, seg_text, scale, avail_w_px, info=None):
    """
    Misura un segmento di testo: ritorna (sw, sh, fit_scale), cioe' le
    dimensioni naturali in pixel logici e la scala (pixel device per pixel
    logico) che lo fa stare nella larghezza disponibile.

    Se `info` e' un dict, lo riempie con i dati per il disegno vettoriale di
    tastiere e diagrammi (non inclusi nel brano): 'sw' (larghezza naturale in
    pixel logici), 'klavier' e 'define' (direttive del segmento), 'font'.
    """
    from .Renderer import Renderer

    dec_measure = _make_decorator(frame_obj)
    dec_measure.showKlavier = False
    r = Renderer(frame_obj.pref.format, dec_measure, frame_obj.pref.notations)

    mdc = wx.MemoryDC(wx.Bitmap(1, 1))
    sw, sh = r.Render(seg_text, mdc)
    sw, sh = max(1, sw), max(1, sh)
    if info is not None:
        info['sw'] = sw
        info['klavier'] = list(getattr(r.song, 'klavier_list', None) or [])
        info['define'] = list(getattr(r.song, 'define_list', None) or [])
        info['font'] = r.song.format.wxFont

    # Scala per adattare alla larghezza disponibile (in pixel a 96 dpi)
    fit_scale = scale
    natural_w = sw * scale
    if natural_w > avail_w_px:
        fit_scale = scale * (avail_w_px / natural_w)
    return sw, sh, fit_scale


def _render_segment_to_png(frame_obj, seg_text, scale, avail_w_px, avail_h_px,
                           info=None):
    """
    Renderizza un segmento di testo in un wx.Bitmap temporaneo.
    Ritorna il Bitmap (dimensioni naturali * scale, ma limitato all'area disponibile).
    Vedi _measure_segment per `info`.
    """
    from .Renderer import Renderer

    sw, sh, fit_scale = _measure_segment(frame_obj, seg_text, scale,
                                         avail_w_px, info)
    bmp_w = int(sw * fit_scale)
    bmp_h = int(sh * fit_scale)
    bmp = wx.Bitmap(max(1, bmp_w), max(1, bmp_h))
    dc = wx.MemoryDC(bmp)
    dc.SetUserScale(fit_scale, fit_scale)
    dc.SetBackground(wx.WHITE_BRUSH)
    dc.Clear()
    # Filigrana DIETRO al contenuto (path PDF Windows/reportlab): la disegniamo
    # prima del brano, cosi' non lo oscura. Sul path Linux/macOS la filigrana la
    # disegna gia' SongpressPrintout. La disegniamo a scala 1:1 sul bitmap, poi
    # ripristiniamo la scala di fit per renderizzare il brano sopra.
    if getattr(frame_obj.pref, 'watermarkEnabled', False):
        try:
            from . import Watermark
            dc.SetUserScale(1.0, 1.0)
            Watermark.draw_watermark(
                dc, bmp.GetWidth(), bmp.GetHeight(),
                frame_obj._GetWatermarkConfig())
        except Exception:
            pass
        dc.SetUserScale(fit_scale, fit_scale)
    dec_draw = _make_decorator(frame_obj)
    dec_draw.showKlavier = False
    r2 = Renderer(frame_obj.pref.format, dec_draw, frame_obj.pref.notations)
    r2.Render(seg_text, dc)
    del dc
    return bmp


def _draw_segment_vector(frame_obj, seg_text, fit_scale, canvas, pt_per_dev):
    """
    Disegna un segmento come testo vettoriale su `canvas` (gia' trasformato:
    origine in alto a sinistra del brano, scala `pt_per_dev` punti per pixel
    device). Con canvas=None fa solo una prova a secco, senza disegnare.
    Solleva _VectorUnsupported se il brano non si puo' rendere cosi'.
    """
    from .Renderer import Renderer

    dec = _make_decorator(frame_obj)
    dec.showKlavier = False
    dec.smp_via_bitmap = True    # simboli oltre il piano base: via bitmap
    r = Renderer(frame_obj.pref.format, dec, frame_obj.pref.notations)
    dc = _SongDC(canvas, pt_per_dev)
    dc.SetUserScale(fit_scale, fit_scale)
    r.Render(seg_text, dc)
    # il decorator inghiotte alcune eccezioni: se una chiamata non supportata
    # e' stata intercettata, lo si sa da qui
    if dc.unsupported:
        raise _VectorUnsupported(dc.unsupported)


def _vector_text_possible(frame_obj):
    """False se il testo del brano va comunque rasterizzato."""
    if not PDF_VECTOR_TEXT:
        return False
    # la filigrana si disegna solo sul bitmap
    return not getattr(frame_obj.pref, 'watermarkEnabled', False)


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
        return False

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
            info = {}
            sw, sh, fit_scale = _measure_segment(
                frame_obj, seg_text, SCALE, avail_w_px, info
            )
            # Dimensioni del brano in "pixel device" (come l'ex bitmap)
            bmp_w = max(1, int(sw * fit_scale))
            bmp_h = max(1, int(sh * fit_scale))

            # Dimensioni in punti (SCALE * 96 dpi → 72 pt)
            px_to_pt = 72.0 / (SCALE * 96.0)
            draw_w = bmp_w * px_to_pt
            draw_h = bmp_h * px_to_pt

            # Tastiere e diagrammi chitarra: vettoriali, in fondo alla pagina.
            # Si riserva sotto al brano lo spazio che occupano a scala naturale.
            sections = _prepare_vector_sections(
                frame_obj, info, avail_w_pt / _PX_TO_PT)
            gap_l = 10   # pixel logici tra una sezione e la successiva
            reserve_pt = sum((h_l + gap_l) * _PX_TO_PT for _d, h_l, _w in sections)

            # Adatta all'area disponibile mantenendo le proporzioni
            song_h_pt = max(1.0, avail_h_pt - reserve_pt)
            scale_fit = min(avail_w_pt / draw_w, song_h_pt / draw_h, 1.0)
            final_w = draw_w * scale_fit
            final_h = draw_h * scale_fit

            # Allineamento orizzontale. Brano, tastiere e diagrammi formano un
            # unico blocco con lo stesso bordo sinistro. Le sezioni vettoriali
            # vanno a capo sull'intera larghezza utile, quindi il blocco e'
            # largo quanto il piu' largo tra brano e sezioni (mai oltre l'area
            # utile): sia a sinistra sia centrato, nulla esce dal bordo destro.
            #   - a sinistra (default): il blocco parte dal margine sinistro;
            #   - al centro (_print_h_center): il blocco intero e' centrato.
            k_sec = final_w / float(info.get('sw') or 1)
            sec_w = max([w_l for _d, _h, w_l in sections] or [0]) * k_sec
            block_w = min(avail_w_pt, max(final_w, sec_w))
            if getattr(frame_obj, '_print_h_center', False):
                x = ml + (avail_w_pt - block_w) / 2.0
            else:
                x = ml
            y = mb + avail_h_pt - final_h  # reportlab: y=0 è in basso

            # Testo vettoriale se possibile, con una prova a secco prima di
            # toccare la pagina (non si puo' annullare cio' che e' disegnato)
            pt_per_dev = final_w / float(bmp_w)
            vector = _vector_text_possible(frame_obj)
            if vector:
                try:
                    _draw_segment_vector(frame_obj, seg_text, fit_scale,
                                         None, pt_per_dev)
                except Exception as e:
                    vector = False
                    sys.stderr.write(
                        'Songpress PDF: testo come bitmap (%s)\n' % e)

            if seg_idx > 0:
                c.showPage()

            if vector:
                c.saveState()
                c.translate(x, y + final_h)      # angolo alto-sinistro del brano
                c.scale(pt_per_dev, pt_per_dev)  # pixel device -> punti
                try:
                    _draw_segment_vector(frame_obj, seg_text, fit_scale,
                                         c, pt_per_dev)
                finally:
                    c.restoreState()
            else:
                bmp = _render_segment_to_png(
                    frame_obj, seg_text, SCALE, avail_w_px, avail_h_px
                )
                img = bmp.ConvertToImage()

                tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                tmp.close()
                img.SaveFile(tmp.name, wx.BITMAP_TYPE_PNG)
                tmp_files.append(tmp.name)
                c.drawImage(tmp.name, x, y, width=final_w, height=final_h)

            # Sezioni vettoriali, con la stessa scala del brano (punti per
            # pixel logico), con lo stesso bordo sinistro del brano (x) e
            # ancorate al margine inferiore.
            if sections:
                k = final_w / float(info.get('sw') or 1)
                top = mb + sum((h_l + gap_l) * k for _d, h_l, _w in sections)
                for draw, h_l, _w in sections:
                    draw(_VectorDC(c, x, top, k), 0, 0)
                    top -= (h_l + gap_l) * k

        c.save()
        return True
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
        h_center=getattr(frame_obj, '_print_h_center', False),
    )

    ok = printer.Print(frame_obj.frame, printout, False)
    printout.Destroy()

    # Su wxGTK printer.Print() puo' restituire True senza aver scritto nulla:
    # non fidarsi del solo valore di ritorno, controllare il file reale.
    created = os.path.isfile(filepath) and os.path.getsize(filepath) > 0

    if ok and created:
        return True
    else:
        wx.MessageBox(
            "Impossibile creare il PDF con il sistema di stampa nativo.\n\n"
            "Su Linux/macOS l'esportazione PDF richiede la libreria "
            "'reportlab':\n    pip install reportlab",
            "Errore esportazione PDF",
            wx.OK | wx.ICON_ERROR,
            frame_obj.frame,
        )
        return False
