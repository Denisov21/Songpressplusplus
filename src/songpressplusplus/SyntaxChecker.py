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

def _(s):
    """Lazy wrapper for wx.GetTranslation.
    Chiamare wx.GetTranslation a livello di modulo può fallire se wx non è
    ancora inizializzato; questo wrapper lo risolve chiamandola a runtime."""
    try:
        return wx.GetTranslation(s)
    except Exception:
        return s


# Livelli di gravità di un problema rilevato.
SEVERITY_ERROR = "error"       # errore vero e proprio (blocca / notazione errata)
SEVERITY_WARNING = "warning"   # avvertimento (probabile, ma non necessariamente errato)


@dataclass
class SyntaxError:
    """Represents a single detected syntax error or warning."""
    line: int          # line number (1-based)
    column: int        # column position in the line (1-based)
    message: str       # error description
    severity: str = SEVERITY_ERROR   # SEVERITY_ERROR oppure SEVERITY_WARNING


@dataclass
class SyntaxCheckResult:
    """Overall result of the syntax check."""
    errors: List[SyntaxError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def error_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == SEVERITY_ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == SEVERITY_WARNING)

    @property
    def has_errors(self) -> bool:
        """True se è presente almeno un problema di gravità 'error'."""
        return self.error_count > 0


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
    # Song structure — ChordPro 6 generic section
    "sop", "start_of_part", "eop", "end_of_part",
    # Song structure — Songpress++ extensions
    "start_verse",     "end_verse",
    "start_verse_num", "end_verse_num",
    "start_chorus",    "end_chorus",
    "start_chord",     "end_chord",
    "start_bridge",    "end_bridge",
    "row", "r",
    "bar",
    "new_song",
    # Metadata — standard
    "artist", "composer", "lyricist", "arranger",
    "album", "year", "copyright",
    "key", "capo",
    "beats_time", "ccli",
    "duration",
    # Metadata — extended (ChordPro 6, metadata-only, not rendered)
    "sorttitle", "keywords", "topic", "collection", "language",
    "pagetype", "columns", "meta",
    # Transpose (ChordPro 6, consumed silently)
    "transpose",
    # Watermark — Songpress++ (metadato per-documento, consumato senza render)
    "watermark",
    # Page / column layout
    "new_page", "np",
    "column_break", "colb",
    # Text formatting
    "textsize", "textfont", "textcolour", "textcolor",
    "textbold", "textitalic", "textunderline",
    "linespacing", "chordtopspacing",
    # Chord formatting
    "chordsize", "chordfont", "chordcolour", "chordcolor",
    "chordbold", "chorditalic", "chordunderline",
    # Musical indications
    "tempo", "tempo_m", "tempo_s", "tempo_sp", "tempo_c", "tempo_cp",
    "tempo_label",
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
    # Accordo tra parentesi tonde, es. '(Do)' o '(La7/Do#)': è una notazione
    # valida (accordo di passaggio/facoltativo). Le parentesi non fanno parte
    # del nome, quindi le rimuoviamo prima di analizzarlo.
    if len(s) >= 2 and s.startswith('(') and s.endswith(')'):
        s = s[1:-1].strip()
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

    # Il '-' indica "minore" ovunque compaia nella parte estensione:
    # in coda ("7-"), subito dopo la radice ("-7", "-9", "-7b5") oppure
    # da solo ("-" → triade minore).
    is_minor = '-' in rest
    if is_minor:
        rest = rest.replace('-', '', 1)

    # Se compare una 'm' ovunque nel resto (es. "m7-", "7m-", "maj7-"),
    # il '-' è ridondante o contraddittorio: "m" indica già il minore,
    # "maj" indica esplicitamente il maggiore. L'accordo è ambiguo e
    # viene considerato non riconosciuto.
    if is_minor and 'm' in rest.lower():
        return None

    # Trova gli intervalli del tipo di accordo
    intervals = [0, 4, 7]   # default maggiore
    for suffix, ivs in _CHORD_INTERVALS:
        if rest.lower().startswith(suffix.lower()):
            intervals = ivs
            break

    if is_minor:
        intervals = [3 if i == 4 else i for i in intervals]

    return {(root + i) % 12 for i in intervals}


