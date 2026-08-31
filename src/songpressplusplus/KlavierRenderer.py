###############################################################
# Name:         KlavierRenderer.py
# Purpose:      Draw piano keyboard diagrams for chords
# Author:       Denisov21
# Created:      2026-03-12
# Copyright:    Denisov21
# License:      GNU GPL v2
###############################################################


import wx
import re

try:
    from .Transpose import translateChord
    _has_transpose = True
except ImportError:
    _has_transpose = False

# Note italiane -> semitono (ordinate per lunghezza decrescente per match corretto)
_ITALIAN_NOTES = [
    ('sol#', 8), ('solb', 6), ('sol', 7),
    ('do#', 1),  ('dob', 11), ('do', 0),
    ('re#', 3),  ('reb', 1),  ('re', 2),
    ('mi#', 5),  ('mib', 3),  ('mi', 4),
    ('fa#', 6),  ('fab', 4),  ('fa', 5),
    ('la#', 10), ('lab', 8),  ('la', 9),
    ('si#', 0),  ('sib', 10), ('si', 11),
]

# Note inglesi -> semitono
_ENGLISH_NOTES = [
    ('c#', 1), ('cb', 11), ('c', 0),
    ('d#', 3), ('db', 1),  ('d', 2),
    ('e#', 5), ('eb', 3),  ('e', 4),
    ('f#', 6), ('fb', 4),  ('f', 5),
    ('g#', 8), ('gb', 6),  ('g', 7),
    ('a#', 10), ('ab', 8), ('a', 9),
    ('b#', 0), ('bb', 10), ('b', 11),
    ('h', 11),
]

# Suffissi accordo -> intervalli (ordinati per lunghezza decrescente)
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

# Tasti bianchi nell'ottava (semitoni), ordinati DO RE MI FA SOL LA SI
_WHITE_KEYS = [0, 2, 4, 5, 7, 9, 11]
# Tasti neri: semitono -> indice spazio tra i bianchi (layout di default da DO)
_BLACK_KEYS = {1: 0, 3: 1, 6: 3, 8: 4, 10: 5}


def _keyboard_layout(start_semi):
    """
    Costruisce il layout dei tasti di una tastiera che parte dal semitono
    `start_semi` (deve essere un tasto bianco: DO RE MI FA SOL LA SI).

    Restituisce:
        white_order : lista di semitoni bianchi, da sinistra a destra
        black_map   : dict {semitono_nero: indice_gap} dei neri visibili

    Di norma la tastiera ha 7 tasti bianchi. Se però la partenza è diversa da
    DO o FA, una finestra di 7 bianchi "taglierebbe" un tasto nero (se ne
    vedrebbero solo 4): in quel caso si aggiunge un OTTAVO tasto bianco in
    fondo — l'ottava della nota iniziale, es. SI...SI — così il nero tagliato
    ricompare e tutte e 12 le note dell'ottava tornano rappresentabili.
    Il tasto nero recuperato si posiziona automaticamente nell'ultimo spazio.
    """
    if start_semi not in _WHITE_KEYS:
        start_semi = 0  # fallback su DO
    idx = _WHITE_KEYS.index(start_semi)
    white_order = _WHITE_KEYS[idx:] + _WHITE_KEYS[:idx]   # 7 bianchi

    def _count_blacks(order):
        return sum(1 for i in range(len(order) - 1)
                   if (order[i + 1] - order[i]) % 12 == 2)

    # Se mancano dei neri (partenza diversa da DO/FA), aggiunge l'ottava in fondo
    if _count_blacks(white_order) < 5:
        white_order = white_order + [white_order[0]]     # 8 bianchi: ...nota iniziale

    black_map = {}
    for gap_idx in range(len(white_order) - 1):           # spazi tra i bianchi
        left = white_order[gap_idx]
        right = white_order[gap_idx + 1]
        if (right - left) % 12 == 2:                      # semitono in mezzo -> nero
            black_map[(left + 1) % 12] = gap_idx
    return white_order, black_map


