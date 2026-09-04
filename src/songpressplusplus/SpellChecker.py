###############################################################
# Name:         SpellChecker.py
# Purpose:      Controllo ortografico per Songpress++
#               - motore PyEnchant (Hunspell)
#               - dizionario personale cross-platform (Debian + Windows)
#               - filtro accordi/direttive ChordPro
#               - ondina rossa live su Scintilla (StyledTextCtrl)
#               - dialogo "Controllo ortografia" in stile Word
# Author:       Denisov21
# Copyright:    Modifications (c) 2026 Denisov21
# License:      GNU GPL v2
###############################################################
#
# DIPENDENZE
# ----------
#   pip install pyenchant
#
#   Debian/Ubuntu (dizionari di sistema):
#       sudo apt install hunspell-it hunspell-en-us
#     In debian/control conviene aggiungere:
#       Depends: python3-enchant
#       Recommends: hunspell-it, hunspell-en-us
#
#   Windows: i dizionari NON sono nel sistema. Si installano dal pannello
#   "Opzioni ortografia..." -> "Installa dizionari..." (download automatico dai
#   dizionari LibreOffice). In alternativa, per un pacchetto self-contained, si
#   puo' spedire una cartella "dict/hunspell/" accanto all'eseguibile.
#
# INTEGRAZIONE IN SongpressFrame.py  (riassunto, il dettaglio e' in fondo al file)
# -------------------------------------------------------------------------------
#   from .SpellChecker import SpellManager
#   # in __init__, dopo aver creato self.text:
#   self.speller = SpellManager(self, lang="it_IT")
#   # nel metodo che fa i Bind():
#   Bind(self.OnSpellCheck, 'spellCheck')          # dialogo (F6)
#   Bind(self.OnSpellLive,  'spellLive')           # toggle ondina live
#
###############################################################

import os
import sys
import platform

import wx
import wx.stc


# ---------------------------------------------------------------------------
# Import "morbido" di enchant: se manca, l'app NON deve crashare.
# ---------------------------------------------------------------------------
def _app_config_dir():
    """Cartella di configurazione dell'app, calcolata SENZA dipendere da wx.

    Questa funzione gira anche a import-time (prima che esista un wx.App),
    quindi non usa wx.StandardPaths ma le variabili d'ambiente standard.

    Debian/Linux : $XDG_CONFIG_HOME/songpress  (di norma ~/.config/songpress)
    Windows      : %APPDATA%\\Songpress
    macOS        : ~/Library/Application Support/Songpress
    """
    sysname = platform.system()
    if sysname == 'Windows':
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        return os.path.join(base, 'Songpress')
    if sysname == 'Darwin':
        return os.path.join(os.path.expanduser('~/Library/Application Support'),
                            'Songpress')
    base = os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
    return os.path.join(base, 'songpress')


def _enchant_data_dir(create=True):
    """Cartella dati Enchant scrivibile dall'utente.

    E' la cartella puntata da ENCHANT_CONFIG_DIR: i dizionari installati
    dall'utente vanno nella sua sottocartella 'hunspell/'.  Enchant li aggiunge
    a quelli gia' presenti nel sistema / nel wheel (non li sostituisce).
    """
    d = os.path.join(_app_config_dir(), 'enchant')
    if create:
        try:
            os.makedirs(os.path.join(d, 'hunspell'), exist_ok=True)
        except OSError:
            pass
    return d


def _bootstrap_dicts():
    """Prepara i percorsi dei dizionari PRIMA che enchant venga importato.

    - Imposta ENCHANT_CONFIG_DIR sulla cartella dati utente scrivibile, cosi'
      i dizionari installati in modo interattivo (vedi DictInstallerDialog)
      vengono trovati da Enchant su tutte le piattaforme.
    - Su Windows supporta anche una cartella 'dict/' spedita con l'app (i suoi
      .dic/.aff vanno in dict/hunspell/): utile per un pacchetto self-contained.
    """
    # 1) cartella utente scrivibile (dove scrive l'installer)
    data = _enchant_data_dir(create=True)
    os.environ.setdefault('ENCHANT_CONFIG_DIR', data)

    # 2) Windows: eventuale cartella 'dict/' bundled accanto all'exe/modulo.
    #    Se presente e contiene dizionari, ha priorita' come config dir.
    if platform.system() == 'Windows':
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        for cand in (os.path.join(base, 'dict'),
                     os.path.join(base, '..', 'dict')):
            cand = os.path.abspath(cand)
            if os.path.isdir(os.path.join(cand, 'hunspell')) or os.path.isdir(cand):
                os.environ['ENCHANT_CONFIG_DIR'] = cand
                os.environ.setdefault('DICPATH', cand)
                break


_bootstrap_dicts()

try:
    import enchant
    from enchant import DictWithPWL
    _ENCHANT_OK = True
    _ENCHANT_ERR = None
except Exception as e:          # ImportError o errori di init del backend
    enchant = None
    DictWithPWL = None
    _ENCHANT_OK = False
    _ENCHANT_ERR = str(e)


def is_available():
    """True se il motore ortografico e' utilizzabile."""
    return _ENCHANT_OK


def engine_error():
    """Messaggio d'errore se il motore non e' disponibile (altrimenti None)."""
    return _ENCHANT_ERR


# ---------------------------------------------------------------------------
# Percorso del dizionario personale (cross-platform)
# ---------------------------------------------------------------------------
def user_dict_path(filename='user_dict.txt'):
    """Percorso del dizionario personale, creando la cartella se serve.

    Debian/Linux : ~/.config/songpress/user_dict.txt
    Windows      : %APPDATA%\\Songpress\\user_dict.txt
    macOS        : ~/Library/Application Support/Songpress/user_dict.txt
    """
    cfg_dir = _app_config_dir()
    try:
        os.makedirs(cfg_dir, exist_ok=True)
    except OSError:
        cfg_dir = os.path.expanduser('~')
    return os.path.join(cfg_dir, filename)


# ---------------------------------------------------------------------------
# Installazione interattiva dei dizionari (download da LibreOffice/dictionaries)
# ---------------------------------------------------------------------------
# I dizionari Hunspell (coppie .aff + .dic) vengono scaricati dal repo ufficiale
# LibreOffice e salvati in <ENCHANT_CONFIG_DIR>/hunspell/, dove Enchant li rileva
# subito (verificato: nessun riavvio necessario).
#
# Ogni voce indica l'URL base del dizionario (senza estensione: l'installer
# aggiunge .aff e .dic) e un'etichetta. La maggior parte viene dal repo
# LibreOffice; il latino da un altro progetto open source. Tutti i percorsi
# sono verificati (HTTP 200). Per aggiungere una lingua basta una riga.
_LO = 'https://raw.githubusercontent.com/LibreOffice/dictionaries/master/'
_TB = 'https://raw.githubusercontent.com/titoBouzout/Dictionaries/master/'

# retro-compatibilita': alcune vecchie configurazioni usavano DICT_BASE_URL
DICT_BASE_URL = _LO

