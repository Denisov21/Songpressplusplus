###############################################################
# Name:             SyntaxChecker.py
# Purpose:    Check square brackets (chords) and curly braces (commands). ChordPro syntax checker.
# Author:         Denisov21
# Created:     2026-03-16
# Copyright:  Denisov21 
# License:     GNU GPL v2
##############################################################

import re
from dataclasses import dataclass, field
from typing import List

import wx
_ = wx.GetTranslation


@dataclass
class SyntaxError:
    """Represents a single detected syntax error."""
    line: int          # line number (1-based)
    column: int        # column position in the line (1-based)
    message: str       # error description


@dataclass
class SyntaxCheckResult:
    """Overall result of the syntax check."""
    errors: List[SyntaxError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


# Known ChordPro commands (standard + Songpress++ extensions)
_KNOWN_COMMANDS = {
    # Song structure — standard
    "t", "title",
    "st", "subtitle",
    "sov", "start_of_verse", "eov", "end_of_verse",
    "soc", "start_of_chorus", "eoc", "end_of_chorus",
    "sob", "start_of_bridge", "eob", "end_of_bridge",
    "sot", "start_of_tab",    "eot", "end_of_tab",
    "sog", "start_of_grid",   "eog", "end_of_grid",
    "grid",
    "verse",
    "c", "comment",
    "ci", "comment_italic",
    "cb", "comment_box",
    # Song structure — Songpress++ extensions
    "start_verse",     "end_verse",
    "start_verse_num", "end_verse_num",
    "start_chorus",    "end_chorus",
    "start_chord",     "end_chord",
    "start_bridge",    "end_bridge",
    "row", "r",
    "new_song",
    # Metadata
    "artist", "composer", "album", "year", "copyright",
    "key", "capo",
    # Page / column layout
    "new_page", "np",
    "column_break", "colb",
    # Text formatting
    "textsize", "textfont", "textcolour", "textcolor",
    "linespacing", "chordtopspacing",
    # Chord formatting
    "chordsize", "chordfont", "chordcolour", "chordcolor",
    # Musical indications
    "tempo", "tempo_m", "tempo_s", "tempo_sp", "tempo_c", "tempo_cp",
    "time",
    # Images
    "image",
    # Chord diagrams / keyboard
    "define", "taste", "fingering",
}

# ── Dati per la validazione di {fingering:} ──────────────────────────────────

# Note italiane → semitono
_IT_NOTES = {
    'do': 0,  'do#': 1,  'dob': 11,
    're': 2,  're#': 3,  'reb': 1,
    'mi': 4,  'mi#': 5,  'mib': 3,
    'fa': 5,  'fa#': 6,  'fab': 4,
    'sol': 7, 'sol#': 8, 'solb': 6,
    'la': 9,  'la#': 10, 'lab': 8,
    'si': 11, 'si#': 0,  'sib': 10,
}

# Note inglesi → semitono
_EN_NOTES = {
    'c': 0,  'c#': 1,  'cb': 11,
    'd': 2,  'd#': 3,  'db': 1,
    'e': 4,  'e#': 5,  'eb': 3,
    'f': 5,  'f#': 6,  'fb': 4,
    'g': 7,  'g#': 8,  'gb': 6,
    'a': 9,  'a#': 10, 'ab': 8,
    'b': 11, 'b#': 0,  'bb': 10,
    'h': 11,
}

# Suffissi accordo → intervalli (semitoni dalla fondamentale)
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

# Semitono → nome canonico italiano (per i messaggi di errore)
_SEMI_TO_IT = {
    0: 'Do', 1: 'Do#', 2: 'Re', 3: 'Re#', 4: 'Mi',
    5: 'Fa', 6: 'Fa#', 7: 'Sol', 8: 'Sol#', 9: 'La',
    10: 'La#', 11: 'Si',
}


def _note_to_semitone(note_str: str):
    """Converte nome nota (IT o EN) in semitono 0-11, o None se non riconosciuta."""
    s = note_str.strip().lower()
    if s in _IT_NOTES:
        return _IT_NOTES[s]
    if s in _EN_NOTES:
        return _EN_NOTES[s]
    return None


def _parse_chord_semitones(chord_str: str):
    """
    Parsa il nome di un accordo e restituisce il set di semitoni (0-11)
    che ne fanno parte, oppure None se l'accordo non è riconosciuto.
    """
    s = chord_str.strip()
    sl = s.lower()
    root = None
    rest = ''

    # Prova notazione italiana (ordine per lunghezza decrescente)
    for name in sorted(_IT_NOTES, key=len, reverse=True):
        if sl.startswith(name):
            root = _IT_NOTES[name]
            rest = s[len(name):]
            break

    # Prova notazione inglese
    if root is None:
        for name in sorted(_EN_NOTES, key=len, reverse=True):
            if sl.startswith(name):
                root = _EN_NOTES[name]
                rest = s[len(name):]
                break

    if root is None:
        return None

    # Ignora il basso dopo /
    rest = rest.split('/')[0].strip()

    # Trova gli intervalli del tipo di accordo
    intervals = [0, 4, 7]   # default maggiore
    for suffix, ivs in _CHORD_INTERVALS:
        if rest.lower().startswith(suffix.lower()):
            intervals = ivs
            break

    return {(root + i) % 12 for i in intervals}


def _validate_fingering(cmd_value: str, line_num: int, col: int,
                        result: SyntaxCheckResult):
    """
    Valida il valore di {fingering: ...}.

    Controlli:
    1. Il primo token deve essere un accordo riconosciuto.
    2. I token successivi devono avere il formato  N=NomeNota  (N intero 1-5).
    3. Ogni nota indicata deve appartenere all'accordo specificato.
    4. Lo stesso dito non può essere assegnato due volte.
    5. La stessa nota non può ricevere due dita diverse.
    """
    parts = cmd_value.strip().split()
    if not parts:
        # Valore vuoto: già gestito da _REQUIRES_VALUE
        return

    chord_name = parts[0]
    chord_semitones = _parse_chord_semitones(chord_name)

    if chord_semitones is None:
        result.errors.append(SyntaxError(
            line=line_num, column=col,
            message=_("{{fingering}}: unrecognized chord '{chord}'").format(
                chord=chord_name)
        ))
        return   # senza accordo valido non ha senso continuare

    # Parsa le assegnazioni dito=nota
    used_fingers = {}   # finger_num → nota_str
    used_semitones = {} # semitono → finger_num

    for token in parts[1:]:
        m = re.match(r'^(\d+)=(.+)$', token)
        if not m:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{{fingering}}: invalid token '{tok}' — expected format: finger=note (e.g. 2=Mi)"
                ).format(tok=token)
            ))
            continue

        finger_num = int(m.group(1))
        note_str   = m.group(2)

        # Dito fuori range 1-5
        if finger_num < 1 or finger_num > 5:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{{fingering}}: finger number {n} is out of range (1–5)"
                ).format(n=finger_num)
            ))
            continue

        # Nota non riconosciuta
        semi = _note_to_semitone(note_str)
        if semi is None:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{{fingering}}: unrecognized note '{note}'"
                ).format(note=note_str)
            ))
            continue

        # Nota non appartiene all'accordo
        if semi not in chord_semitones:
            expected = ', '.join(
                _SEMI_TO_IT[s] for s in sorted(chord_semitones))
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{{fingering}}: note '{note}' does not belong to {chord} ({expected})"
                ).format(note=note_str, chord=chord_name, expected=expected)
            ))
            continue

        # Dito già usato
        if finger_num in used_fingers:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{{fingering}}: finger {n} assigned twice ({a} and {b})"
                ).format(n=finger_num,
                         a=used_fingers[finger_num], b=note_str)
            ))
            continue

        # Nota già assegnata a un altro dito
        if semi in used_semitones:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{{fingering}}: note '{note}' assigned to both finger {a} and finger {b}"
                ).format(note=note_str,
                         a=used_semitones[semi], b=finger_num)
            ))
            continue

        used_fingers[finger_num]  = note_str
        used_semitones[semi]      = finger_num