# Token ammessi tra parentesi quadre che non sono accordi
_NON_CHORD_TOKENS = {'n.c.', 'nc', 'tacet', '%', '|', '||', '*'}


# ── Opzioni tastiera comuni a {taste:} e {fingering:} ────────────────────────
# Note naturali (tasti bianchi) ammesse come nota di partenza (start=)
_WHITE_SEMITONES = {0, 2, 4, 5, 7, 9, 11}   # Do Re Mi Fa Sol La Si
# Valori ammessi per octave=
_OCTAVE_VALUES = {'both', 'one', 'single', 'first'}


def _validate_kbd_option(token: str, line_num: int, col: int,
                         result: SyntaxCheckResult, seen: set,
                         directive: str) -> bool:
    """
    Valida un token opzione della tastiera comune a {taste:} e {fingering:}:
        start=<nota naturale>   → nota di partenza (Do..Si / C..B)
        octave=<both|one>       → evidenziazione dell'ottava (layout a 8 tasti)

    Restituisce True se il token È un'opzione riconosciuta (start=/octave=),
    così il chiamante non lo tratta come accordo/nota; False altrimenti.
    Gli eventuali errori vengono aggiunti a `result`; `seen` rileva i duplicati.
    `directive` è l'etichetta usata nei messaggi (es. "{taste}" o "{fingering}").
    """
    # ── start=<nota> ──────────────────────────────────────────────
    m = re.match(r'^start=(.*)$', token, re.IGNORECASE)
    if m:
        if 'start' in seen:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_("%s: 'start' specified more than once") % directive))
        seen.add('start')
        val = m.group(1)
        semi = _note_to_semitone(val)
        if semi is None:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_("%s: unrecognized start note '%s'") % (directive, val)))
        elif semi not in _WHITE_SEMITONES:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "%s: start note '%s' must be a natural note "
                    "(Do Re Mi Fa Sol La Si)") % (directive, val)))
        return True

    # ── octave=<both|one|single|first> ────────────────────────────
    m = re.match(r'^octave=(.*)$', token, re.IGNORECASE)
    if m:
        if 'octave' in seen:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_("%s: 'octave' specified more than once") % directive))
        seen.add('octave')
        val = m.group(1)
        if val.lower() not in _OCTAVE_VALUES:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "%s: 'octave' must be both or one, got '%s'"
                ) % (directive, val)))
        return True

    return False


def _check_chord_name(content: str, line_num: int, col: int,
                      result: SyntaxCheckResult):
    """Segnala un errore se il contenuto di [...] non è un accordo valido."""
    name = content.strip()
    if not name:
        return
    if name.lower() in _NON_CHORD_TOKENS:
        return
    # Token puramente simbolici (stanghette, ripetizioni, annotazioni)
    if not re.search(r'[A-Za-z]', name):
        return
    if _parse_chord_semitones(name) is None:
        result.errors.append(SyntaxError(
            line=line_num, column=col,
            message=_("Unrecognized or invalid chord '%s'") % name,
            severity=SEVERITY_WARNING
        ))


def _validate_taste(cmd_value: str, line_num: int, col: int,
                    result: SyntaxCheckResult):
    """
    Valida il valore di {taste: ...}: un nome di accordo (o più, separati da
    spazi/virgole) più le eventuali opzioni tastiera start= / octave=.
    Ogni nome di accordo deve essere riconosciuto.
    """
    tokens = [t for t in re.split(r'[\s,]+', cmd_value.strip()) if t]
    kbd_opts_seen = set()
    for token in tokens:
        # Opzioni tastiera (start=, octave=): validate e non trattare come accordo
        if _validate_kbd_option(token, line_num, col, result,
                                kbd_opts_seen, "{taste}"):
            continue
        if _parse_chord_semitones(token) is None:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_("{taste}: unrecognized chord '%s'") % token,
                severity=SEVERITY_WARNING
            ))