AVAILABLE_DICTS = {
    # codice : (url base senza estensione,     etichetta leggibile)
    # Il basename nell'URL puo' differire dal codice (es. tedesco): il file
    # viene comunque salvato come <codice>.dic/.aff, cosi' Enchant usa il codice.
    'it_IT': (_LO + 'it_IT/it_IT',    'Italiano'),
    'en_US': (_LO + 'en/en_US',       'English (US)'),
    'en_GB': (_LO + 'en/en_GB',       'English (UK)'),
    'es_ES': (_LO + 'es/es_ES',       'Español'),
    'pt_PT': (_LO + 'pt_PT/pt_PT',    'Português'),
    'pt_BR': (_LO + 'pt_BR/pt_BR',    'Português (Brasil)'),
    'de_DE': (_LO + 'de/de_DE_frami', 'Deutsch'),
    'nl_NL': (_LO + 'nl_NL/nl_NL',    'Nederlands'),
    'pl_PL': (_LO + 'pl_PL/pl_PL',    'Polski'),
    'ru_RU': (_LO + 'ru_RU/ru_RU',    'Русский'),
    'da_DK': (_LO + 'da_DK/da_DK',    'Dansk'),
    'cs_CZ': (_LO + 'cs_CZ/cs_CZ',    'Čeština'),
    'hu_HU': (_LO + 'hu_HU/hu_HU',    'Magyar'),
    'el_GR': (_LO + 'el_GR/el_GR',    'Ελληνικά'),
    'hr_HR': (_LO + 'hr_HR/hr_HR',    'Hrvatski'),
    'sl_SI': (_LO + 'sl_SI/sl_SI',    'Slovenščina'),
    'ro_RO': (_LO + 'ro/ro_RO',       'Română'),
    'la':    (_TB + 'la',             'Latina'),
}


def installed_languages():
    """Lingue attualmente riconosciute da Enchant (di sistema + installate)."""
    if not _ENCHANT_OK:
        return []
    try:
        return sorted(enchant.Broker().list_languages())
    except Exception:
        return []


def installable_languages():
    """Lingue del catalogo non ancora presenti, come lista (codice, etichetta)."""
    have = set(installed_languages())
    return [(code, AVAILABLE_DICTS[code][1])
            for code in AVAILABLE_DICTS if code not in have]


def dictionary_target_dir():
    """Cartella hunspell scrivibile dove installare i dizionari."""
    d = os.path.join(_enchant_data_dir(create=True), 'hunspell')
    os.makedirs(d, exist_ok=True)
    return d


def download_dictionary(lang, progress_cb=None):
    """Scarica e installa la coppia .aff/.dic per la lingua indicata.

    progress_cb(frac, msg) opzionale: frac in [0,1] o None (indeterminato).
    Ritorna il percorso della cartella di destinazione. Solleva eccezione in
    caso di errore di rete o lingua sconosciuta.
    """
    import urllib.request

    if lang not in AVAILABLE_DICTS:
        raise ValueError("Lingua non nel catalogo: %s" % lang)

    url_base, _label = AVAILABLE_DICTS[lang]
    target = dictionary_target_dir()

    # scarica prima su file temporanei, poi sposta: cosi' un download a meta'
    # non lascia un dizionario corrotto in posizione attiva.
    tmp_files = {}
    try:
        for i, ext in enumerate(('aff', 'dic')):
            url = url_base + '.' + ext
            if progress_cb:
                progress_cb(None, "Scaricamento %s.%s..." % (lang, ext))
            req = urllib.request.Request(
                url, headers={'User-Agent': 'Songpress-SpellInstaller'})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            # alcuni dizionari hanno un BOM UTF-8 iniziale che Hunspell puo'
            # non gradire: rimuovilo.
            if data[:3] == b'\xef\xbb\xbf':
                data = data[3:]
            if not data or (ext == 'dic' and not data[:16].strip()):
                raise IOError("File scaricato non valido: %s" % url)
            tmp = os.path.join(target, lang + '.' + ext + '.part')
            with open(tmp, 'wb') as f:
                f.write(data)
            tmp_files[ext] = tmp
            if progress_cb:
                progress_cb((i + 1) / 2.0, None)

        # entrambi scaricati: rinomina in posizione definitiva
        for ext, tmp in tmp_files.items():
            final = os.path.join(target, lang + '.' + ext)
            if os.path.exists(final):
                os.remove(final)
            os.replace(tmp, final)
    finally:
        # pulizia di eventuali .part rimasti (download fallito a meta')
        for tmp in tmp_files.values():
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass

    return target


def user_installed_languages():
    """Lingue i cui dizionari sono stati installati NELLA cartella utente.

    Sono le uniche rimovibili: i dizionari di sistema (apt) o inclusi nel wheel
    PyEnchant stanno altrove e non vanno toccati. Rileva le lingue in base ai
    file <lang>.dic presenti nella cartella hunspell scrivibile dell'utente.
    """
    target = dictionary_target_dir()
    langs = []
    try:
        for f in os.listdir(target):
            base, ext = os.path.splitext(f)
            if ext.lower() == '.dic' and base not in langs:
                langs.append(base)
    except OSError:
        pass
    return sorted(langs)


def remove_dictionary(lang):
    """Rimuove i file .aff/.dic della lingua DALLA sola cartella utente.

    Ritorna True se ha rimosso almeno un file. Non tocca mai i dizionari di
    sistema o del wheel (che stanno in altre cartelle non scrivibili qui).
    """
    target = dictionary_target_dir()
    removed = False
    for ext in ('aff', 'dic'):
        path = os.path.join(target, lang + '.' + ext)
        if os.path.exists(path):
            try:
                os.remove(path)
                removed = True
            except OSError:
                pass
    return removed


# ---------------------------------------------------------------------------
# Persistenza impostazioni (lingua di default, ondina all'avvio)
# ---------------------------------------------------------------------------
# Usa wx.Config, lo stesso meccanismo gia' impiegato da Songpress per
# tempoDisplay/colori/ecc.  Su Debian finisce in ~/.config/<app>, su Windows
# nel registro/ini a seconda della build: la scelta la fa wx, come per il
# resto delle preferenze dell'app.
class SpellSettings(object):
    """Carica/salva le preferenze del controllo ortografico via wx.Config."""

    PATH = '/SpellCheck'
    DEFAULT_COLOUR = '#DC1E1E'   # rosso (220, 30, 30), come l'ondina classica

    def __init__(self, language='it_IT', live_at_startup=False, enabled=True,
                 merge_chords=True, colour=None):
        self.language = language
        self.live_at_startup = live_at_startup
        self.enabled = enabled          # controllo ortografico attivo del tutto
        self.merge_chords = merge_chords  # ricomponi parole spezzate da accordi
        self.colour = colour or self.DEFAULT_COLOUR  # colore ondina "#RRGGBB"

    @classmethod
    def load(cls, default_language='it_IT'):
        s = cls(language=default_language)
        try:
            cfg = wx.Config.Get()
            cfg.SetPath(cls.PATH)
            s.language = cfg.Read('language', default_language) or default_language
            s.live_at_startup = cfg.ReadBool('liveAtStartup', False)
            s.enabled = cfg.ReadBool('enabled', True)
            s.merge_chords = cfg.ReadBool('mergeChords', True)
            s.colour = cfg.Read('underlineColour', cls.DEFAULT_COLOUR) \
                or cls.DEFAULT_COLOUR
            cfg.SetPath('/')
        except Exception:
            pass
        return s

    def save(self):
        try:
            cfg = wx.Config.Get()
            cfg.SetPath(self.PATH)
            cfg.Write('language', self.language)
            cfg.WriteBool('liveAtStartup', bool(self.live_at_startup))
            cfg.WriteBool('enabled', bool(self.enabled))
            cfg.WriteBool('mergeChords', bool(self.merge_chords))
            cfg.Write('underlineColour', self.colour or self.DEFAULT_COLOUR)
            cfg.SetPath('/')
            cfg.Flush()
        except Exception:
            pass


def colour_from_str(s, default='#DC1E1E'):
    """Converte '#RRGGBB' (o nome colore) in wx.Colour, con fallback robusto."""
    try:
        c = wx.Colour()
        c.Set(s)
        if c.IsOk():
            return c
    except Exception:
        pass
    c = wx.Colour()
    c.Set(default)
    return c


def colour_to_str(colour):
    """Converte un wx.Colour in stringa '#RRGGBB'."""
    try:
        return colour.GetAsString(wx.C2S_HTML_SYNTAX)
    except Exception:
        return SpellSettings.DEFAULT_COLOUR


