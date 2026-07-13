###############################################################
# Name:        chordpro_import.py
# Purpose:     Convert text with chords glued to lyrics into ChordPro
#              (i.e. wrap chord names in square brackets)
# Author:      Denisov21
# License:     GNU GPL v2
##############################################################

"""Conversione "accordi attaccati al testo" -> ChordPro.

    LAProtegga il nostro popoSOLlo   ->   [LA]Protegga il nostro popo[SOL]lo

Il modulo NON dipende da wx: è puro Python e quindi testabile a parte.
L'unica dipendenza è ``Transpose.translateChord``, usata per ricavare i nomi
delle note nella notazione corrente (invece di duplicare le tabelle).

Uso tipico dal frame::

    from .chordpro_import import get_roots, bracket_text, default_aggressive

    notation = self.pref.notations[0]
    roots = get_roots(notation, self.pref.notations)
    new_text = bracket_text(old_text, roots)

COME DISTINGUE ACCORDO DA TESTO
  1. preceduto da minuscola             -> accordo dentro la parola  popo[SOL]lo
  2. inizio parola + MAIUSCOLA dopo     -> accordo                   [SOL]Fa che
  3. inizio parola + minuscola dopo     -> dipende da `aggressive`:
        - notazioni con radici tutte maiuscole e lunghe >= 2 (DO RE MI...):
          accettato, perché "REtuoi" non è una parola italiana
        - notazioni a lettera singola (C D E, A B C) o capitalizzate
          (Do Re Mi): rifiutato per default, altrimenti "Fai" diventerebbe
          [F]ai / [Fa]i
  4. righe di soli accordi              -> racchiuse per intero      [RE] [SOL] [LA]
  5. direttive {...}, commenti #, e testo già tra [ ] -> lasciati intatti
"""

import re

try:                                    # in Songpress++
    from .Transpose import translateChord
except ImportError:                     # uso standalone / test
    translateChord = None


# ---------------------------------------------------------------- radici

#: Nomi delle note nella notazione italiana capitalizzata, usati come sorgente
#: per la traduzione verso la notazione corrente.
IT_BASE = ['Do', 'Re', 'Mi', 'Fa', 'Sol', 'La', 'Si']

#: Fallback usato solo se ``translateChord`` non è disponibile o fallisce.
FALLBACK_ROOTS = {
    'en': ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
    'it': IT_BASE,
    'ituc': [n.upper() for n in IT_BASE],
    'de': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'],
}


def _italian_notation(notations):
    """Restituisce la notazione italiana capitalizzata (sorgente di IT_BASE).

    L'elenco ``pref.notations`` viene riordinato in base alla notazione
    predefinita, quindi non ci si può fidare della posizione: si cerca per id.
    """
    candidates = [n for n in notations if getattr(n, 'id', None)]
    for n in candidates:                       # prima l'id esattamente 'it'
        if n.id.lower() == 'it':
            return n
    for n in candidates:                       # poi qualunque id italiano
        if n.id.lower().startswith('it'):
            return n
    return None


def get_roots(notation, notations):
    """Nomi delle 7 note nella notazione ``notation``, dalla più lunga alla più
    corta (indispensabile: SOL va provata prima di SI)."""
    roots = None
    it = _italian_notation(notations)

    if translateChord is not None and it is not None:
        try:
            roots = [translateChord(n, it, notation) for n in IT_BASE]
        except Exception:
            roots = None

    if not roots:
        key = (getattr(notation, 'id', '') or '').lower()
        roots = FALLBACK_ROOTS.get(key) or FALLBACK_ROOTS['en']

    roots = [r for r in dict.fromkeys(roots) if r]      # dedup, ordine stabile
    roots.sort(key=len, reverse=True)
    return roots


def default_aggressive(roots):
    """True per le notazioni in cui una radice a inizio parola seguita da
    minuscola è quasi certamente un accordo (DO RE MI... maiuscole)."""
    return all(len(r) >= 2 and r.isupper() for r in roots)


# ---------------------------------------------------------------- regex

# Alterazione: la 'b' vale come bemolle solo se non seguita da altre minuscole,
# altrimenti "LAbella" -> LAb + "ella".
_ACC = r"(?:#|\u266f|b(?![a-z])|\u266d)?"

# Qualità: le lettere sono protette dal lookahead per non mangiare la parola
# successiva ("LAmore" -> [LA]more, non [LAm]ore).
_QUAL = (r"(?:-|min(?![a-z])|maj(?![a-z])|dim(?![a-z])|aug(?![a-z])"
         r"|m(?![a-z])|M(?![a-z])|\u00b0|\+)?")

# Estensioni e sospensioni
_EXT = r"(?:sus(?![a-z])|add(?![a-z]))?\d*"

BRACKETED_RE = re.compile(r"\[[^\]]*\]")
DIRECTIVE_RE = re.compile(r"^\s*\{.*\}\s*$")


