#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################
# Name:        CreaIndice.py
# Author:      Denisov21
# Created:     2026
# Copyright:   © 2026 Denisov21
# License:     GNU GPL v2
###############################################################

"""
CreaIndice.py — Create an index (table of contents) PDF for Songpress++
=======================================================================

Scans a folder (and its subfolders) of ChordPro files and, for each file,
reads:

    {subtitle: Canto numero:  22}   -> song number (22)
    {title:    AAAA}   -> title

then produces a PDF with two columns — song number and title —
SORTED by song number.

It can be used in two ways:

  1) Stand-alone (double click or `python3 CreaIndice.py`): opens a window
     with folder selection, a radio-button extension chooser and
     "Generate DOCX" / "Generate PDF" buttons.

  2) From inside Songpress++: File menu -> "Create Index PDF...".
     See `showCreateIndexDialog(parent)` at the bottom of this file.

User-facing strings go through gettext (`_`), so they are English in the
source and translated via the companion catalog (CreaIndice.po / .mo).

Dependencies:  wxPython, reportlab   (pip install wxpython reportlab)
"""

import os
import re
import sys

import wx

# Same translation hook used across Songpress++ (see SongpressFrame.py).
_ = wx.GetTranslation

# On GTK (Linux) the up/down (+/-) buttons of wx.SpinCtrl take more room,
# so a narrow field clips the "+". Give the spin controls extra width there.
_SPIN_W = 96 if sys.platform.startswith('linux') else 70


# ---------------------------------------------------------------------------
#  PERSISTENT SETTINGS  (remember last folder, "open after" preference)
# ---------------------------------------------------------------------------

# Stored via wx.Config, which uses the registry on Windows and a plain file
# (~/.config) on Linux, so the last-used folder survives across launches.
def _config():
    return wx.Config(u"CreaIndice", u"Songpress++")


def _load_last_folder():
    """Return the last folder used, if it still exists on disk, else ''."""
    folder = _config().Read(u"last_folder", u"")
    return folder if folder and os.path.isdir(folder) else u""


def _save_last_folder(folder):
    """Persist the last folder used (only if it is a valid directory)."""
    if folder and os.path.isdir(folder):
        cfg = _config()
        cfg.Write(u"last_folder", folder)
        cfg.Flush()


def _load_open_after(default=True):
    return _config().ReadBool(u"open_after", default)


def _save_open_after(value):
    cfg = _config()
    cfg.WriteBool(u"open_after", bool(value))
    cfg.Flush()


# Watermark spin values (opacity %, angle °, size %). Remembered in the same
# private CreaIndice config as the folder / "open after" preferences, so the
# last-used watermark settings are restored on the next launch.
_WM_DEFAULTS = {u"wm_opacity": 15, u"wm_angle": 45, u"wm_size": 60}


def _load_wm_value(key):
    """Return the stored watermark spin value for `key`, or its default."""
    return _config().ReadInt(key, _WM_DEFAULTS[key])


def _load_default_extension():
    """Return the app-wide "default file extension" preference.

    Songpress++ stores it through wx.Config.Get() under /App -> defaultExtension
    (see Preferences.Load/Save). This is the SHARED, global config — not the
    private CreaIndice one used above — so when this dialog is opened from
    inside Songpress++ we read the very same value shown in
    Options -> General -> "Default file extension".

    Falls back to 'crd' (Songpress++'s own default) when the key is unset or
    the global config is not available (e.g. odd stand-alone launches).
    """
    try:
        cfg = wx.Config.Get()
        old = cfg.GetPath()
        try:
            cfg.SetPath(u"/App")
            ext = cfg.Read(u"defaultExtension", u"")
        finally:
            cfg.SetPath(old)
    except Exception:  # noqa: BLE001
        ext = u""
    return ext or u"crd"


def _open_file(path):
    """Open `path` with the operating system's default application.

    Uses wx.LaunchDefaultApplication (cross-platform); falls back to the
    per-OS command if that is unavailable. Returns True on success.
    """
    try:
        if wx.LaunchDefaultApplication(path):
            return True
    except Exception:  # noqa: BLE001
        pass
    try:
        if sys.platform.startswith('win'):
            os.startfile(path)  # noqa: S606  (Windows only)
        elif sys.platform == 'darwin':
            import subprocess
            subprocess.Popen(['open', path])
        else:
            import subprocess
            subprocess.Popen(['xdg-open', path])
        return True
    except Exception:  # noqa: BLE001
        return False

# ---------------------------------------------------------------------------
#  DATA EXTRACTION FROM CHORDPRO FILES
# ---------------------------------------------------------------------------

# {title: ...}  /  {t: ...}
_TITLE_RE = re.compile(r'\{\s*(?:title|t)\s*:\s*(.*?)\s*\}', re.IGNORECASE)
# {subtitle: ...}  /  {st: ...}
_SUBTITLE_RE = re.compile(r'\{\s*(?:subtitle|st)\s*:\s*(.*?)\s*\}', re.IGNORECASE)
# "numero: 22" or "numero 22" inside a subtitle
_NUM_AFTER_WORD_RE = re.compile(r'numero\s*:?\s*(\d+)', re.IGNORECASE)
# first integer found in a string (fallback)
_ANY_INT_RE = re.compile(r'(\d+)')
# the {watermark ...} directive (draft / stamped copies)
_WATERMARK_RE = re.compile(r'\{\s*watermark', re.IGNORECASE)