# ---------------------------------------------------------------------------
# Tokenizzazione: estrae SOLO le parole cantate, saltando markup ChordPro
# ---------------------------------------------------------------------------
# Consideriamo "parola" una sequenza di lettere (incluse accentate/apostrofate).
# Vengono ESCLUSI dal controllo:
#   - accordi tra parentesi quadre        [Am]  [G7]  [Csus4/E]
#   - direttive tra parentesi graffe      {title: ...}  {comment: ...}
#   - meta-token vari (#, tag, ecc.)
#
# La funzione lavora su TUTTO il testo e restituisce, per ogni parola cantata,
# la tupla (word, start, end) con offset ASSOLUTI nel documento: servono sia
# per posizionare l'ondina su Scintilla sia per il "vai a" del dialogo.

_WORD_LETTERS = None  # inizializzato pigramente


def _is_word_char(ch):
    # lettere + apostrofo dritto/tipografico, trattino e underscore: questi
    # ultimi due fanno "ponte" tra sillabe/segmenti e vengono poi rimossi in
    # fase di ricomposizione (vedi flush in iter_words).
    return ch.isalpha() or ch in "'\u2019-_"


def iter_words(text, merge_chords=True):
    """Genera (word, start, end) per le sole parole di testo cantato.

    Salta il contenuto di [...] (accordi) e {...} (direttive).

    Con merge_chords=True (default) un accordo inline che spezza una parola NON
    la divide: i pezzi adiacenti vengono ricomposti in un'unica parola. Es.
        sal[LA-]varmi   -> "salvarmi"   (una parola, non "sal" + "varmi")
        Quando [Am]arrivi -> "Quando", "arrivi"  (separati: c'e' uno spazio)
    In fase di ricomposizione i trattini '-' e gli underscore '_' (sillabazione
    o giunzione) vengono rimossi, cosi' anche 'can[DO]-tare' -> "cantare".

    Con merge_chords=False vale il comportamento classico: un accordo inline
    spezza la parola in due token distinti.

    'start'/'end' sono gli offset assoluti nel documento (dal primo all'ultimo
    segmento di testo); servono per l'ondina e per il "vai a" del dialogo.
    """
    n = len(text)
    i = 0
    depth_square = 0   # dentro [ ... ]
    depth_curly = 0    # dentro { ... }

    segments = []      # segmenti (start, end) di testo della parola logica
    seg_start = -1     # inizio del segmento corrente

    def close_seg(end):
        nonlocal seg_start
        if seg_start >= 0 and end > seg_start:
            segments.append((seg_start, end))
        seg_start = -1

    def flush():
        nonlocal segments
        if not segments:
            return None
        raw = ''.join(text[s:e] for s, e in segments)
        # rimuovi trattini/underscore (sillabazione o giunzione tra segmenti)
        # e apostrofi/trattini ai bordi
        cleaned = raw.replace('-', '').replace('_', '').strip("'\u2019")
        result = None
        if len(cleaned) >= 2 and any(c.isalpha() for c in cleaned):
            result = (cleaned, segments[0][0], segments[-1][1])
        segments = []
        return result

    while i < n:
        ch = text[i]

        if ch == '[':
            # chiudi il segmento corrente; con merge_chords NON flushare la
            # parola: potrebbe continuare subito dopo la parentesi di chiusura.
            close_seg(i)
            if not merge_chords:
                r = flush()
                if r:
                    yield r
            depth_square += 1
            i += 1
            continue
        if ch == ']':
            if depth_square:
                depth_square -= 1
            i += 1
            continue
        if ch == '{':
            # una direttiva termina sempre la parola in corso
            close_seg(i)
            r = flush()
            if r:
                yield r
            depth_curly += 1
            i += 1
            continue
        if ch == '}':
            if depth_curly:
                depth_curly -= 1
            i += 1
            continue

        if depth_square or depth_curly:
            i += 1
            continue

        if _is_word_char(ch):
            if seg_start < 0:
                seg_start = i
        else:
            # un carattere non-parola (spazio, punteggiatura) chiude la parola
            close_seg(i)
            r = flush()
            if r:
                yield r
        i += 1

    close_seg(n)
    r = flush()
    if r:
        yield r


# ---------------------------------------------------------------------------
# Core: wrapper sul dizionario Enchant + dizionario personale (PWL)
# ---------------------------------------------------------------------------
class SpellChecker(object):
    """Wrapper sottile su enchant con dizionario personale persistente."""

    def __init__(self, lang='it_IT', pwl=None, merge_chords=True):
        if not _ENCHANT_OK:
            raise RuntimeError(_ENCHANT_ERR or 'PyEnchant non disponibile')

        self.lang = lang
        self.merge_chords = merge_chords
        self.pwl = pwl or user_dict_path()
        # assicura che il file esista (DictWithPWL non lo crea in ogni versione)
        if not os.path.exists(self.pwl):
            try:
                open(self.pwl, 'a', encoding='utf-8').close()
            except OSError:
                pass

        self._dict = self._make_dict(lang, self.pwl)

    @staticmethod
    def _make_dict(lang, pwl):
        try:
            return DictWithPWL(lang, pwl)
        except enchant.errors.DictNotFoundError:
            # lingua non installata: prova un fallback ragionevole
            b = enchant.Broker()
            langs = b.list_languages()
            if langs:
                return DictWithPWL(langs[0], pwl)
            raise

    # -- API ----------------------------------------------------------------
    def set_language(self, lang):
        self.lang = lang
        self._dict = self._make_dict(lang, self.pwl)

    @staticmethod
    def available_languages():
        if not _ENCHANT_OK:
            return []
        return sorted(enchant.Broker().list_languages())

    def check(self, word):
        return self._dict.check(word)

    def suggest(self, word):
        try:
            return self._dict.suggest(word)
        except Exception:
            return []

    def add(self, word):
        """Aggiunge la parola al dizionario PERSONALE (persistente su file)."""
        self._dict.add(word)          # enchant scrive nel PWL

    def ignore_session(self, word):
        """Ignora la parola solo per la sessione corrente (non salva su file)."""
        self._dict.add_to_session(word)

    def errors_in(self, text):
        """Genera (word, start, end) per ogni parola NON riconosciuta."""
        for word, start, end in iter_words(text, merge_chords=self.merge_chords):
            # ignora token con cifre (es. residui) o tutto maiuscolo (sigle)
            if any(c.isdigit() for c in word):
                continue
            if not self.check(word):
                yield word, start, end


# ---------------------------------------------------------------------------
# Evidenziazione LIVE su Scintilla (ondina rossa tipo editor moderno)
# ---------------------------------------------------------------------------
class LiveHighlighter(object):
    """Disegna l'ondina rossa sotto gli errori in un wx.stc.StyledTextCtrl."""

    # indicatore Scintilla dedicato (0-31). Nel frame non ne sono usati altri;
    # un valore alto evita conflitti con eventuali lexer.
    INDICATOR = 18

    def __init__(self, stc_ctrl, checker, colour=wx.Colour(220, 30, 30)):
        self.stc = stc_ctrl
        self.checker = checker
        self._setup_indicator(colour)
        self._timer = wx.Timer(stc_ctrl)
        stc_ctrl.Bind(wx.EVT_TIMER, self._on_timer, self._timer)

    def _setup_indicator(self, colour):
        s = self.stc
        s.IndicatorSetStyle(self.INDICATOR, wx.stc.STC_INDIC_SQUIGGLE)
        s.IndicatorSetForeground(self.INDICATOR, colour)

    def set_colour(self, colour):
        self.stc.IndicatorSetForeground(self.INDICATOR, colour)

    def clear(self):
        s = self.stc
        s.SetIndicatorCurrent(self.INDICATOR)
        s.IndicatorClearRange(0, s.GetLength())

    def refresh(self):
        """Ricontrolla l'intero documento e ridisegna le ondine."""
        s = self.stc
        text = s.GetText()
        s.SetIndicatorCurrent(self.INDICATOR)
        s.IndicatorClearRange(0, len(text))
        if not self.checker:
            return
        for _word, start, end in self.checker.errors_in(text):
            # Scintilla lavora in byte UTF-8: converti gli offset carattere->byte
            b_start = len(text[:start].encode('utf-8'))
            b_len = len(text[start:end].encode('utf-8'))
            s.IndicatorFillRange(b_start, b_len)

    def schedule_refresh(self, delay_ms=350):
        """Richiama refresh() con debounce, da agganciare a EVT_STC_MODIFIED."""
        self._timer.Start(delay_ms, oneShot=wx.TIMER_ONE_SHOT)

    def _on_timer(self, _evt):
        self.refresh()

    def word_at_position(self, pos):
        """Ritorna (word, start, end) della parola sotto la posizione byte, o None."""
        s = self.stc
        start = s.WordStartPosition(pos, True)
        end = s.WordEndPosition(pos, True)
        if end > start:
            return s.GetTextRange(start, end), start, end
        return None