def build_chord_re(roots):
    """Compila la regex degli accordi per le radici date."""
    root = r"(?:" + "|".join(re.escape(r) for r in roots) + r")"
    bass = r"(?:/" + root + r"(?:#|b(?![a-z]))?)?"
    return re.compile(root + _ACC + _QUAL + _EXT + bass)


# ---------------------------------------------------------------- logica

def _accept(seg, start, end, aggressive):
    before = seg[start - 1] if start > 0 else ''
    after = seg[end] if end < len(seg) else ''

    if before.isalpha():
        return before.islower()     # dentro la parola sì; dentro un ALLCAPS no
    if not after.isalpha():
        return False                # token isolato: lo gestisce _is_chord_only_line
    if after.isupper():
        return True                 # [LA]Protegga
    return aggressive               # [RE]tuoi


def _bracket_segment(seg, chord_re, aggressive):
    out, pos = [], 0
    for m in chord_re.finditer(seg):
        if not _accept(seg, m.start(), m.end(), aggressive):
            continue
        out.append(seg[pos:m.start()])
        out.append('[' + m.group(0) + ']')
        pos = m.end()
    out.append(seg[pos:])
    return ''.join(out)


def _is_chord_only_line(line, chord_re):
    tokens = line.split()
    return bool(tokens) and all(chord_re.fullmatch(t) for t in tokens)


def bracket_line(line, chord_re, aggressive):
    if DIRECTIVE_RE.match(line) or line.lstrip().startswith('#'):
        return line

    if '[' not in line and _is_chord_only_line(line, chord_re):
        return re.sub(r'\S+', lambda m: '[' + m.group(0) + ']', line)

    out, pos = [], 0
    for skip in BRACKETED_RE.finditer(line):     # salta ciò che è già tra [ ]
        out.append(_bracket_segment(line[pos:skip.start()], chord_re, aggressive))
        out.append(skip.group(0))
        pos = skip.end()
    out.append(_bracket_segment(line[pos:], chord_re, aggressive))
    return ''.join(out)


def bracket_text(text, roots, aggressive=None):
    """Racchiude tra [ ] gli accordi di ``text``. Restituisce il nuovo testo."""
    chord_re = build_chord_re(roots)
    if aggressive is None:
        aggressive = default_aggressive(roots)
    return '\n'.join(bracket_line(l, chord_re, aggressive)
                     for l in text.split('\n'))


def unbracket_text(text):
    """Operazione inversa: toglie le [ ] agli accordi, lasciando le direttive."""
    return '\n'.join(
        line if DIRECTIVE_RE.match(line)
        else BRACKETED_RE.sub(lambda m: m.group(0)[1:-1], line)
        for line in text.split('\n')
    )


def count_chords(text):
    """Quanti accordi risultano racchiusi tra [ ] (per la status bar)."""
    return sum(1 for _ in BRACKETED_RE.finditer(text))


# ---------------------------------------------------------------- esito

#: Codici di esito restituiti da :func:`convert`.
OK = 'ok'                       # conversione riuscita, almeno un accordo aggiunto
EMPTY = 'empty'                 # testo vuoto o solo spazi
ALREADY_CHORDPRO = 'already'    # il testo ha già accordi tra [ ] e non c'è altro da fare
NO_CHORDS = 'no_chords'         # nessun accordo attaccato riconosciuto
NO_NOTATION = 'no_notation'     # notazione non disponibile / radici non ricavabili


class ConversionResult(object):
    """Esito della conversione.

    Attributi:
        status   uno dei codici sopra
        text     testo convertito (== originale se nulla è cambiato)
        added    quanti accordi sono stati racchiusi da questa conversione
        existing quanti accordi erano già tra [ ] prima della conversione
        roots    radici usate (utile per i messaggi diagnostici)
    """

    def __init__(self, status, text, added=0, existing=0, roots=None):
        self.status = status
        self.text = text
        self.added = added
        self.existing = existing
        self.roots = roots or []

    @property
    def changed(self):
        return self.status == OK

    def __repr__(self):
        return ('<ConversionResult %s added=%d existing=%d>'
                % (self.status, self.added, self.existing))


def convert(text, roots, aggressive=None):
    """Converte ``text`` in ChordPro restituendo un :class:`ConversionResult`.

    Non solleva eccezioni per i casi previsti (testo vuoto, nessun accordo,
    testo già convertito): li segnala tramite ``status``. Solleva invece
    ``ValueError`` se ``roots`` è vuoto, perché è un errore di programmazione
    del chiamante (notazione non risolta).
    """
    if not roots:
        raise ValueError('nessuna radice di accordo disponibile per la notazione')

    if not text or not text.strip():
        return ConversionResult(EMPTY, text, roots=roots)

    existing = count_chords(text)
    new_text = bracket_text(text, roots, aggressive)
    added = count_chords(new_text) - existing

    if added > 0:
        return ConversionResult(OK, new_text, added, existing, roots)

    status = ALREADY_CHORDPRO if existing else NO_CHORDS
    return ConversionResult(status, text, 0, existing, roots)