def parse_chord(chord_str):
    """
    Analizza una stringa accordo (notazione italiana o inglese).
    Restituisce (root_semitone, intervals) o None.
    """
    s = chord_str.strip()
    sl = s.lower()
    root = None
    rest = ''

    # Prova prima notazione italiana
    for note_str, semitone in _ITALIAN_NOTES:
        if sl.startswith(note_str):
            root = semitone
            rest = s[len(note_str):]
            break

    # Se non trovato prova inglese
    if root is None:
        for note_str, semitone in _ENGLISH_NOTES:
            if sl.startswith(note_str):
                root = semitone
                rest = s[len(note_str):]
                break

    if root is None:
        return None

    # Ignora il basso dopo /
    rest = rest.split('/')[0].strip()

    # Il '-' indica "minore" ovunque compaia nella parte estensione:
    # sia in coda ("7-"), sia subito dopo la radice come nella notazione
    # jazz standard ("-7", "-9", "-7b5"...), sia da solo ("-" -> triade
    # minore). Lo rimuoviamo e abbassiamo la terza maggiore (semitono 4)
    # a terza minore (semitono 3), lasciando invariate le altre estensioni.
    is_minor = '-' in rest
    if is_minor:
        rest = rest.replace('-', '', 1)

    intervals = [0, 4, 7]  # default maggiore
    for suffix, ivs in _CHORD_INTERVALS:
        if rest.lower().startswith(suffix.lower()):
            intervals = ivs
            break

    # Se compare una 'm' ovunque nel resto (es. "m7-", "Am-", "7m-", ma
    # anche "maj7-"), il '-' è ridondante o contraddittorio: "m" indica
    # già il minore, "maj" indica esplicitamente il maggiore. In entrambi
    # i casi l'accordo è ambiguo e viene considerato non riconosciuto.
    if is_minor and 'm' in rest.lower():
        return None

    if is_minor:
        intervals = [3 if i == 4 else i for i in intervals]

    return root, intervals


def get_chord_keys(chord_str):
    """Restituisce lista di semitoni (0-11) da evidenziare."""
    result = parse_chord(chord_str)
    if result is None:
        return None
    root, intervals = result
    return [(root + i) % 12 for i in intervals]


def _normalize_chord(chord_str, notations):
    """
    Converte l'accordo dalla notazione corrente verso l'italiano
    usando translateChord, così il parser funziona sempre.
    """
    if not _has_transpose or notations is None:
        return chord_str
    try:
        italian_notation = None
        for n in notations:
            if hasattr(n, 'id') and ('it' in n.id.lower() or 'italian' in n.id.lower()):
                italian_notation = n
                break
        if italian_notation is None:
            return chord_str
        current = notations[0] if notations else None
        if current is None:
            return chord_str
        return translateChord(chord_str, current, italian_notation)
    except Exception:
        return chord_str


def _note_name_to_semitone(note_str):
    """
    Converte un nome di nota (italiano o inglese) in semitono (0-11).
    Restituisce None se non riconosciuta.
    """
    s = note_str.strip().lower()
    for name, semi in _ITALIAN_NOTES:
        if s == name:
            return semi
    for name, semi in _ENGLISH_NOTES:
        if s == name:
            return semi
    return None


def start_note_to_semitone(note_str):
    """
    Converte la nota di partenza nel semitono da passare come `start_note` a
    draw_keyboard / draw_*_section.

    Accetta:
      - un intero già in forma di semitono (0-11): restituito se è un tasto
        bianco, altrimenti 0;
      - un nome di nota naturale, italiano (DO..SI) o inglese (C..B).

    Per note alterate, valori non riconosciuti o None restituisce 0 (DO), così
    il chiamante può passare direttamente l'input dell'utente senza validarlo.
    """
    if isinstance(note_str, bool):
        return 0
    if isinstance(note_str, int):
        return note_str if note_str in _WHITE_KEYS else 0
    if note_str is None:
        return 0
    semi = _note_name_to_semitone(str(note_str))
    if semi is None or semi not in _WHITE_KEYS:
        return 0
    return semi


def parse_fingering(fingering_str):
    """
    Parsa la stringa del comando {fingering: ...}.

    Formati supportati:
        "Am"                               → accordo senza diteggiatura
        "Am hand=R 1=Do 2=Mi 3=La"        → mano destra
        "Am hand=L 1=Do 2=Mi 3=La"        → mano sinistra
        "Am 1=Do 2=Mi 3=La"               → senza indicazione di mano

    Restituisce:
        chord_name  : str  — il nome dell'accordo (prima parola)
        finger_map  : dict — {semitono: numero_dito}
        hand        : str  — 'R', 'L' o None
    """
    parts = fingering_str.strip().split()
    if not parts:
        return None, {}, None

    chord_name = parts[0]
    finger_map = {}
    hand = None

    for token in parts[1:]:
        # hand=R o hand=L
        m_hand = re.match(r'^hand=([RLrl])$', token, re.IGNORECASE)
        if m_hand:
            hand = m_hand.group(1).upper()
            continue
        # dito=nota
        m = re.match(r'^(\d+)=(.+)$', token)
        if not m:
            continue
        finger_num = int(m.group(1))
        note_name  = m.group(2)
        semi = _note_name_to_semitone(note_name)
        if semi is not None:
            finger_map[semi] = finger_num

    return chord_name, finger_map, hand


