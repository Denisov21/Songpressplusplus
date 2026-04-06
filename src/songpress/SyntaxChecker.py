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
    "define", "taste",
}

# Pattern per un accordo valido tra parentesi quadre
# Notazione italiana: Do Re Mi Fa Sol La Si (con alterazioni # b)
# Notazione inglese:  C D E F G A B (con alterazioni # b)
_CHORD_PATTERN = re.compile(
    r'^[A-Ga-g]?(?:Do|Re|Mi|Fa|Sol|La|Si|[A-G])'  # nota base
    r'[#b]?'                                         # alterazione opzionale
    r'(?:m|min|maj|aug|dim|sus)?'                    # qualità opzionale
    r'\d*'                                           # numero opzionale (es. 7, 9)
    r'(?:/[A-G](?:Do|Re|Mi|Fa|Sol|La|Si)?[#b]?)?'   # basso opzionale (es. /Sol)
    r'$'
)


def _strip_inline_comment(line: str) -> str:
    """Return the portion of *line* before any bare # comment marker.
    A # inside [] or {} is part of a chord/command and is NOT a comment.
    """
    depth_sq = 0  # inside []
    depth_cu = 0  # inside {}
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
    """
    Run a syntax check on the ChordPro text.

    Checks:
    - Unclosed or spurious square brackets (chords)
    - Empty chord brackets []
    - Unclosed or spurious curly braces (commands)
    - Unknown commands
    - Commands that require a value but have none (e.g. {title:} with no text)

    Returns a SyntaxCheckResult with the list of errors found.
    """
    result = SyntaxCheckResult()
    lines = text.splitlines()

    for line_idx, line in enumerate(lines):
        line_num = line_idx + 1

        # Skip full-line comments
        if line.lstrip().startswith("#"):
            continue

        # Strip inline comment: everything after a bare # that is not inside
        # [] or {} is treated as a comment and must not be analysed.
        line = _strip_inline_comment(line)

        _check_square_brackets(line, line_num, result)
        _check_curly_braces(line, line_num, result)

    return result


def _check_square_brackets(line: str, line_num: int, result: SyntaxCheckResult):
    """Check square brackets (chords)."""
    i = 0
    while i < len(line):
        ch = line[i]

        if ch == '[':
            # Look for the matching closing bracket
            close = line.find(']', i + 1)
            if close == -1:
                result.errors.append(SyntaxError(
                    line=line_num,
                    column=i + 1,
                    message=_("Opening square bracket '[' not closed")
                ))
                break  # no point continuing on this line
            else:
                content = line[i + 1:close].strip()
                if content == "":
                    result.errors.append(SyntaxError(
                        line=line_num,
                        column=i + 1,
                        message=_("Empty chord '[]'")
                    ))
                i = close + 1

        elif ch == ']':
            # Closing bracket without opening
            result.errors.append(SyntaxError(
                line=line_num,
                column=i + 1,
                message=_("Closing square bracket ']' without opening")
            ))
            i += 1

        else:
            i += 1


def _check_curly_braces(line: str, line_num: int, result: SyntaxCheckResult):
    """Check commands inside curly braces."""
    i = 0
    while i < len(line):
        ch = line[i]

        if ch == '{':
            close = line.find('}', i + 1)
            if close == -1:
                result.errors.append(SyntaxError(
                    line=line_num,
                    column=i + 1,
                    message=_("Opening curly brace '{' not closed")
                ))
                break
            else:
                content = line[i + 1:close].strip()
                _validate_command(content, line_num, i + 1, result)
                i = close + 1

        elif ch == '}':
            result.errors.append(SyntaxError(
                line=line_num,
                column=i + 1,
                message=_("Closing curly brace '}' without opening")
            ))
            i += 1

        else:
            i += 1


def _validate_command(content: str, line_num: int, col: int, result: SyntaxCheckResult):
    """Validate the content of a {…} command."""
    if not content:
        result.errors.append(SyntaxError(
            line=line_num,
            column=col,
            message=_("Empty command '{}'")
        ))
        return

    # Separa nome comando e valore opzionale
    if ':' in content:
        cmd_name, cmd_value = content.split(':', 1)
        cmd_name = cmd_name.strip().lower()
        cmd_value = cmd_value.strip()
    else:
        cmd_name = content.strip().lower()
        cmd_value = None

    # Commands that ALWAYS require a non-empty value (omitting the value is an error).
    _REQUIRES_VALUE = {
        "t", "title",
        "st", "subtitle",
        "c", "comment", "ci", "comment_italic", "cb", "comment_box",
        "artist", "composer", "album", "year", "copyright",
        "key", "capo",
        "tempo", "tempo_m", "tempo_s", "tempo_sp", "tempo_c", "tempo_cp",
        "time",
        "define", "taste",
        "start_chord",
        "image",
    }

    # Commands where the value is OPTIONAL:
    # used WITH a value to set, used WITHOUT a value to reset to default.
    #   {textfont:Arial}  → set font
    #   {textfont}        → reset to default  ← NOT an error
    _OPTIONAL_VALUE = {
        "textsize", "textfont", "textcolour", "textcolor",
        "chordsize", "chordfont", "chordcolour", "chordcolor",
        "linespacing", "chordtopspacing",
    }

    # Commands whose value, when present, must be numeric (int or float).
    _REQUIRES_NUMERIC_VALUE = {
        "textsize", "chordsize",
        "linespacing", "chordtopspacing",
        "capo",
        "tempo", "tempo_m", "tempo_s", "tempo_sp", "tempo_c", "tempo_cp",
    }

    # Commands whose value must be a time signature: two positive integers
    # separated by '/', e.g. 4/4, 3/4, 6/8.
    _REQUIRES_TIME_SIGNATURE = {"time"}

    if cmd_name not in _KNOWN_COMMANDS:
        result.errors.append(SyntaxError(
            line=line_num,
            column=col,
            message=_("Unknown command: '{cmd}'").format(cmd="{" + cmd_name + "}")
        ))
        return

    # Se i due punti sono presenti ma il valore è vuoto, è sempre un errore:
    # la forma corretta per il reset è {cmd} senza i due punti.
    if cmd_value is not None and cmd_value == "" and cmd_name in _OPTIONAL_VALUE:
        result.errors.append(SyntaxError(
            line=line_num,
            column=col,
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
                line=line_num,
                column=col,
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
                line=line_num,
                column=col,
                message=_("Command '{cmd}' requires a numeric value, got: '{val}'").format(
                    cmd="{" + cmd_name + ":}",
                    val=cmd_value,
                )
            ))
            return

    if cmd_name in _REQUIRES_VALUE:
        if cmd_value is None or cmd_value == "":
            result.errors.append(SyntaxError(
                line=line_num,
                column=col,
                message=_("Command '{cmd}' requires a value").format(cmd="{" + cmd_name + ":}")
            ))