def _validate_fingering(cmd_value: str, line_num: int, col: int,
                        result: SyntaxCheckResult):
    """
    Valida il valore di {fingering: ...}.

    Controlli:
    1. Il primo token deve essere un accordo riconosciuto.
    2. I token successivi devono avere il formato  N=NomeNota  (N intero 1-5)
       oppure  hand=R  /  hand=L  (indicazione di mano, opzionale).
    3. Ogni nota indicata deve appartenere all'accordo specificato.
    4. Lo stesso dito non può essere assegnato due volte.
    5. La stessa nota non può ricevere due dita diverse.
    6. Il token hand= accetta solo i valori R e L (case-insensitive).
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
            message=_("{fingering}: unrecognized chord '%s'") % chord_name,
            severity=SEVERITY_WARNING
        ))
        return   # senza accordo valido non ha senso continuare

    # Parsa le assegnazioni dito=nota (e i token hand=, start=, octave= opzionali)
    used_fingers = {}   # finger_num → nota_str
    used_semitones = {} # semitono → finger_num
    hand_seen = False
    kbd_opts_seen = set()   # per start= / octave= (rileva duplicati)

    for token in parts[1:]:
        # ── Token hand=R / hand=L ────────────────────────────────
        m_hand = re.match(r'^hand=(.+)$', token, re.IGNORECASE)
        if m_hand:
            hand_val = m_hand.group(1).upper()
            if hand_val not in ('R', 'L'):
                result.errors.append(SyntaxError(
                    line=line_num, column=col,
                    message=_(
                        "{fingering}: hand must be R (right) or L (left), got '%s'"
                    ) % m_hand.group(1)
                ))
            elif hand_seen:
                result.errors.append(SyntaxError(
                    line=line_num, column=col,
                    message=_("{fingering}: 'hand' specified more than once")
                ))
            hand_seen = True
            continue

        # ── Opzioni tastiera start= / octave= ────────────────────
        if _validate_kbd_option(token, line_num, col, result,
                                kbd_opts_seen, "{fingering}"):
            continue

        m = re.match(r'^(\d+)=(.+)$', token)
        if not m:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{fingering}: invalid token '%s' — expected format: finger=note (e.g. 2=Mi)"
                ) % token
            ))
            continue

        finger_num = int(m.group(1))
        note_str   = m.group(2)

        # Dito fuori range 1-5
        if finger_num < 1 or finger_num > 5:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{fingering}: finger number %d is out of range (1–5)"
                ) % finger_num
            ))
            continue

        # Nota non riconosciuta
        semi = _note_to_semitone(note_str)
        if semi is None:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{fingering}: unrecognized note '%s'"
                ) % note_str
            ))
            continue

        # Nota non appartiene all'accordo
        if semi not in chord_semitones:
            expected = ', '.join(
                _SEMI_TO_IT[s] for s in sorted(chord_semitones))
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{fingering}: note '%s' does not belong to %s (%s)"
                ) % (note_str, chord_name, expected)
            ))
            continue

        # Dito già usato
        if finger_num in used_fingers:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{fingering}: finger %d assigned twice (%s and %s)"
                ) % (finger_num, used_fingers[finger_num], note_str)
            ))
            continue

        # Nota già assegnata a un altro dito
        if semi in used_semitones:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{fingering}: note '%s' assigned to both finger %d and finger %d"
                ) % (note_str, used_semitones[semi], finger_num)
            ))
            continue

        used_fingers[finger_num]  = note_str
        used_semitones[semi]      = finger_num



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

    # Passata multi-riga: coerenza {beats_time:} ↔ riga di accordi.
    _check_beats_time_coherence(lines, result)

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
                else:
                    _check_chord_name(content, line_num, i + 1, result)
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


def _validate_image_options(opts_str: str, line_num: int, col: int,
                            result: SyntaxCheckResult):
    """Valida le opzioni della direttiva {image:} che seguono il path o il token base64.

    Opzioni valide: width=N[%], height=N[%], scale=N%, align=left|center|right,
                    border[=N], e le parole chiave bare left/center/right/border.
    Segnala errore per chiavi sconosciute o valori non numerici.
    """
    import re as _re
    if not opts_str:
        return
    _VALID_ALIGN = {"left", "center", "right"}
    _VALID_KEYS  = {"width", "height", "scale", "align", "border"}
    _BARE_OK     = {"left", "center", "right", "border"}

    for token in opts_str.split():
        if "=" in token:
            key, _sep, val = token.partition("=")
            key = key.strip().lower()
            val = val.strip()
            if key not in _VALID_KEYS:
                result.errors.append(SyntaxError(
                    line=line_num, column=col,
                    message=_("{image}: unknown option '%s'") % token
                ))
            elif key == "align":
                if val.lower() not in _VALID_ALIGN:
                    result.errors.append(SyntaxError(
                        line=line_num, column=col,
                        message=_(
                            "{image}: align must be left, center or right, got '%s'"
                        ) % val
                    ))
            elif key in ("width", "height", "scale", "border"):
                num = val.rstrip("%")
                try:
                    float(num)
                except ValueError:
                    result.errors.append(SyntaxError(
                        line=line_num, column=col,
                        message=_(
                            "{image}: option '%s' requires a numeric value, got '%s'"
                        ) % (key, val)
                    ))
        else:
            if token.lower() not in _BARE_OK:
                result.errors.append(SyntaxError(
                    line=line_num, column=col,
                    message=_("{image}: unknown option '%s'") % token
                ))


def _validate_duration(cmd_value: str, line_num: int, col: int,
                       result: SyntaxCheckResult):
    """
    Valida il valore di {duration: ...}.

    Formato atteso: durata numerica — mm:ss oppure hh:mm:ss.
      - Tutti i segmenti devono essere numeri interi (0-99).
      - I secondi devono essere 0-59.
      - Sono accettati anche valori senza separatori come '180' (secondi).
    Vengono segnalati come errore:
      - Placeholder letterali come 'mm:ss' o 'hh:mm:ss'.
      - Valori che sembrano token ACCORDO=N (appartengono a {beats_time:}).
      - Qualsiasi formato non riconoscibile.
    """
    import re as _re
    val = cmd_value.strip()
    if not val:
        return

    # Errore: sembra una lista di token ACCORDO=N → suggerisci {beats_time:}
    if _re.fullmatch(r'([A-Za-z][A-Za-z0-9#b\-]*=\d+\s*)+', val):
        result.errors.append(SyntaxError(
            line=line_num, column=col,
            message=_(
                "{duration}: value looks like chord beats (e.g. 'Do=2 Sol=1') — "
                "use {beats_time:} for per-chord beat counts; "
                "{duration:} is for song duration (e.g. '3:45')"
            )
        ))
        return

    # Errore: placeholder letterale mm:ss / hh:mm:ss (non compilato)
    if _re.fullmatch(r'[hmHMS:]+', val) and not _re.search(r'\d', val):
        result.errors.append(SyntaxError(
            line=line_num, column=col,
            message=_(
                "{duration}: '%s' looks like an unfilled placeholder — "
                "use a real duration value (e.g. '3:45' or '1:02:30')"
            ) % val
        ))
        return

    # Formato valido: solo cifre (secondi totali), mm:ss, hh:mm:ss
    if _re.fullmatch(r'\d+', val):
        return   # secondi interi — ok

    m = _re.fullmatch(r'(\d{1,2}):(\d{2})', val)
    if m:
        if int(m.group(2)) > 59:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{duration}: seconds value '%s' is out of range (0-59)"
                ) % m.group(2)
            ))
        return

    m = _re.fullmatch(r'(\d{1,2}):(\d{2}):(\d{2})', val)
    if m:
        if int(m.group(2)) > 59:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{duration}: minutes value '%s' is out of range (0-59)"
                ) % m.group(2)
            ))
        elif int(m.group(3)) > 59:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{duration}: seconds value '%s' is out of range (0-59)"
                ) % m.group(3)
            ))
        return

    # Nessun formato riconoscibile
    result.errors.append(SyntaxError(
        line=line_num, column=col,
        message=_(
            "{duration}: invalid format '%s' — "
            "expected mm:ss or hh:mm:ss (e.g. '3:45' or '1:02:30')"
        ) % val
    ))


def _validate_beats_time(cmd_value: str, line_num: int, col: int,
                       result: SyntaxCheckResult):
    """
    Valida il valore di {beats_time: ...}.

    Formato atteso: uno o più token nella forma  NomeAccordo=N
      - NomeAccordo  deve essere un nome accordo riconoscibile (IT o EN)
      - N            deve essere un intero >= 1
    """
    parts = cmd_value.strip().split()
    if not parts:
        # Valore vuoto: già gestito da _REQUIRES_VALUE
        return

    for token in parts:
        if '=' not in token:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{beats_time}: invalid token '%s' — expected format: chord=beats (e.g. Sol=2)"
                ) % token
            ))
            continue

        chord_part, _sep, beats_part = token.partition('=')
        chord_part = chord_part.strip()
        beats_part = beats_part.strip()

        # ── Controlla il nome accordo ────────────────────────────
        chord_semitones = _parse_chord_semitones(chord_part)
        if chord_semitones is None:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{beats_time}: unrecognized chord '%s'"
                ) % chord_part
            ))
            continue   # non validare i battiti se l'accordo non è riconosciuto

        # ── Controlla i battiti ──────────────────────────────────
        if not beats_part:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{beats_time}: missing beat count for chord '%s'"
                ) % chord_part
            ))
            continue

        try:
            n = int(beats_part)
            if n < 1:
                raise ValueError
        except ValueError:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{beats_time}: beat count for '%s' must be a positive integer, got '%s'"
                ) % (chord_part, beats_part)
            ))


# ── Coerenza {beats_time:} ↔ riga di accordi ─────────────────────────────────
#
#
# La sequenza di accordi nella direttiva deve coincidere, in numero e ordine,
# con quella degli accordi [..] della riga di testo associata. Le parentesi
# tonde vengono ignorate nel confronto, così '[(Do)]' equivale a '[Do]' e
# '(Do)=2' equivale a 'Do=2'. Il confronto è inoltre insensibile a maiuscole/
# minuscole. In caso di discordanza viene emesso un errore.

# Per emettere un avvertimento anziché un errore, basta cambiare la costante:
_BEATS_TIME_COHERENCE_SEVERITY = SEVERITY_ERROR

_BEATS_TIME_RE = re.compile(r'\{\s*beats_time\s*:([^}]*)\}', re.IGNORECASE)


def _normalize_chord_token(tok: str) -> str:
    """Normalizza un accordo per il confronto: rimuove le parentesi tonde e gli
    spazi, e riduce a minuscolo. '(Do)', 'DO' e 'do' diventano tutti 'do'."""
    return tok.replace('(', '').replace(')', '').strip().lower()


def _is_real_chord_token(name: str) -> bool:
    """True se il contenuto di [..] va considerato un accordo (e non una
    stanghetta '|', 'N.C.', '%', ecc.). Riproduce il criterio di
    _check_chord_name così i due controlli restano coerenti."""
    n = name.strip()
    if not n:
        return False
    if n.lower() in _NON_CHORD_TOKENS:
        return False
    if not re.search(r'[A-Za-z]', n):   # token puramente simbolici: | || % *
        return False
    return True


def _extract_inline_chords(line: str):
    """Estrae, nell'ordine di comparsa, gli accordi [..] di una riga di testo,
    scartando stanghette e token non-accordo. Restituisce i nomi grezzi."""
    chords = []
    for m in re.finditer(r'\[([^\]]*)\]', line):
        content = m.group(1).strip()
        if _is_real_chord_token(content):
            chords.append(content)
    return chords


def _beats_time_chords(value: str):
    """Estrae, nell'ordine di comparsa, i nomi accordo dai token
    'accordo=battiti' del valore di {beats_time:}."""
    names = []
    for token in value.split():
        chord_part = token.partition('=')[0].strip()
        if chord_part:
            names.append(chord_part)
    return names


def _report_beats_time_mismatch(result, line_num, col,
                                bt_chords, text_chords, text_line_no):
    """Compone e registra il messaggio di discordanza più informativo:
    se cambia il numero di accordi lo segnala; se il numero coincide,
    indica la prima posizione che differisce."""
    bt_str  = ' '.join(bt_chords)   if bt_chords   else '—'
    txt_str = ' '.join(text_chords) if text_chords else '—'

    if len(bt_chords) != len(text_chords):
        msg = _(
            "{beats_time}: chord sequence does not match line %d — "
            "{beats_time} lists %d chord(s) [%s] but the line has %d [%s]"
        ) % (text_line_no,
             len(bt_chords), bt_str,
             len(text_chords), txt_str)
    else:
        pos = next(
            (k for k in range(len(bt_chords))
             if _normalize_chord_token(bt_chords[k])
                != _normalize_chord_token(text_chords[k])),
            0)
        msg = _(
            "{beats_time}: chord %d does not match line %d — "
            "{beats_time} has '%s', the text has '%s'  ([%s] vs [%s])"
        ) % (pos + 1, text_line_no,
             bt_chords[pos], text_chords[pos],
             bt_str, txt_str)

    result.errors.append(SyntaxError(
        line=line_num, column=col, message=msg,
        severity=_BEATS_TIME_COHERENCE_SEVERITY))


def _check_beats_time_coherence(lines, result: SyntaxCheckResult):
    """Passata multi-riga: per ogni {beats_time:} confronta la sua sequenza di
    accordi con quella della riga di accordi associata (la prima riga di
    contenuto successiva che contenga almeno un accordo [..]). Le parentesi
    tonde e le maiuscole/minuscole sono ignorate nel confronto.

    Se prima di trovare una riga di accordi si incontra un altro {beats_time:}
    o la fine del testo, la direttiva viene lasciata stare (nessun errore):
    non c'è una "seconda riga" da confrontare."""
    n = len(lines)

    # Righe effettive: rimuovi i commenti inline e marca le righe di commento
    # (None) così da saltarle, coerentemente con check().
    effective = []
    for raw in lines:
        if raw.lstrip().startswith('#'):
            effective.append(None)
        else:
            effective.append(_strip_inline_comment(raw))

    for idx in range(n):
        eff = effective[idx]
        if eff is None:
            continue
        m = _BEATS_TIME_RE.search(eff)
        if not m:
            continue

        bt_chords = _beats_time_chords(m.group(1))
        if not bt_chords:
            continue   # valore vuoto/malformato: già gestito da _validate_beats_time

        # Cerca la riga di accordi associata.
        text_idx = None
        for j in range(idx + 1, n):
            ej = effective[j]
            if ej is None or ej.strip() == '':
                continue
            if _BEATS_TIME_RE.search(ej):
                break   # nuovo gruppo beats_time: la corrente non ha riga di accordi
            if _extract_inline_chords(ej):
                text_idx = j
                break
            # riga di contenuto senza accordi (lyric semplice, altra direttiva):
            # continua a cercare la vera riga di accordi

        if text_idx is None:
            continue   # nessuna riga di accordi da confrontare: non segnalare

        text_chords = _extract_inline_chords(effective[text_idx])

        bt_norm  = [_normalize_chord_token(c) for c in bt_chords]
        txt_norm = [_normalize_chord_token(c) for c in text_chords]
        if bt_norm == txt_norm:
            continue   # coerenti

        _report_beats_time_mismatch(
            result, idx + 1, m.start() + 1,
            bt_chords, text_chords, text_idx + 1)