def parse_start_note(fingering_str):
    """
    Estrae la nota di partenza da un eventuale token 'start=<nota>' presente
    nella direttiva (es. "DO start=SI" o "Am hand=R start=Fa").

    Restituisce il semitono (0-11) del primo tasto bianco, oppure None se il
    token è assente. Restituendo None (e non 0) il chiamante può distinguere
    "nessun override" da "parti esplicitamente da DO", e quindi ricadere sul
    default globale quando il token manca.

    Il token è ignorato da parse_fingering (che considera solo 'hand=' e
    'numero='), quindi le due funzioni convivono senza interferenze.
    """
    for token in fingering_str.strip().split():
        m = re.match(r'^start=(.+)$', token, re.IGNORECASE)
        if m:
            return start_note_to_semitone(m.group(1))
    return None


def parse_octave_both(fingering_str):
    """
    Estrae dall'eventuale token 'octave=...' se, nelle tastiere a 8 tasti, la
    nota iniziale (presente a entrambe le estremità) vada evidenziata su tutte
    e due le ottave o solo sulla prima.

    Valori riconosciuti:
        octave=both              -> True  (entrambe le estremità)
        octave=one|single|first  -> False (solo quella di sinistra)

    Restituisce True/False, oppure None se il token è assente (il chiamante
    usa il proprio default).
    """
    for token in fingering_str.strip().split():
        m = re.match(r'^octave=(both|one|single|first)$', token, re.IGNORECASE)
        if m:
            return m.group(1).lower() == 'both'
    return None


def keyboard_has_octave_key(start_note):
    """
    True se la tastiera che parte da `start_note` usa 8 tasti bianchi, cioè
    aggiunge l'ottava della nota iniziale in fondo (partenza diversa da DO/FA).
    Solo in questo caso la scelta 'evidenzia su entrambe le ottave' ha effetto.
    Accetta un semitono intero o un nome di nota (vedi start_note_to_semitone).
    """
    semi = start_note_to_semitone(start_note)
    white_order, _ = _keyboard_layout(semi)
    return len(white_order) == 8


def keyboard_header_height(dc, label_font, chord_name, hand=None):
    """
    Restituisce l'altezza totale dello spazio necessario sopra la tastiera
    per le etichette (nome accordo + eventuale etichetta mano).

    Utile per chi chiama draw_keyboard direttamente (es. anteprima dialogo)
    per calcolare il valore corretto di `y`:
        header_h = keyboard_header_height(dc, label_font, chord_name, hand)
        draw_keyboard(dc, x, y + header_h, w, h, ...)
    """
    if label_font:
        dc.SetFont(label_font)
    _, chord_lh = dc.GetTextExtent(chord_name)
    total = chord_lh + 2  # spazio nome accordo + gap

    if hand in ('R', 'L'):
        hand_font = wx.Font(
            max(5, chord_lh - 3),
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_ITALIC,
            wx.FONTWEIGHT_NORMAL,
        )
        dc.SetFont(hand_font)
        try:
            hand_label = wx.GetTranslation(u"Right hand") if hand == 'R' else wx.GetTranslation(u"Left hand")
        except Exception:
            hand_label = u"Right hand" if hand == 'R' else u"Left hand"
        _, hand_lh = dc.GetTextExtent(hand_label)
        total += hand_lh + 2

    return total


