###############################################################
# Name:         ChordProDirectives.py
# Purpose:      Dati delle direttive ChordPro / Songpress++ per
#               l'intellisense dell'editor.
# Author:       Denisov21
# Created:      2026
# Copyright:    Modifications © 2026 Denisov21
# License:      GNU GPL v2
###############################################################
#
# Questo modulo è l'unico punto in cui aggiungere, rimuovere o
# riclassificare direttive per il popup intellisense.
#
# Classificazione icone nel popup:
#   ✅  CHORDPRO    – direttiva ufficiale (chordpro.org/chordpro/chordpro-directives/)
#   🔧  SPPLUSPLUS  – direttiva esclusiva Songpress++
###############################################################


# ── Direttive senza valore ────────────────────────────────────────────────────
# Queste direttive vengono chiuse con '}' direttamente, senza inserire ':|}'.
DIRECTIVES_NO_VALUE = {
    'end_of_chorus', 'end_of_verse', 'end_of_bridge',
    'end_of_tab', 'end_of_grid', 'end_verse', 'end_verse_num',
    'end_chord', 'new_page', 'column_break',
    'end_of_part', 'row', 'bar',
    'eoc', 'eov', 'eob', 'eot', 'np', 'eop',
    'new_song',
}


# ── Direttive esclusive Songpress++ ──────────────────────────────────────────
# Usato per assegnare l'icona 🔧 nel popup intellisense.
SPPLUSPLUS_DIRECTIVES = {
    # Metadati estesi non ufficiali
    'beats_time',                              # S++ – battiti per accordo
    'ccli',                                    # S++ – codice CCLI (non in spec)
    'arranger',                                # S++ – non in spec ufficiale
    'keywords', 'topic', 'collection',        # S++ – non in spec ufficiale
    'language',                                # S++ – non in spec ufficiale
    'watermark',                               # S++ – filigrana per-documento
    # Varianti tempo proprietarie
    'tempo_label',                             # S++ – indicazione agogica
    'tempo_m', 'tempo_s', 'tempo_sp',
    'tempo_c', 'tempo_cp',
    # Struttura proprietaria
    'start_of_part', 'end_of_part',           # S++ – non in spec
    'start_verse', 'end_verse',               # S++ – non in spec
    'start_verse_num', 'end_verse_num',       # S++ – non in spec
    'start_chord', 'end_chord',               # S++ – non in spec
    'row', 'bar',                             # S++ – non in spec
    'sop', 'eop',                             # S++ – alias non ufficiali
    # Formattazione proprietaria
    'linespacing', 'chordtopspacing',         # S++ – non in spec
    'chordbold', 'chorditalic', 'chordunderline',   # S++ – stile accordo
    'textbold', 'textitalic', 'textunderline',      # S++ – stile testo
    # Diagrammi/tastiera proprietari
    'taste', 'fingering',                     # S++ – estensioni S++
}


# ── Lista completa direttive mostrate nell'intellisense ───────────────────────
# La classificazione ✅/🔧 è derivata dalla specifica ufficiale:
# https://www.chordpro.org/chordpro/chordpro-directives/
DIRECTIVES = [
    # ── Metadati ufficiali ChordPro ✅ ────────────────────────────────────────
    'title', 'subtitle', 'artist', 'composer', 'lyricist',
    'copyright', 'album', 'year', 'key', 'time', 'tempo', 'capo',
    'duration', 'sorttitle', 'meta',
    # ── Metadati estesi ✅ (ChordPro 6) ──────────────────────────────────────
    'pagetype', 'columns',
    # ── Metadati Songpress++ 🔧 ───────────────────────────────────────────────
    'arranger',                                        # non in spec
    'beats_time',                                      # S++ esclusivo
    'ccli',                                            # non in spec
    'keywords', 'topic', 'collection', 'language',    # non in spec
    'watermark',                                       # S++ – filigrana per-documento
    'tempo_m', 'tempo_s', 'tempo_sp', 'tempo_c', 'tempo_cp',
    'tempo_label',                                     # S++ – indicazione agogica
    # ── Struttura ufficiale ChordPro ✅ ───────────────────────────────────────
    'start_of_chorus', 'end_of_chorus',
    'start_of_verse', 'end_of_verse',
    'start_of_bridge', 'end_of_bridge',
    'start_of_tab', 'end_of_tab',
    'start_of_grid', 'end_of_grid',
    'new_page', 'column_break',
    'new_song',
    # ── Struttura Songpress++ 🔧 ──────────────────────────────────────────────
    'start_of_part', 'end_of_part',
    'start_verse', 'end_verse',
    'start_verse_num', 'end_verse_num',
    'start_chord', 'end_chord',
    'row', 'bar',
    # ── Formattazione ufficiale ChordPro ✅ ───────────────────────────────────
    'comment', 'comment_italic', 'comment_box',
    'image',
    'textfont', 'textsize', 'textcolour',
    'chordfont', 'chordsize', 'chordcolour',
    'transpose',
    # ── Formattazione Songpress++ 🔧 ──────────────────────────────────────────
    'linespacing', 'chordtopspacing',
    'chordbold', 'chorditalic', 'chordunderline',
    'textbold', 'textitalic', 'textunderline',
    # ── Alias ufficiali ChordPro ✅ ───────────────────────────────────────────
    't', 'st', 'c', 'ci', 'cb', 'np',
    'soc', 'eoc', 'sov', 'eov', 'sob', 'eob', 'sot', 'eot',
    # ── Alias Songpress++ 🔧 ──────────────────────────────────────────────────
    'sop', 'eop',
    # ── Diagrammi/accordi ufficiali ChordPro ✅ ───────────────────────────────
    'define',
    # ── Diagrammi/tastiera Songpress++ 🔧 ────────────────────────────────────
    'taste', 'fingering',
]


