###############################################################
# Name:         ChordProDirectiveHelp.py
# Purpose:      Short descriptions of ChordPro / Songpress++ directives,
#               shown as a tooltip next to the editor intellisense popup.
# Author:       Denisov21
# Created:      2026
# Copyright:    Modifications © 2026 Denisov21
# License:      GNU GPL v2
###############################################################
#
# To add a description: add an entry to _HELP (English text, it is
# translated at display time through wx.GetTranslation).
# Aliases (t, st, c, ...) point to their canonical directive.

import re

import wx

# alias -> canonical directive
_ALIASES = {
    't': 'title', 'st': 'subtitle', 'c': 'comment', 'ci': 'comment_italic',
    'cb': 'comment_box', 'np': 'new_page',
    'soc': 'start_of_chorus', 'eoc': 'end_of_chorus',
    'sov': 'start_of_verse', 'eov': 'end_of_verse',
    'sob': 'start_of_bridge', 'eob': 'end_of_bridge',
    'sot': 'start_of_tab', 'eot': 'end_of_tab',
    'sop': 'start_of_part', 'eop': 'end_of_part',
    'sog': 'start_of_grid', 'grid': 'start_of_grid', 'eog': 'end_of_grid',
    'colb': 'column_break', 'r': 'row',
    'textcolor': 'textcolour', 'chordcolor': 'chordcolour',
}