# Pattern per un accordo valido tra parentesi quadre
_CHORD_PATTERN = re.compile(
    r'^[A-Ga-g]?(?:Do|Re|Mi|Fa|Sol|La|Si|[A-G])'
    r'[#b]?'
    r'(?:m|min|maj|aug|dim|sus)?'
    r'\d*'
    r'(?:/[A-G](?:Do|Re|Mi|Fa|Sol|La|Si)?[#b]?)?'
    r'$'
)


def _strip_inline_comment(line: str) -> str:
    depth_sq = 0
    depth_cu = 0
    for i, ch in enumerate(line):
        if ch == '[':
            depth_sq += 1
        elif ch == ']':
            depth_sq = max(0, depth_sq - 1)
        elif ch == '{':
            depth_cu += 1
        elif ch == '}':
            depth_cu = max(0, depth_cu - 1)
        elif ch == '#' and depth_sq == 0 and depth_cu == 0:
            return line[:i]
    return line


def check(text: str) -> SyntaxCheckResult:
    result = SyntaxCheckResult()
    lines = text.splitlines()

    for line_idx, line in enumerate(lines):
        line_num = line_idx + 1
        if line.lstrip().startswith("#"):
            continue
        line = _strip_inline_comment(line)
        _check_square_brackets(line, line_num, result)
        _check_curly_braces(line, line_num, result)

    return result