# ── Opzioni delle direttive (completamento dentro una direttiva già scritta) ──
# Se il cursore è dentro una direttiva con argomenti, es. "{taste:SOL start=SI |}",
# Ctrl+Space propone le opzioni ancora mancanti (middlec=, octave=, ...).
#
# Formato: direttiva -> lista di (opzione, valori)
#   valori = None   -> opzione "flag", senza '=' (es. "rel", "border")
#   valori = []     -> richiede '=' con un valore libero (es. "start=")
#   valori = [...]  -> richiede '=' con uno dei valori elencati
_KEYBOARD_OPTIONS = [
    ('start',   []),
    ('octave',  ['both', 'one', 'single', 'first']),
    ('hand',    ['R', 'L']),
    ('middlec', ['show', 'hide', 'on', 'off', 'yes', 'no', '1', '0']),
]

DIRECTIVE_OPTIONS = {
    'taste':     _KEYBOARD_OPTIONS,
    'fingering': _KEYBOARD_OPTIONS,
    'start_of_grid': [
        ('size',            []),
        ('chordtopspacing', []),
        ('linespacing',     []),
        ('sizedir',         ['horizontal', 'vertical', 'both']),
    ],
    'image': [
        ('width',  []),
        ('height', []),
        ('scale',  []),
        ('align',  ['left', 'center', 'right']),
        ('border', []),
        ('left',   None),
        ('center', None),
        ('right',  None),
    ],
    'linespacing': [
        ('rel', None),
    ],
}

# alias -> direttiva canonica per DIRECTIVE_OPTIONS
OPTION_ALIASES = {
    'sog': 'start_of_grid',
    'grid': 'start_of_grid',
}


def _option_spec(directive):
    key = (directive or '').strip().lower()
    key = OPTION_ALIASES.get(key, key)
    return DIRECTIVE_OPTIONS.get(key)


def option_values(directive, option):
    """Elenco dei valori proposti per `option` di `directive` ([] se nessuno)."""
    spec = _option_spec(directive)
    if not spec:
        return []
    opt = (option or '').strip().lower()
    for name, values in spec:
        if name == opt:
            return list(values or [])
    return []


def directive_context(text_before, text_after=''):
    """Analizza la posizione del cursore dentro una direttiva già scritta.

    text_before : testo della riga dall'inizio fino al cursore
    text_after  : testo della riga dal cursore alla fine

    Ritorna None se il cursore non è negli argomenti di una direttiva
    (ad es. si sta ancora digitando il nome: vale la lista delle direttive).
    Altrimenti un dizionario:
        kind      'option' | 'value' | 'none'
        directive nome della direttiva (minuscolo)
        option    opzione di cui si propongono i valori (solo kind 'value')
        prefix    parte già digitata, da sostituire (len = typed_len)
        items     voci da mostrare nel popup (vuoto se kind 'none')
    """
    import re
    brace = text_before.rfind('{')
    if brace == -1 or '}' in text_before[brace + 1:]:
        return None
    inner = text_before[brace + 1:]
    m = re.match(r'\s*([A-Za-z_]+)[:\s]', inner)
    if not m:
        return None                       # nome ancora in digitazione
    name = m.group(1).lower()
    spec = _option_spec(name)
    ctx = {'kind': 'none', 'directive': name, 'option': '', 'prefix': '', 'items': []}
    if not spec:
        return ctx

    args = inner[m.end() - 1:]            # include il separatore (':' o spazio)
    args = args[1:] if args[:1] == ':' else args
    before_tokens = re.split(r'\s+', args)
    current = before_tokens[-1]
    done = before_tokens[:-1]

    # token a destra del cursore (fino a '}'); il primo è la continuazione
    # del token corrente se il cursore non è subito prima di uno spazio
    rest = (text_after or '').split('}')[0]
    after_tokens = rest.split()
    if current and rest and not rest[0].isspace() and after_tokens:
        after_tokens = after_tokens[1:]

    present = set()
    for tok in done + after_tokens:
        present.add(tok.split('=')[0].strip().lower())

    if '=' in current:
        opt, _sep, valprefix = current.partition('=')
        values = option_values(name, opt)
        items = [v for v in values if v.lower().startswith(valprefix.lower())]
        if items:
            ctx.update(kind='value', option=opt.lower(), prefix=valprefix, items=items)
        return ctx

    low = current.lower()
    items = []
    for opt, values in spec:
        if not opt.startswith(low) or opt in present:
            continue
        items.append(opt if values is None else opt + '=')
    if items:
        ctx.update(kind='option', prefix=current, items=items)
    return ctx