# extensions treated as binaries and skipped by the "All files" choice
_BINARY_EXTS = ('.pdf', '.png', '.jpg', '.jpeg', '.svg', '.emf')


def _walk_files(folder, recursive):
    """Yield (root, filename) for every *file* under `folder`.

    In non-recursive mode entries that are directories are skipped (unlike a
    bare os.listdir, which would also return subfolder names)."""
    if recursive:
        for root, _dirs, files in os.walk(folder):
            for name in files:
                yield root, name
    else:
        for name in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, name)):
                yield folder, name


def _read_text(path):
    """Read a text file trying several encodings (UTF-8 with/without BOM,
    then latin-1 as a last resort). Always returns a string."""
    for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
            with open(path, 'r', encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    # last resort: raw bytes, replacing invalid characters
    with open(path, 'rb') as f:
        return f.read().decode('latin-1', errors='replace')


def file_contains_watermark(path):
    """Return True if the file contains a `{watermark: ...}` directive.

    Used by the optional filter that excludes songs carrying a watermark
    (draft / stamped copies). Only the directive is matched, so the plain
    word "watermark" in a comment does not trigger the filter. Unreadable
    files are treated as *not* containing it, so they are kept.
    """
    try:
        return bool(_WATERMARK_RE.search(_read_text(path)))
    except OSError:
        return False


def extract_song_info(path):
    """Extract (number, title) from a ChordPro file.

    - number: int if found in a subtitle such as "Canto numero: 22",
              otherwise None.
    - title: the first {title:...} directive; if absent, the file name.
    """
    text = _read_text(path)

    # --- title ---
    m = _TITLE_RE.search(text)
    if m and m.group(1).strip():
        title = m.group(1).strip()
    else:
        title = os.path.splitext(os.path.basename(path))[0]

    # --- song number: searched in ALL subtitles ---
    number = None
    for sm in _SUBTITLE_RE.finditer(text):
        sub = sm.group(1)
        nm = _NUM_AFTER_WORD_RE.search(sub)
        if nm:
            number = int(nm.group(1))
            break
        # if the subtitle contains only a number, use it as well
        am = _ANY_INT_RE.search(sub)
        if am and number is None:
            number = int(am.group(1))
            # do not break: prefer a later "numero: N" match if present

    return number, title


def collect_songs(folder, extension, recursive=True, exclude_watermark=False):
    """Walk the folder and return a sorted list of dicts:
        {'number': int|None, 'title': str, 'path': str}

    `extension` may be:
        - a string with or without a dot ('.cho', 'cho'),
        - '*' or '' to take every file.
    If `exclude_watermark` is True, files that contain the "watermark"
    keyword (e.g. a {watermark: ...} directive) are skipped.
    Sorting is by ascending song number; files without a number go last,
    sorted alphabetically by title.
    """
    ext = extension.strip().lower()
    if ext in ('', '*', '.*', 'all'):
        ext = None
    elif not ext.startswith('.'):
        ext = '.' + ext

    songs = []
    for root, name in _walk_files(folder, recursive):
        if ext is not None and not name.lower().endswith(ext):
            continue
        if ext is None and name.lower().endswith(_BINARY_EXTS):
            continue  # with "all files" skip the obvious binaries
        path = os.path.join(root, name)
        if exclude_watermark and file_contains_watermark(path):
            continue  # skip files carrying a watermark keyword
        number, title = extract_song_info(path)
        songs.append({'number': number, 'title': title, 'path': path})

    # numbered first (by number, then title), then unnumbered (by title)
    songs.sort(key=lambda s: (
        s['number'] is None,
        s['number'] if s['number'] is not None else 0,
        s['title'].lower(),
    ))
    return songs


def count_by_extension(folder, recursive=True, exclude_watermark=False):
    """Count files by extension in `folder`.

    Returns (counts, total) where `counts` maps a lowercased extension
    (e.g. '.cho') to the number of files with it, and `total` is the number
    of files excluding the obvious binaries (the "All files" count).

    Normally only file *names* are read. If `exclude_watermark` is True the
    text files are opened and those containing the "watermark" keyword are
    left out of the counts, so the figures match what the index will hold.
    """
    counts = {}
    total = 0
    for root, name in _walk_files(folder, recursive):
        is_binary = name.lower().endswith(_BINARY_EXTS)
        # the watermark keyword only makes sense in text files, so binaries
        # are never read (and are excluded from `total` anyway)
        if exclude_watermark and not is_binary \
                and file_contains_watermark(os.path.join(root, name)):
            continue
        ext = os.path.splitext(name)[1].lower()
        counts[ext] = counts.get(ext, 0) + 1
        if not is_binary:
            total += 1
    return counts, total


# ---------------------------------------------------------------------------
#  WATERMARK (shared by PDF and DOCX)
# ---------------------------------------------------------------------------

def _make_watermark(path, opacity, angle, grayscale=False):
    """Return (image, orig_w, orig_h) for the background watermark.

    `opacity` (0-100) is baked into the alpha channel and `angle` (degrees)
    is baked in by rotating the image, so both PDF and DOCX can simply place
    the resulting picture behind the text. When `grayscale` is True the image
    is converted to black and white (its transparency is preserved). Raises
    RuntimeError if Pillow is missing.
    """
    try:
        from PIL import Image
    except ImportError as e:
        raise RuntimeError(_(
            u"The 'Pillow' module is not installed.\n\n"
            u"Install it with:\n    pip install Pillow")) from e

    img = Image.open(path).convert('RGBA')
    orig_w, orig_h = img.size
    if grayscale:
        # desaturate the RGB channels but keep the original alpha channel
        r, g, b, a = img.split()
        gray = Image.merge('RGB', (r, g, b)).convert('L')
        img = Image.merge('RGBA', (gray, gray, gray, a))
    opacity = max(0, min(100, int(opacity)))
    if opacity < 100:
        alpha = img.split()[3].point(lambda v: int(v * opacity / 100))
        img.putalpha(alpha)
    if int(angle) % 360:
        img = img.rotate(int(angle), expand=True, resample=Image.BICUBIC)
    return img, orig_w, orig_h


# ---------------------------------------------------------------------------
#  PDF GENERATION
# ---------------------------------------------------------------------------

def build_index_pdf(songs, out_path, heading=None, watermark=None):
    """Create the two-column (number | title) PDF at `out_path`.

    `watermark`, if given, is a dict {'path', 'opacity', 'angle', 'size'}; the
    image is drawn behind the text on every page. Returns (total, with_number).
    Raises RuntimeError if reportlab is not installed.
    """
    if heading is None:
        heading = _(u"Index")
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                        Paragraph, Spacer)
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.utils import ImageReader
    except ImportError as e:
        raise RuntimeError(_(
            u"The 'reportlab' module is not installed.\n\n"
            u"Install it with:\n    pip install reportlab")) from e

    # prepare the watermark once (opacity + rotation baked in)
    wm_img = wm_ow = None
    if watermark and watermark.get('path'):
        wm_img, wm_ow, _oh = _make_watermark(
            watermark['path'], watermark.get('opacity', 100),
            watermark.get('angle', 0), watermark.get('grayscale', False))

    def _draw_watermark(canvas, _doc):
        if wm_img is None:
            return
        pw, ph = A4
        factor = (pw * float(watermark.get('size', 100)) / 100.0) / wm_ow
        dw, dh = wm_img.width * factor, wm_img.height * factor
        canvas.saveState()
        canvas.drawImage(ImageReader(wm_img), (pw - dw) / 2.0, (ph - dh) / 2.0,
                         dw, dh, mask='auto')
        canvas.restoreState()

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('IdxHeading', parent=styles['Title'],
                                 fontName='Helvetica-Bold', fontSize=20,
                                 spaceAfter=10 * mm)
    num_style = ParagraphStyle('IdxNum', parent=styles['Normal'],
                               fontName='Helvetica-Bold', fontSize=11,
                               alignment=TA_LEFT)
    txt_style = ParagraphStyle('IdxTitle', parent=styles['Normal'],
                               fontName='Helvetica', fontSize=11, leading=15,
                               alignment=TA_LEFT)
    head_style = ParagraphStyle('IdxHead', parent=styles['Normal'],
                                fontName='Helvetica-Bold', fontSize=11,
                                textColor=colors.white)

    doc = SimpleDocTemplate(out_path, pagesize=A4,
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            title=heading)

    data = [[Paragraph(_(u"No."), head_style),
             Paragraph(_(u"Title"), head_style)]]
    n_with_number = 0
    for s in songs:
        if s['number'] is not None:
            num_cell = Paragraph(str(s['number']), num_style)
            n_with_number += 1
        else:
            num_cell = Paragraph(u"\u2014", num_style)  # em dash
        data.append([num_cell, Paragraph(_escape(s['title']), txt_style)])

    # usable width ~170mm: narrow number column, title takes the rest
    table = Table(data, colWidths=[18 * mm, 152 * mm], repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#404040')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, 0), 0.75, colors.HexColor('#404040')),
        ('LINEBELOW', (0, 1), (-1, -1), 0.25, colors.HexColor('#cccccc')),
    ]
    if wm_img is None:
        # opaque zebra only without a watermark, so the image can show through
        style.append(('ROWBACKGROUNDS', (0, 1), (-1, -1),
                      [colors.white, colors.HexColor('#f2f2f2')]))
    table.setStyle(TableStyle(style))

    story = [Paragraph(_escape(heading), title_style), table,
             Spacer(1, 6 * mm)]
    doc.build(story, onFirstPage=_draw_watermark, onLaterPages=_draw_watermark)
    return len(songs), n_with_number