# ---------------------------------------------------------------------------
# Dialogo "Controllo ortografia" in stile Word (batch, scorre gli errori)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Icone dei pulsanti del dialogo (cartella img/ dell'app)
# ---------------------------------------------------------------------------
# Nome file -> pulsante:
#   minus_checked.png        -> Ignora / Ignora tutto  (salta la parola)
#   minus_checked_all.png    -> Ignora tutto  (salta la parola)
#   plus_checked.png         -> Aggiungi al dizionario
#   substitution_checked.png -> Cambia / Cambia tutto   (sostituisci)
#   substitution_checked_all.png -> Cambia tutto   (sostituisci)
_ICON_CACHE = {}


def _button_icon(name):
    """Restituisce un wx.Bitmap 16x16 per un pulsante, o wx.NullBitmap.

    Cerca prima con il meccanismo standard dell'app (Globals.glb.AddPath),
    poi ripiega su una cartella 'img/' accanto al modulo (dev) o all'exe
    (build "frozen"). Non solleva mai eccezioni: se l'icona manca, il
    pulsante resta senza immagine.
    """
    if name in _ICON_CACHE:
        return _ICON_CACHE[name]

    path = None
    try:
        from .Globals import glb          # meccanismo standard di Songpress
        cand = glb.AddPath('img/' + name)
        if cand and os.path.isfile(cand):
            path = cand
    except Exception:
        path = None

    if path is None:
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        cand = os.path.join(base, 'img', name)
        if os.path.isfile(cand):
            path = cand

    bmp = wx.NullBitmap
    if path:
        try:
            img = wx.Image(path, wx.BITMAP_TYPE_PNG)
            if img.IsOk():
                bmp = wx.Bitmap(img)
        except Exception:
            bmp = wx.NullBitmap

    _ICON_CACHE[name] = bmp
    return bmp


