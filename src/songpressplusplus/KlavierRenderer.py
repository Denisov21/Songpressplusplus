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

# Frecce di direzione (suffisso ^ = su, v = giù) come per gli accordi nel testo
try:
    from .ChordArrow import split_arrow, arrow_points, render_icon, ARROW_ASPECT
    _has_arrow = True
except ImportError:
    _has_arrow = False
    ARROW_ASPECT = 1.0

    def split_arrow(text):
        return text, ''

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

# Colore globale del tasto "ottava" (il duplicato più a destra nelle tastiere a
# 8 tasti, es. il SI alto in una tastiera SI...SI). None = stesso colore degli
# altri tasti evidenziati. Viene impostato dall'applicazione in base alle
# preferenze (vedi set_octave_highlight_color), così tutti i punti che
# disegnano tastiere — anteprima, stampa, esportazione, anteprima del dialogo —
# lo usano senza dover passare un parametro in più.
_octave_highlight_color = None

# Sentinella: "parametro non passato, usa il default globale"
_USE_GLOBAL = object()

# Token che il Renderer aggiunge in coda a una voce della lista tastiere quando,
# nell'editor, tra la direttiva precedente ({taste:}/{fingering:}) e questa è
# stata lasciata una riga vuota. Significa "questa tastiera va su una nuova
# riga". Non contiene '=' né coincide con 'hand=', 'start=' o 'octave=', quindi
# parse_fingering / parse_start_note / parse_octave_both lo ignorano.
NEW_ROW_TOKEN = '<newrow>'

# Segnaposto al posto del nome accordo nella modalità "solo note":
# {fingering: - hand=R 0=Do 2=Mi}. Nessun accordo: si evidenziano solo i tasti
# elencati (dito 0 = solo puntino, tasto non colorato) e non si scrive il nome.
NOTES_ONLY_TOKEN = '-'


def has_new_row(entry):
    """True se la voce (stringa direttiva) è marcata come 'inizia nuova riga'."""
    return NEW_ROW_TOKEN in entry.split()


def _split_chord_arrow(chord_name):
    """
    Separa dal nome accordo l'eventuale suffisso di direzione: '^' = su,
    'v' = giù (es. 'DO^', 'LA-v'), come per gli accordi nel testo.

    Restituisce (nome_senza_suffisso, arrow) con arrow in {'', 'up', 'down'}.
    Se togliendo il suffisso non resta nulla, lascia il nome com'era.
    """
    name, arrow = split_arrow(chord_name)
    if not name or not name.strip():
        return chord_name, ''
    return name, arrow


def _draw_arrow(dc, arrow, col, x0, top, aw, ah, use_bitmap=True):
    """
    Disegna la freccia di direzione: bitmap anti-aliased a risoluzione device
    (schermo) oppure sagoma vettoriale (stampa/PDF, dove le bitmap con
    trasparenza non sono affidabili). Stessa resa delle frecce degli accordi.
    """
    if not _has_arrow:
        return
    if use_bitmap:
        sx = sy = 1.0
        try:
            sx, sy = dc.GetUserScale()
            dw = max(4, int(round(aw * sx)))
            dh = max(4, int(round(ah * sy)))
            icon = render_icon(arrow, dw, dh, (col.Red(), col.Green(), col.Blue()))
            if icon is not None:
                w, h, rgb, alpha = icon
                img = wx.Image(w, h)
                img.SetData(rgb)
                img.SetAlpha(alpha)
                bmp = wx.Bitmap(img)
                dx = int(round(x0 * sx))
                dy = int(round(top * sy))
                dc.SetUserScale(1.0, 1.0)
                try:
                    dc.DrawBitmap(bmp, dx, dy, True)
                finally:
                    dc.SetUserScale(sx, sy)
                return
        except Exception:
            try:
                dc.SetUserScale(sx, sy)
            except Exception:
                pass
    pts = arrow_points(arrow, x0, top, aw, ah)
    dc.SetPen(wx.Pen(col, 1))
    dc.SetBrush(wx.Brush(col, wx.BRUSHSTYLE_SOLID))
    dc.DrawPolygon([wx.Point(int(round(px)), int(round(py))) for px, py in pts])
    dc.SetBrush(wx.NullBrush)
    dc.SetPen(wx.NullPen)