def _escape(s):
    """Minimal escaping for reportlab Paragraphs (they use XML-like markup)."""
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def _docx_cell(cell, text, width_mm=None, bold=False, fill=None,
               color=None, align=None):
    """Fill a python-docx table cell: text, width, bold, shading, colour."""
    from docx.shared import Mm, Pt
    from docx.enum.table import WD_ALIGN_VERTICAL
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    if width_mm is not None:
        cell.width = Mm(width_mm)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = cell.paragraphs[0]
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(11)
    if color is not None:
        run.font.color.rgb = color
    if fill:
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:fill'), fill)
        tcPr.append(shd)


def _docx_add_bg_watermark(doc, pil_img, orig_w, size_pct):
    """Place `pil_img` (opacity + rotation already baked in) behind the text,
    in the section header so it repeats on every page, centred on the page and
    sized so the original image width is `size_pct`% of the page width."""
    import tempfile
    from docx.shared import Emu
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    section = doc.sections[0]
    page_w = int(section.page_width)
    page_h = int(section.page_height)

    per_px = (page_w * float(size_pct) / 100.0) / orig_w  # EMU per pixel
    disp_w = int(pil_img.width * per_px)
    disp_h = int(pil_img.height * per_px)
    x = int((page_w - disp_w) / 2)
    y = int((page_h - disp_h) / 2)

    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    tmp.close()
    pil_img.save(tmp.name)

    header = section.header
    header.is_linked_to_previous = False
    para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    run = para.add_run()
    run.add_picture(tmp.name, width=Emu(disp_w), height=Emu(disp_h))

    # turn the inline picture into a floating anchor placed behind the text
    inline = run._r.find(qn('w:drawing')).find(qn('wp:inline'))
    inline.tag = qn('wp:anchor')
    for k, v in (('behindDoc', '1'), ('distT', '0'), ('distB', '0'),
                 ('distL', '0'), ('distR', '0'), ('simplePos', '0'),
                 ('locked', '0'), ('layoutInCell', '1'),
                 ('allowOverlap', '1'), ('relativeHeight', '0')):
        inline.set(k, v)

    def _el(tag, **attrs):
        e = OxmlElement(tag)
        for kk, vv in attrs.items():
            e.set(kk, str(vv))
        return e

    extent = inline.find(qn('wp:extent'))
    simple = _el('wp:simplePos', x='0', y='0')
    posH = _el('wp:positionH', relativeFrom='page')
    offH = _el('wp:posOffset'); offH.text = str(x); posH.append(offH)
    posV = _el('wp:positionV', relativeFrom='page')
    offV = _el('wp:posOffset'); offV.text = str(y); posV.append(offV)
    extent.addprevious(simple)
    extent.addprevious(posH)
    extent.addprevious(posV)

    wrap = _el('wp:wrapNone')
    effect = inline.find(qn('wp:effectExtent'))
    (effect if effect is not None else extent).addnext(wrap)


