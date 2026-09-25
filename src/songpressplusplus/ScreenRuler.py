###############################################################
# Name:        ScreenRuler.py
# Purpose:     Righello a schermo (stile Screen Ruler)
#              per misurare altezza/larghezza di testo ed elementi
#              visibili sullo schermo.
# Project:     Songpress++
# Author:      Denisov21
# Created:     2026
# Copyright:   © 2026 Denisov21
# License:     GNU GPL v2
###############################################################
"""
Righello a schermo per Songpress++.

Funziona come "Screen Ruler": viene catturata un'immagine
dello schermo, mostrata in una finestra a tutto schermo sulla quale si
misura con il mouse. Modalita':

  1  Riquadro     trascina un rettangolo -> larghezza x altezza.
                  Con "Adatta al contenuto" il rettangolo si stringe
                  automaticamente attorno al contenuto (ideale per
                  misurare altezza/larghezza reale di un testo).
  2  Spaziatura   croce automatica: misura lo spazio uniforme
                  orizzontale e verticale attorno al cursore.
  3  Orizzontale  solo distanza orizzontale tra i bordi.
  4  Verticale    solo distanza verticale tra i bordi.

Tasti:
  Esc              chiude (o annulla il trascinamento in corso)
  1..4             cambia modalita'
  F                attiva/disattiva "Adatta al contenuto"
  C                mostra/nasconde la croce di misura
  S                attiva/disattiva "Ingrandimento morbido"
  H                attiva/disattiva "Alta risoluzione" (solo schermi HiDPI)
  U                cambia unita' (px, pt, mm, cm, in)
  Frecce           sposta il cursore di 1 px (Maiusc = 10 px)
  + / -            ingrandisce / riduce la vista attorno al cursore
  0                torna alla vista 1:1
  Ctrl+rotellina   ingrandisce / riduce
  Rotellina        con zoom attivo scorre la vista (Maiusc = in orizzontale)
  Tasto centrale   trascinandolo sposta la vista ingrandita
  Ctrl+C           copia l'ultima misura negli appunti
  Canc / Backspace cancella le misure fissate
  Clic sinistro    fissa la misura e la copia negli appunti
  Clic destro      cancella le misure (se non ce ne sono, chiude)

Integrazione in SongpressFrame.py:

    from .ScreenRuler import ScreenRulerMixin
    (la voce di menu 'screenRuler', tasto F9, e' definita negli XRC;
     se manca viene creata da codice)

    class SongpressFrame(SDIMainFrame, PrintManager, CopyAIBeatsPromptMixin,
                         SongpressToolbarsMixin, ScreenRulerMixin):
        ...
        def __init__(self, res):
            ...
            self._BuildNewFromTemplateMenu()
            self._InstallScreenRuler()      # <-- aggiungere
"""

import os
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
from operator import itemgetter
from urllib.parse import unquote, urlparse

import wx
from wx import xrc

_ = wx.GetTranslation


# ---------------------------------------------------------------------------
# Costanti
# ---------------------------------------------------------------------------

_LINE_COLOUR = wx.Colour(255, 69, 0)          # arancio stile
_PIN_COLOUR = wx.Colour(0, 170, 255)          # misure fissate
_CROSS_COLOUR = wx.Colour(128, 128, 128)
_LABEL_BG = wx.Colour(32, 32, 32)
_LABEL_FG = wx.Colour(255, 255, 255)

_DEFAULT_TOLERANCE = 30

# Livelli di ingrandimento. Lo zoom cambia solo la VISUALIZZAZIONE: le misure
# restano sempre calcolate sui pixel reali dello schermo.
# Passo 1 da 1x (1:1) fino a 8x.
_ZOOM_LEVELS = [1, 2, 3, 4, 5, 6, 7, 8]


def _zoom_text(z):
    return "%g\u00d7" % z

# Impostazioni ricordate tra un'apertura e l'altra del righello
# (per tutta la sessione di Songpress++).
_session = {'showCross': True, 'smooth': False, 'hires': True}

# (chiave, fattore da pollici)
_UNITS = [
    ('px', None),
    ('pt', 72.0),
    ('mm', 25.4),
    ('cm', 2.54),
    ('in', 1.0),
]

# Scorciatoie candidate: si usa la prima non gia' occupata nei menu.
_ACCEL_CANDIDATES = ["Ctrl+Shift+M", "Ctrl+Alt+M", "Ctrl+Shift+U", "Ctrl+Alt+R"]


def _load_image_bitmap(relpath, size=None):
    """Carica un'immagine delle risorse di Songpress++ (es. 'img/close.png',
    la stessa usata dall'XRC come ../img/close.png). Ritorna None se manca."""
    candidates = []
    try:
        from .Globals import glb
        candidates.append(glb.AddPath(relpath))
    except Exception:
        pass
    # esecuzione autonoma / fallback: accanto a questo modulo
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), relpath))
    for path in candidates:
        if path and os.path.isfile(path):
            img = wx.Image(path, wx.BITMAP_TYPE_ANY)
            if img.IsOk():
                if size and (img.GetWidth(), img.GetHeight()) != tuple(size):
                    img = img.Scale(size[0], size[1], wx.IMAGE_QUALITY_HIGH)
                return wx.Bitmap(img)
    return None


_ICON_SIZE = (16, 16)     # icone dei pulsanti della barra (minus, plus, close)


def _no_dpi_scaling(window, bmp):
    """Mantiene l'icona a 16x16 pixel REALI anche con ridimensionamento dello
    schermo oltre il 100% (es. Windows al 150%).

    Da wxPython 4.2 una bitmap senza fattore di scala viene considerata
    "a 100%" e ingrandita (e sfocata) secondo i DPI dello schermo. Dichiarando
    che la bitmap e' gia' alla scala dello schermo, wx la disegna cosi' com'e',
    pixel per pixel. Con le versioni precedenti, o a 100%, non cambia nulla."""
    try:
        scale = window.GetDPIScaleFactor()          # wx >= 4.1 (Windows e GTK)
    except AttributeError:
        try:
            scale = window.GetContentScaleFactor()
        except Exception:
            scale = 1.0
    if scale and scale > 1.0:
        try:
            bmp.SetScaleFactor(scale)
        except Exception:
            pass
    return bmp


def _icon_button(parent, relpath, fallbackText, noDpiScale=True):
    """Pulsante con l'icona delle risorse di Songpress++; se l'immagine
    manca, pulsante di testo con fallbackText."""
    bmp = _load_image_bitmap(relpath, _ICON_SIZE)
    if bmp is not None:
        if noDpiScale:
            bmp = _no_dpi_scaling(parent, bmp)
        return wx.BitmapButton(parent, -1, bmp)
    return wx.Button(parent, -1, fallbackText, size=(28, -1), style=wx.BU_EXACTFIT)


# Icone dei pulsanti delle modalita' (cartella img/ di Songpress++, 16x16).
# Se un file manca, l'icona viene disegnata da _make_mode_bitmap().
_MODE_ICONS = {
    'bounds': 'img/ruler_bounds.png',
    'spacing': 'img/ruler_spacing.png',
    'horizontal': 'img/ruler_horizontal.png',
    'vertical': 'img/ruler_vertical.png',
}


def _mode_bitmap(mode, size=16):
    """Icona della modalita': prima il file in img/, poi quella disegnata."""
    bmp = _load_image_bitmap(_MODE_ICONS.get(mode, ''), (size, size))
    if bmp is not None:
        return bmp
    return _make_mode_bitmap(mode, size)


def _make_mode_bitmap(mode, size=16):
    """Icona di una modalita' di misura, disegnata al volo (nessun file).
    Le coordinate sono pensate su una griglia 16x16 e scalate su 'size'."""
    bmp = wx.Bitmap.FromRGBA(size, size, 0, 0, 0, 0)
    dc = wx.MemoryDC(bmp)
    gc = wx.GraphicsContext.Create(dc)
    if gc is not None:
        k = size / 16.0

        def mkpen(colour, width):
            # wx.Pen accetta solo spessori INTERI (con 1.5 solleva TypeError):
            # per gli spessori decimali si usa una penna del GraphicsContext.
            try:
                return gc.CreatePen(wx.GraphicsPenInfo(colour).Width(width).Cap(wx.CAP_BUTT))
            except Exception:
                pen = wx.Pen(colour, max(1, int(round(width))))
                pen.SetCap(wx.CAP_BUTT)
                return pen

        orange = mkpen(_LINE_COLOUR, max(1.0, 1.5 * k))
        tick = mkpen(_LINE_COLOUR, max(1.0, 1.0 * k))
        grey = wx.Colour(90, 90, 90)

        def line(pen, x0, y0, x1, y1):
            gc.SetPen(pen)
            gc.StrokeLine(x0 * k, y0 * k, x1 * k, y1 * k)

        if mode == 'bounds':
            # rettangolo di misura attorno a due "righe di testo"
            gc.SetPen(orange)
            gc.SetBrush(wx.TRANSPARENT_BRUSH)
            gc.DrawRectangle(2 * k, 3 * k, 12 * k, 10 * k)
            gc.SetPen(wx.TRANSPARENT_PEN)
            gc.SetBrush(wx.Brush(grey))
            gc.DrawRectangle(4.5 * k, 5.5 * k, 7 * k, 1.5 * k)
            gc.DrawRectangle(4.5 * k, 9 * k, 5 * k, 1.5 * k)
        elif mode == 'spacing':
            # croce con i trattini di estremita' sui quattro lati
            line(orange, 1.5, 8, 14.5, 8)
            line(orange, 8, 1.5, 8, 14.5)
            line(tick, 1.5, 5.5, 1.5, 10.5)
            line(tick, 14.5, 5.5, 14.5, 10.5)
            line(tick, 5.5, 1.5, 10.5, 1.5)
            line(tick, 5.5, 14.5, 10.5, 14.5)
        elif mode == 'horizontal':
            # |------|  (linea con trattini di estremita', senza punte)
            line(orange, 2, 8, 14, 8)
            line(tick, 1.5, 3.5, 1.5, 12.5)
            line(tick, 14.5, 3.5, 14.5, 12.5)
        elif mode == 'vertical':
            # stessa icona ruotata di 90 gradi
            line(orange, 8, 2, 8, 14)
            line(tick, 3.5, 1.5, 12.5, 1.5)
            line(tick, 3.5, 14.5, 12.5, 14.5)
        del gc
    dc.SelectObject(wx.NullBitmap)
    return bmp