def set_octave_highlight_color(colour):
    """
    Imposta il colore di default del tasto d'ottava (il duplicato a destra
    nelle tastiere a 8 tasti). Passare None per usare lo stesso colore di
    evidenziazione degli altri tasti.
    """
    global _octave_highlight_color
    _octave_highlight_color = colour


def get_octave_highlight_color():
    """Restituisce il colore di default del tasto d'ottava (o None)."""
    return _octave_highlight_color


# Colore globale del puntino sul DO centrale (vedi show_middle_c in
# draw_keyboard). None = grigio scuro predefinito. Impostato
# dall'applicazione in base alle preferenze, come per il tasto d'ottava.
_middle_c_color = None
_MIDDLE_C_DEFAULT = (70, 70, 70)


def set_middle_c_color(colour):
    """Imposta il colore di default del puntino del DO centrale (None = predefinito)."""
    global _middle_c_color
    _middle_c_color = colour


def get_middle_c_color():
    """Restituisce il colore di default del puntino del DO centrale (o None)."""
    return _middle_c_color




# Limite destro (in px logici, stessa origine di start_x) oltre il quale le
# tastiere non devono essere disegnate. Lo imposta chi stampa (PrintDialog) col
# bordo destro reale della colonna: serve quando il Renderer non passa
# `content_w` e si ricadrebbe sui 560 px di default, più larghi della colonna
# (la terza tastiera di una riga, es. il SIb, finiva tagliata dal clip).
# None = nessun limite (comportamento di prima).
_content_right_limit = None


def set_content_right_limit(limit):
    """Imposta (o con None rimuove) il limite destro di impaginazione."""
    global _content_right_limit
    _content_right_limit = limit


def get_content_right_limit():
    """Restituisce il limite destro di impaginazione corrente (o None)."""
    return _content_right_limit


def _effective_row_w(content_w, start_x, kbd_w):
    """Larghezza utile della riga: content_w (o 560) ridotta, se impostato, al
    limite destro della colonna. Mai sotto una tastiera."""
    row_w = int(content_w) if content_w and content_w > kbd_w else 560
    lim = _content_right_limit
    if lim is not None:
        row_w = min(row_w, int(lim) - start_x)
    return max(row_w, kbd_w)


# Dimensione delle tastiere in fondo alla pagina, in percentuale (100 = misure
# originali). Impostata dall'applicazione dalle preferenze; vale per anteprima,
# stampa ed esportazione che usano draw_klavier_section / draw_fingering_section.
KBD_SCALE_MIN = 50
KBD_SCALE_MAX = 200
_keyboard_scale_pct = 100


def set_keyboard_scale_pct(pct):
    """Imposta la dimensione delle tastiere (%), limitata a KBD_SCALE_MIN..MAX."""
    global _keyboard_scale_pct
    try:
        pct = int(pct)
    except (TypeError, ValueError):
        pct = 100
    _keyboard_scale_pct = max(KBD_SCALE_MIN, min(pct, KBD_SCALE_MAX))


def get_keyboard_scale_pct():
    """Restituisce la dimensione corrente delle tastiere (%)."""
    return _keyboard_scale_pct


def _section_metrics():
    """Misure delle tastiere della sezione, scalate con la preferenza.
    Restituisce (white_w, kbd_w, kbd_h, padding_x, padding_y). Con 100% sono
    esattamente le misure di prima (16, 112, 44, 22, 14)."""
    f = _keyboard_scale_pct / 100.0
    white_w = max(8, int(round(16 * f)))
    kbd_w = white_w * 7
    kbd_h = max(22, int(round(44 * f)))
    padding_x = max(8, int(round(22 * f)))
    padding_y = max(8, int(round(14 * f)))
    return white_w, kbd_w, kbd_h, padding_x, padding_y


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


