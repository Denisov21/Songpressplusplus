###############################################################
# Name:             SyntaxChecker.py
# Purpose:    Controlla parentesi quadre degli accordi e comandi tra parentesi graffe. Verifica sintattica di un testo in formato ChordPro.
# Author:         Denisov21
# Created:     2026-03-16
# Copyright:  Denisov21 
# License:     GNU GPL v2
##############################################################

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class SyntaxError:
    """Rappresenta un singolo errore sintattico rilevato."""
    line: int          # numero di riga (1-based)
    column: int        # posizione nella riga (1-based)
    message: str       # descrizione dell'errore


@dataclass
class SyntaxCheckResult:
    """Risultato complessivo della verifica sintattica."""
    errors: List[SyntaxError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


# Comandi ChordPro riconosciuti (standard + estensioni Songpress)
_KNOWN_COMMANDS = {
    # Struttura
    "t", "title",
    "st", "subtitle",
    "soc", "start_of_chorus",
    "eoc", "end_of_chorus",
    "verse",
    "c", "comment",
    "ci", "comment_italic",
    "cb", "comment_box",
    # Estensioni Songpress
    "start_verse", "end_verse",
    "start_verse_num", "end_verse_num",
    "start_chorus", "end_chorus",
    "start_chord", "end_chord",
    "start_bridge", "end_bridge",
    "row", "r",
    "new_song",
    # Metadati
    "artist", "composer", "album", "year", "copyright", "key", "capo",
    # Layout
    "new_page", "np",
    "column_break", "colb",
    # Formattazione testo
    "textsize", "textfont", "textcolour", "textcolor",
    "linespacing", "chordtopspacing",
    # Formattazione accordi
    "chordsize", "chordfont", "chordcolour", "chordcolor",
    # Indicazioni musicali
    "tempo", "time",
    # Diagrammi
    "define",
    # Tastiera pianoforte (Songpress)
    "taste",
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


def check(text: str) -> SyntaxCheckResult:
    """
    Esegue la verifica sintattica del testo ChordPro.

    Controlla:
    - Parentesi quadre degli accordi non chiuse o non aperte
    - Accordi vuoti []
    - Parentesi graffe dei comandi non chiuse o non aperte
    - Comandi sconosciuti
    - Comandi che richiedono un valore ma non lo hanno (es. {t:} senza testo)
    - Comandi che richiedono parentesi di chiusura mancante

    Restituisce un SyntaxCheckResult con la lista degli errori trovati.
    """
    result = SyntaxCheckResult()
    lines = text.splitlines()

    for line_idx, line in enumerate(lines):
        line_num = line_idx + 1

        # Ignora righe commento
        if line.lstrip().startswith("#"):
            continue

        _check_square_brackets(line, line_num, result)
        _check_curly_braces(line, line_num, result)

    return result


def _check_square_brackets(line: str, line_num: int, result: SyntaxCheckResult):
    """Verifica le parentesi quadre degli accordi."""
    i = 0
    while i < len(line):
        ch = line[i]

        if ch == '[':
            # Cerca la parentesi chiusa corrispondente
            close = line.find(']', i + 1)
            if close == -1:
                result.errors.append(SyntaxError(
                    line=line_num,
                    column=i + 1,
                    message="Parentesi quadra aperta '[' non chiusa"
                ))
                break  # inutile continuare su questa riga
            else:
                content = line[i + 1:close].strip()
                if content == "":
                    result.errors.append(SyntaxError(
                        line=line_num,
                        column=i + 1,
                        message="Accordo vuoto '[]'"
                    ))
                i = close + 1

        elif ch == ']':
            # Parentesi chiusa senza apertura
            result.errors.append(SyntaxError(
                line=line_num,
                column=i + 1,
                message="Parentesi quadra chiusa ']' senza apertura"
            ))
            i += 1

        else:
            i += 1


def _check_curly_braces(line: str, line_num: int, result: SyntaxCheckResult):
    """Verifica i comandi tra parentesi graffe."""
    i = 0
    while i < len(line):
        ch = line[i]

        if ch == '{':
            close = line.find('}', i + 1)
            if close == -1:
                result.errors.append(SyntaxError(
                    line=line_num,
                    column=i + 1,
                    message="Parentesi graffa aperta '{' non chiusa"
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
                message="Parentesi graffa chiusa '}' senza apertura"
            ))
            i += 1

        else:
            i += 1


def _validate_command(content: str, line_num: int, col: int, result: SyntaxCheckResult):
    """Valida il contenuto di un comando {…}."""
    if not content:
        result.errors.append(SyntaxError(
            line=line_num,
            column=col,
            message="Comando vuoto '{}'"
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

    # Comandi che richiedono un valore
    _REQUIRES_VALUE = {
        "t", "title", "st", "subtitle",
        "c", "comment", "ci", "comment_italic", "cb", "comment_box",
        "artist", "composer", "album", "year", "copyright",
        "key", "capo", "tempo", "time",
        "textsize", "textfont", "textcolour", "textcolor",
        "chordsize", "chordfont", "chordcolour", "chordcolor",
        "linespacing", "chordtopspacing",
        "define", "taste",
        "start_chord",
    }

    if cmd_name not in _KNOWN_COMMANDS:
        result.errors.append(SyntaxError(
            line=line_num,
            column=col,
            message=f"Comando sconosciuto: '{{{cmd_name}}}'"
        ))
        return

    if cmd_name in _REQUIRES_VALUE:
        if cmd_value is None or cmd_value == "":
            result.errors.append(SyntaxError(
                line=line_num,
                column=col,
                message=f"Il comando '{{{cmd_name}:}}' richiede un valore"
            ))