def _modes():
    # Funzione (e non costante) perche' le traduzioni devono essere
    # risolte dopo l'inizializzazione di i18n.
    return [
        ('bounds', _("Bounds"), _("Drag a rectangle to measure width and height (1)")),
        ('spacing', _("Spacing"), _("Measure horizontal and vertical spacing around the cursor (2)")),
        ('horizontal', _("Horizontal"), _("Measure horizontal spacing (3)")),
        ('vertical', _("Vertical"), _("Measure vertical spacing (4)")),
    ]


# ---------------------------------------------------------------------------
# Cattura dello schermo
# ---------------------------------------------------------------------------

def _virtual_screen_rect():
    """Rettangolo che racchiude tutti i monitor."""
    rect = None
    for i in range(wx.Display.GetCount()):
        g = wx.Display(i).GetGeometry()
        rect = wx.Rect(g) if rect is None else rect.Union(g)
    if rect is None:
        w, h = wx.GetDisplaySize()
        rect = wx.Rect(0, 0, w, h)
    return rect


def _image_is_blank(img):
    """True se l'immagine e' uniformemente nera (tipico di wx.ScreenDC su
    Wayland). Campiona una griglia 32x32 su tutta l'immagine: un passo
    lineare sui byte rischierebbe di cadere sempre sulla stessa colonna."""
    w, h = img.GetWidth(), img.GetHeight()
    if w <= 0 or h <= 0:
        return True
    data = img.GetData()
    for gy in range(32):
        y = (gy * 2 + 1) * h // 64
        for gx in range(32):
            x = (gx * 2 + 1) * w // 64
            i = (y * w + x) * 3
            if data[i] or data[i + 1] or data[i + 2]:
                return False
    return True


def _capture_with_wx(rect, allowBlank=False):
    try:
        bmp = wx.Bitmap(rect.width, rect.height)
        mdc = wx.MemoryDC(bmp)
        sdc = wx.ScreenDC()
        mdc.Blit(0, 0, rect.width, rect.height, sdc, rect.x, rect.y)
        mdc.SelectObject(wx.NullBitmap)
        img = bmp.ConvertToImage()
        if img.IsOk() and (allowBlank or not _image_is_blank(img)):
            return img
    except Exception:
        pass
    return None


# Variabili che l'AppImage (AppRun + hook GTK di linuxdeploy) e il wrapper
# del .deb impostano per il SOLO Python di Songpress++: passate ai programmi
# del sistema (python3 con PyGObject, gdbus, grim, spectacle,
# gnome-screenshot) li farebbero fallire o comportare male.
_HOST_ENV_DROP = (
    'PYTHONHOME', 'PYTHONPATH', 'PYTHONDONTWRITEBYTECODE',
    'GDK_BACKEND',            # forzato a x11: su Wayland la cattura sarebbe nera
    'GTK_PATH', 'GTK_EXE_PREFIX', 'GTK_DATA_PREFIX', 'GTK_IM_MODULE_FILE',
    'GTK_THEME', 'GDK_PIXBUF_MODULE_FILE', 'GDK_PIXBUF_MODULEDIR',
    'GIO_MODULE_DIR', 'GIO_EXTRA_MODULES', 'GI_TYPELIB_PATH',
    'GSETTINGS_SCHEMA_DIR', 'QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH',
)


def _host_env():
    """Ambiente pulito per lanciare programmi del sistema ospite."""
    env = dict(os.environ)
    for key in _HOST_ENV_DROP:
        env.pop(key, None)
    appdir = os.environ.get('APPDIR')
    if appdir and os.path.isdir(appdir):
        appdir = os.path.realpath(appdir)
        # Toglie dai percorsi (LD_LIBRARY_PATH, XDG_DATA_DIRS, PATH, ...)
        # le voci interne all'AppImage.
        for key, value in list(env.items()):
            if appdir not in value:
                continue
            parts = [x for x in value.split(os.pathsep)
                     if x and not os.path.realpath(x).startswith(appdir)]
            if parts:
                env[key] = os.pathsep.join(parts)
            elif key not in ('APPDIR', 'APPIMAGE', 'ARGV0', 'OWD'):
                env.pop(key, None)
    return env