def order_fingering_directive(fingering_str, start_note=None):
    """
    Riordina i token 'dito=NOTA' di una direttiva {fingering: ...} secondo la
    posizione delle note sulla tastiera, da sinistra a destra, partendo da
    `start_note`.

    start_note:
        - None  -> usa l'eventuale token 'start=' presente nella direttiva
                   stessa; se manca parte da DO;
        - nome nota (DO..SI / C..B) o semitono intero (0-11) -> forza quel via.

    Vengono spostati SOLO i token 'dito=NOTA'; nome accordo, 'hand=', 'start=',
    'octave=' e ogni altro token restano dove sono, nell'ordine originale, e i
    token diteggiatura riordinati vengono accodati in fondo. È la forma pensata
    per l'opzione "Ordina le note come sulla tastiera" del dialogo: passa la
    stringa attuale e riscrivi l'anteprima direttiva col risultato.

    La chiave d'ordine è (semitono - start) % 12, cioè la distanza cromatica
    verso destra dal primo tasto: es. con start=SI l'ordine è SI, MI, SOL, così
    'MI- hand=R start=SI 5=SOL 1=SI 3=MI' -> 'MI- hand=R start=SI 1=SI 3=MI 5=SOL'.
    """
    parts = fingering_str.strip().split()
    if not parts:
        return fingering_str

    if start_note is None:
        s = parse_start_note(fingering_str)
        start_semi = s if s is not None else 0
    else:
        start_semi = start_note_to_semitone(start_note)

    finger_tokens = []   # (semitono, token)
    other_tokens  = []   # token non-diteggiatura, ordine preservato
    for tok in parts:
        m = re.match(r'^(\d+)=(.+)$', tok)
        if m:
            semi = _note_name_to_semitone(m.group(2))
            if semi is not None:
                finger_tokens.append((semi, tok))
                continue
        other_tokens.append(tok)

    finger_tokens.sort(key=lambda st: (st[0] - start_semi) % 12)
    return ' '.join(other_tokens + [tok for _, tok in finger_tokens])


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


def parse_middle_c(fingering_str):
    """
    Estrae dall'eventuale token 'middlec=...' se vada mostrato il DO centrale
    (un puntino sul tasto DO) nella tastiera disegnata.

    Valori riconosciuti (insensibili alle maiuscole):
        middlec=show | on | yes | 1   -> True  (mostra)
        middlec=hide | off | no | 0   -> False (nascondi)

    Restituisce True/False, oppure None se il token è assente (il chiamante
    usa il proprio default). Ha effetto solo se la tastiera NON parte da DO
    (vedi keyboard_has_middle_c_option).
    """
    for token in fingering_str.strip().split():
        m = re.match(r'^middlec=(show|hide|on|off|yes|no|1|0)$', token,
                     re.IGNORECASE)
        if m:
            return m.group(1).lower() in ('show', 'on', 'yes', '1')
    return None