def _validate_command(content: str, line_num: int, col: int,
                      result: SyntaxCheckResult):
    if not content:
        result.errors.append(SyntaxError(
            line=line_num, column=col,
            message=_("Empty command (write the command name without a colon, e.g. '{soc}')")
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
        "artist", "composer", "lyricist", "arranger",
        "album", "year", "copyright",
        "key", "capo",
        "beats_time", "ccli",
        "duration",
        "tempo", "tempo_m", "tempo_s", "tempo_sp", "tempo_c", "tempo_cp",
        "tempo_label",
        "time",
        "define", "taste", "fingering",
        "image",
        # Metadati estesi: richiedono un valore (non ha senso scriverli vuoti)
        "sorttitle", "keywords", "topic", "collection", "language",
        "meta",
        # Watermark S++: porta sempre la config (text=...; ...)
        "watermark",
    }

    _OPTIONAL_VALUE = {
        # Formattazione testo/accordo: senza valore = reset al default
        "textsize", "textfont", "textcolour", "textcolor",
        "chordsize", "chordfont", "chordcolour", "chordcolor",
        "textbold", "textitalic", "textunderline",
        "chordbold", "chorditalic", "chordunderline",
        "linespacing", "chordtopspacing",
        # Sezioni con etichetta opzionale
        "start_of_verse", "end_of_verse", "sov", "eov",
        "start_of_chorus", "end_of_chorus", "soc", "eoc",
        "start_of_bridge", "end_of_bridge", "sob", "eob",
        "start_of_tab",    "sot",
        "start_of_grid",   "sog", "grid",
        "start_of_part",   "end_of_part", "sop", "eop",
        "start_verse",     "start_verse_num",
        "start_chorus",    "start_bridge",
        "verse",
        # Metadati opzionali
        "pagetype", "columns", "transpose",
    }

    _REQUIRES_NUMERIC_VALUE = {
        "textsize", "chordsize",
        "textbold", "textitalic", "textunderline",
        "chordbold", "chorditalic", "chordunderline",
        "linespacing", "chordtopspacing",
        "capo",
        "tempo", "tempo_m", "tempo_s", "tempo_sp", "tempo_c", "tempo_cp",
        "columns",
        "transpose",
    }

    _REQUIRES_TIME_SIGNATURE = {"time"}

    # Comandi che richiedono obbligatoriamente i due punti (con o senza valore).
    # Scrivere {verse} senza ':' è un errore; le forme corrette sono
    # {verse:} oppure {verse: etichetta}.
    _REQUIRES_COLON = {"verse"}

    if cmd_name not in _KNOWN_COMMANDS:
        result.errors.append(SyntaxError(
            line=line_num, column=col,
            message=_("Unknown command: '{%s}'") % cmd_name
        ))
        return

    if cmd_name in _REQUIRES_COLON and cmd_value is None:
        result.errors.append(SyntaxError(
            line=line_num, column=col,
            message=_(
                "Command '{%s}' requires ':'; use '{%s:}' or '{%s: label}'"
            ) % (cmd_name, cmd_name, cmd_name)
        ))
        return

    if cmd_value is not None and cmd_value == "" and cmd_name not in _OPTIONAL_VALUE and cmd_name not in _REQUIRES_VALUE:
        result.errors.append(SyntaxError(
            line=line_num, column=col,
            message=_("Command '{%s:}' has ':' but no value; use '{%s}' to reset") % (
                cmd_name,
                cmd_name,
            )
        ))
        return

    if cmd_name in _REQUIRES_TIME_SIGNATURE and cmd_value is not None and cmd_value != "":
        import re as _re
        if not _re.fullmatch(r'[1-9][0-9]*/[1-9][0-9]*', cmd_value.strip()):
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_("Command '{%s:}' requires a time signature (e.g. 4/4), got: '%s'") % (
                    cmd_name,
                    cmd_value,
                )
            ))
            return

    if cmd_name in _REQUIRES_NUMERIC_VALUE and cmd_value is not None and cmd_value != "":
        # {tempo: N,M}
        # N = BPM
        # M = display mode (-1, 0, 1, 2, 3)

        value_to_check = cmd_value

        # ── {linespacing: N} oppure {linespacing: N rel} ──────────────
        # 'rel' = i beats_time non aggiungono altezza al passo di riga.
        if cmd_name == "linespacing" and cmd_value.strip():
            toks = cmd_value.split()
            ok = False
            try:
                float(toks[0])
                extra = toks[1:]
                ok = (len(extra) == 0) or (
                    len(extra) == 1 and extra[0].lower() == "rel")
            except (ValueError, IndexError):
                ok = False
            if not ok:
                result.errors.append(SyntaxError(
                    line=line_num, column=col,
                    message=_(
                        "Command '{linespacing:}' requires N or 'N rel', got: '%s'"
                    ) % cmd_value
                ))
                return
            value_to_check = None   # già validato: salta il controllo numerico generico

        if cmd_name == "tempo" and ',' in cmd_value:

            bpm_part, sep, mode_part = cmd_value.partition(',')

            bpm_part = bpm_part.strip()
            mode_part = mode_part.strip()

            # ── Validazione BPM ─────────────────────────────
            try:
                float(bpm_part)

            except ValueError:
                result.errors.append(SyntaxError(
                    line=line_num,
                    column=col,
                    message=_(
                        "Command '{%s:}' requires a numeric BPM value before the comma, got: '%s'"
                    ) % (
                        cmd_name,
                        bpm_part,
                    )
                ))
                return

            # ── Validazione display mode ───────────────────
            try:
                mode_int = int(mode_part)

                if mode_int not in (-1, 0, 1, 2, 3):
                    raise ValueError

            except ValueError:
                result.errors.append(SyntaxError(
                    line=line_num,
                    column=col,
                    message=_(
                        "Command '{%s:}': display mode must be -1, 0, 1, 2 or 3, got: '%s'"
                    ) % (
                        cmd_name,
                        mode_part,
                    )
                ))
                return

            # tutto valido
            value_to_check = None

        # ── Validazione numerica standard ─────────────────
        if value_to_check is not None:

            try:
                float(value_to_check)

            except ValueError:
                result.errors.append(SyntaxError(
                    line=line_num,
                    column=col,
                    message=_(
                        "Command '{%s:}' requires a numeric value, got: '%s'"
                    ) % (
                        cmd_name,
                        cmd_value,
                    )
                ))
                return

    if cmd_name in _REQUIRES_VALUE:
        if cmd_value is None or cmd_value == "":
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_("Command '{%s:}' requires a value") % cmd_name
            ))
            return

    # ── Validazione specifica per {image:} ──────────────────────
    # Il valore di {image:} può essere:
    #   1. Un percorso file (relativo o assoluto, con o senza virgolette)
    #   2. Un data: URI base64 con opzioni facoltative dopo il token:
    #      data:<mime>;base64,<dati> [width=N] [height=N] [scale=N%]
    #      [align=left|center|right] [border[=N]]
    if cmd_name == "image" and cmd_value:
        stripped = cmd_value.strip()
        if stripped.startswith("data:"):
            # Estrai solo il token base64 (il primo token prima del primo spazio)
            data_token = stripped.split()[0] if " " in stripped else stripped
            if ";" not in data_token or "base64," not in data_token:
                result.errors.append(SyntaxError(
                    line=line_num, column=col,
                    message=_(
                        "{image}: malformed embedded data URI "
                        "(expected 'data:<mime>;base64,<data>')"
                    )
                ))
            else:
                # Valida le opzioni che seguono il token base64
                _validate_image_options(
                    stripped[len(data_token):].strip(),
                    line_num, col, result
                )
            return   # non applicare ulteriori controlli sul valore
        else:
            # Percorso file: valida le eventuali opzioni (tutto dopo il path)
            # Il path può essere tra virgolette o no
            import shlex as _shlex
            try:
                lex = _shlex.shlex(stripped, posix=False)
                lex.whitespace_split = True
                lex.whitespace = " \t"
                raw = list(lex)
            except ValueError:
                raw = stripped.split()
            if len(raw) > 1:
                _validate_image_options(
                    " ".join(raw[1:]), line_num, col, result
                )

    # ── Validazione specifica per {fingering:} ────────────────────
    if cmd_name == "fingering" and cmd_value:
        _validate_fingering(cmd_value, line_num, col, result)

    # ── Validazione specifica per {taste:} ────────────────────────
    if cmd_name == "taste" and cmd_value:
        _validate_taste(cmd_value, line_num, col, result)

    # ── Validazione specifica per {beats_time:} ─────────────────
    if cmd_name == "beats_time" and cmd_value:
        _validate_beats_time(cmd_value, line_num, col, result)

    # ── Validazione specifica per {duration:} ────────────────────
    if cmd_name == "duration" and cmd_value:
        _validate_duration(cmd_value, line_num, col, result)

    # ── Validazione specifica per {meta:} ─────────────────────────
    # Il formato atteso è:  {meta: chiave valore}  (almeno due token)
    if cmd_name == "meta" and cmd_value:
        parts = cmd_value.strip().split()
        if len(parts) < 2:
            result.errors.append(SyntaxError(
                line=line_num, column=col,
                message=_(
                    "{meta} requires 'key value' format, got: '%s'"
                ) % cmd_value
            ))

    # ── Controllo: {bar} e {row}/{r} non accettano valori ─────────
    if cmd_name in ("bar", "row", "r") and cmd_value is not None:
        result.errors.append(SyntaxError(
            line=line_num, column=col,
            message=_(
                "Command '{%s}' does not accept a value"
            ) % cmd_name
        ))
