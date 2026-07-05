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