class SpellCheckDialog(wx.Dialog):
    """Scorre gli errori uno per uno con Ignora / Ignora tutto / Aggiungi /
    Cambia / Cambia tutto. Applica le sostituzioni direttamente sul controllo
    Scintilla passato come 'target'."""

    def __init__(self, parent, checker, target_stc, show_icons=True):
        wx.Dialog.__init__(self, parent, title=_tr("Spell check"),
                           style=wx.DEFAULT_DIALOG_STYLE)
        self.checker = checker
        self.stc = target_stc
        self.show_icons = show_icons
        self._errors = []       # lista di (word, start, end) in offset CARATTERE
        self._idx = 0
        self._ignored_all = set()
        self._replace_all = {}  # word -> replacement
        self._no_errors = False

        self._build_ui()
        self._collect_errors()
        # Il primo aggiornamento va eseguito DOPO che ShowModal ha reso il
        # dialogo modale: CallAfter lo accoda al ciclo eventi successivo, cosi'
        # se non ci sono errori EndModal() viene chiamato su un dialogo modale.
        wx.CallAfter(self._show_current)

    # -- UI -----------------------------------------------------------------
    def _build_ui(self):
        outer = wx.BoxSizer(wx.VERTICAL)

        # contatore errori ancora da correggere (aggiornato in _show_current)
        self.lblCount = wx.StaticText(self, label="")
        f = self.lblCount.GetFont()
        f.SetWeight(wx.FONTWEIGHT_BOLD)
        self.lblCount.SetFont(f)
        outer.Add(self.lblCount, 0, wx.LEFT | wx.RIGHT | wx.TOP, 12)

        grid = wx.FlexGridSizer(2, 2, 6, 8)
        grid.AddGrowableCol(1, 1)

        grid.Add(wx.StaticText(self, label=_tr("Not in dictionary:")),
                 0, wx.ALIGN_CENTER_VERTICAL)
        self.txtWord = wx.TextCtrl(self, size=(280, -1))
        grid.Add(self.txtWord, 1, wx.EXPAND)

        grid.Add(wx.StaticText(self, label=_tr("Suggestions:")),
                 0, wx.ALIGN_TOP)
        self.lstSuggest = wx.ListBox(self, size=(280, 120))
        grid.Add(self.lstSuggest, 1, wx.EXPAND)

        outer.Add(grid, 1, wx.EXPAND | wx.ALL, 12)

        # riga lingua
        lang_row = wx.BoxSizer(wx.HORIZONTAL)
        lang_row.Add(wx.StaticText(self, label=_tr("Language:")),
                     0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.choLang = wx.Choice(self, choices=self.checker.available_languages())
        if self.checker.lang in self.checker.available_languages():
            self.choLang.SetStringSelection(self.checker.lang)
        self.choLang.Bind(wx.EVT_CHOICE, self._on_lang)
        lang_row.Add(self.choLang, 0)
        outer.Add(lang_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # pulsanti
        btns = wx.BoxSizer(wx.HORIZONTAL)
        self.btnIgnore = wx.Button(self, label=_tr("Ignore"))
        self.btnIgnoreAll = wx.Button(self, label=_tr("Ignore all"))
        self.btnAdd = wx.Button(self, label=_tr("Add to dictionary"))
        self.btnChange = wx.Button(self, label=_tr("Change"))
        self.btnChangeAll = wx.Button(self, label=_tr("Change all"))
        self.btnClose = wx.Button(self, wx.ID_CLOSE)
        for b in (self.btnIgnore, self.btnIgnoreAll, self.btnAdd,
                  self.btnChange, self.btnChangeAll, self.btnClose):
            btns.Add(b, 0, wx.RIGHT, 6)
        outer.Add(btns, 0, wx.ALL, 12)

        self.SetSizerAndFit(outer)

        # icone accanto ai pulsanti (opzione in Preferenze -> Controllo
        # ortografico). Va fatto DOPO SetSizerAndFit: applica i bitmap e
        # ridimensiona il dialogo per i pulsanti diventati piu' larghi.
        if self.show_icons:
            self._apply_button_icons()

        self.btnIgnore.Bind(wx.EVT_BUTTON, self._on_ignore)
        self.btnIgnoreAll.Bind(wx.EVT_BUTTON, self._on_ignore_all)
        self.btnAdd.Bind(wx.EVT_BUTTON, self._on_add)
        self.btnChange.Bind(wx.EVT_BUTTON, self._on_change)
        self.btnChangeAll.Bind(wx.EVT_BUTTON, self._on_change_all)
        self.btnClose.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))
        self.lstSuggest.Bind(wx.EVT_LISTBOX_DCLICK, self._on_change)

    def _apply_button_icons(self):
        """Mette un'icona 16x16 accanto ai pulsanti d'azione.

        Se un'icona manca (file non trovato) il relativo pulsante resta solo
        testo: _button_icon() ritorna wx.NullBitmap e SetBitmap la ignora.
        """
        mapping = (
            (self.btnIgnore,    'minus_checked.png'),
            (self.btnIgnoreAll, 'minus_checked_all.png'),
            (self.btnAdd,       'plus_checked.png'),
            (self.btnChange,    'substitution_checked.png'),
            (self.btnChangeAll, 'substitution_checked_all.png'),
        )
        for btn, icon in mapping:
            bmp = _button_icon(icon)
            if bmp and bmp.IsOk():
                btn.SetBitmap(bmp)
                # icona a sinistra dell'etichetta, con un piccolo margine
                try:
                    btn.SetBitmapMargins(4, 0)
                except Exception:
                    pass
        # ricalcola la disposizione: i pulsanti ora sono piu' larghi
        sizer = self.GetSizer()
        if sizer is not None:
            sizer.Fit(self)

    # -- logica -------------------------------------------------------------
    def _collect_errors(self):
        text = self.stc.GetText()
        self._errors = list(self.checker.errors_in(text))
        self._idx = 0

    def _show_current(self):
        # salta parole ignorate globalmente / gia' sostituite ovunque
        while self._idx < len(self._errors):
            word, s, e = self._errors[self._idx]
            if word in self._ignored_all or word in self._replace_all:
                if word in self._replace_all:
                    self._apply_replacement(s, e, self._replace_all[word])
                    self._collect_errors()  # gli offset cambiano: ricalcola
                    continue
                self._idx += 1
                continue
            break

        if self._idx >= len(self._errors):
            wx.MessageBox(_tr("Spell check complete."),
                          _tr("Spell check"), wx.OK | wx.ICON_INFORMATION, self)
            # Chiudi in modo sicuro: EndModal solo se il dialogo e' gia' modale
            # (se _show_current viene chiamato durante __init__, prima di
            # ShowModal, EndModal fallirebbe con "non modal dialog").
            if self.IsModal():
                self.EndModal(wx.ID_OK)
            else:
                self._no_errors = True
                self.Close()
            return

        word, s, e = self._errors[self._idx]
        self.txtWord.SetValue(word)
        self.lstSuggest.Set(self.checker.suggest(word) or [])
        if self.lstSuggest.GetCount():
            self.lstSuggest.SetSelection(0)
        # aggiorna il contatore di errori ancora da correggere
        self._update_count()
        # evidenzia nel testo
        b_s = self._char_to_byte(s)
        b_e = self._char_to_byte(e)
        self.stc.SetSelection(b_s, b_e)
        self.stc.EnsureCaretVisible()

    def _remaining_count(self):
        """Numero di errori dalla posizione corrente in poi non ancora gestiti
        (esclude quelli ignorati globalmente o gia' sostituiti ovunque)."""
        n = 0
        for k in range(self._idx, len(self._errors)):
            w = self._errors[k][0]
            if w in self._ignored_all or w in self._replace_all:
                continue
            n += 1
        return n

    def _update_count(self):
        n = self._remaining_count()
        if n == 1:
            self.lblCount.SetLabel(_tr("1 error left"))
        else:
            self.lblCount.SetLabel(_tr("%d errors left") % n)
        self.lblCount.GetParent().Layout()

    def _char_to_byte(self, char_off):
        """Converte un offset in caratteri in offset byte UTF-8 (Scintilla)."""
        text = self.stc.GetText()
        return len(text[:char_off].encode('utf-8'))

    def _apply_replacement(self, s, e, repl):
        b_s = self._char_to_byte(s)
        b_e = self._char_to_byte(e)
        self.stc.SetTargetStart(b_s)
        self.stc.SetTargetEnd(b_e)
        self.stc.ReplaceTarget(repl)

    def _chosen_replacement(self):
        sel = self.lstSuggest.GetStringSelection()
        typed = self.txtWord.GetValue().strip()
        # se l'utente ha modificato la parola a mano, usa quella
        word = self._errors[self._idx][0]
        if typed and typed != word:
            return typed
        return sel or typed

    # -- handler ------------------------------------------------------------
    def _on_lang(self, _evt):
        self.checker.set_language(self.choLang.GetStringSelection())
        self._collect_errors()
        self._show_current()

    def _on_ignore(self, _evt):
        self._idx += 1
        self._show_current()

    def _on_ignore_all(self, _evt):
        word = self._errors[self._idx][0]
        self._ignored_all.add(word)
        self.checker.ignore_session(word)
        self._idx += 1
        self._show_current()

    def _on_add(self, _evt):
        word = self._errors[self._idx][0]
        self.checker.add(word)         # salva nel dizionario personale
        self._ignored_all.add(word)
        self._idx += 1
        self._show_current()

    def _on_change(self, _evt):
        repl = self._chosen_replacement()
        if not repl:
            return
        _w, s, e = self._errors[self._idx]
        self._apply_replacement(s, e, repl)
        self._collect_errors()          # offset cambiati
        self._show_current()

    def _on_change_all(self, _evt):
        repl = self._chosen_replacement()
        if not repl:
            return
        word = self._errors[self._idx][0]
        self._replace_all[word] = repl
        _w, s, e = self._errors[self._idx]
        self._apply_replacement(s, e, repl)
        self._collect_errors()
        self._show_current()