def build_index_docx(songs, out_path, heading=None, watermark=None):
    """Create the two-column (number | title) Word document at `out_path`.

    `watermark`, if given, is a dict {'path', 'opacity', 'angle', 'size'}; the
    image is placed behind the text on every page. Returns (total, with_number).
    Raises RuntimeError if python-docx is not installed.
    """
    if heading is None:
        heading = _(u"Index")
    try:
        from docx import Document
        from docx.shared import Pt, Mm, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError as e:
        raise RuntimeError(_(
            u"The 'python-docx' module is not installed.\n\n"
            u"Install it with:\n    pip install python-docx")) from e

    doc = Document()
    for section in doc.sections:
        section.top_margin = Mm(18)
        section.bottom_margin = Mm(18)
        section.left_margin = Mm(20)
        section.right_margin = Mm(20)

    # heading — black, bold, centred
    hp = doc.add_paragraph()
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hp.paragraph_format.space_after = Pt(14)
    hr = hp.add_run(heading)
    hr.bold = True
    hr.font.size = Pt(20)

    col_num_mm, col_title_mm = 18, 152
    white = RGBColor(0xFF, 0xFF, 0xFF)
    table = doc.add_table(rows=1, cols=2)
    table.allow_autofit = False

    hdr = table.rows[0].cells
    _docx_cell(hdr[0], _(u"No."), width_mm=col_num_mm, bold=True,
               fill='404040', color=white, align=WD_ALIGN_PARAGRAPH.CENTER)
    _docx_cell(hdr[1], _(u"Title"), width_mm=col_title_mm, bold=True,
               fill='404040', color=white)

    n_with_number = 0
    for i, s in enumerate(songs):
        row = table.add_row().cells
        if s['number'] is not None:
            num = str(s['number'])
            n_with_number += 1
        else:
            num = u"\u2014"  # em dash
        # opaque zebra only without a watermark, so the image can show through
        fill = None if (watermark and watermark.get('path')) \
            else ('F2F2F2' if i % 2 else None)
        _docx_cell(row[0], num, width_mm=col_num_mm, bold=True, fill=fill,
                   align=WD_ALIGN_PARAGRAPH.CENTER)
        _docx_cell(row[1], s['title'], width_mm=col_title_mm, fill=fill)

    if watermark and watermark.get('path'):
        wm_img, wm_ow, _oh = _make_watermark(
            watermark['path'], watermark.get('opacity', 100),
            watermark.get('angle', 0), watermark.get('grayscale', False))
        _docx_add_bg_watermark(doc, wm_img, wm_ow, watermark.get('size', 100))

    doc.save(out_path)
    return len(songs), n_with_number


# ---------------------------------------------------------------------------
#  wxPython PANEL / DIALOG
# ---------------------------------------------------------------------------

# Fixed file extensions offered as radio buttons (NOT translatable: they are
# literal extensions). Two extra choices are added at build time: "All files"
# and "Other…" (which enables a free-text field). Kinds: 'ext' / 'all' / 'other'.
_FIXED_EXTS = ['.cho', '.chopro', '.pro', '.crd', '.txt']