# directive -> (description, example or '')
_HELP = {
    # ── Metadata ─────────────────────────────────────────────────────────
    'title':      ("Song title.", ""),
    'subtitle':   ("Subtitle, shown under the title.", ""),
    'artist':     ("Artist or performer.", ""),
    'composer':   ("Composer of the music.", ""),
    'lyricist':   ("Author of the lyrics.", ""),
    'copyright':  ("Copyright notice.", ""),
    'album':      ("Album the song belongs to.", ""),
    'year':       ("Year of publication.", ""),
    'key':        ("Musical key of the song.", ""),
    'time':       ("Time signature.", ""),
    'tempo':      ("Tempo in beats per minute.", ""),
    'capo':       ("Capo position (fret number).", ""),
    'duration':   ("Duration of the song.", "{duration: 3:40}"),
    'sorttitle':  ("Title used for sorting in indexes.", ""),
    'meta':       ("Custom metadata: name followed by its value.", "{meta: label value}"),
    'arranger':   ("Arranger of the song.", ""),
    'beats_time': ("Duration in beats of each chord on the line below, as "
                   "Chord=beats. Shown above the chords in the preview.",
                   "{beats_time: @C@=4 @G@=2 @Am@=2 @F@=4}"),
    'keywords':   ("Keywords for searching.", ""),
    'topic':      ("Topic of the song.", ""),
    'collection': ("Collection or songbook the song belongs to.", ""),
    'language':   ("Language of the lyrics.", ""),
    'tempo_label': ("Tempo marking in words (e.g. Allegro).", ""),
    'ccli':       ("CCLI licence number of the song. Stored only, not displayed (Songpress++).", ""),
    'pagetype':   ("Page type (ChordPro 6). Accepted for compatibility, not rendered.", ""),
    'columns':    ("Number of columns (ChordPro 6). Accepted for compatibility, "
                   "not rendered.", ""),
    'transpose':  ("Transposition in semitones (ChordPro 6). Accepted for "
                   "compatibility, ignored.", ""),
    'watermark':  ("Watermark of this song (diagonal text behind the lyrics), "
                   "written by File > Watermark.",
                   "{watermark: text=DRAFT; opacity=12; ...}"),
    'tempo_m':    ("Tempo variant (Songpress++).", ""),
    'tempo_s':    ("Tempo variant (Songpress++).", ""),
    'tempo_sp':   ("Tempo variant (Songpress++).", ""),
    'tempo_c':    ("Tempo variant (Songpress++).", ""),
    'tempo_cp':   ("Tempo variant (Songpress++).", ""),
    # ── Structure ────────────────────────────────────────────────────────
    'start_of_chorus': ("Begins a chorus.", ""),
    'end_of_chorus':   ("Ends the chorus.", ""),
    'start_of_verse':  ("Begins a verse.", ""),
    'end_of_verse':    ("Ends the verse.", ""),
    'start_chorus':    ("Begins a chorus, with an optional label (Songpress++ form).",
                        "{start_chorus: Label}"),
    'end_chorus':      ("Ends the chorus.", ""),
    'start_bridge':    ("Begins a bridge, with an optional label (default: Bridge).",
                        "{start_bridge: Label}"),
    'end_bridge':      ("Ends the bridge.", ""),
    'verse':           ("Opens a verse with a custom label.", "{verse: 1}"),
    'start_of_bridge': ("Begins a bridge.", ""),
    'end_of_bridge':   ("Ends the bridge.", ""),
    'start_of_tab':    ("Begins a tablature block (monospaced).", ""),
    'end_of_tab':      ("Ends the tablature block.", ""),
    'start_of_grid':   ("Begins a chord grid.", ""),
    'end_of_grid':     ("Ends the chord grid.", ""),
    'new_page':        ("Forces a page break.", ""),
    'column_break':    ("Forces a column break.", ""),
    'new_song':        ("Starts a new song in the same file.", ""),
    'start_of_part':   ("Begins a generic part (Songpress++).", ""),
    'end_of_part':     ("Ends the part.", ""),
    'start_verse':     ("Begins an unnumbered verse, with an optional label.", ""),
    'end_verse':       ("Ends the verse.", ""),
    'start_verse_num': ("Begins a numbered verse (Songpress++).", ""),
    'end_verse_num':   ("Ends the numbered verse.", ""),
    'start_chord':     ("Begins an intro chord block, with an optional label "
                        "(default: Intro).", ""),
    'end_chord':       ("Ends the chord-only block.", ""),
    'row':             ("Inserts a blank spacer row (vertical space). Takes no value.", ""),
    'bar':             ("Explicit bar separator inside a grid block.", ""),
    # ── Formatting ───────────────────────────────────────────────────────
    'comment':         ("Comment line, shown highlighted.", ""),
    'comment_italic':  ("Comment line in italic.", ""),
    'comment_box':     ("Comment line inside a box.", ""),
    'image':           ("Inserts an image.", "{image: file.png}"),
    'textfont':        ("Font of the lyrics from here on.", ""),
    'textsize':        ("Size of the lyrics from here on.", ""),
    'textcolour':      ("Colour of the lyrics from here on.", ""),
    'chordfont':       ("Font of the chords from here on.", ""),
    'chordsize':       ("Size of the chords from here on.", ""),
    'chordcolour':     ("Colour of the chords from here on.", ""),
    'linespacing':     ("Line spacing (Songpress++).", ""),
    'chordtopspacing': ("Space above the chords (Songpress++).", ""),
    'chordbold':       ("Chords in bold (Songpress++).", ""),
    'chorditalic':     ("Chords in italic (Songpress++).", ""),
    'chordunderline':  ("Chords underlined (Songpress++).", ""),
    'textbold':        ("Lyrics in bold (Songpress++).", ""),
    'textitalic':      ("Lyrics in italic (Songpress++).", ""),
    'textunderline':   ("Lyrics underlined (Songpress++).", ""),
    # ── Chord diagrams / keyboard ───────────────────────────────────────
    'define':     ("Defines the fingering of a chord.", ""),
    'taste':      ("Draws a piano keyboard with the chord notes highlighted. "
                   "A blank line before the next directive starts a new row.",
                   "{taste: @C@ start=@C@}"),
    'fingering':  ("Draws a keyboard with finger numbers on the keys. "
                   "Use - instead of the chord to pick only some notes "
                   "(0=NOTE = dot only, key not coloured).",
                   "{fingering: @C@ hand=R 1=@C@ 3=@E@ 5=@G@}"),
    # ── Comment line ('#') ──────────────────────────────────────────────
    # Not a directive: a line starting with '#'. Used by find_help_at().
    '#': ("Comment line: treated as a blank line, it does not appear in the "
          "preview or in print.", "# This is a comment"),
    # ── Print settings stored in the song ───────────────────────────────
    # Not a real directive: it is a comment line ("# {print_options: ...}")
    # that must be the first line of the song. Written by Print options >
    # "Save in editor".
    'print_options': ("Print settings saved in the song. It is a comment on "
                      "the first line of the file: create it with "
                      "Print options > Save in editor.",
                      "# {print_options: pages=2; cols=1; scale=100; ...}"),
}

# option -> description (options offered inside an already written directive)
_OPTION_HELP = {
    'start':   "Note the keyboard starts from (e.g. start=SI).",
    'octave':  "On 8-key keyboards: both = highlight the octave key at both ends; one, single or first = left end only.",
    'hand':    "R = right hand, L = left hand (label above the keyboard).",
    'middlec': "Show or hide the middle C label (show, hide, on, off, yes, no, 1, 0).",
    'size':    "Grid scale factor (e.g. size=1.5).",
    'chordtopspacing': "Space above the chords, inside this grid only.",
    'linespacing':     "Line spacing, inside this grid only.",
    'sizedir': "Direction the size applies to: horizontal, vertical or both.",
    'width':   "Image width.",
    'height':  "Image height.",
    'scale':   "Image scale (e.g. scale=50% or scale=0.5).",
    'align':   "Image alignment: left, center or right.",
    'border':  "Draws a border around the image.",
    'left':    "Aligns the image to the left.",
    'center':  "Centres the image.",
    'right':   "Aligns the image to the right.",
    'rel':     "Relative mode, to be used with {beats_time}: spacing is relative to the chord-to-text distance.",
}