def _check_square_brackets(line: str, line_num: int, result: SyntaxCheckResult):
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '[':
            close = line.find(']', i + 1)
            if close == -1:
                result.errors.append(SyntaxError(
                    line=line_num, column=i + 1,
                    message=_("Opening square bracket '[' not closed")
                ))
                break
            else:
                content = line[i + 1:close].strip()
                if content == "":
                    result.errors.append(SyntaxError(
                        line=line_num, column=i + 1,
                        message=_("Empty chord '[]'")
                    ))
                i = close + 1
        elif ch == ']':
            result.errors.append(SyntaxError(
                line=line_num, column=i + 1,
                message=_("Closing square bracket ']' without opening")
            ))
            i += 1
        else:
            i += 1


def _check_curly_braces(line: str, line_num: int, result: SyntaxCheckResult):
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '{':
            close = line.find('}', i + 1)
            if close == -1:
                result.errors.append(SyntaxError(
                    line=line_num, column=i + 1,
                    message=_("Opening curly brace '{' not closed")
                ))
                break
            else:
                content = line[i + 1:close].strip()
                _validate_command(content, line_num, i + 1, result)
                i = close + 1
        elif ch == '}':
            result.errors.append(SyntaxError(
                line=line_num, column=i + 1,
                message=_("Closing curly brace '}' without opening")
            ))
            i += 1
        else:
            i += 1


def _validate_command(content: str, line_num: int, col: int,
                      result: SyntaxCheckResult):
    if not content:
        result.errors.append(SyntaxError(
            line=line_num, column=col,
            message=_("Empty command '{}'")
        ))
        return

    if ':' in content:
        cmd_name, cmd_value = content.split(':', 1)
        cmd_name  = cmd_name.strip().lower()
        cmd_value = cmd_value.strip()
    else:
        cmd_name  = content.strip().lower()
        cmd_value = None

    _REQUIRES_VALUE = {
        "t", "title",
        "st", "subtitle",
        "c", "comment", "ci", "comment_italic", "cb", "comment_box",
        "artist", "composer", "album", "year", "copyright",
        "key", "capo",
        "tempo", "tempo_m", "tempo_s", "tempo_sp", "tempo_c", "tempo_cp",
        "time",
        "define", "taste", "fingering",
        "start_chord",
        "image",
    }

    _OPTIONAL_VALUE = {
        "textsize", "textfont", "textcolour", "textcolor",
        "chordsize", "chordfont", "chordcolour", "chordcolor",
        "linespacing", "chordtopspacing",
    }

    _REQUIRES_NUMERIC_VALUE = {
        "textsize", "chordsize",
        "linespacing", "chordtopspacing",
        "capo",
        "tempo", "tempo_m", "tempo_s", "tempo_sp", "tempo_c", "tempo_cp",
    }

    _REQUIRES_TIME_SIGNATURE = {"time"}

    if cmd_name not in _KNOWN_COMMANDS:
        result.errors.append(SyntaxError(
            line=line_num, column=col,
            message=_("Unknown command: '{cmd}'").format(
                cmd="{" + cmd_name + "}")
        ))
        return

    if cmd_value is not None and cmd_value == "" and cmd_name in _OPTIONAL_VALUE:
        result.errors.append(SyntaxError(
            line=line_num, column=col,
            message=_("Command '{cmd}' has ':' but no value; use '{reset}' to reset").format(
                cmd="{" + cmd_name + ":}",
                reset="{" + cmd_name + "}",
            )
        ))
        return

    if cmd_name in _REQUIRES_TIME_SIGNATURE and cmd_value is not None and cmd_value != "":
        import re as _re
        if not _re.fullmatch(r'[1-9][0-9]*/[1-9][0-9]*', cmd_value.strip()):
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_("Command '{cmd}' requires a time signature (e.g. 4/4), got: '{val}'").format(
                    cmd="{" + cmd_name + ":}",
                    val=cmd_value,
                )
            ))
            return

    if cmd_name in _REQUIRES_NUMERIC_VALUE and cmd_value is not None and cmd_value != "":
        try:
            float(cmd_value)
        except ValueError:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_("Command '{cmd}' requires a numeric value, got: '{val}'").format(
                    cmd="{" + cmd_name + ":}",
                    val=cmd_value,
                )
            ))
            return

    if cmd_name in _REQUIRES_VALUE:
        if cmd_value is None or cmd_value == "":
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_("Command '{cmd}' requires a value").format(
                    cmd="{" + cmd_name + ":}")
            ))
            return

    # ── Validazione specifica per {fingering:} ────────────────────
    if cmd_name == "fingering" and cmd_value:
        _validate_fingering(cmd_value, line_num, col, result)