def keyboard_has_middle_c_option(start_note):
    """
    True se ha senso mostrare/nascondere il DO centrale, cioè se la tastiera
    parte da una nota diversa da DO. Partendo da DO il primo tasto a sinistra
    è già il DO e non serve alcun segnaposto.
    Accetta un semitono intero o un nome di nota (vedi start_note_to_semitone).
    """
    return start_note_to_semitone(start_note) != 0


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
                  highlight_octave_both=True, octave_color=_USE_GLOBAL,
                  arrow='', arrow_colours=None, arrow_pct=90,
                  arrow_bitmap=True, show_middle_c=False,
                  middle_c_color=_USE_GLOBAL):
    """
    Disegna una tastiera di un'ottava su dc.

    arrow            : '' | 'up' | 'down' — freccia di direzione disegnata
                       accanto al nome accordo (suffisso ^ / v nella direttiva).
    arrow_colours    : dict {'up': colour, 'down': colour}; se manca la
                       direzione, la freccia ha il colore del testo (nero).
    arrow_pct        : altezza della freccia in % dell'altezza del testo.
    arrow_bitmap     : True = bitmap anti-aliased (schermo); False = sagoma
                       vettoriale (stampa / PDF).
    show_middle_c    : se True disegna un puntino sul tasto DO (il DO centrale)
                       quando la tastiera parte da una nota diversa da DO, per
                       orientarsi sulla tastiera. Con partenza DO è ininfluente.
    middle_c_color   : colore del puntino del DO centrale. Se omesso usa il
                       default globale impostato con set_middle_c_color(); se
                       None (o default globale None) usa il grigio scuro.

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
    octave_color     : colore del tasto d'ottava evidenziato (il duplicato più
                       a destra nei layout a 8 tasti). Se omesso usa il default
                       globale impostato con set_octave_highlight_color(); se
                       None (o default globale None) usa highlight_color.
    """
    if highlight_color is None:
        highlight_color = wx.Colour(210, 60, 60)
    if octave_color is _USE_GLOBAL:
        octave_color = _octave_highlight_color
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
        is_octave_key = (n_white == 8 and i == n_white - 1)
        if hl and not highlight_octave_both and is_octave_key:
            hl = False
        if hl and is_octave_key and octave_color is not None:
            # Tasto d'ottava (es. SI alto): secondo colore, se impostato
            dc.SetBrush(wx.Brush(octave_color))
        elif hl:
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

    # ── DO centrale: puntino in basso sul tasto DO ────────────────
    # Solo se la tastiera non parte da DO (altrimenti il DO è il primo tasto).
    mc_idx = None
    mc_h = 0   # altezza del puntino (serve a spostare il numero del dito)
    if show_middle_c and white_order[0] != 0 and 0 in white_order:
        mc_idx = white_order.index(0)
        mc_col = _middle_c_color if middle_c_color is _USE_GLOBAL else middle_c_color
        if mc_col is None:
            mc_col = wx.Colour(*_MIDDLE_C_DEFAULT)
        # Pallino pieno nel colore scelto, in basso al centro del tasto.
        mc_r = max(3, white_w // 5)
        mc_h = 2 * mc_r
        dc.SetBrush(wx.Brush(mc_col))
        dc.SetPen(wx.Pen(mc_col, 1))
        dc.DrawCircle(x + mc_idx * white_w + white_w // 2, y + h - mc_r - 4, mc_r)

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

            if finger_num == 0:
                # 0 = tasto selezionato senza numero di dito (modalità "solo
                # note"): al posto del numero si disegna un puntino pieno. Il
                # tasto non e' colorato, quindi il puntino e' sempre a contrasto
                # con il tasto (nero sul bianco, bianco sul nero), senza usare il
                # colore dei numeri (che puo' essere chiaro e sparirebbe).
                d_r = max(3, white_w // 5)
                if semi in black_map:
                    gap_idx = black_map[semi]
                    dcx = x + gap_idx * white_w + white_w
                    dcy = y + black_h - d_r - 4
                    d_col = wx.WHITE   # tasto nero non colorato: puntino bianco
                else:
                    white_idx = white_order.index(semi)
                    dcx = x + white_idx * white_w + white_w // 2
                    dcy = y + h - d_r - 4
                    if mc_idx is not None and white_idx == mc_idx:
                        dcy -= mc_h + 3
                    d_col = wx.BLACK   # tasto bianco non colorato: puntino nero
                dc.SetBrush(wx.Brush(d_col))
                dc.SetPen(wx.Pen(d_col, 1))
                dc.DrawCircle(dcx, dcy, d_r)
                continue
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
                # Sul DO con puntino il numero sale sopra il puntino
                if mc_idx is not None and white_idx == mc_idx:
                    cy -= mc_h + 3
                # Colore custom o nero di default (contrasto su bianco)
                dc.SetTextForeground(finger_num_color if finger_num_color else wx.BLACK)

            dc.DrawText(label, cx - lw // 2, cy)

    # ── Etichette sopra la tastiera: mano (facoltativa) + nome accordo ───
    # Calcola prima tutte le altezze, poi disegna dall'alto verso il basso.

    # 1) Misura nome accordo con label_font
    if label_font:
        dc.SetFont(label_font)
    chord_lw, chord_lh = dc.GetTextExtent(chord_name or u"A")
    if not chord_name:
        chord_lw = 0   # modalità "solo note": nessun nome da scrivere

    # Freccia accanto al nome: stesse proporzioni di quella degli accordi nel testo
    arrow_w = arrow_h = 0
    if arrow and _has_arrow:
        _ah0 = max(8, int(chord_lh * arrow_pct / 100))
        arrow_w = max(6, int(_ah0 * 0.8))
        arrow_h = max(4, int(arrow_w / ARROW_ASPECT))
    arrow_gap = 3 if arrow_w else 0
    label_w = chord_lw + arrow_gap + arrow_w   # nome + freccia, centrati insieme

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
    else:
        chord_ty = y - chord_lh - 3
        dc.SetTextForeground(wx.BLACK)

    label_x = x + (kbd_w - label_w) // 2
    dc.DrawText(chord_name, label_x, chord_ty)
    if arrow_w:
        col = (arrow_colours or {}).get(arrow) or wx.BLACK
        _draw_arrow(dc, arrow, col,
                    label_x + chord_lw + arrow_gap,
                    chord_ty + (chord_lh - arrow_h) // 2,
                    arrow_w, arrow_h, arrow_bitmap)


def _entry_keys(chord_name, finger_map, notations):
    """Tasti da evidenziare per una voce. Con nome vuoto (modalità "solo note")
    sono quelli elencati nella diteggiatura; altrimenti quelli dell'accordo."""
    if not chord_name:
        # "Solo note": si colorano solo i tasti con un dito (1-5); quelli con
        # il puntino (0) restano del colore normale, con il solo puntino.
        if not finger_map:
            return None
        return [k for k, f in finger_map.items() if f != 0]
    keys = get_chord_keys(_normalize_chord(chord_name, notations))
    if keys is None:
        keys = get_chord_keys(chord_name)
    return keys


def draw_klavier_section(dc, klavier_list, start_x, start_y, base_font,
                         pen_scale=1.0, notations=None, highlight_color=None,
                         finger_num_color=None, content_w=None, start_note=0,
                         highlight_octave_both=True, arrow_colours=None,
                         arrow_pct=90, arrow_bitmap=True, show_middle_c=False):
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

    white_w, kbd_w, kbd_h, padding_x, padding_y = _section_metrics()
    # label_h aumentato per ospitare sia il nome accordo sia l'etichetta mano sopra
    label_h   = 34
    row_h     = label_h + kbd_h + padding_y

    # Larghezza massima della riga: usa content_w se fornito, altrimenti 560px
    row_max_w = _effective_row_w(content_w, start_x, kbd_w)
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
    force_new_row = False  # riga vuota nell'editor -> prossima tastiera a capo

    for entry in klavier_list:
        # Riga vuota nell'editor prima di questa direttiva: va a capo. Il flag
        # resta attivo finché non viene disegnata una tastiera (se la voce non
        # è riconosciuta e viene saltata, vale per la successiva).
        if has_new_row(entry):
            force_new_row = True

        # Parsa: potrebbe essere "Am" oppure "Am hand=R 1=Do 2=Mi 3=La"
        chord_name, finger_map, hand = parse_fingering(entry)
        if chord_name is None:
            continue
        # Suffisso di direzione: "Am^" (su) / "Amv" (giù) -> freccia
        if chord_name == NOTES_ONLY_TOKEN:
            chord_name, arrow = u"", ''
        else:
            chord_name, arrow = _split_chord_arrow(chord_name)

        # Nota di partenza: token 'start=' della direttiva se presente,
        # altrimenti il default passato dal chiamante (impostazione globale).
        entry_start = parse_start_note(entry)
        eff_start = entry_start if entry_start is not None else start_note

        # Evidenziazione ottava doppia: token 'octave=' se presente, altrimenti default
        entry_oct = parse_octave_both(entry)
        eff_oct = entry_oct if entry_oct is not None else highlight_octave_both

        # DO centrale: token 'middlec=' se presente, altrimenti default
        entry_mc = parse_middle_c(entry)
        eff_mc = entry_mc if entry_mc is not None else show_middle_c

        keys = _entry_keys(chord_name, finger_map, notations)
        if keys is None:
            continue

        # A capo forzato (solo se la riga corrente contiene già qualcosa:
        # sulla prima tastiera non c'è nulla da spezzare)
        if force_new_row and cur_x > start_x:
            cur_x = start_x
            cur_y += row_h
        force_new_row = False

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
            arrow=arrow,
            arrow_colours=arrow_colours,
            arrow_pct=arrow_pct,
            arrow_bitmap=arrow_bitmap,
            show_middle_c=eff_mc,
        )
        # used_w = bordo destro REALE dell'ultima tastiera disegnata: il
        # padding che segue non è contenuto, e se contasse allargherebbe la
        # larghezza del brano (centraggio in stampa, riduzione, virtual size).
        max_drawn_x = max(max_drawn_x, cur_x + kbd_w)
        cur_x += kbd_w + padding_x

    total_h = (cur_y + row_h) - start_y + 10
    used_w  = max_drawn_x - start_x
    return total_h, used_w


def draw_fingering_section(dc, fingering_list, start_x, start_y, base_font,
                           pen_scale=1.0, notations=None, highlight_color=None,
                           finger_num_color=None, content_w=None, start_note=0,
                           highlight_octave_both=True, arrow_colours=None,
                           arrow_pct=90, arrow_bitmap=True,
                           show_middle_c=False):
    """
    Identico a draw_klavier_section ma destinato alle tastiere {fingering:}.
    Non mostra titolo di sezione.

    content_w : larghezza utile disponibile (in px logici, senza start_x).
                Se None usa 560 come fallback per retrocompatibilità.

    Restituisce (total_h, used_w).
    """
    if not fingering_list:
        return 0, 0

    white_w, kbd_w, kbd_h, padding_x, padding_y = _section_metrics()
    # label_h aumentato per ospitare sia il nome accordo sia l'etichetta mano sopra
    label_h   = 34
    row_h     = label_h + kbd_h + padding_y

    row_max_w = _effective_row_w(content_w, start_x, kbd_w)
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
    force_new_row = False  # riga vuota nell'editor -> prossima tastiera a capo

    for entry in fingering_list:
        # Riga vuota nell'editor prima di questa direttiva: va a capo.
        if has_new_row(entry):
            force_new_row = True

        chord_name, finger_map, hand = parse_fingering(entry)
        if chord_name is None:
            continue
        # Suffisso di direzione: "Am^" (su) / "Amv" (giù) -> freccia
        if chord_name == NOTES_ONLY_TOKEN:
            chord_name, arrow = u"", ''
        else:
            chord_name, arrow = _split_chord_arrow(chord_name)

        # Nota di partenza: token 'start=' della direttiva se presente,
        # altrimenti il default passato dal chiamante (impostazione globale).
        entry_start = parse_start_note(entry)
        eff_start = entry_start if entry_start is not None else start_note

        # Evidenziazione ottava doppia: token 'octave=' se presente, altrimenti default
        entry_oct = parse_octave_both(entry)
        eff_oct = entry_oct if entry_oct is not None else highlight_octave_both

        # DO centrale: token 'middlec=' se presente, altrimenti default
        entry_mc = parse_middle_c(entry)
        eff_mc = entry_mc if entry_mc is not None else show_middle_c

        keys = _entry_keys(chord_name, finger_map, notations)
        if keys is None:
            continue

        if force_new_row and cur_x > start_x:
            cur_x = start_x
            cur_y += row_h
        force_new_row = False

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
            arrow=arrow,
            arrow_colours=arrow_colours,
            arrow_pct=arrow_pct,
            arrow_bitmap=arrow_bitmap,
            show_middle_c=eff_mc,
        )
        # used_w = bordo destro REALE dell'ultima tastiera disegnata: il
        # padding che segue non è contenuto, e se contasse allargherebbe la
        # larghezza del brano (centraggio in stampa, riduzione, virtual size).
        max_drawn_x = max(max_drawn_x, cur_x + kbd_w)
        cur_x += kbd_w + padding_x

    total_h = (cur_y + row_h) - start_y + 10
    used_w  = max_drawn_x - start_x
    return total_h, used_w