# option -> value -> description (values offered after "option=")
_SHOW = "Shows the middle C label."
_HIDE = "Hides the middle C label."
_OCT_BOTH = "Highlights the octave key at both ends."
_OCT_ONE = "Highlights the octave key at the left end only."
_VALUE_HELP = {
    'hand': {'R': "Right hand", 'L': "Left hand"},
    'octave': {'both': _OCT_BOTH, 'one': _OCT_ONE, 'single': _OCT_ONE, 'first': _OCT_ONE},
    'middlec': {'show': _SHOW, 'on': _SHOW, 'yes': _SHOW, '1': _SHOW,
                'hide': _HIDE, 'off': _HIDE, 'no': _HIDE, '0': _HIDE},
    'align': {'left': "Aligns the image to the left.",
              'center': "Centres the image.",
              'right': "Aligns the image to the right."},
    'sizedir': {'horizontal': "Applies the size horizontally only.",
                'vertical': "Applies the size vertically only.",
                'both': "Applies the size in both directions."},
}


# Directive-specific option help. When a directive is listed here ONLY its own
# table is used (the generic _OPTION_HELP / _VALUE_HELP are not consulted):
# the same name can mean different things, e.g. 'scale' is a percentage for
# print_options but a factor or percentage of the image for {image:}.
_DIRECTIVE_OPTION_HELP = {
    'print_options': {
        'pages':     "Pages per sheet: 1 or 2.",
        'cols':      "Columns per page: 1 or 2.",
        'fit':       "Shrink if it exceeds the page (0 = off, 1 = on): "
                     "reduces the content only when it does not fit, never enlarges it.",
        'shrink':    "Shrink to fit the current page (0 = off, 1 = on): "
                     "avoids clipping at the bottom.",
        'minmargin': "Minimum margin, in mm, used by Shrink (0-50).",
        'nomirror':  "No mirroring (0 = off, 1 = on): in 2-pages mode, print only "
                     "on the left half and leave the right half blank.",
        'blank':     "Remove blank pages (0 = off, 1 = on).",
        'blankthr':  "Blank page threshold, in %: a page filled less than this "
                     "is considered blank (1-95).",
        'scale':     "Scale of the whole printed content, in % (50-200, default 100).",
        'kbd':       "Size of the chord keyboards, in %, for printing only (50-200). "
                     "Optional.",
        'paper':     "Paper size, as a numeric ID (3 = A4).",
        'orient':    "Orientation: 1 = portrait, 2 = landscape.",
        'margins':   "Page margins in mm: top, bottom, left, right (0-100 each).",
    },
}

# {fingering:} numeric keys (1=DO 3=MI ...) are handled in get_option_help;
# the other fingering options use the generic _OPTION_HELP table.
_BEATS_HELP = "Duration in beats of this chord (on the chord line below)."

_FINGER_HELP = ("Finger number = note. 0=NOTE draws only a dot "
                "(the key is not coloured).")

_DIRECTIVE_VALUE_HELP = {
    'print_options': {
        'pages':    {'1': "One page per sheet.", '2': "Two pages per sheet."},
        'cols':     {'1': "One column per page.", '2': "Two columns per page."},
        'fit':      {'0': "Do not shrink when the content exceeds the page.",
                     '1': "Shrink when the content exceeds the page."},
        'shrink':   {'0': "Do not shrink to fit the current page.",
                     '1': "Shrink to fit the current page."},
        'nomirror': {'0': "Mirroring: in 2-pages mode the page is repeated on the right half.",
                     '1': "No mirroring: in 2-pages mode the right half stays blank."},
        'blank':    {'0': "Blank pages are kept.", '1': "Blank pages are removed."},
        'orient':   {'1': "Portrait.", '2': "Landscape."},
        'paper':    {'3': "A4 paper."},
    },
}


def _canon(directive):
    d = (directive or '').strip().lower()
    return _ALIASES.get(d, d)


def get_value_help(directive, option, value):
    """Return the translated tooltip for an option value, or ''."""
    opt = (option or '').strip().lower()
    d = _canon(directive)
    if d in _DIRECTIVE_VALUE_HELP:
        vals = _DIRECTIVE_VALUE_HELP[d].get(opt, {})
    else:
        vals = _VALUE_HELP.get(opt, {})
    v = (value or '').strip()
    desc = vals.get(v) or vals.get(v.lower()) or vals.get(v.upper())
    return wx.GetTranslation(desc) if desc else ''