def _capture_with_tools(names=None):
    """Cattura tramite programmi esterni (necessario su Wayland).
    names: sottoinsieme/ordine dei programmi da provare (default: tutti)."""
    path = os.path.join(tempfile.gettempdir(), 'songpress_screenruler_%d.png' % os.getpid())
    commands = {
        'grim': ['grim', path],                                  # Sway / wlroots
        'spectacle': ['spectacle', '-b', '-n', '-f', '-o', path],  # KDE
        'gnome-screenshot': ['gnome-screenshot', '-f', path],    # GNOME
        'import': ['import', '-window', 'root', path],           # ImageMagick (X11)
        'scrot': ['scrot', '-o', path],                          # X11
        'maim': ['maim', path],                                  # X11
    }
    if names is None:
        names = list(commands)
    for name in names:
        cmd = commands[name]
        if not shutil.which(cmd[0]):
            continue
        try:
            if os.path.exists(path):
                os.remove(path)
            subprocess.run(cmd, timeout=10, env=_host_env(),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                img = wx.Image(path, wx.BITMAP_TYPE_PNG)
                try:
                    os.remove(path)
                except OSError:
                    pass
                if img.IsOk() and not _image_is_blank(img):
                    return img
        except Exception:
            continue
    return None


# ---------------------------------------------------------------------------
# Cattura tramite xdg-desktop-portal (standard Wayland: GNOME, KDE, ...)
# ---------------------------------------------------------------------------
#
# Il portale org.freedesktop.portal.Screenshot e' disponibile di serie su
# GNOME e KDE e non richiede programmi aggiuntivi. Al primo utilizzo il
# desktop puo' chiedere all'utente il permesso di catturare lo schermo.
# La risposta arriva come segnale D-Bus "Response" sull'oggetto Request:
# per non introdurre dipendenze Python si usa PyGObject (gi) in un processo
# separato, se disponibile, altrimenti lo strumento a riga di comando gdbus.

_PORTAL_BUS = 'org.freedesktop.portal.Desktop'
_PORTAL_PATH = '/org/freedesktop/portal/desktop'
_PORTAL_TIMEOUT = 90       # secondi: lascia il tempo di rispondere al permesso

_PORTAL_GI_SCRIPT = r"""
import sys
try:
    from gi.repository import Gio, GLib
except Exception:
    sys.exit(12)
token = sys.argv[1]
timeout = int(sys.argv[2])
try:
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
except Exception:
    sys.exit(11)
loop = GLib.MainLoop()
result = {}

def on_response(conn, sender, path, iface, signal, params, data):
    if not path.endswith('/' + token):
        return
    code, res = params.unpack()
    result['code'] = code
    result['uri'] = res.get('uri')
    loop.quit()

bus.signal_subscribe(None, 'org.freedesktop.portal.Request', 'Response',
                     None, None, Gio.DBusSignalFlags.NONE, on_response, None)
opts = {'handle_token': GLib.Variant('s', token),
        'interactive': GLib.Variant('b', False),
        'modal': GLib.Variant('b', True)}
try:
    bus.call_sync('org.freedesktop.portal.Desktop', '/org/freedesktop/portal/desktop',
                  'org.freedesktop.portal.Screenshot', 'Screenshot',
                  GLib.Variant('(sa{sv})', ('', opts)), GLib.VariantType('(o)'),
                  Gio.DBusCallFlags.NONE, -1, None)
except Exception:
    sys.exit(11)
GLib.timeout_add_seconds(timeout, loop.quit)
loop.run()
if result.get('code') == 0 and result.get('uri'):
    print(result['uri'])
    sys.exit(0)
sys.exit(10)
"""


def _portal_python_candidates():
    """Interpreti Python con cui provare PyGObject. Quello di Songpress++
    per primo; poi quello di sistema (AppImage e venv spesso non hanno gi).
    Nell'eseguibile congelato sys.executable non e' un interprete Python."""
    exes = [] if getattr(sys, 'frozen', False) else [sys.executable]
    exes += ['/usr/bin/python3', shutil.which('python3')]
    seen = []
    for exe in exes:
        if exe and os.path.isfile(exe) and exe not in seen:
            seen.append(exe)
    return seen


def _portal_uri_with_gi(token):
    """Ritorna (uri, esito): esito 'ok', 'denied' oppure 'unavailable'."""
    for exe in _portal_python_candidates():
        try:
            p = subprocess.run([exe, '-c', _PORTAL_GI_SCRIPT, token, str(_PORTAL_TIMEOUT)],
                               env=_host_env(),
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               timeout=_PORTAL_TIMEOUT + 10, text=True)
        except Exception:
            continue
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.strip().splitlines()[-1], 'ok'
        if p.returncode == 10:
            return None, 'denied'      # portale presente, cattura rifiutata/annullata
        if p.returncode == 11:
            return None, 'unavailable'  # nessun portale / nessun bus di sessione
        # 12 = gi non disponibile con questo interprete; qualsiasi altro codice
        # (es. interprete che non parte): si prova il successivo
    return None, 'unavailable'


def _portal_uri_with_gdbus(token):
    gdbus = shutil.which('gdbus')
    if not gdbus:
        return None, 'unavailable'
    try:
        mon = subprocess.Popen([gdbus, 'monitor', '--session', '--dest', _PORTAL_BUS],
                               env=_host_env(),
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               text=True, bufsize=1)
    except Exception:
        return None, 'unavailable'
    try:
        # attende che il monitor sia pronto ("Monitoring signals ...")
        ready = select.select([mon.stdout], [], [], 3)[0]
        if ready:
            mon.stdout.readline()
        opts = "{'handle_token': <'%s'>, 'interactive': <false>, 'modal': <true>}" % token
        call = subprocess.run([gdbus, 'call', '--session', '--dest', _PORTAL_BUS,
                               '--object-path', _PORTAL_PATH,
                               '--method', 'org.freedesktop.portal.Screenshot.Screenshot',
                               '', opts],
                              env=_host_env(),
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              timeout=15, text=True)
        if call.returncode != 0:
            return None, 'unavailable'
        deadline = time.time() + _PORTAL_TIMEOUT
        while time.time() < deadline:
            if not select.select([mon.stdout], [], [], 1)[0]:
                if mon.poll() is not None:
                    break
                continue
            line = mon.stdout.readline()
            if not line:
                break
            if ('/' + token) not in line or 'Response' not in line:
                continue
            code = re.search(r'uint32 (\d+)', line)
            uri = re.search(r"'uri': <'([^']*)'>", line)
            if code and code.group(1) == '0' and uri:
                return uri.group(1), 'ok'
            return None, 'denied'
        return None, 'denied'
    except Exception:
        return None, 'unavailable'
    finally:
        try:
            mon.terminate()
            mon.wait(2)
        except Exception:
            pass


def _capture_with_portal():
    """Cattura tramite xdg-desktop-portal. Ritorna (wx.Image | None, esito)."""
    if sys.platform.startswith('win') or sys.platform == 'darwin':
        return None, 'unavailable'
    token = 'songpress_%d_%d' % (os.getpid(), int(time.time() * 1000) % 1000000)
    uri, status = _portal_uri_with_gi(token)
    if status == 'unavailable':
        uri, status = _portal_uri_with_gdbus(token)
    if status != 'ok' or not uri:
        return None, status
    path = unquote(urlparse(uri).path)
    if not os.path.isfile(path):
        return None, 'unavailable'
    img = wx.Image(path, wx.BITMAP_TYPE_ANY)
    # Il portale salva lo screenshot (di solito nella cartella Immagini):
    # e' un file creato solo per noi, quindi lo si rimuove.
    try:
        os.remove(path)
    except OSError:
        pass
    if img.IsOk() and not _image_is_blank(img):
        return img, 'ok'
    return None, 'unavailable'


def capture_screen(rect):
    """Restituisce un wx.Image dello schermo grande esattamente rect.size,
    oppure None se la cattura non e' possibile."""
    return capture_screen_ex(rect)[0]


def capture_screen_ex(rect):
    """Come capture_screen, ma ritorna (immagine, immagine_piena):
    immagine_piena e' la cattura originale in pixel fisici quando lo
    schermo e' HiDPI (piu' grande di rect), altrimenti None."""
    wayland = os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland' \
        or bool(os.environ.get('WAYLAND_DISPLAY'))
    if wayland:
        # 1) strumenti silenziosi del desktop (Sway/wlroots, KDE)
        img = _capture_with_tools(['grim', 'spectacle'])
        # 2) portale standard (GNOME, KDE, ...): nessun pacchetto aggiuntivo
        if img is None:
            img, status = _capture_with_portal()
            if status == 'denied':
                return None, None   # l'utente ha rifiutato/annullato: non insistere
        # 3) ultime risorse
        if img is None:
            img = _capture_with_tools(['gnome-screenshot']) or _capture_with_wx(rect)
    else:
        # Su X11 / Windows wx.ScreenDC e' affidabile: uno schermo davvero
        # tutto nero e' comunque un'immagine valida.
        img = _capture_with_wx(rect, allowBlank=True) or _capture_with_tools()
    if img is None:
        return None, None
    # Con scaling HiDPI la cattura esterna e' in pixel fisici: la riportiamo
    # in pixel logici (NEAREST mantiene i bordi netti) per le misure, ma
    # conserviamo l'originale per la vista ingrandita ad alta risoluzione.
    full = None
    if img.GetWidth() != rect.width or img.GetHeight() != rect.height:
        if img.GetWidth() > rect.width and img.GetHeight() > rect.height:
            full = img
        img = img.Scale(rect.width, rect.height, wx.IMAGE_QUALITY_NEAREST)
    return img, full


# ---------------------------------------------------------------------------
# Barra strumenti del righello
# ---------------------------------------------------------------------------

class _RulerToolbar(wx.Panel):

    def __init__(self, overlay):
        wx.Panel.__init__(self, overlay, style=wx.BORDER_SIMPLE)
        self.overlay = overlay
        # Colori espliciti: su GTK un pannello figlio di una finestra con
        # BG_STYLE_PAINT risulterebbe trasparente (etichette illeggibili).
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        self.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT))
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.modeButtons = {}
        # Icone 16x16 al posto delle scritte (stessa dimensione di
        # _ICON_SIZE, usata per meno/piu'/chiudi): il nome della modalita'
        # resta nel suggerimento.
        # Icone o scritte secondo Opzioni › Generale › "Pulsanti modalita'
        # del Righello a schermo" (pref.rulerModeButtons).
        iconPx = _ICON_SIZE[0]
        for key, label, tip in _modes():
            if not overlay.modeIcons:
                b = wx.ToggleButton(self, -1, label, style=wx.BU_EXACTFIT)
                b.SetToolTip(tip)
                b.Bind(wx.EVT_TOGGLEBUTTON, lambda e, k=key: overlay.SetMode(k))
                sizer.Add(b, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 3)
                self.modeButtons[key] = b
                continue
            b = wx.ToggleButton(self, -1, "", style=wx.BU_EXACTFIT)
            try:
                bmp = _mode_bitmap(key, iconPx)
                if overlay.iconsNoDpiScale:
                    bmp = _no_dpi_scaling(self, bmp)
                b.SetBitmap(bmp)
            except Exception as exc:
                # ripiego: pulsante di testo (l'errore resta visibile in console)
                sys.stderr.write("ScreenRuler: icona '%s' non disponibile: %r\n" % (key, exc))
                b.SetLabel(label)
            b.SetToolTip("%s \u2014 %s" % (label, tip))
            b.Bind(wx.EVT_TOGGLEBUTTON, lambda e, k=key: overlay.SetMode(k))
            sizer.Add(b, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 3)
            self.modeButtons[key] = b

        sizer.Add(wx.StaticLine(self, size=(1, 20), style=wx.LI_VERTICAL), 0,
                  wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)

        # Caselle delle opzioni: affiancate nella barra oppure raggruppate in
        # una lista verticale aperta dal pulsante img/ruler_list.png
        # (Opzioni › Generale › "Opzioni 'Righello a schermo...'").
        self.fit = self.cross = self.smooth = self.hires = None
        self.optionsPopup = None
        self.listBtn = None
        if overlay.optionsList:
            self.listBtn = _icon_button(self, 'img/ruler_list.png', "\u2630",
                                        overlay.iconsNoDpiScale)
            self.listBtn.SetToolTip(_("Options: fit to content (F), show cross (C), "
                                      "smooth zoom (S), high resolution (H)"))
            self.listBtn.Bind(wx.EVT_BUTTON, self.OnOptionsList)
            sizer.Add(self.listBtn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 3)
        else:
            for cb in self._MakeOptionChecks(self):
                sizer.Add(cb, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 3)

        # Tolleranza: nella barra solo se richiesto in Opzioni › Generale ›
        # Righello a schermo; il valore e' comunque quello delle Opzioni.
        self.tol = None
        if overlay.showTolerance:
            sizer.Add(wx.StaticText(self, -1, _("Tolerance:")), 0,
                      wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 8)
            # Su GTK la larghezza naturale evita pulsanti +/- tagliati.
            spinSize = (60, -1) if wx.Platform == '__WXMSW__' else wx.DefaultSize
            self.tol = wx.SpinCtrl(self, -1, size=spinSize,
                                   min=0, max=255, initial=overlay.tolerance)
            self.tol.SetToolTip(_("Maximum colour difference considered as the same area"))
            self.tol.Bind(wx.EVT_SPINCTRL, lambda e: overlay.SetTolerance(self.tol.GetValue()))
            self.tol.Bind(wx.EVT_TEXT, lambda e: overlay.SetTolerance(self.tol.GetValue()))
            sizer.Add(self.tol, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 3)

        sizer.Add(wx.StaticText(self, -1, _("Unit:")), 0,
                  wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 8)
        self.unit = wx.Choice(self, -1, choices=[u[0] for u in _UNITS])
        self.unit.SetSelection(0)
        self.unit.SetToolTip(_("Measurement unit (U). Physical units depend on the screen DPI."))
        self.unit.Bind(wx.EVT_CHOICE, lambda e: overlay.SetUnit(self.unit.GetSelection()))
        sizer.Add(self.unit, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 3)

        sizer.Add(wx.StaticText(self, -1, _("Zoom:")), 0,
                  wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 8)
        zout = _icon_button(self, 'img/minus.png', "\u2212", overlay.iconsNoDpiScale)
        zout.SetToolTip(_("Zoom out (-)"))
        zout.Bind(wx.EVT_BUTTON, lambda e: overlay.ZoomStep(-1))
        sizer.Add(zout, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        self.zoomLabel = wx.StaticText(self, -1, _zoom_text(_ZOOM_LEVELS[-1]),
                                       style=wx.ALIGN_CENTRE_HORIZONTAL | wx.ST_NO_AUTORESIZE)
        # Larghezza FISSA pari all'etichetta piu' larga fra tutti i livelli:
        # cambiando zoom ("1x" -> "8x") l'etichetta non deve ridimensionarsi,
        # altrimenti la barra si allarga/restringe.
        lw = max(self.zoomLabel.GetTextExtent(_zoom_text(z))[0] for z in _ZOOM_LEVELS) + 6
        lh = self.zoomLabel.GetBestSize().height
        self.zoomLabel.SetMinSize((lw, lh))
        self.zoomLabel.SetMaxSize((lw, lh))
        self.zoomLabel.SetToolTip(_("Zoom only enlarges the view: measurements are always in real screen pixels (0 = 1:1)"))
        sizer.Add(self.zoomLabel, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        zin = _icon_button(self, 'img/plus.png', "+", overlay.iconsNoDpiScale)
        zin.SetToolTip(_("Zoom in (+, Ctrl+mouse wheel)"))
        zin.Bind(wx.EVT_BUTTON, lambda e: overlay.ZoomStep(+1))
        sizer.Add(zin, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)

        close = _icon_button(self, 'img/close.png', "\u2715", overlay.iconsNoDpiScale)
        close.SetToolTip(_("Close (Esc)"))
        close.Bind(wx.EVT_BUTTON, lambda e: overlay.Close())
        sizer.Add(close, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 3)

        # Tutti i pulsanti a icona (modalita', meno, piu', chiudi) diventano
        # quadrati identici: lato = dimensione piu' grande richiesta da uno
        # qualsiasi di essi. I pulsanti di testo di ripiego restano liberi.
        square = [b for b in self.modeButtons.values() if b.GetBitmap().IsOk()]
        square += [b for b in (zout, zin, close, self.listBtn) if isinstance(b, wx.BitmapButton)]
        if square:
            side = max(max(b.GetBestSize()) for b in square)
            for b in square:
                b.SetMinSize((side, side))
                b.SetMaxSize((side, side))

        self.SetSizerAndFit(sizer)
        # Dimensione della barra calcolata UNA volta e bloccata: lo zoom del
        # righello ingrandisce solo la vista dello schermo, mai la barra.
        self.fixedSize = wx.Size(self.GetSize())
        self.SetMinSize(self.fixedSize)
        self.SetMaxSize(self.fixedSize)

    def _MakeOptionChecks(self, parent):
        """Crea le quattro caselle delle opzioni su 'parent' (la barra oppure
        la lista a comparsa) e le ritorna nell'ordine di visualizzazione."""
        o = self.overlay
        self.fit = wx.CheckBox(parent, -1, _("Fit to content"))
        self.fit.SetToolTip(_("Shrink the rectangle around its content, "
                              "e.g. to measure the real height of a text (F)"))
        self.fit.Bind(wx.EVT_CHECKBOX, lambda e: o.SetFit(e.IsChecked()))

        self.cross = wx.CheckBox(parent, -1, _("Show cross"))
        self.cross.SetToolTip(_("Show or hide the measuring cross and lines; "
                                "the measurement label is always shown (C)"))
        self.cross.Bind(wx.EVT_CHECKBOX, lambda e: o.SetShowCross(e.IsChecked()))

        self.smooth = wx.CheckBox(parent, -1, _("Smooth zoom"))
        self.smooth.SetToolTip(_("Enlarge the view with interpolation: no visible "
                                 "squares, but edges become blurred. Measurements "
                                 "are always in real screen pixels (S)"))
        self.smooth.Bind(wx.EVT_CHECKBOX, lambda e: o.SetSmooth(e.IsChecked()))

        self.hires = wx.CheckBox(parent, -1, _("High resolution"))
        self.hires.SetToolTip(_("On HiDPI screens (scaling above 100%) use all the "
                                "physical pixels of the screen for the enlarged view, "
                                "for sharper details. Measurements stay in logical "
                                "pixels. Not available at 100% scaling (H)"))
        self.hires.Bind(wx.EVT_CHECKBOX, lambda e: o.SetHires(e.IsChecked()))
        return [self.fit, self.cross, self.smooth, self.hires]

    def OnOptionsList(self, evt):
        if self.optionsPopup:
            self.optionsPopup.Close()
            return
        # Il clic sul pulsante chiude prima la lista (clic "fuori" dalla
        # lista): senza questo controllo la riaprirebbe subito.
        if time.time() - getattr(self, '_popupClosedAt', 0) < 0.3:
            return
        popup = _OptionsPopup(self)
        self.optionsPopup = popup
        self.Sync()
        btn = self.listBtn
        # sotto il pulsante (wx lo sposta sopra se in basso non c'e' spazio)
        popup.Position(btn.ClientToScreen(wx.Point(0, 0)), wx.Size(0, btn.GetSize().height))
        popup.Popup()

    def _OptionsPopupClosed(self):
        self.optionsPopup = None
        self.fit = self.cross = self.smooth = self.hires = None
        self.overlay._FocusCanvas()

    def Sync(self):
        o = self.overlay
        for key, b in self.modeButtons.items():
            b.SetValue(key == o.mode)
        # Le caselle esistono solo se sono nella barra o se la lista e' aperta
        if self.fit:
            self.fit.SetValue(o.fit)
            self.cross.SetValue(o.showCross)
            self.smooth.SetValue(o.smooth)
            self.hires.Enable(o.HasHires())
            self.hires.SetValue(o.hires and o.HasHires())
        self.unit.SetSelection(o.unitIdx)
        label = _zoom_text(o.zoom)
        if self.zoomLabel.GetLabel() != label:
            # Solo il testo cambia: niente Layout/Fit, la barra resta ferma.
            self.zoomLabel.SetLabel(label)
            self.zoomLabel.Refresh()


class _OptionsPopup(wx.PopupTransientWindow):
    """Lista a comparsa con le caselle delle opzioni, una sotto l'altra.
    Resta aperta mentre si cliccano le caselle; si chiude cliccando altrove,
    con Esc o premendo di nuovo il pulsante."""

    def __init__(self, toolbar):
        wx.PopupTransientWindow.__init__(self, toolbar, wx.BORDER_SIMPLE)
        self.toolbar = toolbar
        panel = wx.Panel(self)
        panel.SetBackgroundColour(toolbar.GetBackgroundColour())
        panel.SetForegroundColour(toolbar.GetForegroundColour())
        sizer = wx.BoxSizer(wx.VERTICAL)
        for cb in toolbar._MakeOptionChecks(panel):
            sizer.Add(cb, 0, wx.ALL, 5)
        panel.SetSizer(sizer)
        sizer.Fit(panel)
        self.SetClientSize(panel.GetSize())
        self.Bind(wx.EVT_CHAR_HOOK, self._OnKey)

    def _OnKey(self, evt):
        if evt.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
        else:
            evt.Skip()

    def Close(self):
        """Chiude la lista da codice (Esc, pulsante): Dismiss() non chiama
        OnDismiss(), che quindi viene chiamato qui."""
        self.Dismiss()
        self.OnDismiss()

    def OnDismiss(self):
        if getattr(self, '_closed', False):     # gia' chiusa
            return
        self._closed = True
        tb = self.toolbar
        tb._popupClosedAt = time.time()
        # chiusura differita: OnDismiss arriva mentre la finestra e' ancora attiva
        wx.CallAfter(tb._OptionsPopupClosed)
        wx.CallAfter(self.Destroy)


# ---------------------------------------------------------------------------
# Finestra di misura
# ---------------------------------------------------------------------------

class ScreenRulerOverlay(wx.Frame):

    def __init__(self, parent, image, screenRect, onClose=None, fullImage=None,
                 modeIcons=True, iconsNoDpiScale=True, optionsList=False,
                 tolerance=_DEFAULT_TOLERANCE, showTolerance=True,
                 onToleranceChanged=None):
        style = wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP | wx.BORDER_NONE
        if parent is not None:
            style |= wx.FRAME_FLOAT_ON_PARENT
        wx.Frame.__init__(self, parent, -1, _("Screen ruler"),
                          pos=screenRect.GetTopLeft(), size=screenRect.GetSize(),
                          style=style)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self._onClose = onClose

        self.screenRect = wx.Rect(screenRect)
        self.W = image.GetWidth()
        self.H = image.GetHeight()
        self.data = bytes(image.GetData())
        self.bitmap = wx.Bitmap(image)
        self._image = image.Copy()      # sorgente per la vista ingrandita
        # Cattura originale in pixel fisici (solo schermi HiDPI)
        self._full = fullImage.Copy() if fullImage is not None and fullImage.IsOk() else None

        # offset client -> immagine (se il WM sposta la finestra)
        self.offX = 0
        self.offY = 0

        self.mode = 'bounds'
        self.fit = True
        self.showCross = _session['showCross']
        self.modeIcons = bool(modeIcons)   # pulsanti modalita': icone o scritte
        # icone a 16x16 pixel reali anche con ridimensionamento > 100%
        self.iconsNoDpiScale = bool(iconsNoDpiScale)
        # opzioni: caselle affiancate nella barra oppure lista a comparsa
        self.optionsList = bool(optionsList)
        # Tolleranza: valore iniziale dalle Opzioni; ogni modifica fatta nella
        # barra viene riportata alle Opzioni tramite onToleranceChanged.
        self.showTolerance = bool(showTolerance)
        self._onToleranceChanged = onToleranceChanged
        self.smooth = _session['smooth']
        self.hires = _session['hires']
        try:
            self.tolerance = max(0, min(255, int(tolerance)))
        except (TypeError, ValueError):
            self.tolerance = _DEFAULT_TOLERANCE
        self.unitIdx = 0
        ppi = wx.ScreenDC().GetPPI()
        self.ppiX = float(ppi.x or 96)
        self.ppiY = float(ppi.y or 96)

        # Vista: zoom (multiplo di 0.5) e pixel dell'immagine nell'angolo
        # in alto a sinistra
        self.zoom = 1.0
        self.viewX = 0
        self.viewY = 0
        self._viewBmp = None       # cache dell'immagine ingrandita
        self._panStart = None

        self.mouse = None          # posizione in coordinate immagine
        self.dragStart = None
        self.dragEnd = None
        self.pins = []             # misure fissate
        self.lastText = ''

        self.toolbar = _RulerToolbar(self)
        self.toolbarAtTop = True
        self.toolbar.Sync()

        self._UpdateCursor()

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMiddleDown)
        self.Bind(wx.EVT_MIDDLE_UP, self.OnMiddleUp)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.OnCaptureLost)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnCharHook)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    # ---- visualizzazione ------------------------------------------------

    def Start(self):
        if wx.Display.GetCount() <= 1:
            self.ShowFullScreen(True, wx.FULLSCREEN_ALL)
        else:
            self.SetSize(self.screenRect)
            self.Show()
        self.Raise()
        wx.CallAfter(self._AfterShow)

    def _AfterShow(self):
        if not self:
            return
        try:
            origin = self.ClientToScreen(wx.Point(0, 0))
            self.offX = self.screenRect.x - origin.x
            self.offY = self.screenRect.y - origin.y
        except Exception:
            self.offX = self.offY = 0
        self._PlaceToolbar()
        self._FocusCanvas()
        self.Refresh()

    def OnSize(self, evt):
        # NON chiamare evt.Skip(): il gestore predefinito di wx.Frame
        # ridimensiona l'unico figlio (la barra) a tutta la finestra.
        self._PlaceToolbar()
        self._ClampView()
        self._viewBmp = None

    def _PlaceToolbar(self):
        cw, ch = self.GetClientSize()
        # Dimensione fissa (non GetBestSize, che varia con lo zoom/etichette)
        tw, th = self.toolbar.fixedSize
        if self.toolbar.GetSize() != self.toolbar.fixedSize:
            self.toolbar.SetSize(tw, th)
        y = 10 if self.toolbarAtTop else ch - th - 10
        self.toolbar.SetPosition(wx.Point(max(0, (cw - tw) // 2), max(0, y)))

    def _AvoidToolbar(self, cx, cy):
        """Sposta la barra in basso/in alto se il cursore ci si avvicina."""
        r = self.toolbar.GetRect()
        r.Inflate(20, 20)
        if r.Contains(cx, cy):
            self.toolbarAtTop = not self.toolbarAtTop
            self._PlaceToolbar()

    # ---- impostazioni ---------------------------------------------------

    def _UpdateCursor(self):
        """In modalita' Orizzontale/Verticale il cursore a croce coprirebbe
        proprio il punto misurato: lo si nasconde, la posizione e' gia'
        indicata dalla linea di misura."""
        if self.mode in ('vertical', 'horizontal'):
            self.SetCursor(wx.Cursor(wx.CURSOR_BLANK))
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_CROSS))

    def _FocusCanvas(self):
        """Porta il focus sulla finestra di misura. Su GTK un wx.Frame con
        figli cede il focus al primo controllo (spesso il campo Tolleranza),
        che consumerebbe i tasti 1-4, F, U, C: in quel caso il focus va al
        pulsante della modalita' corrente, che non li consuma."""
        if self.toolbar.optionsPopup:
            return      # la lista delle opzioni e' aperta: il focus resta li'
        self.SetFocus()
        if wx.Window.FindFocus() is not self:
            btn = self.toolbar.modeButtons.get(self.mode)
            if btn:
                btn.SetFocus()

    def SetMode(self, mode):
        self.mode = mode
        self.dragStart = self.dragEnd = None
        self._UpdateCursor()
        self.toolbar.Sync()
        self._FocusCanvas()
        self.Refresh()

    def SetShowCross(self, show):
        self.showCross = bool(show)
        _session['showCross'] = self.showCross
        self.toolbar.Sync()
        self._FocusCanvas()
        self.Refresh()

    def HasHires(self):
        return self._full is not None

    def SetSmooth(self, smooth):
        self.smooth = bool(smooth)
        _session['smooth'] = self.smooth
        self._viewBmp = None
        self.toolbar.Sync()
        self._FocusCanvas()
        self.Refresh(False)

    def SetHires(self, hires):
        if not self.HasHires():
            return
        self.hires = bool(hires)
        _session['hires'] = self.hires
        self._viewBmp = None
        self.toolbar.Sync()
        self._FocusCanvas()
        self.Refresh(False)

    def SetFit(self, fit):
        self.fit = fit
        self.toolbar.Sync()
        self._FocusCanvas()
        self.Refresh()

    def SetTolerance(self, tol):
        try:
            self.tolerance = max(0, min(255, int(tol)))
        except (TypeError, ValueError):
            return
        if self._onToleranceChanged is not None:
            try:
                self._onToleranceChanged(self.tolerance)
            except Exception:
                pass
        self.Refresh()

    def SetUnit(self, idx):
        self.unitIdx = idx % len(_UNITS)
        self.toolbar.Sync()
        self._FocusCanvas()
        self.Refresh()

    # ---- pixel ----------------------------------------------------------

    def _px(self, x, y):
        i = (y * self.W + x) * 3
        d = self.data
        return d[i], d[i + 1], d[i + 2]

    def _differs(self, a, b):
        t = self.tolerance
        return abs(a[0] - b[0]) > t or abs(a[1] - b[1]) > t or abs(a[2] - b[2]) > t

    def _scan(self, x, y, dx, dy):
        """Avanza da (x, y) finche' il colore resta simile; ritorna l'ultimo
        punto simile."""
        ref = self._px(x, y)
        W, H = self.W, self.H
        while True:
            nx, ny = x + dx, y + dy
            if nx < 0 or ny < 0 or nx >= W or ny >= H:
                break
            if self._differs(self._px(nx, ny), ref):
                break
            x, y = nx, ny
        return x, y

    def _background(self, x0, y0, x1, y1):
        corners = [self._px(x0, y0), self._px(x1, y0), self._px(x0, y1), self._px(x1, y1)]
        return max(corners, key=corners.count)

    def _row_has_content(self, y, x0, x1, bg, bgRow):
        i0 = (y * self.W + x0) * 3
        i1 = (y * self.W + x1 + 1) * 3
        if self.data[i0:i1] == bgRow:          # percorso veloce: riga identica
            return False
        for x in range(x0, x1 + 1):
            if self._differs(self._px(x, y), bg):
                return True
        return False

    def _col_has_content(self, x, y0, y1, bg):
        for y in range(y0, y1 + 1):
            if self._differs(self._px(x, y), bg):
                return True
        return False

    def _fit_rect(self, x0, y0, x1, y1):
        """Restringe il rettangolo attorno al contenuto diverso dallo sfondo."""
        bg = self._background(x0, y0, x1, y1)
        bgRow = bytes(bg) * (x1 - x0 + 1)
        while y0 <= y1 and not self._row_has_content(y0, x0, x1, bg, bgRow):
            y0 += 1
        if y0 > y1:
            return None
        while not self._row_has_content(y1, x0, x1, bg, bgRow):
            y1 -= 1
        while not self._col_has_content(x0, y0, y1, bg):
            x0 += 1
        while not self._col_has_content(x1, y0, y1, bg):
            x1 -= 1
        return x0, y0, x1, y1

    # ---- misure ---------------------------------------------------------

    def _fmt(self, px, horizontal):
        key, factor = _UNITS[self.unitIdx]
        if factor is None:
            return "%d" % px
        ppi = self.ppiX if horizontal else self.ppiY
        return "%.2f" % (px / ppi * factor)

    def _unit(self):
        return _UNITS[self.unitIdx][0]

    def _current_bounds(self):
        if self.dragStart is None or self.dragEnd is None:
            return None
        (ax, ay), (bx, by) = self.dragStart, self.dragEnd
        x0, x1 = sorted((ax, bx))
        y0, y1 = sorted((ay, by))
        fitted = None
        if self.fit and (x1 > x0 or y1 > y0):
            fitted = self._fit_rect(x0, y0, x1, y1)
        return (x0, y0, x1, y1), fitted

    def _current_spacing(self):
        if self.mouse is None:
            return None
        x, y = self.mouse
        m = {'x': x, 'y': y, 'kind': self.mode}
        if self.mode in ('spacing', 'horizontal'):
            m['left'] = self._scan(x, y, -1, 0)[0]
            m['right'] = self._scan(x, y, 1, 0)[0]
        if self.mode in ('spacing', 'vertical'):
            m['top'] = self._scan(x, y, 0, -1)[1]
            m['bottom'] = self._scan(x, y, 0, 1)[1]
        return m

    def _text_for_rect(self, r):
        x0, y0, x1, y1 = r
        w, h = x1 - x0 + 1, y1 - y0 + 1
        return "%s \u00d7 %s %s" % (self._fmt(w, True), self._fmt(h, False), self._unit())

    def _text_for_spacing(self, m):
        parts = []
        if 'left' in m:
            parts.append(self._fmt(m['right'] - m['left'] + 1, True))
        if 'top' in m:
            parts.append(self._fmt(m['bottom'] - m['top'] + 1, False))
        return "%s %s" % (" \u00d7 ".join(parts), self._unit())

    def _copy(self, text):
        self.lastText = text
        if wx.TheClipboard.Open():
            try:
                wx.TheClipboard.SetData(wx.TextDataObject(text))
            finally:
                wx.TheClipboard.Close()

    # ---- mouse ----------------------------------------------------------

    # ---- zoom / vista ---------------------------------------------------

    # Lo zoom e' un multiplo di 0.5: tutti i calcoli usano z2 = 2*zoom
    # (intero) per restare esatti.  Convenzione unica per disegno e misura:
    #   pixel client d  ->  pixel immagine floor(d / zoom)
    #   pixel immagine x ->  primo pixel client ceil(x * zoom)
    # Con zoom 1.5 i pixel reali diventano quindi quadrati alternati di
    # 1 e 2 pixel, ma il riquadro disegnato coincide sempre con la misura.

    def _z2(self):
        return int(round(self.zoom * 2))

    def _X(self, x):
        """Coordinata immagine -> client (bordo sinistro del pixel)."""
        return self.offX - ((-(x - self.viewX) * self._z2()) // 2)

    def _Y(self, y):
        return self.offY - ((-(y - self.viewY) * self._z2()) // 2)

    def _half(self):
        """Meta' della dimensione a schermo di un pixel reale."""
        return int(self.zoom) // 2

    def _viewSize(self):
        """Quanti pixel dell'immagine sono visibili con lo zoom corrente."""
        cw, ch = self.GetClientSize()
        z2 = self._z2()
        return (min(self.W, ((cw - self.offX) * 2 + z2 - 1) // z2),
                min(self.H, ((ch - self.offY) * 2 + z2 - 1) // z2))

    def _ClampView(self):
        vw, vh = self._viewSize()
        self.viewX = max(0, min(self.viewX, self.W - vw))
        self.viewY = max(0, min(self.viewY, self.H - vh))

    def SetZoom(self, zoom, anchor=None):
        """Cambia lo zoom mantenendo fermo il pixel sotto 'anchor'
        (coordinate client; default: posizione del mouse o centro)."""
        zoom = max(_ZOOM_LEVELS[0], min(_ZOOM_LEVELS[-1], float(zoom)))
        zoom = int(round(zoom))                 # solo livelli interi
        if anchor is None:
            anchor = self.ScreenToClient(wx.GetMousePosition())
            cw, ch = self.GetClientSize()
            if not (0 <= anchor.x < cw and 0 <= anchor.y < ch):
                anchor = wx.Point(cw // 2, ch // 2)
        ix, iy = self._to_image(anchor, clamp=False)
        self.zoom = zoom
        z2 = self._z2()
        self.viewX = ix - ((anchor.x - self.offX) * 2) // z2
        self.viewY = iy - ((anchor.y - self.offY) * 2) // z2
        self._ClampView()
        self._viewBmp = None
        self.mouse = self._to_image(anchor)
        if self.dragStart is not None:
            self.dragEnd = self.mouse
        self.toolbar.Sync()
        self.Refresh(False)

    def ZoomStep(self, direction, anchor=None):
        levels = _ZOOM_LEVELS
        if direction > 0:
            nxt = next((z for z in levels if z > self.zoom), levels[-1])
        else:
            nxt = next((z for z in reversed(levels) if z < self.zoom), levels[0])
        self.SetZoom(nxt, anchor)
        self._FocusCanvas()

    def Pan(self, dx, dy):
        """Sposta la vista di dx, dy pixel dell'immagine."""
        if self.zoom == 1:
            return
        self.viewX += dx
        self.viewY += dy
        self._ClampView()
        self._viewBmp = None
        pos = self.ScreenToClient(wx.GetMousePosition())
        self.mouse = self._to_image(pos)
        if self.dragStart is not None:
            self.dragEnd = self.mouse
        self.Refresh(False)

    def _view_bitmap(self):
        """Porzione visibile dell'immagine, ingrandita senza interpolazione.
        Il ridimensionamento e' fatto qui (e non con wx.Image.Scale) perche'
        usi ESATTAMENTE la stessa corrispondenza pixel di _X/_to_image:
        con zoom non interi wx arrotonda diversamente e il riquadro di misura
        risulterebbe sfasato di un pixel rispetto all'immagine."""
        if self.zoom == 1:
            return self.bitmap
        if self._viewBmp is None:
            vw, vh = self._viewSize()
            vw = min(vw, self.W - self.viewX)
            vh = min(vh, self.H - self.viewY)
            z2 = self._z2()
            dw = (vw * z2 + 1) // 2
            dh = (vh * z2 + 1) // 2
            quality = wx.IMAGE_QUALITY_BICUBIC if self.smooth else wx.IMAGE_QUALITY_NEAREST
            if self.hires and self._full is not None:
                # Stessa porzione, presa dalla cattura in pixel fisici
                fW, fH = self._full.GetWidth(), self._full.GetHeight()
                sx, sy = fW / float(self.W), fH / float(self.H)
                fx = min(fW - 1, int(round(self.viewX * sx)))
                fy = min(fH - 1, int(round(self.viewY * sy)))
                fw = max(1, min(fW - fx, int(round(vw * sx))))
                fh = max(1, min(fH - fy, int(round(vh * sy))))
                sub = self._full.GetSubImage(wx.Rect(fx, fy, fw, fh))
                if (fw, fh) != (dw, dh):
                    sub = sub.Scale(dw, dh, quality)
                self._viewBmp = wx.Bitmap(sub)
                return self._viewBmp
            if self.smooth:
                sub = self._image.GetSubImage(wx.Rect(self.viewX, self.viewY, vw, vh))
                self._viewBmp = wx.Bitmap(sub.Scale(dw, dh, quality))
                return self._viewBmp
            x0, y0 = self.viewX, self.viewY
            idx = []
            for d in range(dw):
                o = (x0 + (2 * d) // z2) * 3
                idx.extend((o, o + 1, o + 2))
            pick = itemgetter(*idx)
            rowLen = self.W * 3
            data = self.data
            rows = {}
            out = []
            for d in range(dh):
                sy = y0 + (2 * d) // z2
                r = rows.get(sy)
                if r is None:
                    base = sy * rowLen
                    r = rows[sy] = bytes(pick(data[base:base + rowLen]))
                out.append(r)
            self._viewBmp = wx.Bitmap(wx.Image(dw, dh, b''.join(out)))
        return self._viewBmp

    def _to_image(self, pos, clamp=True):
        z2 = self._z2()
        x = self.viewX + ((pos.x - self.offX) * 2) // z2
        y = self.viewY + ((pos.y - self.offY) * 2) // z2
        if not clamp:
            return x, y
        return min(max(x, 0), self.W - 1), min(max(y, 0), self.H - 1)

    def OnWheel(self, evt):
        rot = evt.GetWheelRotation()
        if rot == 0:
            return
        if evt.ControlDown():
            self.ZoomStep(1 if rot > 0 else -1, evt.GetPosition())
            return
        step = max(1, int(60 // self.zoom)) * (-1 if rot > 0 else 1)
        horizontal = evt.ShiftDown() or evt.GetWheelAxis() == wx.MOUSE_WHEEL_HORIZONTAL
        if horizontal:
            self.Pan(step, 0)
        else:
            self.Pan(0, step)

    def OnMiddleDown(self, evt):
        if self.zoom == 1:
            return
        self._panStart = (evt.GetPosition(), self.viewX, self.viewY)
        self.SetCursor(wx.Cursor(wx.CURSOR_SIZING))
        if not self.HasCapture():
            self.CaptureMouse()

    def OnMiddleUp(self, evt):
        self._panStart = None
        if self.HasCapture() and self.dragStart is None:
            self.ReleaseMouse()
        self._UpdateCursor()

    def OnMotion(self, evt):
        pos = evt.GetPosition()
        if self._panStart is not None and evt.MiddleIsDown():
            p0, vx, vy = self._panStart
            z2 = self._z2()
            self.viewX = vx - ((pos.x - p0.x) * 2) // z2
            self.viewY = vy - ((pos.y - p0.y) * 2) // z2
            self._ClampView()
            self._viewBmp = None
            self.mouse = self._to_image(pos)
            self.Refresh(False)
            return
        # La barra si sposta solo durante un trascinamento: altrimenti
        # "scapperebbe" dal mouse e i pulsanti non sarebbero cliccabili.
        if self.dragStart is not None and evt.LeftIsDown():
            self._AvoidToolbar(pos.x, pos.y)
        self.mouse = self._to_image(pos)
        if self.dragStart is not None and evt.LeftIsDown():
            self.dragEnd = self.mouse
        self.Refresh(False)

    def OnLeftDown(self, evt):
        self._FocusCanvas()
        self.mouse = self._to_image(evt.GetPosition())
        if self.mode == 'bounds':
            self.dragStart = self.dragEnd = self.mouse
            if not self.HasCapture():
                self.CaptureMouse()
        self.Refresh(False)

    def OnLeftUp(self, evt):
        if self.HasCapture():
            self.ReleaseMouse()
        if self.mode == 'bounds':
            cur = self._current_bounds()
            if cur is not None:
                raw, fitted = cur
                r = fitted or raw
                if r[2] > r[0] or r[3] > r[1]:
                    self.pins.append(('rect', r))
                    self._copy(self._text_for_rect(r))
            self.dragStart = self.dragEnd = None
        else:
            m = self._current_spacing()
            if m is not None:
                self.pins.append(('spacing', m))
                self._copy(self._text_for_spacing(m))
        self.Refresh(False)

    def OnRightUp(self, evt):
        if self.pins or self.dragStart is not None:
            self.pins = []
            self.dragStart = self.dragEnd = None
            self.Refresh(False)
        else:
            self.Close()

    def OnLeave(self, evt):
        if self.dragStart is None:
            self.mouse = None
            self.Refresh(False)

    def OnCaptureLost(self, evt):
        self.dragStart = self.dragEnd = None
        self._panStart = None
        self._UpdateCursor()

    # ---- tastiera -------------------------------------------------------

    def OnCharHook(self, evt):
        code = evt.GetKeyCode()
        focus = wx.Window.FindFocus()
        typing = focus is not None and focus is not self and \
            isinstance(focus, (wx.SpinCtrl, wx.TextCtrl))

        if code == wx.WXK_ESCAPE:
            if self.dragStart is not None:
                if self.HasCapture():
                    self.ReleaseMouse()
                self.dragStart = self.dragEnd = None
                self.Refresh(False)
            else:
                self.Close()
            return
        if typing:
            evt.Skip()
            return
        if evt.ControlDown() and code in (ord('C'), ord('c')):
            text = self._live_text() or self.lastText
            if text:
                self._copy(text)
            return
        if evt.HasAnyModifiers() and not evt.ShiftDown():
            evt.Skip()
            return
        uni = evt.GetUnicodeKey()
        if code in (wx.WXK_ADD, wx.WXK_NUMPAD_ADD) or uni in (ord('+'), ord('=')) \
                or code in (ord('+'), ord('=')):
            self.ZoomStep(+1)
            return
        if code in (wx.WXK_SUBTRACT, wx.WXK_NUMPAD_SUBTRACT) or uni == ord('-') \
                or code == ord('-'):
            self.ZoomStep(-1)
            return
        if code in (ord('0'), wx.WXK_NUMPAD0):
            self.SetZoom(1)
            return
        if code in (ord('1'), ord('2'), ord('3'), ord('4')):
            self.SetMode(_modes()[code - ord('1')][0])
            return
        if code in (ord('S'), ord('s')):
            self.SetSmooth(not self.smooth)
            return
        if code in (ord('H'), ord('h')):
            self.SetHires(not self.hires)
            return
        if code in (ord('C'), ord('c')):
            self.SetShowCross(not self.showCross)
            return
        if code in (ord('F'), ord('f')):
            self.SetFit(not self.fit)
            return
        if code in (ord('U'), ord('u')):
            self.SetUnit(self.unitIdx + 1)
            return
        if code in (wx.WXK_DELETE, wx.WXK_BACK):
            self.pins = []
            self.Refresh(False)
            return
        arrows = {wx.WXK_LEFT: (-1, 0), wx.WXK_RIGHT: (1, 0),
                  wx.WXK_UP: (0, -1), wx.WXK_DOWN: (0, 1)}
        if code in arrows:
            dx, dy = arrows[code]
            # 1 pixel REALE per pressione, qualunque sia lo zoom:
            # il puntatore va al centro del pixel reale successivo.
            n = 10 if evt.ShiftDown() else 1
            pos = self.ScreenToClient(wx.GetMousePosition())
            ix, iy = self._to_image(pos, clamp=False)
            nx = self._X(ix + dx * n) + self._half()
            ny = self._Y(iy + dy * n) + self._half()
            cw, ch = self.GetClientSize()
            # se si esce dalla vista ingrandita, la vista scorre
            if self.zoom > 1 and not (0 <= nx < cw and 0 <= ny < ch):
                shift = 10 if evt.ShiftDown() else 1
                self.Pan(dx * shift, dy * shift)
                return
            self.WarpPointer(nx, ny)
            return
        evt.Skip()

    def _live_text(self):
        if self.mode == 'bounds':
            cur = self._current_bounds()
            if cur is not None:
                return self._text_for_rect(cur[1] or cur[0])
            return ''
        m = self._current_spacing()
        return self._text_for_spacing(m) if m else ''

    # ---- disegno --------------------------------------------------------

    def OnPaint(self, evt):
        dc = wx.AutoBufferedPaintDC(self)
        if self.zoom > 1:
            dc.SetBackground(wx.BLACK_BRUSH)
            dc.Clear()
        dc.DrawBitmap(self._view_bitmap(), self.offX, self.offY)
        dc.SetFont(wx.Font(wx.FontInfo(10).Bold()))

        for kind, item in self.pins:
            if kind == 'rect':
                self._draw_rect(dc, item, _PIN_COLOUR, self._text_for_rect(item))
            else:
                self._draw_spacing(dc, item, _PIN_COLOUR)

        if self.mode == 'bounds':
            cur = self._current_bounds()
            if cur is not None:
                raw, fitted = cur
                if fitted is not None and fitted != raw:
                    self._draw_rect(dc, raw, _CROSS_COLOUR, None, dashed=True)
                r = fitted or raw
                self._draw_rect(dc, r, _LINE_COLOUR, self._text_for_rect(r))
            elif self.mouse is not None and self.showCross:
                self._draw_crosshair(dc)
        elif self.mouse is not None:
            m = self._current_spacing()
            if m is not None:
                self._draw_spacing(dc, m, _LINE_COLOUR, lines=self.showCross)

    def _pen(self, colour, dashed=False):
        return wx.Pen(colour, 1, wx.PENSTYLE_SHORT_DASH if dashed else wx.PENSTYLE_SOLID)

    def _draw_crosshair(self, dc):
        x, y = self.mouse
        h = self._half()
        cw, ch = self.GetClientSize()
        dc.SetPen(self._pen(_CROSS_COLOUR, True))
        dc.DrawLine(0, self._Y(y) + h, cw, self._Y(y) + h)
        dc.DrawLine(self._X(x) + h, 0, self._X(x) + h, ch)

    def _draw_rect(self, dc, r, colour, text, dashed=False):
        x0, y0, x1, y1 = r
        dc.SetPen(self._pen(colour, dashed))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        # Il bordo e' disegnato all'esterno dei pixel misurati
        X0, Y0 = self._X(x0) - 1, self._Y(y0) - 1
        X1, Y1 = self._X(x1 + 1), self._Y(y1 + 1)
        dc.DrawRectangle(X0, Y0, X1 - X0 + 1, Y1 - Y0 + 1)
        if text:
            self._draw_label(dc, text, (X0 + X1) // 2, Y1 + 8, below=True)

    def _draw_spacing(self, dc, m, colour, lines=True):
        h = self._half()
        x, y = self._X(m['x']) + h, self._Y(m['y']) + h
        t = 5 + h
        dc.SetPen(self._pen(colour))
        if lines and 'left' in m:
            l, r = self._X(m['left']), self._X(m['right'] + 1) - 1
            dc.DrawLine(l, y, r + 1, y)
            dc.DrawLine(l, y - t, l, y + t + 1)
            dc.DrawLine(r, y - t, r, y + t + 1)
        if lines and 'top' in m:
            tp, b = self._Y(m['top']), self._Y(m['bottom'] + 1) - 1
            dc.DrawLine(x, tp, x, b + 1)
            dc.DrawLine(x - t, tp, x + t + 1, tp)
            dc.DrawLine(x - t, b, x + t + 1, b)
        self._draw_label(dc, self._text_for_spacing(m), x + 16, y + 16)

    def _draw_label(self, dc, text, x, y, below=False):
        tw, th = dc.GetTextExtent(text)
        pad = 5
        w, h = tw + 2 * pad, th + 2 * pad
        if below:
            x -= w // 2
        cw, ch = self.GetClientSize()
        x = max(4, min(x, cw - w - 4))
        if y + h > ch - 4:
            y = ch - h - 4
        y = max(4, y)
        dc.SetPen(wx.Pen(_LABEL_BG))
        dc.SetBrush(wx.Brush(_LABEL_BG))
        dc.DrawRoundedRectangle(x, y, w, h, 4)
        dc.SetTextForeground(_LABEL_FG)
        dc.DrawText(text, x + pad, y + pad)

    # ---- chiusura -------------------------------------------------------

    def OnCloseWindow(self, evt):
        if self.HasCapture():
            self.ReleaseMouse()
        cb, self._onClose = self._onClose, None
        if cb is not None:
            try:
                cb()
            except Exception:
                pass
        self.Destroy()


# ---------------------------------------------------------------------------
# Mixin per SongpressFrame
# ---------------------------------------------------------------------------

def _make_ruler_bitmap(size=16):
    """Icona di un righello disegnata al volo (nessun file necessario)."""
    bmp = wx.Bitmap(size, size, 32)
    dc = wx.MemoryDC(bmp)
    dc.SetBackground(wx.Brush(wx.Colour(0, 0, 0, 0)))
    dc.Clear()
    gc = wx.GraphicsContext.Create(dc)
    if gc is not None:
        gc.SetPen(wx.Pen(wx.Colour(90, 90, 90), 1))
        gc.SetBrush(wx.Brush(wx.Colour(235, 200, 90)))
        gc.Translate(size / 2.0, size / 2.0)
        gc.Rotate(-0.785398)
        gc.DrawRectangle(-size * 0.6, -size * 0.2, size * 1.2, size * 0.4)
        for i in range(6):
            x = -size * 0.5 + i * size * 0.2
            ln = size * 0.18 if i % 2 else size * 0.1
            gc.StrokeLine(x, -size * 0.2, x, -size * 0.2 + ln)
    dc.SelectObject(wx.NullBitmap)
    return bmp


def _used_accels(menubar):
    used = set()

    def walk(menu):
        for item in menu.GetMenuItems():
            acc = item.GetAccel()
            if acc is not None:
                used.add(acc.ToString().replace('-', '+').lower())
            if item.GetSubMenu() is not None:
                walk(item.GetSubMenu())

    for i in range(menubar.GetMenuCount()):
        walk(menubar.GetMenu(i))
    return used


class ScreenRulerMixin(object):
    """Aggiunge 'Strumenti -> Righello a schermo' a SongpressFrame."""

    def _InstallScreenRuler(self):
        self._screenRuler = None
        mb = self.menuBar

        # Caso normale: la voce 'screenRuler' e' definita nell'XRC
        # (menu Strumenti, F9). Basta collegarla.
        xrcId = xrc.XRCID('screenRuler')
        if mb.FindItemById(xrcId) is not None:
            self._screenRulerMenuId = xrcId
            self.frame.Bind(wx.EVT_MENU, self.OnScreenRuler, id=xrcId)
            return

        # Ripiego: XRC vecchio senza la voce -> la si crea da codice.

        # Il menu Strumenti viene individuato tramite una voce nota
        # (indipendente dalla lingua dell'interfaccia).
        target = None
        for name in ('songStatistics', 'syntaxCheck', 'spellCheck'):
            item = mb.FindItemById(xrc.XRCID(name))
            if item is not None and item.GetMenu() is not None:
                target = item.GetMenu()
                break
        if target is None:
            target = wx.Menu()
            pos = max(0, mb.GetMenuCount() - 1)   # prima di '?' / Aiuto
            mb.Insert(pos, target, _("&Tools"))

        used = _used_accels(mb)
        accel = next((a for a in _ACCEL_CANDIDATES if a.lower() not in used), None)
        label = _("Screen ruler...")
        if accel:
            label += "\t" + accel

        self._screenRulerMenuId = wx.NewIdRef()
        if target.GetMenuItemCount() > 0:
            target.AppendSeparator()
        item = wx.MenuItem(target, self._screenRulerMenuId, label,
                           _("Measure width and height of text and objects on screen"))
        try:
            item.SetBitmap(_make_ruler_bitmap())
        except Exception:
            pass
        target.Append(item)
        self.frame.Bind(wx.EVT_MENU, self.OnScreenRuler, id=self._screenRulerMenuId)

    def OnScreenRuler(self, evt=None):
        sr = getattr(self, '_screenRuler', None)
        if sr is True:                  # apertura gia' in corso
            return
        if sr:
            sr.Raise()
            return
        # Il menu (su Windows con animazione di dissolvenza) deve essere
        # sparito e la finestra ridisegnata PRIMA della cattura, altrimenti
        # nello screenshot resta l'immagine sbiadita della voce di menu.
        self._screenRuler = True        # blocca aperture multiple
        try:
            self.frame.Refresh()
            self.frame.Update()
        except Exception:
            pass
        wx.CallLater(600, self._OpenScreenRuler)

    def _OpenScreenRuler(self):
        self._screenRuler = None
        # Completa i ridisegni in sospeso (menu appena chiuso).
        try:
            self.frame.Update()
            wx.SafeYield(self.frame, True)
        except Exception:
            pass
        rect = _virtual_screen_rect()
        wx.BeginBusyCursor()
        try:
            img, full = capture_screen_ex(rect)
        finally:
            wx.EndBusyCursor()
        if img is None:
            wx.MessageBox(
                _("Unable to capture the screen.\n\n"
                  "On Wayland the screenshot permission may have been denied, or "
                  "xdg-desktop-portal is not available. Alternatively install one of: "
                  "grim, gnome-screenshot, spectacle."),
                _("Screen ruler"), wx.OK | wx.ICON_WARNING, self.frame)
            return

        def _closed():
            self._screenRuler = None
            # Salva la tolleranza eventualmente cambiata nella barra
            if pref is not None and hasattr(pref, 'SaveRulerTolerance'):
                try:
                    pref.SaveRulerTolerance()
                except Exception:
                    pass

        def _toleranceChanged(value):
            if pref is not None:
                pref.rulerTolerance = value

        pref = getattr(self, 'pref', None)
        modeIcons = getattr(pref, 'rulerModeButtons', 'icons') != 'text'
        noDpi = getattr(pref, 'rulerIconsNoDpiScale', True)
        optList = getattr(pref, 'rulerOptionsLayout', 'inline') == 'list'
        self._screenRuler = ScreenRulerOverlay(self.frame, img, rect, onClose=_closed,
                                               fullImage=full, modeIcons=modeIcons,
                                               iconsNoDpiScale=noDpi,
                                               optionsList=optList,
                                               tolerance=getattr(pref, 'rulerTolerance', _DEFAULT_TOLERANCE),
                                               showTolerance=getattr(pref, 'rulerShowTolerance', True),
                                               onToleranceChanged=_toleranceChanged)
        self._screenRuler.Start()


# ---------------------------------------------------------------------------
# Esecuzione autonoma (test): python3 ScreenRuler.py
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app = wx.App(False)
    r = _virtual_screen_rect()
    im, full = capture_screen_ex(r)
    if im is None:
        print("Cattura dello schermo non riuscita")
    else:
        ov = ScreenRulerOverlay(None, im, r, onClose=app.ExitMainLoop,
                                fullImage=full)
        ov.Start()
        app.MainLoop()