def draw_keyboard(dc, x, y, w, h, chord_name, highlighted_keys,
                  label_font=None, highlight_color=None, finger_map=None,
                  finger_num_color=None, hand=None, start_note=0,
                  highlight_octave_both=True):
    """
    Disegna una tastiera di un'ottava su dc.

    highlighted_keys : lista di semitoni (0-11) da evidenziare.
    highlight_color  : wx.Colour per i tasti evidenziati (default rosso).
    finger_map       : dict {semitono: numero_dito}.
    hand             : 'R' = mano destra, 'L' = mano sinistra, None = non mostrato.
    start_note       : semitono (0-11) del primo tasto bianco a sinistra
                       (default 0 = DO). Deve essere un tasto bianco; usare
                       start_note_to_semitone() per convertire un nome di nota.
    highlight_octave_both : nelle tastiere a 8 tasti (partenza != DO/FA) la
                       nota iniziale compare a entrambe le estremità. Se True
                       (default) viene evidenziata su entrambe; se False solo
                       su quella di sinistra. Ininfluente nei layout a 7 tasti.
    """
    if highlight_color is None:
        highlight_color = wx.Colour(210, 60, 60)
    if finger_map is None:
        finger_map = {}

    # Layout dei tasti in funzione della nota di partenza (7 bianchi, oppure
    # 8 se la partenza aggiunge l'ottava in fondo per recuperare il nero tagliato)
    white_order, black_map = _keyboard_layout(start_note)
    n_white = len(white_order)

    # I tasti si distribuiscono nello stesso ingombro `w`: con 8 tasti risultano
    # un po' più stretti, ma la larghezza totale della tastiera resta invariata,
    # così l'impaginazione (a capo, centratura, anteprima) non cambia.
    white_w = w // n_white
    black_w = max(4, int(white_w * 0.55))
    black_h = int(h * 0.62)
    kbd_w   = white_w * n_white

    # ── Sfondo e bordo esterno ────────────────────────────────────
    dc.SetBrush(wx.WHITE_BRUSH)
    dc.SetPen(wx.Pen(wx.Colour(80, 80, 80), 1))
    dc.DrawRectangle(x, y, kbd_w, h)

    # ── Tasti bianchi ─────────────────────────────────────────────
    for i, semi in enumerate(white_order):
        kx = x + i * white_w
        hl = semi in highlighted_keys
        # In layout a 8 tasti l'ultimo tasto è l'ottava del primo: se non si
        # vuole l'evidenziazione doppia, non evidenziare il duplicato in fondo.
        if hl and not highlight_octave_both and n_white == 8 and i == n_white - 1:
            hl = False
        if hl:
            dc.SetBrush(wx.Brush(highlight_color))
        else:
            dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetPen(wx.Pen(wx.Colour(80, 80, 80), 1))
        dc.DrawRectangle(kx, y, white_w, h)

    # ── Tasti neri ────────────────────────────────────────────────
    for semi, gap_idx in black_map.items():
        kx = x + gap_idx * white_w + white_w - black_w // 2
        if semi in highlighted_keys:
            dc.SetBrush(wx.Brush(highlight_color))
        else:
            dc.SetBrush(wx.BLACK_BRUSH)
        dc.SetPen(wx.Pen(wx.Colour(40, 40, 40), 1))
        dc.DrawRectangle(kx, y, black_w, black_h)

    # ── Numeri delle dita sui tasti ───────────────────────────────
    if finger_map:
        finger_font = wx.Font(
            max(5, white_w - 4),
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD,
        )
        dc.SetFont(finger_font)

        for semi, finger_num in finger_map.items():
            # Determina se il tasto è visibile nella finestra corrente e di che tipo
            if semi in black_map:
                is_black = True
            elif semi in white_order:
                is_black = False
            else:
                continue  # nota fuori dalla finestra di 7 bianchi: non disegnabile

            label = str(finger_num)
            lw, lh = dc.GetTextExtent(label)

            if is_black:
                # Tasto nero: numero nella parte bassa del tasto nero
                gap_idx = black_map[semi]
                kx = x + gap_idx * white_w + white_w - black_w // 2
                cx = kx + black_w // 2
                cy = y + black_h - lh - 2
                # Colore custom o bianco di default (contrasto su nero)
                dc.SetTextForeground(finger_num_color if finger_num_color else wx.WHITE)
            else:
                # Tasto bianco: numero nella parte bassa del tasto
                white_idx = white_order.index(semi)
                kx = x + white_idx * white_w
                cx = kx + white_w // 2
                cy = y + h - lh - 3
                # Colore custom o nero di default (contrasto su bianco)
                dc.SetTextForeground(finger_num_color if finger_num_color else wx.BLACK)

            dc.DrawText(label, cx - lw // 2, cy)

    # ── Etichette sopra la tastiera: mano (facoltativa) + nome accordo ───
    # Calcola prima tutte le altezze, poi disegna dall'alto verso il basso.

    # 1) Misura nome accordo con label_font
    if label_font:
        dc.SetFont(label_font)
    chord_lw, chord_lh = dc.GetTextExtent(chord_name)

    if hand in ('R', 'L'):
        # 2) Font mano e misura
        hand_font = wx.Font(
            max(5, chord_lh - 3),
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_ITALIC,
            wx.FONTWEIGHT_NORMAL,
        )
        dc.SetFont(hand_font)
        try:
            hand_label = wx.GetTranslation(u"Right hand") if hand == 'R' else wx.GetTranslation(u"Left hand")
        except Exception:
            hand_label = u"Right hand" if hand == 'R' else u"Left hand"
        hand_lw, hand_lh = dc.GetTextExtent(hand_label)

        # 3) Nome accordo direttamente sopra la tastiera, mano una riga più su
        chord_ty = y - chord_lh - 2
        hand_ty  = chord_ty - hand_lh - 2

        dc.SetTextForeground(wx.Colour(90, 90, 90))
        dc.DrawText(hand_label, x + (kbd_w - hand_lw) // 2, hand_ty)

        if label_font:
            dc.SetFont(label_font)
        dc.SetTextForeground(wx.BLACK)
        dc.DrawText(chord_name, x + (kbd_w - chord_lw) // 2, chord_ty)
    else:
        dc.SetTextForeground(wx.BLACK)
        dc.DrawText(chord_name, x + (kbd_w - chord_lw) // 2, y - chord_lh - 3)


def draw_klavier_section(dc, klavier_list, start_x, start_y, base_font,
                         pen_scale=1.0, notations=None, highlight_color=None,
                         finger_num_color=None, content_w=None, start_note=0,
                         highlight_octave_both=True):
    """
    Disegna tutte le tastiere in klavier_list in fondo alla canzone.
    Ogni elemento può essere una stringa accordo semplice ("Am")
    oppure una stringa con diteggiatura ("Am 1=Do 2=Mi 3=La").

    content_w : larghezza utile disponibile (in px logici, senza start_x).
                Se None usa 560 come fallback per retrocompatibilità.

    Restituisce (total_h, used_w):
        total_h : altezza totale occupata
        used_w  : larghezza massima effettivamente disegnata (da start_x)
    """
    if not klavier_list:
        return 0, 0

    white_w  = 16
    kbd_w    = white_w * 7
    kbd_h    = 44
    padding_x = 22
    padding_y = 14
    # label_h aumentato per ospitare sia il nome accordo sia l'etichetta mano sopra
    label_h   = 34
    row_h     = label_h + kbd_h + padding_y

    # Larghezza massima della riga: usa content_w se fornito, altrimenti 560px
    row_max_w = int(content_w) if content_w and content_w > kbd_w else 560
    max_x = start_x + row_max_w

    label_font = wx.Font(
        max(7, int(base_font.GetPointSize() * 0.85)),
        wx.FONTFAMILY_DEFAULT,
        wx.FONTSTYLE_NORMAL,
        wx.FONTWEIGHT_BOLD,
        False,
        base_font.GetFaceName()
    )

    # ── Linea separatrice (lunga quanto il contenuto effettivo) ───
    sep_y = start_y + 10
    dc.SetPen(wx.Pen(wx.Colour(180, 180, 180),
                     max(1, round(1 / pen_scale)), wx.PENSTYLE_DOT))
    dc.DrawLine(start_x, sep_y, start_x + row_max_w, sep_y)

    # ── Titolo sezione ────────────────────────────────────────────
    title_font = wx.Font(
        max(7, int(base_font.GetPointSize() * 0.8)),
        wx.FONTFAMILY_DEFAULT,
        wx.FONTSTYLE_ITALIC,
        wx.FONTWEIGHT_NORMAL,
        False,
        base_font.GetFaceName()
    )
    dc.SetFont(title_font)
    dc.SetPen(wx.NullPen)
    dc.SetTextForeground(wx.Colour(110, 110, 110))
    dc.DrawText("Accordi", start_x, sep_y + 4)
    dc.SetTextForeground(wx.BLACK)

    cur_x = start_x
    cur_y = sep_y + 26
    max_drawn_x = start_x  # tiene traccia della x destra massima usata

    for entry in klavier_list:
        # Parsa: potrebbe essere "Am" oppure "Am hand=R 1=Do 2=Mi 3=La"
        chord_name, finger_map, hand = parse_fingering(entry)
        if chord_name is None:
            continue

        # Nota di partenza: token 'start=' della direttiva se presente,
        # altrimenti il default passato dal chiamante (impostazione globale).
        entry_start = parse_start_note(entry)
        eff_start = entry_start if entry_start is not None else start_note

        # Evidenziazione ottava doppia: token 'octave=' se presente, altrimenti default
        entry_oct = parse_octave_both(entry)
        eff_oct = entry_oct if entry_oct is not None else highlight_octave_both

        normalized = _normalize_chord(chord_name, notations)
        keys = get_chord_keys(normalized)
        if keys is None:
            keys = get_chord_keys(chord_name)   # fallback
        if keys is None:
            continue

        if cur_x + kbd_w > max_x:
            cur_x = start_x
            cur_y += row_h

        draw_keyboard(
            dc, cur_x, cur_y + label_h, kbd_w, kbd_h,
            chord_name, keys, label_font, highlight_color,
            finger_map=finger_map,
            finger_num_color=finger_num_color,
            hand=hand,
            start_note=eff_start,
            highlight_octave_both=eff_oct,
        )
        cur_x += kbd_w + padding_x
        max_drawn_x = max(max_drawn_x, cur_x)

    total_h = (cur_y + row_h) - start_y + 10
    used_w  = max_drawn_x - start_x
    return total_h, used_w


def draw_fingering_section(dc, fingering_list, start_x, start_y, base_font,
                           pen_scale=1.0, notations=None, highlight_color=None,
                           finger_num_color=None, content_w=None, start_note=0,
                           highlight_octave_both=True):
    """
    Identico a draw_klavier_section ma destinato alle tastiere {fingering:}.
    Non mostra titolo di sezione.

    content_w : larghezza utile disponibile (in px logici, senza start_x).
                Se None usa 560 come fallback per retrocompatibilità.

    Restituisce (total_h, used_w).
    """
    if not fingering_list:
        return 0, 0

    white_w   = 16
    kbd_w     = white_w * 7
    kbd_h     = 44
    padding_x = 22
    padding_y = 14
    # label_h aumentato per ospitare sia il nome accordo sia l'etichetta mano sopra
    label_h   = 34
    row_h     = label_h + kbd_h + padding_y

    row_max_w = int(content_w) if content_w and content_w > kbd_w else 560
    max_x = start_x + row_max_w

    label_font = wx.Font(
        max(7, int(base_font.GetPointSize() * 0.85)),
        wx.FONTFAMILY_DEFAULT,
        wx.FONTSTYLE_NORMAL,
        wx.FONTWEIGHT_BOLD,
        False,
        base_font.GetFaceName()
    )

    # ── Linea separatrice ─────────────────────────────────────────
    sep_y = start_y + 10
    dc.SetPen(wx.Pen(wx.Colour(180, 180, 180),
                     max(1, round(1 / pen_scale)), wx.PENSTYLE_DOT))
    dc.DrawLine(start_x, sep_y, start_x + row_max_w, sep_y)

    cur_x = start_x
    cur_y = sep_y + 8
    max_drawn_x = start_x

    for entry in fingering_list:
        chord_name, finger_map, hand = parse_fingering(entry)
        if chord_name is None:
            continue

        # Nota di partenza: token 'start=' della direttiva se presente,
        # altrimenti il default passato dal chiamante (impostazione globale).
        entry_start = parse_start_note(entry)
        eff_start = entry_start if entry_start is not None else start_note

        # Evidenziazione ottava doppia: token 'octave=' se presente, altrimenti default
        entry_oct = parse_octave_both(entry)
        eff_oct = entry_oct if entry_oct is not None else highlight_octave_both

        normalized = _normalize_chord(chord_name, notations)
        keys = get_chord_keys(normalized)
        if keys is None:
            keys = get_chord_keys(chord_name)
        if keys is None:
            continue

        if cur_x + kbd_w > max_x:
            cur_x = start_x
            cur_y += row_h

        draw_keyboard(
            dc, cur_x, cur_y + label_h, kbd_w, kbd_h,
            chord_name, keys, label_font, highlight_color,
            finger_map=finger_map,
            finger_num_color=finger_num_color,
            hand=hand,
            start_note=eff_start,
            highlight_octave_both=eff_oct,
        )
        cur_x += kbd_w + padding_x
        max_drawn_x = max(max_drawn_x, cur_x)

    total_h = (cur_y + row_h) - start_y + 10
    used_w  = max_drawn_x - start_x
    return total_h, used_w