def get_option_help(directive, option):
    """Return the translated tooltip for a directive option, or ''."""
    key = (option or '').strip().lower().rstrip('=')
    d = _canon(directive)
    if d == 'fingering' and key.isdigit():
        return wx.GetTranslation(_FINGER_HELP)
    if d == 'beats_time' and key:           # Chord=N: any chord name is valid
        return wx.GetTranslation(_BEATS_HELP)
    if d in _DIRECTIVE_OPTION_HELP:
        desc = _DIRECTIVE_OPTION_HELP[d].get(key)
    else:
        desc = _OPTION_HELP.get(key)
    return wx.GetTranslation(desc) if desc else ''


# Examples are kept in _HELP but not shown by default; set to True to show them.
SHOW_EXAMPLES = False

# Chords in the examples are written @C@ (English notation) and shown in the
# user's preferred notation. The frame calls set_notation() before a lookup.
_notation = None
_CHORD_MARK = re.compile(r'@([^@\s]+)@')


def set_notation(notation):
    """Set the chord notation used to display example chords (None = English)."""
    global _notation
    _notation = notation


def _localize_example(text):
    def conv(m):
        chord = m.group(1)
        if _notation is None:
            return chord
        try:
            try:
                from .Transpose import translateChord, enNotation
            except ImportError:
                from Transpose import translateChord, enNotation
            return translateChord(chord, enNotation, _notation)
        except Exception:
            return chord
    return _CHORD_MARK.sub(conv, text)


def get_directive_help(name):
    """Return the translated tooltip text for a directive, or '' if none."""
    key = (name or '').strip().lower()
    key = _ALIASES.get(key, key)
    entry = _HELP.get(key)
    if not entry:
        return ''
    desc, example = entry
    text = wx.GetTranslation(desc)
    if example and SHOW_EXAMPLES:
        text += u'\n' + _localize_example(example)
    return text


# ── Help for the term under the mouse pointer ────────────────────────────────
# A directive is written "{name: arg arg key=value}" (print_options uses
# "key=value; key=value"). The text of the line is examined, not the editor.

_BRACE_RE = re.compile(r'\{([^{}]*)(?:\}|$)')
_NAME_RE = re.compile(r'\s*([A-Za-z_]+)')
_TOKEN_RE = re.compile(r'[^\s;]+')


def find_help_at(line, col):
    """Help for the term at character index *col* of *line*.

    Returns (text, start, end) -- *start*/*end* are the character indexes of the
    hovered term in *line*, used to anchor the popup -- or None when the
    position is not on a directive name, option or option value that has a
    description. Works on any line, including "# {print_options: ...}"."""
    if not line or col is None or col < 0:
        return None
    line = line.rstrip('\r\n')
    # '#' as first non-blank character: comment line. Only that '#' is
    # described; a '#' elsewhere is part of a chord ([C#]), a colour
    # ({textcolor:#A52A2A}) or the lyrics.
    hash_at = len(line) - len(line.lstrip())
    if line[hash_at:hash_at + 1] == '#' and col == hash_at:
        return get_directive_help('#'), hash_at, hash_at + 1
    for bm in _BRACE_RE.finditer(line):
        if not (bm.start() <= col < bm.end()):
            continue
        inner, base = bm.group(1), bm.start(1)
        nm = _NAME_RE.match(inner)
        if not nm:
            return None
        name = nm.group(1)
        name_start, name_end = base + nm.start(1), base + nm.end(1)
        if col < name_end:                      # '{', spaces or the name itself
            text = get_directive_help(name)
            return (text, name_start, name_end) if text else None
        args_off = base + nm.end()
        for tm in _TOKEN_RE.finditer(inner[nm.end():]):
            ts, te = args_off + tm.start(), args_off + tm.end()
            if not (ts <= col < te):
                continue
            tok = tm.group(0)
            if tok.startswith(':'):             # "{name:arg ..." separator
                if col == ts:                   # the ':' itself -> the directive
                    text = get_directive_help(name)
                    return (text, name_start, name_end) if text else None
                tok, ts = tok[1:], ts + 1
            if '=' in tok:
                key, _eq, val = tok.partition('=')
                key_end = ts + len(key)
                if col > key_end:               # on the value
                    text = get_value_help(name, key, val)
                    if text:
                        return text, key_end + 1, te
                text = get_option_help(name, key)
                return (text, ts, key_end) if text else None
            text = get_option_help(name, tok)
            return (text, ts, te) if text else None
        return None
    return None


def get_help_at(line, col):
    """Translated help text for the term at *col* of *line*, or ''."""
    found = find_help_at(line, col)
    return found[0] if found else ''