# ---------------------------------------------------------------------------
# Pannello preferenze ortografia (lingua di default + ondina all'avvio)
# ---------------------------------------------------------------------------
class SpellPrefsDialog(wx.Dialog):
    """Piccolo pannello di preferenze per il controllo ortografico.

    Permette di scegliere la lingua di default, attivare l'ondina all'avvio,
    e gestire il dizionario personale (apri file / svuota). Le impostazioni
    vengono salvate in wx.Config tramite SpellSettings.
    """

    def __init__(self, parent, settings, available_langs, pwl_path, pref=None):
        wx.Dialog.__init__(self, parent, title=_tr("Spell check options"),
                           style=wx.DEFAULT_DIALOG_STYLE)
        self.settings = settings
        # Preferenze generali (Preferences): qui vive l'opzione "icone accanto
        # ai pulsanti", la stessa presente nella scheda Preferenze -> Controllo
        # ortografico. Le due caselle restano quindi sincronizzate.
        self.pref = pref
        self.pwl_path = pwl_path

        outer = wx.BoxSizer(wx.VERTICAL)

        box = wx.StaticBoxSizer(
            wx.StaticBox(self, label=_tr("Spell checking")), wx.VERTICAL)

        # abilita del tutto
        self.cbEnabled = wx.CheckBox(self, label=_tr("Enable spell checking"))
        self.cbEnabled.SetValue(settings.enabled)
        box.Add(self.cbEnabled, 0, wx.ALL, 6)

        # lingua di default
        lang_row = wx.BoxSizer(wx.HORIZONTAL)
        lang_row.Add(wx.StaticText(self, label=_tr("Default language:")),
                     0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        choices = available_langs or [settings.language]
        self.choLang = wx.Choice(self, choices=choices)
        if settings.language in choices:
            self.choLang.SetStringSelection(settings.language)
        elif choices:
            self.choLang.SetSelection(0)
        lang_row.Add(self.choLang, 0)
        box.Add(lang_row, 0, wx.ALL, 6)

        # ondina all'avvio
        self.cbLive = wx.CheckBox(
            self, label=_tr("Underline misspelled words at startup"))
        self.cbLive.SetValue(settings.live_at_startup)
        box.Add(self.cbLive, 0, wx.ALL, 6)

        # ricomposizione parole spezzate dagli accordi inline
        self.cbMerge = wx.CheckBox(
            self, label=_tr("Merge words split by inline chords (e.g. sal[LA-]varmi)"))
        self.cbMerge.SetValue(getattr(settings, 'merge_chords', True))
        self.cbMerge.SetToolTip(_tr(
            "Treat a chord inside a word as invisible: 'sal[LA-]varmi' is "
            "checked as 'salvarmi' instead of 'sal' + 'varmi'."))
        box.Add(self.cbMerge, 0, wx.ALL, 6)

        # colore dell'ondina sotto le parole errate
        col_row = wx.BoxSizer(wx.HORIZONTAL)
        col_row.Add(wx.StaticText(self, label=_tr("Underline colour:")),
                    0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.cpColour = wx.ColourPickerCtrl(
            self, colour=colour_from_str(getattr(settings, 'colour',
                                                 SpellSettings.DEFAULT_COLOUR)))
        col_row.Add(self.cpColour, 0, wx.ALIGN_CENTER_VERTICAL)
        box.Add(col_row, 0, wx.ALL, 6)

        # icone accanto ai pulsanti del dialogo di controllo (Ignora /
        # Aggiungi / Cambia ...). Legata a Preferences.showSpellButtonIcons:
        # e' la stessa opzione della scheda Preferenze -> Controllo ortografico.
        self.cbShowIcons = wx.CheckBox(
            self, label=_tr("Show icons next to buttons"))
        self.cbShowIcons.SetValue(
            getattr(self.pref, 'showSpellButtonIcons', True))
        self.cbShowIcons.SetToolTip(_tr(
            "Show a small icon next to the Ignore / Add to dictionary / "
            "Change buttons in the spell check dialog."))
        box.Add(self.cbShowIcons, 0, wx.ALL, 6)

        outer.Add(box, 0, wx.EXPAND | wx.ALL, 10)

        # dizionario personale
        dbox = wx.StaticBoxSizer(
            wx.StaticBox(self, label=_tr("Personal dictionary")), wx.VERTICAL)
        dbox.Add(wx.StaticText(self, label=pwl_path), 0, wx.ALL, 6)
        drow = wx.BoxSizer(wx.HORIZONTAL)
        self.btnOpen = wx.Button(self, label=_tr("Open..."))
        self.btnClear = wx.Button(self, label=_tr("Empty"))
        drow.Add(self.btnOpen, 0, wx.RIGHT, 6)
        drow.Add(self.btnClear, 0)
        dbox.Add(drow, 0, wx.ALL, 6)
        outer.Add(dbox, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # installer dizionari (attivo anche senza lingue: serve proprio a quello)
        self.btnInstallDicts = wx.Button(
            self, label=_tr("Manage dictionaries..."))
        outer.Add(self.btnInstallDicts, 0,
                  wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # OK / Annulla
        btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        outer.Add(btns, 0, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(outer)

        self.btnOpen.Bind(wx.EVT_BUTTON, self._on_open_dict)
        self.btnClear.Bind(wx.EVT_BUTTON, self._on_clear_dict)
        self.btnInstallDicts.Bind(wx.EVT_BUTTON, self._on_install_dicts)
        self.Bind(wx.EVT_BUTTON, self._on_ok, id=wx.ID_OK)

        # se il motore non e' installato, disabilita i controlli e avvisa
        if not available_langs:
            self.choLang.Enable(False)
            self.cbLive.Enable(False)

    # -- installer dizionari (ripopola la scelta lingua) --------------------
    def _on_install_dicts(self, _evt):
        def _after(lang):
            cur = self.choLang.GetStringSelection()
            langs = SpellChecker.available_languages()
            self.choLang.Set(langs)
            if cur in langs:
                self.choLang.SetStringSelection(cur)
            elif lang in langs:
                self.choLang.SetStringSelection(lang)
            self.choLang.Enable(bool(langs))
            self.cbLive.Enable(bool(langs))
        dlg = DictInstallerDialog(self, on_installed=_after)
        dlg.ShowModal()
        dlg.Destroy()

    # -- persistenza sull'oggetto settings ---------------------------------
    def _on_ok(self, evt):
        self.settings.enabled = self.cbEnabled.GetValue()
        if self.choLang.GetStringSelection():
            self.settings.language = self.choLang.GetStringSelection()
        self.settings.live_at_startup = self.cbLive.GetValue()
        self.settings.merge_chords = self.cbMerge.GetValue()
        self.settings.colour = colour_to_str(self.cpColour.GetColour())
        self.settings.save()
        # icone pulsanti -> preferenza globale (sincronizzata con Preferenze)
        if self.pref is not None:
            self.pref.showSpellButtonIcons = self.cbShowIcons.GetValue()
            try:
                self.pref.Save()
            except Exception:
                pass
        evt.Skip()   # lascia proseguire la chiusura con ID_OK

    # -- dizionario personale ----------------------------------------------
    def _on_open_dict(self, _evt):
        path = self.pwl_path
        if not os.path.exists(path):
            try:
                open(path, 'a', encoding='utf-8').close()
            except OSError:
                pass
        # apri con l'editor di sistema
        try:
            if platform.system() == 'Windows':
                os.startfile(path)                      # noqa
            elif platform.system() == 'Darwin':
                import subprocess
                subprocess.Popen(['open', path])
            else:
                import subprocess
                subprocess.Popen(['xdg-open', path])
        except Exception:
            wx.MessageBox(path, _tr("Personal dictionary"),
                          wx.OK | wx.ICON_INFORMATION, self)

    def _on_clear_dict(self, _evt):
        if wx.MessageBox(
                _tr("Remove all words from the personal dictionary?"),
                _tr("Personal dictionary"),
                wx.YES_NO | wx.ICON_QUESTION, self) == wx.YES:
            try:
                open(self.pwl_path, 'w', encoding='utf-8').close()
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Installer interattivo dei dizionari
# ---------------------------------------------------------------------------
class DictInstallerDialog(wx.Dialog):
    """Mostra le lingue installate e quelle scaricabili, e installa quella scelta.

    on_installed(lang) opzionale: callback chiamata dopo un'installazione
    riuscita (il manager la usa per ricreare il checker e aggiornare le liste).
    """

    def __init__(self, parent, on_installed=None):
        wx.Dialog.__init__(self, parent, title=_tr("Manage dictionaries"),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.on_installed = on_installed

        outer = wx.BoxSizer(wx.VERTICAL)

        if not is_available():
            outer.Add(wx.StaticText(
                self, label=_tr("Spell checking engine not available.")),
                0, wx.ALL, 12)
            outer.Add(self.CreateButtonSizer(wx.CLOSE), 0, wx.EXPAND | wx.ALL, 10)
            self.SetSizerAndFit(outer)
            return

        # lingue installate
        outer.Add(wx.StaticText(self, label=_tr("Installed languages:")),
                  0, wx.LEFT | wx.RIGHT | wx.TOP, 12)
        self.lstInstalled = wx.ListBox(self, size=(320, 90))
        outer.Add(self.lstInstalled, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)

        # lingue installabili
        outer.Add(wx.StaticText(self, label=_tr("Available to download:")),
                  0, wx.LEFT | wx.RIGHT | wx.TOP, 12)
        self.lstAvail = wx.ListBox(self, size=(320, 110))
        outer.Add(self.lstAvail, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)

        note = wx.StaticText(self, label=_tr(
            "Dictionaries are downloaded from the LibreOffice project."))
        note.SetForegroundColour(wx.Colour(110, 110, 110))
        outer.Add(note, 0, wx.ALL, 12)

        # pulsanti
        row = wx.BoxSizer(wx.HORIZONTAL)
        self.btnInstall = wx.Button(self, label=_tr("Install selected"))
        self.btnUninstall = wx.Button(self, label=_tr("Uninstall"))
        row.Add(self.btnInstall, 0, wx.RIGHT, 8)
        row.Add(self.btnUninstall, 0, wx.RIGHT, 8)
        row.AddStretchSpacer(1)
        self.btnClose = wx.Button(self, wx.ID_CLOSE)
        row.Add(self.btnClose, 0)
        outer.Add(row, 0, wx.EXPAND | wx.ALL, 12)

        self.SetSizerAndFit(outer)

        self.btnInstall.Bind(wx.EVT_BUTTON, self._on_install)
        self.btnUninstall.Bind(wx.EVT_BUTTON, self._on_uninstall)
        self.lstAvail.Bind(wx.EVT_LISTBOX_DCLICK, self._on_install)
        self.lstInstalled.Bind(wx.EVT_LISTBOX, self._on_select_installed)
        self.btnClose.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))

        self._refresh_lists()

    def _refresh_lists(self):
        # codici installati, nell'ordine mostrato; segna quelli rimovibili
        self._installed_codes = installed_languages()
        self._removable = set(user_installed_languages())
        labels = []
        for code in self._installed_codes:
            name = "  (%s)" % AVAILABLE_DICTS[code][1] if code in AVAILABLE_DICTS else ""
            tag = "" if code in self._removable else _tr("  [system]")
            labels.append("%s%s%s" % (code, name, tag))
        self.lstInstalled.Set(labels)

        self._avail = installable_languages()   # lista (code, label)
        self.lstAvail.Set(["%s  —  %s" % (code, label)
                           for code, label in self._avail])
        if self._avail:
            self.lstAvail.SetSelection(0)
        self.btnInstall.Enable(bool(self._avail))
        self.btnUninstall.Enable(False)   # finche' non si seleziona una rimovibile

    def _on_select_installed(self, _evt):
        sel = self.lstInstalled.GetSelection()
        removable = (sel != wx.NOT_FOUND and sel < len(self._installed_codes)
                     and self._installed_codes[sel] in self._removable)
        self.btnUninstall.Enable(bool(removable))

    def _on_uninstall(self, _evt):
        sel = self.lstInstalled.GetSelection()
        if sel == wx.NOT_FOUND or sel >= len(self._installed_codes):
            return
        code = self._installed_codes[sel]
        if code not in self._removable:
            return
        label = AVAILABLE_DICTS[code][1] if code in AVAILABLE_DICTS else code
        if wx.MessageBox(
                _tr("Remove the '%s' dictionary?") % label,
                _tr("Manage dictionaries"),
                wx.YES_NO | wx.ICON_QUESTION, self) != wx.YES:
            return
        if remove_dictionary(code):
            wx.MessageBox(_tr("'%s' removed.") % label,
                          _tr("Manage dictionaries"),
                          wx.OK | wx.ICON_INFORMATION, self)
            if self.on_installed:
                self.on_installed(code)   # il manager ricrea il checker
            self._refresh_lists()
        else:
            wx.MessageBox(_tr("Could not remove '%s'.") % label,
                          _tr("Manage dictionaries"),
                          wx.OK | wx.ICON_ERROR, self)

    def _on_install(self, _evt):
        sel = self.lstAvail.GetSelection()
        if sel == wx.NOT_FOUND or sel >= len(self._avail):
            return
        code, label = self._avail[sel]

        prog = wx.ProgressDialog(
            _tr("Manage dictionaries"),
            _tr("Downloading %s...") % label,
            maximum=100, parent=self,
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)

        def cb(frac, msg):
            if frac is None:
                prog.Pulse(msg or "")
            else:
                prog.Update(int(frac * 100), msg or "")

        ok, err = False, None
        try:
            with wx.BusyCursor():
                download_dictionary(code, progress_cb=cb)
            ok = True
        except Exception as e:
            err = str(e)
        finally:
            prog.Destroy()

        if ok:
            wx.MessageBox(
                _tr("'%s' installed successfully.") % label,
                _tr("Manage dictionaries"),
                wx.OK | wx.ICON_INFORMATION, self)
            if self.on_installed:
                self.on_installed(code)
            self._refresh_lists()
        else:
            wx.MessageBox(
                _tr("Could not install '%s'.\n\n%s") % (label, err or ""),
                _tr("Manage dictionaries"),
                wx.OK | wx.ICON_ERROR, self)


# ---------------------------------------------------------------------------
# Traduzione: usa il _ di Songpress se presente, altrimenti identita'
# ---------------------------------------------------------------------------
try:
    _tr = wx.GetTranslation
except Exception:
    def _tr(s):
        return s


# ---------------------------------------------------------------------------
# Facade per SongpressFrame: una sola classe che tiene tutto insieme.
# ---------------------------------------------------------------------------
class SpellManager(object):
    """Punto d'ingresso unico per il frame.

    Uso in SongpressFrame:
        self.speller = SpellManager(self, lang="it_IT")

        def OnSpellCheck(self, evt):
            self.speller.open_dialog()

        def OnSpellLive(self, evt):
            self.speller.toggle_live()
    """

    def __init__(self, owner, lang='it_IT'):
        self.owner = owner
        self.frame = owner.frame
        self.stc = owner.text
        self.checker = None
        self.highlighter = None
        self._live = False

        # impostazioni persistenti (lingua di default, ondina all'avvio, on/off)
        self.settings = SpellSettings.load(default_language=lang)

        if not is_available() or not self.settings.enabled:
            return
        try:
            self.checker = SpellChecker(lang=self.settings.language,
                                        merge_chords=self.settings.merge_chords)
            self.highlighter = LiveHighlighter(
                self.stc, self.checker,
                colour=colour_from_str(self.settings.colour))
            # applica l'ondina all'avvio se richiesto nelle preferenze
            if self.settings.live_at_startup:
                self.toggle_live(enable=True)
        except Exception as e:
            self.checker = None
            self._init_error = str(e)

    # -- stato --------------------------------------------------------------
    def ready(self):
        return self.checker is not None

    def _warn_unavailable(self):
        msg = _tr("Spell checking is not available.\n"
                  "Install PyEnchant (pip install pyenchant) and the "
                  "dictionaries (e.g. hunspell-it, hunspell-en-us).")
        if _ENCHANT_ERR:
            msg += "\n\n(%s)" % _ENCHANT_ERR
        wx.MessageBox(msg, _tr("Spell check"), wx.OK | wx.ICON_WARNING, self.frame)

    # -- dialogo batch ------------------------------------------------------
    def open_dialog(self):
        if not self.ready():
            self._warn_unavailable()
            return
        # Pre-controllo: se non ci sono errori, mostra solo l'avviso senza
        # aprire (e chiudere subito) il dialogo.
        text = self.stc.GetText()
        if next(self.checker.errors_in(text), None) is None:
            wx.MessageBox(_tr("Spell check complete. No errors found."),
                          _tr("Spell check"), wx.OK | wx.ICON_INFORMATION,
                          self.frame)
            return
        # l'opzione "icone accanto ai pulsanti" vive nelle Preferenze generali
        # (Preferences.showSpellButtonIcons). Fallback a True se assente.
        pref = getattr(getattr(self, 'owner', None), 'pref', None) \
            or getattr(self.frame, 'pref', None)
        show_icons = getattr(pref, 'showSpellButtonIcons', True) if pref else True
        dlg = SpellCheckDialog(self.frame, self.checker, self.stc,
                               show_icons=show_icons)
        dlg.ShowModal()
        dlg.Destroy()
        if self.highlighter:
            self.highlighter.refresh()

    # -- ondina live --------------------------------------------------------
    def toggle_live(self, enable=None):
        if not self.ready():
            self._warn_unavailable()
            return False
        self._live = (not self._live) if enable is None else enable
        if self._live:
            self.stc.Bind(wx.stc.EVT_STC_MODIFIED, self._on_modified)
            self.highlighter.refresh()
        else:
            self.stc.Unbind(wx.stc.EVT_STC_MODIFIED, handler=self._on_modified)
            self.highlighter.clear()
        return self._live

    def is_live(self):
        return self._live

    def _on_modified(self, evt):
        # ridisegna solo su inserimenti/cancellazioni di testo
        if evt.GetModificationType() & (wx.stc.STC_MOD_INSERTTEXT |
                                        wx.stc.STC_MOD_DELETETEXT):
            self.highlighter.schedule_refresh()
        evt.Skip()

    def set_language(self, lang):
        if self.checker:
            self.checker.set_language(lang)
            if self._live:
                self.highlighter.refresh()

    # -- pannello preferenze ------------------------------------------------
    def open_preferences(self):
        """Mostra il pannello preferenze ortografia e applica le scelte."""
        langs = SpellChecker.available_languages() if is_available() else []
        pwl = self.checker.pwl if self.checker else user_dict_path()
        was_enabled = self.settings.enabled

        pref = getattr(getattr(self, 'owner', None), 'pref', None) \
            or getattr(self.frame, 'pref', None)
        dlg = SpellPrefsDialog(self.frame, self.settings, langs, pwl, pref=pref)
        if dlg.ShowModal() == wx.ID_OK:
            # 1) on/off globale
            if self.settings.enabled and self.checker is None and is_available():
                # era disattivato: crea ora il checker
                try:
                    self.checker = SpellChecker(
                        lang=self.settings.language,
                        merge_chords=self.settings.merge_chords)
                    self.highlighter = LiveHighlighter(
                        self.stc, self.checker,
                        colour=colour_from_str(self.settings.colour))
                except Exception as e:
                    self.checker = None
                    self._init_error = str(e)
            elif not self.settings.enabled and self.checker is not None:
                # disattivato ora: spegni ondina e pulisci
                self.toggle_live(enable=False)
                self.checker = None

            # 2) lingua, ricomposizione parole e colore ondina
            if self.checker:
                self.set_language(self.settings.language)
                self.checker.merge_chords = self.settings.merge_chords
                if self.highlighter:
                    self.highlighter.set_colour(
                        colour_from_str(self.settings.colour))

            # 3) ondina: allinea lo stato attuale alla preferenza "all'avvio"
            #    (comodo: la spunta accende/spegne subito l'ondina)
            if self.checker:
                self.toggle_live(enable=self.settings.live_at_startup)

        dlg.Destroy()
        return self.settings

    # -- installer dizionari ------------------------------------------------
    def open_dict_installer(self):
        """Apre l'installer interattivo dei dizionari (download da LibreOffice)."""
        if not is_available():
            self._warn_unavailable()
            return

        def _after_install(lang):
            # ricrea il checker cosi' la nuova lingua e' subito disponibile
            try:
                cur = self.settings.language
                self.checker = SpellChecker(
                    lang=cur, merge_chords=self.settings.merge_chords)
                if self.highlighter:
                    self.highlighter.checker = self.checker
                    if self._live:
                        self.highlighter.refresh()
            except Exception:
                pass

        dlg = DictInstallerDialog(self.frame, on_installed=_after_install)
        dlg.ShowModal()
        dlg.Destroy()


###############################################################
#  ISTRUZIONI DI INTEGRAZIONE  (da fare in SongpressFrame.py e nell'XRC)
###############################################################
#
# 1) SongpressFrame.py -- import (in cima, con gli altri "from .")
#
#        from .SpellChecker import SpellManager
#
# 2) SongpressFrame.py -- nel __init__ del frame, DOPO "self.text = Editor(self)"
#    (intorno alla riga 839):
#
#        self.speller = SpellManager(self, lang="it_IT")
#
# 3) SongpressFrame.py -- nel metodo dove ci sono gli altri Bind(...)
#    (vicino a  Bind(self.OnSyntaxCheck, 'syntaxCheck')  ~riga 1532):
#
#        Bind(self.OnSpellCheck,   'spellCheck')
#        Bind(self.OnSpellLive,    'spellLive')
#        Bind(self.OnSpellOptions, 'spellOptions')
#
# 4) SongpressFrame.py -- aggiungi i tre handler (accanto a OnSyntaxCheck):
#
#        def OnSpellCheck(self, evt):
#            self.speller.open_dialog()
#
#        def OnSpellLive(self, evt):
#            on = self.speller.toggle_live()
#            self.menuBar.Check(self.spellLiveMenuId, on)   # se usi un check item
#
#        def OnSpellOptions(self, evt):
#            self.speller.open_preferences()
#            # riallinea l'eventuale check item "ondina live" allo stato attuale
#            if hasattr(self, 'spellLiveMenuId'):
#                self.menuBar.Check(self.spellLiveMenuId, self.speller.is_live())
#
# 5) songpress.xrc  e  songpress_it.xrc -- aggiungi tre voci nel menu Strumenti,
#    subito dopo il blocco <object class="wxMenuItem" name="syntaxCheck"> ... </object>:
#
#        <object class="wxMenuItem" name="spellCheck">
#          <label>_Spell check...</label>
#          <accel>F6</accel>
#          <help>Check spelling of the song lyrics (chords are ignored)</help>
#        </object>
#        <object class="wxMenuItem" name="spellLive" checkable="1">
#          <label>Live spell _underline</label>
#          <help>Underline misspelled words while typing</help>
#        </object>
#        <object class="wxMenuItem" name="spellOptions">
#          <label>Spell check o_ptions...</label>
#          <help>Default language, live underline at startup, personal dictionary</help>
#        </object>
#
#    (nel file _it.xrc traduci label/help in italiano:
#       "Controllo _ortografico...", "_Sottolineatura ortografica live",
#       "O_pzioni ortografia...")
#
#    NB: se preferisci un'unica finestra di preferenze, puoi incastonare i tre
#    controlli di SpellPrefsDialog (Choice lingua, checkbox "ondina all'avvio",
#    gestione dizionario) in una nuova pagina di MyPreferencesDialog, leggendo/
#    scrivendo su self.speller.settings e chiamandone .save() nell'OnOK del
#    dialogo principale. La logica di persistenza (SpellSettings) resta la stessa.
#
# 6) DIZIONARIO PERSONALE
#    - Salvato automaticamente in:
#        Debian : ~/.config/songpress/user_dict.txt
#        Windows: %APPDATA%\Songpress\user_dict.txt
#    - "Aggiungi al dizionario" nel dialogo, oppure add() dell'ondina live,
#      scrivono qui una parola per riga. E' un semplice file di testo che
#      l'utente puo' anche modificare a mano.
#
# 7) INSTALLER DIZIONARI (interattivo)
#    - Dal pannello "Opzioni ortografia..." -> pulsante "Installa dizionari..."
#      (oppure self.speller.open_dict_installer() da una voce di menu).
#    - Scarica le coppie .aff/.dic dal repo ufficiale LibreOffice/dictionaries
#      e le salva in:
#        Debian : ~/.config/songpress/enchant/hunspell/
#        Windows: %APPDATA%\Songpress\enchant\hunspell\
#      cartella puntata automaticamente da ENCHANT_CONFIG_DIR (impostata in
#      _bootstrap_dicts() PRIMA dell'import di enchant). La nuova lingua e'
#      subito utilizzabile, senza riavvio.
#    - Lingue nel catalogo: it_IT, en_US, en_GB, es_ES, pt_PT (percorsi repo
#      verificati). Per aggiungerne altre basta estendere AVAILABLE_DICTS con
#      la coppia (percorso_nel_repo, etichetta).
#    - Su Windows NON serve piu' copiare i dizionari a mano: l'installer fa
#      tutto. (In alternativa, per un pacchetto self-contained, si puo' ancora
#      spedire una cartella "dict/hunspell/" accanto all'exe: _bootstrap_dicts()
#      la rileva e la usa come ENCHANT_CONFIG_DIR.)
#
###############################################################