class IndexPanel(wx.Panel):
    """The body of the UI, reusable both in the stand-alone window and in a
    wx.Dialog opened from the Songpress++ menu."""

    def __init__(self, parent, default_folder=None, default_ext=None):
        super().__init__(parent)
        # If the caller passes an explicit preference (e.g. Songpress++ handing
        # over preferences.defaultExtension), use it; otherwise read the shared,
        # app-wide value from Options -> "Default file extension".
        self._default_ext = default_ext if default_ext is not None \
            else _load_default_extension()
        self._build_ui(default_folder)

    def _build_ui(self, default_folder):
        outer = wx.BoxSizer(wx.VERTICAL)

        # --- main folder ---
        box_dir = wx.StaticBoxSizer(wx.VERTICAL, self, _(u"Main folder"))
        row = wx.BoxSizer(wx.HORIZONTAL)
        # when opened without an explicit folder, restore the last one used
        chosen_folder = default_folder or _load_last_folder()
        start_folder = chosen_folder or os.path.expanduser('~')
        self.dirPicker = wx.DirPickerCtrl(
            box_dir.GetStaticBox(),
            path=start_folder,
            message=_(u"Choose the folder with the songs"),
            style=wx.DIRP_USE_TEXTCTRL | wx.DIRP_DIR_MUST_EXIST)
        row.Add(self.dirPicker, 1, wx.EXPAND | wx.ALL, 4)
        box_dir.Add(row, 0, wx.EXPAND)

        self.recursiveCb = wx.CheckBox(box_dir.GetStaticBox(),
                                       label=_(u"Include subfolders"))
        self.recursiveCb.SetValue(True)
        box_dir.Add(self.recursiveCb, 0, wx.ALL, 4)

        # optional filter: leave out files carrying a watermark directive
        self.excludeWmCb = wx.CheckBox(
            box_dir.GetStaticBox(),
            label=_(u"Exclude files with a \u201cwatermark\u201d directive"))
        self.excludeWmCb.SetValue(False)
        box_dir.Add(self.excludeWmCb, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 4)
        outer.Add(box_dir, 0, wx.EXPAND | wx.ALL, 8)

        # --- extension (radio buttons, with per-extension file counts) ---
        box_ext = wx.StaticBoxSizer(wx.VERTICAL, self, _(u"File extension"))
        # A fixed-column grid gives a deterministic size on every platform
        # (unlike wx.WrapSizer, whose reported height is unreliable and left
        # a large empty gap / clipped the controls below it on Windows).
        # 3 columns: the 5 fixed extensions + "All files" fill two rows and
        # "Other…" sits by itself on the last row.
        grid = wx.FlexGridSizer(cols=3, hgap=4, vgap=2)
        # each entry: (radiobutton, kind, value, base_label)
        self.extButtons = []
        self._count_cache = None
        first = True
        for ext in _FIXED_EXTS:
            rb = wx.RadioButton(box_ext.GetStaticBox(), label=ext,
                                style=wx.RB_GROUP if first else 0)
            first = False
            grid.Add(rb, 0, wx.ALL, 6)
            self.extButtons.append((rb, 'ext', ext, ext))
        rb_all = wx.RadioButton(box_ext.GetStaticBox(), label=_(u"All files"))
        grid.Add(rb_all, 0, wx.ALL, 6)
        self.extButtons.append((rb_all, 'all', '*', _(u"All files")))
        rb_other = wx.RadioButton(box_ext.GetStaticBox(), label=_(u"Other\u2026"))
        grid.Add(rb_other, 0, wx.ALL, 6)
        self.extButtons.append((rb_other, 'other', None, _(u"Other\u2026")))

        # free-text field for a custom extension, placed right beside the
        # "Other…" radio (same row of the grid)
        self.customExt = wx.TextCtrl(box_ext.GetStaticBox(), value=".txt",
                                     size=(120, -1))
        self.customExt.Enable(False)
        self.customExt.Bind(wx.EVT_TEXT, self._update_other_count)
        grid.Add(self.customExt, 0,
                 wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        for rb, _kind, _val, _base in self.extButtons:
            rb.Bind(wx.EVT_RADIOBUTTON, self._on_ext_changed)
        # preselect the radio matching the app-wide default extension
        # (Options -> "Default file extension"); '.cho' if nothing matches
        self._preselect_extension(self._default_ext)
        box_ext.Add(grid, 0, wx.EXPAND)

        # recompute the counts when the folder or the recursion option changes
        self.dirPicker.Bind(wx.EVT_DIRPICKER_CHANGED, self._update_counts)
        self.recursiveCb.Bind(wx.EVT_CHECKBOX, self._update_counts)
        # the watermark filter changes which files are counted, too
        self.excludeWmCb.Bind(wx.EVT_CHECKBOX, self._update_counts)

        outer.Add(box_ext, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # --- background watermark (optional) ---
        box_wm = wx.StaticBoxSizer(wx.VERTICAL, self,
                                   _(u"Background watermark (optional)"))
        sb = box_wm.GetStaticBox()
        wrow = wx.BoxSizer(wx.HORIZONTAL)
        wrow.Add(wx.StaticText(sb, label=_(u"Image:")),
                 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 6)
        self.wmPicker = wx.FilePickerCtrl(
            sb, message=_(u"Choose the watermark image"),
            wildcard=_(u"Images (*.png;*.jpg;*.jpeg)|*.png;*.jpg;*.jpeg"),
            style=wx.FLP_USE_TEXTCTRL | wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST)
        wrow.Add(self.wmPicker, 1, wx.EXPAND | wx.RIGHT, 6)
        box_wm.Add(wrow, 0, wx.EXPAND | wx.ALL, 4)

        orow = wx.BoxSizer(wx.HORIZONTAL)
        self.opacityLabel = wx.StaticText(sb, label=_(u"Opacity (%):"))
        orow.Add(self.opacityLabel,
                 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 6)
        self.opacitySpin = wx.SpinCtrl(sb, min=0, max=100,
                                       initial=_load_wm_value(u"wm_opacity"),
                                       size=(_SPIN_W, -1))
        orow.Add(self.opacitySpin, 0, wx.RIGHT, 12)
        self.angleLabel = wx.StaticText(sb, label=_(u"Angle (\u00b0):"))
        orow.Add(self.angleLabel, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.angleSpin = wx.SpinCtrl(sb, min=-180, max=180,
                                     initial=_load_wm_value(u"wm_angle"),
                                     size=(_SPIN_W, -1))
        orow.Add(self.angleSpin, 0, wx.RIGHT, 12)
        self.sizeLabel = wx.StaticText(sb, label=_(u"Size (%):"))
        orow.Add(self.sizeLabel, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.sizeSpin = wx.SpinCtrl(sb, min=1, max=100,
                                    initial=_load_wm_value(u"wm_size"),
                                    size=(_SPIN_W, -1))
        orow.Add(self.sizeSpin, 0, wx.RIGHT, 6)
        box_wm.Add(orow, 0, wx.ALL, 4)

        # colour vs black-and-white rendering of the watermark image
        crow = wx.BoxSizer(wx.HORIZONTAL)
        self.wmRenderLabel = wx.StaticText(sb, label=_(u"Rendering:"))
        crow.Add(self.wmRenderLabel,
                 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 6)
        self.wmColorRb = wx.RadioButton(sb, label=_(u"Colour"),
                                        style=wx.RB_GROUP)
        self.wmGrayRb = wx.RadioButton(sb, label=_(u"Black and white"))
        crow.Add(self.wmColorRb, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        crow.Add(self.wmGrayRb, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        box_wm.Add(crow, 0, wx.ALL, 4)
        # restore the last-used choice
        if _config().ReadBool(u"wm_grayscale", False):
            self.wmGrayRb.SetValue(True)
        else:
            self.wmColorRb.SetValue(True)

        outer.Add(box_wm, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # the watermark settings (opacity/angle/size and the Colour /
        # Black-and-white choice) only make sense when an image is selected:
        # enable them only while the watermark path is non-empty, and keep
        # them in sync whenever the file picker changes.
        self.wmPicker.Bind(wx.EVT_FILEPICKER_CHANGED, self._on_wm_path_changed)
        self._update_wm_controls_enabled()

        # persist the watermark spin values whenever they change (both the
        # arrows and manual typing), so they survive close/reopen — mirroring
        # how the folder and "open after" options are already remembered.
        for _spin in (self.opacitySpin, self.angleSpin, self.sizeSpin):
            _spin.Bind(wx.EVT_SPINCTRL, self._save_wm_values)
            _spin.Bind(wx.EVT_TEXT, self._save_wm_values)
        # the colour / black-and-white choice is remembered the same way
        for _rb in (self.wmColorRb, self.wmGrayRb):
            _rb.Bind(wx.EVT_RADIOBUTTON, self._save_wm_values)

        # --- index title ---
        box_h = wx.BoxSizer(wx.HORIZONTAL)
        box_h.Add(wx.StaticText(self, label=_(u"Index title:")),
                  0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 8)
        self.headingCtrl = wx.TextCtrl(self, value=_(u"Index"))
        box_h.Add(self.headingCtrl, 1, wx.EXPAND | wx.RIGHT, 8)
        outer.Add(box_h, 0, wx.EXPAND | wx.BOTTOM, 8)

        # --- generate buttons + status ---
        btnRow = wx.BoxSizer(wx.HORIZONTAL)
        # open the generated file automatically once it is created
        self.openAfterCb = wx.CheckBox(self, label=_(u"Open the PDF now"))
        self.openAfterCb.SetValue(_load_open_after(True))
        self.openAfterCb.Bind(
            wx.EVT_CHECKBOX,
            lambda evt: _save_open_after(self.openAfterCb.GetValue()))
        btnRow.Add(self.openAfterCb, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
        btnRow.AddStretchSpacer(1)
        self.docxBtn = wx.Button(self, label=_(u"Generate DOCX"))
        self.docxBtn.Bind(wx.EVT_BUTTON, self.on_generate_docx)
        btnRow.Add(self.docxBtn, 0, wx.RIGHT, 6)
        self.pdfBtn = wx.Button(self, label=_(u"Generate PDF"))
        self.pdfBtn.Bind(wx.EVT_BUTTON, self.on_generate_pdf)
        btnRow.Add(self.pdfBtn, 0)
        outer.Add(btnRow, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.status = wx.StaticText(self, label="")
        outer.Add(self.status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.SetSizer(outer)

        # Show the file counts right away when we start on a real folder —
        # whether it was passed explicitly or restored from the last session —
        # instead of waiting for the user to change the folder. The home
        # fallback is left unscanned (it may be huge and was not user-chosen).
        if chosen_folder and os.path.isdir(chosen_folder):
            self._update_counts()

    # -- events -------------------------------------------------------------

    def _on_ext_changed(self, _evt):
        self.customExt.Enable(self.extButtons[-1][0].GetValue())  # "Other…"
        self._update_other_count()

    def _on_wm_path_changed(self, _evt):
        self._update_wm_controls_enabled()

    def _update_wm_controls_enabled(self):
        """Enable the watermark settings (opacity/angle/size and the
        Colour / Black-and-white choice) only when a watermark image is
        selected; grey them out, labels included, otherwise."""
        has_path = bool(self.wmPicker.GetPath().strip())
        for _w in (self.opacityLabel, self.opacitySpin,
                   self.angleLabel, self.angleSpin,
                   self.sizeLabel, self.sizeSpin,
                   self.wmRenderLabel, self.wmColorRb, self.wmGrayRb):
            _w.Enable(has_path)

    def _save_wm_values(self, _evt=None):
        """Persist the three watermark spin values (opacity/angle/size) so they
        are restored the next time the dialog is opened. Written together with
        a single flush."""
        cfg = _config()
        cfg.WriteInt(u"wm_opacity", self.opacitySpin.GetValue())
        cfg.WriteInt(u"wm_angle", self.angleSpin.GetValue())
        cfg.WriteInt(u"wm_size", self.sizeSpin.GetValue())
        cfg.WriteBool(u"wm_grayscale", self.wmGrayRb.GetValue())
        cfg.Flush()

    def _preselect_extension(self, ext):
        """Select the radio button matching `ext` (the app-wide default from
        Options). `ext` may be given with or without a leading dot ('crd' or
        '.crd'):

          - if it matches one of the fixed extensions, that radio is chosen;
          - otherwise the 'Other…' radio is selected and the custom-text field
            is filled with it;
          - if `ext` is empty, the historical default ('.cho') is kept.
        """
        norm = (ext or u"").strip().lower()
        if norm and not norm.startswith(u'.'):
            norm = u'.' + norm

        # 1) try to match one of the fixed-extension radios (.cho, .crd, …)
        if norm:
            for rb, kind, value, _base in self.extButtons:
                if kind == 'ext' and value.lower() == norm:
                    rb.SetValue(True)
                    self.customExt.Enable(False)
                    return

            # 2) not a fixed extension: fall back to "Other…" + custom value
            other_rb = self.extButtons[-1][0]  # the 'Other…' radio
            other_rb.SetValue(True)
            self.customExt.SetValue(norm)
            self.customExt.Enable(True)
            return

        # 3) nothing usable: keep the historical default (.cho)
        self.extButtons[0][0].SetValue(True)

    def _other_label(self, base, counts):
        """Label for the 'Other…' button, with a count if a custom
        extension has been typed."""
        if self.customExt.IsEnabled():
            ext = self.customExt.GetValue().strip().lower()
            if ext:
                if not ext.startswith('.'):
                    ext = '.' + ext
                return u"%s (%d)" % (base, counts.get(ext, 0))
        return base

    def _update_counts(self, _evt=None):
        """Rescan the folder and append the file count to each label."""
        folder = self.dirPicker.GetPath()
        recursive = self.recursiveCb.GetValue()
        if not folder or not os.path.isdir(folder):
            self._count_cache = None
            for rb, kind, value, base in self.extButtons:
                rb.SetLabel(base)
            self.Layout()
            return

        wx.BeginBusyCursor()
        try:
            counts, total = count_by_extension(
                folder, recursive,
                exclude_watermark=self.excludeWmCb.GetValue())
        finally:
            wx.EndBusyCursor()
        self._count_cache = (folder, recursive, counts, total)
        _save_last_folder(folder)  # remember the last folder used

        for rb, kind, value, base in self.extButtons:
            if kind == 'ext':
                rb.SetLabel(u"%s (%d)" % (base, counts.get(value.lower(), 0)))
            elif kind == 'all':
                rb.SetLabel(u"%s (%d)" % (base, total))
            else:  # other
                rb.SetLabel(self._other_label(base, counts))
        self.Layout()

    def _update_other_count(self, _evt=None):
        """Update only the 'Other…' count from the cached scan (used while
        typing a custom extension, to avoid rescanning on every keystroke)."""
        rb, kind, value, base = self.extButtons[-1]
        counts = self._count_cache[2] if self._count_cache else {}
        rb.SetLabel(self._other_label(base, counts))
        self.Layout()

    def _selected_extension(self):
        for rb, kind, value, base in self.extButtons:
            if rb.GetValue():
                if kind == 'all':
                    return '*'
                if kind == 'other':
                    return self.customExt.GetValue().strip() or '*'
                return value
        return '*'

    def on_generate_pdf(self, _evt):
        self._generate('pdf')

    def on_generate_docx(self, _evt):
        self._generate('docx')

    def _generate(self, fmt):
        """Build the index in the given format ('pdf' or 'docx')."""
        if fmt == 'docx':
            builder = build_index_docx
            suffix = '.docx'
            wildcard = _(u"Word files (*.docx)|*.docx")
        else:
            builder = build_index_pdf
            suffix = '.pdf'
            wildcard = _(u"PDF files (*.pdf)|*.pdf")

        folder = self.dirPicker.GetPath()
        if not folder or not os.path.isdir(folder):
            wx.MessageBox(_(u"Please select a valid folder."), _(u"Warning"),
                          wx.OK | wx.ICON_WARNING, self)
            return

        ext = self._selected_extension()
        recursive = self.recursiveCb.GetValue()
        heading = self.headingCtrl.GetValue().strip() or _(u"Index")

        watermark = None
        wm_path = self.wmPicker.GetPath()
        if wm_path and os.path.isfile(wm_path):
            watermark = {'path': wm_path,
                         'opacity': self.opacitySpin.GetValue(),
                         'angle': self.angleSpin.GetValue(),
                         'size': self.sizeSpin.GetValue(),
                         'grayscale': self.wmGrayRb.GetValue()}

        self.status.SetLabel(_(u"Scanning files\u2026"))
        wx.BeginBusyCursor()
        try:
            songs = collect_songs(
                folder, ext, recursive=recursive,
                exclude_watermark=self.excludeWmCb.GetValue())
        finally:
            wx.EndBusyCursor()

        if not songs:
            self.status.SetLabel("")
            wx.MessageBox(
                _(u"No files found with the selected extension."),
                _(u"No results"), wx.OK | wx.ICON_INFORMATION, self)
            return

        # where to save
        default_name = os.path.basename(os.path.normpath(folder)) + "_index" + suffix
        with wx.FileDialog(
                self, _(u"Save the index as\u2026"),
                defaultDir=folder, defaultFile=default_name,
                wildcard=wildcard,
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                self.status.SetLabel("")
                return
            out_path = dlg.GetPath()
        if not out_path.lower().endswith(suffix):
            out_path += suffix

        wx.BeginBusyCursor()
        try:
            total, with_num = builder(songs, out_path, heading=heading,
                                      watermark=watermark)
        except RuntimeError as e:
            wx.EndBusyCursor()
            self.status.SetLabel("")
            wx.MessageBox(str(e), _(u"Error"), wx.OK | wx.ICON_ERROR, self)
            return
        except Exception as e:  # noqa: BLE001
            wx.EndBusyCursor()
            self.status.SetLabel("")
            wx.MessageBox(_(u"Could not create the file:\n%s") % e,
                          _(u"Error"), wx.OK | wx.ICON_ERROR, self)
            return
        wx.EndBusyCursor()

        # the index was created: remember this folder for next time
        _save_last_folder(folder)

        without = total - with_num
        msg = _(u"Created the index with %d songs") % total
        if without:
            msg += _(u" (%d without a number, placed at the end)") % without
        msg += ".\n\n%s" % out_path
        self.status.SetLabel(_(u"Done: %s") % out_path)
        wx.MessageBox(msg, _(u"Index created"),
                      wx.OK | wx.ICON_INFORMATION, self)

        # open the generated file with the default application, if requested
        if self.openAfterCb.GetValue():
            if not _open_file(out_path):
                wx.MessageBox(_(u"Could not open the file automatically:\n%s")
                              % out_path, _(u"Warning"),
                              wx.OK | wx.ICON_WARNING, self)


# ---------------------------------------------------------------------------
#  1) STAND-ALONE WINDOW
# ---------------------------------------------------------------------------

class IndexFrame(wx.Frame):
    def __init__(self, default_folder=None, default_ext=None):
        super().__init__(None, title=_(u"Create Index PDF") + " — Songpress++")
        panel = IndexPanel(self, default_folder=default_folder,
                           default_ext=default_ext)
        # Size the window to what the content actually needs, on every
        # platform (accounting for its own fonts/paddings), so nothing is
        # clipped and there is no empty gap. The fitted size is also the
        # minimum, so the window can't be shrunk below its content.
        best = panel.GetBestSize()
        # a little horizontal slack so the rightmost radio label ("Other…")
        # is never clipped at the box/window edge
        best = wx.Size(best.width + 24, best.height)
        self.SetClientSize(best)
        self.SetMinClientSize(best)
        self.CentreOnScreen()


def main():
    app = wx.App(False)
    start = sys.argv[1] if len(sys.argv) > 1 else None
    frame = IndexFrame(default_folder=start)
    frame.Show()
    app.MainLoop()


# ---------------------------------------------------------------------------
#  2) DIALOG CALLABLE FROM THE SONGPRESS++ MENU
# ---------------------------------------------------------------------------

def showCreateIndexDialog(parent, default_folder=None, default_ext=None):
    """Call this from the File -> "Create Index PDF..." menu handler.

    The extension radio is preselected from the app-wide "Default file
    extension" preference automatically (it is read from the shared wx.Config),
    so no extra wiring is required. If you prefer to hand it over explicitly,
    pass ``default_ext=self.preferences.defaultExtension``.

    Example in SongpressFrame.py:

        from . import CreaIndice
        ...
        Bind(self.OnCreateIndex, 'createIndex')
        ...
        def OnCreateIndex(self, evt):
            CreaIndice.showCreateIndexDialog(self.frame)
            # or, explicitly:
            # CreaIndice.showCreateIndexDialog(
            #     self.frame, default_ext=self.preferences.defaultExtension)
    """
    dlg = wx.Dialog(parent, title=_(u"Create Index PDF"),
                    style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
    sizer = wx.BoxSizer(wx.VERTICAL)
    panel = IndexPanel(dlg, default_folder=default_folder,
                       default_ext=default_ext)
    sizer.Add(panel, 1, wx.EXPAND)
    sizer.Add(wx.StaticLine(dlg), 0, wx.EXPAND | wx.TOP, 4)
    closeBtn = wx.Button(dlg, wx.ID_CLOSE, _(u"Close"))
    closeBtn.Bind(wx.EVT_BUTTON, lambda evt: dlg.EndModal(wx.ID_CLOSE))
    sizer.Add(closeBtn, 0, wx.ALIGN_RIGHT | wx.ALL, 8)
    # Fit the dialog to its content on every platform, then use that as the
    # minimum size — nothing is clipped and there is no empty gap. A little
    # horizontal slack keeps the rightmost radio label ("Other…") fully visible.
    dlg.SetSizerAndFit(sizer)
    sz = wx.Size(dlg.GetSize().width + 24, dlg.GetSize().height)
    dlg.SetSize(sz)
    dlg.SetMinSize(sz)
    dlg.CentreOnParent()
    dlg.ShowModal()
    dlg.Destroy()


if __name__ == '__main__':
    main()
