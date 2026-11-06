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
}

# directive -> (description, example or '')
_HELP = {
    # ── Metadata ─────────────────────────────────────────────────────────
    'title':      ("Song title.", "{title: Amazing Grace}"),
    'subtitle':   ("Subtitle, shown under the title.", "{subtitle: Traditional}"),
    'artist':     ("Artist or performer.", "{artist: John Newton}"),
    'composer':   ("Composer of the music.", "{composer: ...}"),
    'lyricist':   ("Author of the lyrics.", "{lyricist: ...}"),
    'copyright':  ("Copyright notice.", "{copyright: 2026 Name}"),
    'album':      ("Album the song belongs to.", "{album: ...}"),
    'year':       ("Year of publication.", "{year: 1779}"),
    'key':        ("Musical key of the song.", "{key: G}"),
    'time':       ("Time signature.", "{time: 3/4}"),
    'tempo':      ("Tempo in beats per minute.", "{tempo: 90}"),
    'capo':       ("Capo position (fret number).", "{capo: 2}"),
    'duration':   ("Duration of the song.", "{duration: 3:40}"),
    'sorttitle':  ("Title used for sorting in indexes.", "{sorttitle: Amazing Grace}"),
    'meta':       ("Custom metadata: name followed by its value.", "{meta: label value}"),
    'arranger':   ("Arranger of the song.", "{arranger: ...}"),
    'beats_time': ("Beats per chord (Songpress++).", "{beats_time: 4}"),
    'keywords':   ("Keywords for searching.", "{keywords: ...}"),
    'topic':      ("Topic of the song.", "{topic: ...}"),
    'collection': ("Collection or songbook the song belongs to.", "{collection: ...}"),
    'language':   ("Language of the lyrics.", "{language: it}"),
    'tempo_label': ("Tempo marking in words (e.g. Allegro).", "{tempo_label: Allegro}"),
    'tempo_m':    ("Tempo variant (Songpress++).", ""),
    'tempo_s':    ("Tempo variant (Songpress++).", ""),
    'tempo_sp':   ("Tempo variant (Songpress++).", ""),
    'tempo_c':    ("Tempo variant (Songpress++).", ""),
    'tempo_cp':   ("Tempo variant (Songpress++).", ""),
    # ── Structure ────────────────────────────────────────────────────────
    'start_of_chorus': ("Begins a chorus.", "{start_of_chorus}"),
    'end_of_chorus':   ("Ends the chorus.", ""),
    'start_of_verse':  ("Begins a verse.", "{start_of_verse}"),
    'end_of_verse':    ("Ends the verse.", ""),
    'start_of_bridge': ("Begins a bridge.", "{start_of_bridge}"),
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
    'start_verse':     ("Begins a verse (Songpress++).", ""),
    'end_verse':       ("Ends the verse.", ""),
    'start_verse_num': ("Begins a numbered verse (Songpress++).", ""),
    'end_verse_num':   ("Ends the numbered verse.", ""),
    'start_chord':     ("Begins a chord-only block (Songpress++).", ""),
    'end_chord':       ("Ends the chord-only block.", ""),
    'row':             ("Starts a new row (Songpress++).", ""),
    'bar':             ("Inserts a bar line (Songpress++).", ""),
    # ── Formatting ───────────────────────────────────────────────────────
    'comment':         ("Comment line, shown highlighted.", "{comment: Repeat twice}"),
    'comment_italic':  ("Comment line in italic.", "{comment_italic: ...}"),
    'comment_box':     ("Comment line inside a box.", "{comment_box: ...}"),
    'image':           ("Inserts an image.", "{image: file.png}"),
    'textfont':        ("Font of the lyrics from here on.", "{textfont: Arial}"),
    'textsize':        ("Size of the lyrics from here on.", "{textsize: 12}"),
    'textcolour':      ("Colour of the lyrics from here on.", "{textcolour: blue}"),
    'chordfont':       ("Font of the chords from here on.", "{chordfont: Arial}"),
    'chordsize':       ("Size of the chords from here on.", "{chordsize: 10}"),
    'chordcolour':     ("Colour of the chords from here on.", "{chordcolour: red}"),
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
                   "Options: start=, octave=, hand=, middlec=. "
                   "Add ^ or v after the chord for an arrow. "
                   "A blank line before the next directive starts a new row.",
                   "{taste: DO start=DO}"),
    'fingering':  ("Draws a keyboard with finger numbers on the keys. "
                   "Options: hand=L|R, start=, octave=, middlec=. "
                   "Use - instead of the chord to pick only some notes "
                   "(0=NOTE = dot only, key not coloured).",
                   "{fingering: DO hand=R 1=DO 3=MI 5=SOL}"),
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


def get_value_help(directive, option, value):
    """Return the translated tooltip for an option value, or ''."""
    vals = _VALUE_HELP.get((option or '').strip().lower(), {})
    v = (value or '').strip()
    desc = vals.get(v) or vals.get(v.lower()) or vals.get(v.upper())
    return wx.GetTranslation(desc) if desc else ''


def get_option_help(directive, option):
    """Return the translated tooltip for a directive option, or ''."""
    key = (option or '').strip().lower().rstrip('=')
    desc = _OPTION_HELP.get(key)
    return wx.GetTranslation(desc) if desc else ''


def get_directive_help(name):
    """Return the translated tooltip text for a directive, or '' if none."""
    key = (name or '').strip().lower()
    key = _ALIASES.get(key, key)
    entry = _HELP.get(key)
    if not entry:
        return ''
    desc, example = entry
    text = wx.GetTranslation(desc)
    if example:
        text += u'\n' + example
    return text
