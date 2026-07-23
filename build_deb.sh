#!/usr/bin/env bash
# =============================================================================
# build_deb.sh — Costruisce il pacchetto .deb per SongpressPlusPlus
#
# Uso:
#   chmod +x build_deb.sh
#   ./build_deb.sh
#
# Prerequisiti sul sistema:
#   - Python >= 3.12
#   - pip, venv
#   - dpkg-deb  (pacchetto dpkg, già presente su ogni Debian/Ubuntu)
#   - fakeroot  (facoltativo ma raccomandato per creare il .deb senza root)
#
# Lo script:
#   1. Legge versione e nome dal pyproject.toml presente nella stessa cartella
#   2. Costruisce la wheel con pip/hatchling
#   3. Crea l'albero di directory DEBIAN-compliant
#   4. Installa la wheel nell'albero con pip --prefix
#   5. Crea wrapper GDK_BACKEND=x11 e symlink minuscolo
#   6. Scrive il file DEBIAN/control
#   7. Chiama fakeroot dpkg-deb per produrre il .deb finale
# =============================================================================

set -euo pipefail

# ── Marcatore di stato: "V" verde ─────────────────────────────────────────────
# Se stdout è un terminale usa il colore ANSI, altrimenti solo il carattere.
if [[ -t 1 ]]; then
    OK=$'\e[1;32m✔\e[0m'
else
    OK='✔'
fi

# ── Configurazione ────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# FIX 1: tutto il resto dello script (lettura di pyproject.toml, find su
# src/songpressplusplus nelle patch) usa percorsi RELATIVI. Senza questo cd
# lo script funziona solo se lanciato dalla propria cartella: da altrove le
# patch non trovano nulla e produrrebbero un .deb non corretto, in silenzio.
cd "$SCRIPT_DIR"

# ── Helper ImageMagick ────────────────────────────────────────────────────────
# FIX 6: su ImageMagick 7 (Debian 13/trixie in poi) il comando "convert" non
# esiste più: si usa "magick". Qui rileviamo una volta sola quale è presente.
if command -v magick &>/dev/null; then
    IM() { magick "$@"; }
    HAVE_IM=1
elif command -v convert &>/dev/null; then
    IM() { convert "$@"; }
    HAVE_IM=1
else
    IM() { return 1; }
    HAVE_IM=0
fi

# Legge versione e nome da pyproject.toml
PKG_NAME=$(python3 - <<'PY'
import tomllib
with open("pyproject.toml", "rb") as f:
    d = tomllib.load(f)
print(d["project"]["name"])
PY
)
PKG_VERSION=$(python3 - <<'PY'
import tomllib
with open("pyproject.toml", "rb") as f:
    d = tomllib.load(f)
print(d["project"]["version"])
PY
)

# Nome del pacchetto deb: tutto minuscolo, trattini al posto di trattini bassi
DEB_NAME=$(echo "$PKG_NAME" | tr '[:upper:]' '[:lower:]' | tr '_' '-')
DEB_VERSION="$PKG_VERSION"
DEB_ARCH="all"
# NB: il campo Maintainer DEVE essere nel formato "Nome <email>",
#     altrimenti Discover/GDebi mostrano "Autore sconosciuto".
#     Cambia l'email se ne hai una tua; questa noreply di GitHub è valida.
MAINTAINER="Denisov21 <Denisov21@users.noreply.github.com>"
AUTHOR_NAME="Denisov21"
# Licenza in formato SPDX (mostrata da Discover al posto di "Sconosciuta").
LICENSE="GPL-2.0-only"
DESCRIPTION="Songpress++ is a free, easy-to-use song typesetting program
 that generates high-quality songbooks (PDF, PPTX)."
HOMEPAGE="https://github.com/Denisov21/Songpressplusplus"

# Dipendenze runtime disponibili come pacchetti Debian/Ubuntu.
# python3-pip serve al postinst per installare le dipendenze solo-PyPI.
# xdg-utils fornisce xdg-open, usato per aprire la cartella dei template
# (e in generale cartelle/file) con il gestore file predefinito del desktop.
DEPENDS="python3 (>= 3.12), python3-pip, python3-wxgtk4.0 | python3-wxpython4, \
python3-requests, python3-reportlab, python3-markdown, python3-mistune, \
python3-pypdf, xdg-utils"

# Dipendenze consigliate (installate da apt di default, ma non obbligatorie):
#   - wl-clipboard  → fornisce wl-copy, usato per copiare l'immagine dello
#                     spartito negli appunti su sessioni Wayland (la clipboard
#                     immagine di wxGTK su Wayland registra solo testo).
#     Su X11 non serve. Se manca, l'app avvisa come installarlo.
RECOMMENDS="wl-clipboard"

# Dipendenze che NON esistono nei repo Debian: si installano via pip nel postinst.
# Formato: "nome_pip:nome_modulo_import" (uno per riga).
#   - python-pptx  → modulo "pptx"       (necessario su Linux)
#   - pyshortcuts  → modulo "pyshortcuts"
# NB: pywin32 è escluso di proposito, è solo per Windows.
PIP_DEPS="python-pptx:pptx
pyshortcuts:pyshortcuts"

# Cartelle di lavoro
BUILD_DIR="$SCRIPT_DIR/build_deb"
PKG_ROOT="$BUILD_DIR/${DEB_NAME}_${DEB_VERSION}"
INSTALL_PREFIX="$PKG_ROOT/usr"

# ── Pulizia precedente build ──────────────────────────────────────────────────
echo "$OK Pulizia build precedente..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

PYTHON="${VIRTUAL_ENV:+$VIRTUAL_ENV/bin/python3}"
PYTHON="${PYTHON:-python3}"

# ── 1b. Patch SongpressFrame.py: SetForegroundColour nella finestra About ────
echo "$OK Patch SetForegroundColour finestra About..."
"$PYTHON" - <<'PATCH'
import re, sys

path = None
import subprocess
result = subprocess.run(
    ["find", "src/songpressplusplus", "-name", "SongpressFrame.py"],
    capture_output=True, text=True
)
candidates = result.stdout.strip().splitlines()
if candidates:
    path = candidates[0]

if not path:
    print("    SongpressFrame.py non trovato, skip patch.")
    sys.exit(0)

with open(path, "r") as f:
    content = f.read()

fixes = [
    (
        '            title_lbl.SetFont(font_title)\n            hbox_title.Add(title_lbl, 0, wx.ALIGN_CENTER_VERTICAL)',
        '            title_lbl.SetFont(font_title)\n            title_lbl.SetForegroundColour(wx.BLACK)\n            hbox_title.Add(title_lbl, 0, wx.ALIGN_CENTER_VERTICAL)'
    ),
    (
        '        except Exception:\n            title_lbl = wx.StaticText(panel, label=u"Songpress++ - The Song Editor {}".format(glb.VERSION))\n            vbox.Add(title_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 10)',
        '        except Exception:\n            title_lbl = wx.StaticText(panel, label=u"Songpress++ - The Song Editor {}".format(glb.VERSION))\n            title_lbl.SetForegroundColour(wx.BLACK)\n            vbox.Add(title_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 10)'
    ),
    (
        '        def add_text(text):\n            lbl = wx.StaticText(panel, label=text)\n            vbox.Add(lbl, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 15)',
        '        def add_text(text):\n            lbl = wx.StaticText(panel, label=text)\n            lbl.SetForegroundColour(wx.BLACK)\n            vbox.Add(lbl, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 15)'
    ),
]

count = sum(1 for old, new in fixes if old in content)
for old, new in fixes:
    content = content.replace(old, new)

with open(path, "w") as f:
    f.write(content)
print(f"    Patch applicata: {count}/3 fix in {path}")
PATCH

# ── 1e. Patch SongpressFrame.py: Statistiche brano tema scuro ────────────────
echo "$OK Patch Statistiche brano (BG sistema, stelle+verdetto, testo tema scuro)..."
"$PYTHON" - <<'PATCH_STATS'
import re, subprocess, sys

result = subprocess.run(
    ["find", "src/songpressplusplus", "-name", "SongpressFrame.py"],
    capture_output=True, text=True
)
candidates = result.stdout.strip().splitlines()
if not candidates:
    print("    SongpressFrame.py non trovato, skip patch.")
    sys.exit(0)

path = candidates[0]
with open(path, encoding='utf-8') as f:
    content = f.read()

FG = "wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)"
fixes = []

# 1. BG hardcoded → colore di sistema
fixes.append((
    'BG      = wx.Colour(250, 250, 252)',
    'BG      = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)'
))

# 2. eval_panel caso multi-tab → sizer diretto su page, senza pannello bianco
fixes.append((
    "                    eval_panel = wx.Panel(page)\n"
    "                    eval_panel.SetBackgroundColour(wx.Colour(240, 245, 255))\n"
    "                    eval_sz = wx.BoxSizer(wx.HORIZONTAL)\n"
    "                    lbl_stars = wx.StaticText(eval_panel, label=st['stars'])\n"
    "                    f_s = lbl_stars.GetFont()\n"
    "                    f_s.SetPointSize(f_s.GetPointSize() + 6)\n"
    "                    lbl_stars.SetFont(f_s)\n"
    "                    lbl_stars.SetForegroundColour(STAR_ON)\n"
    "                    lbl_verdict = wx.StaticText(eval_panel, label='  ' + st['verdict'])\n"
    "                    f_v = lbl_verdict.GetFont()\n"
    "                    f_v.SetWeight(wx.FONTWEIGHT_BOLD)\n"
    "                    lbl_verdict.SetFont(f_v)\n"
    "                    eval_sz.Add(lbl_stars,   0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)\n"
    "                    eval_sz.Add(lbl_verdict, 0, wx.ALIGN_CENTER_VERTICAL)\n"
    "                    eval_panel.SetSizer(eval_sz)\n"
    "                    body.Add(eval_panel, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 6)",
    "                    _eval_sz = wx.BoxSizer(wx.HORIZONTAL)\n"
    "                    _lbl_stars = wx.StaticText(page, label=st['stars'])\n"
    "                    _fs = _lbl_stars.GetFont()\n"
    "                    _fs.SetPointSize(_fs.GetPointSize() + 6)\n"
    "                    _lbl_stars.SetFont(_fs)\n"
    "                    _lbl_stars.SetForegroundColour(STAR_ON)\n"
    "                    _lbl_verdict = wx.StaticText(page, label='  ' + st['verdict'])\n"
    "                    _fv = _lbl_verdict.GetFont()\n"
    "                    _fv.SetWeight(wx.FONTWEIGHT_BOLD)\n"
    "                    _lbl_verdict.SetFont(_fv)\n"
    f"                    _lbl_verdict.SetForegroundColour({FG})\n"
    "                    _eval_sz.Add(_lbl_stars,   0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)\n"
    "                    _eval_sz.Add(_lbl_verdict, 0, wx.ALIGN_CENTER_VERTICAL)\n"
    "                    body.Add(_eval_sz, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 6)"
))

# 3. eval_panel caso singolo brano → sizer diretto su scroll
fixes.append((
    "            eval_panel = wx.Panel(scroll)\n"
    "            eval_panel.SetBackgroundColour(wx.Colour(240, 245, 255))\n"
    "            eval_sz = wx.BoxSizer(wx.HORIZONTAL)\n"
    "            lbl_stars = wx.StaticText(eval_panel, label=st['stars'])\n"
    "            f_s = lbl_stars.GetFont()\n"
    "            f_s.SetPointSize(f_s.GetPointSize() + 6)\n"
    "            lbl_stars.SetFont(f_s)\n"
    "            lbl_stars.SetForegroundColour(STAR_ON)\n"
    "            lbl_verdict = wx.StaticText(eval_panel, label='  ' + st['verdict'])\n"
    "            f_v = lbl_verdict.GetFont()\n"
    "            f_v.SetWeight(wx.FONTWEIGHT_BOLD)\n"
    "            lbl_verdict.SetFont(f_v)\n"
    "            eval_sz.Add(lbl_stars,   0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)\n"
    "            eval_sz.Add(lbl_verdict, 0, wx.ALIGN_CENTER_VERTICAL)\n"
    "            eval_panel.SetSizer(eval_sz)\n"
    "            body.Add(eval_panel, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 6)",
    "            _eval_sz = wx.BoxSizer(wx.HORIZONTAL)\n"
    "            _lbl_stars = wx.StaticText(scroll, label=st['stars'])\n"
    "            _fs = _lbl_stars.GetFont()\n"
    "            _fs.SetPointSize(_fs.GetPointSize() + 6)\n"
    "            _lbl_stars.SetFont(_fs)\n"
    "            _lbl_stars.SetForegroundColour(STAR_ON)\n"
    "            _lbl_verdict = wx.StaticText(scroll, label='  ' + st['verdict'])\n"
    "            _fv = _lbl_verdict.GetFont()\n"
    "            _fv.SetWeight(wx.FONTWEIGHT_BOLD)\n"
    "            _lbl_verdict.SetFont(_fv)\n"
    f"            _lbl_verdict.SetForegroundColour({FG})\n"
    "            _eval_sz.Add(_lbl_stars,   0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)\n"
    "            _eval_sz.Add(_lbl_verdict, 0, wx.ALIGN_CENTER_VERTICAL)\n"
    "            body.Add(_eval_sz, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 6)"
))

# 4. Testo _row multi-tab → SYS_COLOUR_WINDOWTEXT
fixes.append((
    "                    k_lbl = wx.StaticText(_page, label=key)\n"
    "                    v_lbl = wx.StaticText(_page, label=str(value))",
    "                    k_lbl = wx.StaticText(_page, label=key)\n"
    f"                    k_lbl.SetForegroundColour({FG})\n"
    "                    v_lbl = wx.StaticText(_page, label=str(value))\n"
    f"                    v_lbl.SetForegroundColour({FG})"
))

# 5. Testo _row singolo brano → SYS_COLOUR_WINDOWTEXT
fixes.append((
    "            k_lbl = wx.StaticText(scroll, label=key)\n"
    "            v_lbl = wx.StaticText(scroll, label=str(value))",
    "            k_lbl = wx.StaticText(scroll, label=key)\n"
    f"            k_lbl.SetForegroundColour({FG})\n"
    "            v_lbl = wx.StaticText(scroll, label=str(value))\n"
    f"            v_lbl.SetForegroundColour({FG})"
))

# 6. Rimuovi gauge rimasti
lines = content.splitlines(keepends=True)
lines = [l for l in lines if not re.search(
    r'gauge\s*=\s*wx\.Gauge|gauge\.SetValue|body\.Add\(gauge', l)]
content = ''.join(lines)

count = sum(1 for old, _ in fixes if old in content)
for old, new in fixes:
    content = content.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"    Patch 1e: {count}/{len(fixes)} fix applicati in {path}")
PATCH_STATS

# ── 1c. Patch PreferencesDialog.py: disabilita pulsanti assoc su Linux ───────
echo "$OK Patch pulsanti associazione file (Linux)..."
"$PYTHON" - <<'PATCH2'
import subprocess, sys

result = subprocess.run(
    ["find", "src/songpressplusplus", "-name", "PreferencesDialog.py"],
    capture_output=True, text=True
)
candidates = result.stdout.strip().splitlines()
if not candidates:
    print("    PreferencesDialog.py non trovato, skip patch.")
    sys.exit(0)

path = candidates[0]
with open(path, "r") as f:
    content = f.read()

fixes = [
    (
        '            btnAssocAll.Bind(wx.EVT_BUTTON, self.OnAssociateAll)\n            btnUnassocAll.Bind(wx.EVT_BUTTON, self.OnUnassociateAll)\n            self._btnAssocAll   = btnAssocAll\n            self._btnUnassocAll = btnUnassocAll',
        '            btnAssocAll.Bind(wx.EVT_BUTTON, self.OnAssociateAll)\n            btnUnassocAll.Bind(wx.EVT_BUTTON, self.OnUnassociateAll)\n            self._btnAssocAll   = btnAssocAll\n            self._btnUnassocAll = btnUnassocAll\n            import platform as _pl\n            if _pl.system() == \'Linux\':\n                btnAssocAll.Disable()\n                btnUnassocAll.Disable()'
    ),
    (
        '            btnApply.Bind(wx.EVT_BUTTON, self.OnApplyFileAssoc)\n            self._btnApplyFileAssoc = btnApply',
        '            btnApply.Bind(wx.EVT_BUTTON, self.OnApplyFileAssoc)\n            self._btnApplyFileAssoc = btnApply\n            import platform as _pl2\n            if _pl2.system() == \'Linux\':\n                btnApply.Disable()'
    ),
    (
        '            for ext in self._fileAssocExts:\n                cb = wx.CheckBox(self.fileAssocPanel, wx.ID_ANY, u"." + ext)\n                cb.SetToolTip(_(u"Associate the .%s file extension with Songpress++.") % ext)\n                self._fileAssocCBs[ext] = cb\n                bSizerFA.Add(cb, 0, wx.ALL, 4)',
        '            import platform as _plcb\n            for ext in self._fileAssocExts:\n                cb = wx.CheckBox(self.fileAssocPanel, wx.ID_ANY, u"." + ext)\n                cb.SetToolTip(_(u"Associate the .%s file extension with Songpress++.") % ext)\n                self._fileAssocCBs[ext] = cb\n                if _plcb.system() == \'Linux\':\n                    cb.Disable()\n                bSizerFA.Add(cb, 0, wx.ALL, 4)'
    ),
]

count = sum(1 for old, new in fixes if old in content)
for old, new in fixes:
    content = content.replace(old, new)

with open(path, "w") as f:
    f.write(content)
print(f"    Patch applicata: {count}/3 fix in {path}")
PATCH2

# ── 1d. Patch MyPreferencesDialog.py: IsOk() prima di Red()/Green()/Blue() ────
echo "$OK Patch crash colore selettore (IsOk)..."
"$PYTHON" - <<'PATCH3'
import subprocess, sys

result = subprocess.run(
    ["find", "src/songpressplusplus", "-name", "MyPreferencesDialog.py"],
    capture_output=True, text=True
)
candidates = result.stdout.strip().splitlines()
if not candidates:
    print("    MyPreferencesDialog.py non trovato, skip patch.")
    sys.exit(0)

path = candidates[0]
with open(path, "r") as f:
    content = f.read()

old = '''    def _colour_to_hex(self, colour):
        return '#{:02X}{:02X}{:02X}'.format(colour.Red(), colour.Green(), colour.Blue())'''

new = '''    def _colour_to_hex(self, colour):
        if not colour.IsOk():
            return '#FFFFFF'
        return '#{:02X}{:02X}{:02X}'.format(colour.Red(), colour.Green(), colour.Blue())'''

if old in content:
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print(f"    Patch applicata: 1/1 fix in {path}")
else:
    print(f"    Patch già presente o testo non trovato in {path}")
PATCH3

# ── 1f. Patch crash _mgr al cambio lingua / chiusura ─────────────────────────
echo "$OK Patch crash _mgr (cambio lingua / teardown)..."
"$PYTHON" - <<'PATCH1F'
import subprocess, sys

def find(name):
    r = subprocess.run(["find", "src/songpressplusplus", "-name", name],
                       capture_output=True, text=True)
    c = r.stdout.strip().splitlines()
    return c[0] if c else None

fr = find("SongpressFrame.py")
tb = find("SongpressToolbars.py")
if not fr or not tb:
    print("    File non trovati, skip patch 1f.")
    sys.exit(0)

with open(fr) as f: frc = f.read()
with open(tb) as f: tbc = f.read()

old_a = '''                    def _deferred_tb_update():
                        self._tb_layout_pending = False
                        if self.frame:
                            self._FinalizeToolbarLayout()'''
new_a = '''                    def _deferred_tb_update():
                        self._tb_layout_pending = False
                        # Durante la chiusura/riavvio l'AUI manager puo' essere
                        # gia' stato smontato (UnInit): _mgr non esiste piu'.
                        # self.frame resta "truthy" ma il layout non va toccato.
                        if (self.frame
                                and getattr(self, '_mgr', None) is not None
                                and not getattr(self, '_closing', False)):
                            self._FinalizeToolbarLayout()'''
old_b = '''    def OnClose(self, evt):
        if hasattr(self, '_lockKeysTimer') and self._lockKeysTimer.IsRunning():'''
new_b = '''    def OnClose(self, evt):
        self._closing = True
        if hasattr(self, '_lockKeysTimer') and self._lockKeysTimer.IsRunning():'''
old_c = '''        self._tb_finalizing = True
        try:
            for tb in (self.mainToolBar, self.formatToolBar,
                       self.insertToolBar, self.viewToolBar):
                tb.SetGripperVisible(False)'''
new_c = '''        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        self._tb_finalizing = True
        try:
            for tb in (self.mainToolBar, self.formatToolBar,
                       self.insertToolBar, self.viewToolBar):
                tb.SetGripperVisible(False)'''

count = 0
for old, new in ((old_a, new_a), (old_b, new_b)):
    if old in frc:
        frc = frc.replace(old, new); count += 1
if old_c in tbc:
    tbc = tbc.replace(old_c, new_c); count += 1

with open(fr, "w") as f: f.write(frc)
with open(tb, "w") as f: f.write(tbc)
print(f"    Patch 1f: {count}/3 fix applicati")
PATCH1F

# ── 1g. Patch warning "Cannot set locale" (i18n.py) ──────────────────────────
echo "$OK Patch warning locale mancante (i18n)..."
"$PYTHON" - <<'PATCH1G'
import subprocess, sys

r = subprocess.run(["find", "src/songpressplusplus", "-name", "i18n.py"],
                   capture_output=True, text=True)
c = r.stdout.strip().splitlines()
if not c:
    print("    i18n.py non trovato, skip patch 1g.")
    sys.exit(0)
path = c[0]

with open(path) as f:
    content = f.read()

old = '''def setLang(l):
    global current_language, mylocale, _
    current_language = l
    langid = wx.Locale.FindLanguageInfo(l).Language
    mylocale = wx.Locale(langid)
    localedir = os.path.join(glb.path, "locale")'''
new = '''def setLang(l):
    global current_language, mylocale, _
    current_language = l
    info = wx.Locale.FindLanguageInfo(l)
    langid = info.Language if info is not None else wx.LANGUAGE_DEFAULT

    # Su sistemi dove il locale C della lingua richiesta (es. en_US.UTF-8)
    # non e' stato generato con locale-gen, wx.Locale non riesce a chiamare
    # setlocale() ed emette un wxLogWarning che, col log target GUI di
    # default, compare come finestra "Cannot set locale to language ...".
    # La traduzione (cataloghi .mo) funziona comunque, perche' dipende dalla
    # lingua impostata in wx.Locale e non dal locale C: silenziamo quindi
    # solo quel warning durante la costruzione, senza perdere le traduzioni
    # ne' l'oggetto mylocale (usato da wx.GetLocale() altrove).
    _nolog = wx.LogNull()
    try:
        mylocale = wx.Locale(langid)
    finally:
        del _nolog

    localedir = os.path.join(glb.path, "locale")'''

if old in content:
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print(f"    Patch 1g: 1/1 fix applicato in {path}")
else:
    print(f"    Patch 1g già presente o testo non trovato in {path}")
PATCH1G

# ── 1h. Patch Gtk-CRITICAL sui menu: SetBitmap prima di Append ───────────────
# La doc di wxMenuItem è esplicita: SetBitmap() va chiamato PRIMA che la voce
# sia aggiunta al menu. Con l'ordine invertito wxGTK ha già creato un
# GtkMenuItem semplice e poi prova a trattarlo come GtkImageMenuItem:
#   Gtk-CRITICAL: gtk_image_menu_item_set_image: assertion
#                 'GTK_IS_IMAGE_MENU_ITEM (image_menu_item)' failed
#
# Trasformazione applicata (equivalente su tutte le piattaforme: le icone
# restano funzionanti su Windows):
#
#   item = menu.Append(id, testo, help)  →  item = wx.MenuItem(menu, id, testo, help)
#   item.SetBitmap(bmp)                     item.SetBitmap(bmp)
#                                           menu.Append(item)
#
# Le firme combaciano: wxMenu::Append(id, text, help, kind) e
# wxMenuItem(parentMenu, id, text, help, kind) differiscono solo per il menu
# in prima posizione, quindi gli argomenti si trasferiscono invariati.
echo "$OK Patch Gtk-CRITICAL menu (SetBitmap prima di Append)..."
"$PYTHON" - <<'PATCH1H'
import re, subprocess, sys

r = subprocess.run(["find", "src/songpressplusplus", "-name", "*.py"],
                   capture_output=True, text=True)
files = [f for f in r.stdout.strip().splitlines() if f]
if not files:
    print("    Nessun sorgente trovato, skip patch 1h.")
    sys.exit(0)

# Cattura la coppia di righe consecutive:
#     <ind><item> = <menu>.Append(<args>)
#     <ind><item>.SetBitmap(<bmp>)
PAT = re.compile(
    r'^(?P<ind>[ \t]*)(?P<item>[A-Za-z_][\w.]*)[ \t]*=[ \t]*'
    r'(?P<menu>[A-Za-z_][\w.]*)\.Append\((?P<args>[^\n]*)\)[ \t]*$\n'
    r'(?P=ind)(?P=item)\.SetBitmap\((?P<bmp>[^\n]*)\)[ \t]*$',
    re.MULTILINE)

def repl(m):
    d = m.groupdict()
    args = d['args'].strip()
    sep = ', ' if args else ''
    return (f"{d['ind']}{d['item']} = wx.MenuItem({d['menu']}{sep}{args})\n"
            f"{d['ind']}{d['item']}.SetBitmap({d['bmp']})\n"
            f"{d['ind']}{d['menu']}.Append({d['item']})")

total = 0
touched = []
notutf8 = []
for path in files:
    # I sorgenti del progetto non sono tutti UTF-8 (qualcuno è latin-1).
    # 'surrogateescape' mappa i byte non decodificabili su surrogati privati
    # e li riscrive identici in fase di encode: il round-trip è quindi
    # lossless per QUALSIASI byte, e i file estranei non vengono corrotti.
    try:
        with open(path, encoding='utf-8') as f:
            content = f.read()
        enc_errors = 'strict'
    except UnicodeDecodeError:
        with open(path, encoding='utf-8', errors='surrogateescape') as f:
            content = f.read()
        enc_errors = 'surrogateescape'
        notutf8.append(path)

    new, n = PAT.subn(repl, content)
    if n:
        with open(path, 'w', encoding='utf-8', errors=enc_errors) as f:
            f.write(new)
        total += n
        touched.append(f"{path} ({n})")

if notutf8:
    print(f"    Nota: {len(notutf8)} file non sono UTF-8 validi "
          f"(letti e riscritti byte-per-byte):")
    for p in notutf8:
        print(f"      - {p}")

if total:
    print(f"    Patch 1h: {total} riordini applicati")
    for t in touched:
        print(f"      - {t}")
else:
    # Non è un errore: o la patch è già stata applicata in una build
    # precedente, o le chiamate non usano la forma su due righe consecutive
    # (es. Append spezzato su più righe). In quel caso i Gtk-CRITICAL restano,
    # ma il wrapper li filtra e l'app funziona ugualmente.
    print("    Patch 1h: nessuna occorrenza (già applicata o forma diversa)")
PATCH1H

# ── 2. Build della wheel (DOPO le patch) ─────────────────────────────────────
echo "$OK Costruzione wheel con pip + hatchling..."
WHEEL_DIR="$BUILD_DIR/wheel"
mkdir -p "$WHEEL_DIR"

"$PYTHON" -m pip wheel \
    --no-deps \
    --wheel-dir "$WHEEL_DIR" \
    "$SCRIPT_DIR"

WHEEL_FILE=$(ls "$WHEEL_DIR"/*.whl | head -n1)
echo "    Wheel: $WHEEL_FILE"

# ── 3. Installazione nell'albero del pacchetto ────────────────────────────────
echo "$OK Installazione nell'albero del pacchetto..."
mkdir -p "$INSTALL_PREFIX/share/applications"
mkdir -p "$INSTALL_PREFIX/share/pixmaps"
mkdir -p "$INSTALL_PREFIX/share/mime/packages"

"$PYTHON" -m pip install \
    --no-deps \
    --ignore-installed \
    --prefix "$INSTALL_PREFIX" \
    --no-compile \
    "$WHEEL_FILE"

# ── 3a. Normalizzazione del layout Debian ────────────────────────────────────
# FIX 5: la Debian Policy vieta ai pacchetti di installare file sotto
# /usr/local (è riservata all'amministratore locale). Il pip di Debian però
# applica lo schema "posix_local" e, anche con --prefix, deposita tutto in
# <prefix>/local/... Qui riportiamo l'albero nella posizione corretta:
#
#   usr/local/lib/pythonX.Y/site-packages  →  usr/lib/python3/dist-packages
#   usr/local/bin                          →  usr/bin
#
# Nota: la destinazione è python3/dist-packages SENZA numero di versione.
# È l'unica directory di sistema realmente presente in sys.path su Debian
# (/usr/lib/python3.13/dist-packages NON lo è) e rende il pacchetto immune
# agli aggiornamenti di minor version di Python.
echo "$OK Normalizzazione layout (usr/local → usr, dist-packages)..."

DIST_PKG="$INSTALL_PREFIX/lib/python3/dist-packages"
PY_PKGS_SRC=$(find "$INSTALL_PREFIX" -maxdepth 6 -type d \
    \( -name "site-packages" -o -name "dist-packages" \) 2>/dev/null | head -n1 || true)

if [[ -n "$PY_PKGS_SRC" && "$PY_PKGS_SRC" != "$DIST_PKG" ]]; then
    mkdir -p "$DIST_PKG"
    (
        shopt -s dotglob nullglob
        mv "$PY_PKGS_SRC"/* "$DIST_PKG"/ 2>/dev/null || true
    )
    rm -rf "$PY_PKGS_SRC"
    # rimuove la cartella pythonX.Y ormai svuotata
    rmdir "$(dirname "$PY_PKGS_SRC")" 2>/dev/null || true
    echo "    Moduli Python → ${DIST_PKG#$PKG_ROOT}"
fi

# Tutto ciò che resta sotto usr/local (bin, share, ...) viene fuso in usr.
if [[ -d "$INSTALL_PREFIX/local" ]]; then
    ( cd "$INSTALL_PREFIX/local" && tar cf - . ) | ( cd "$INSTALL_PREFIX" && tar xf - )
    rm -rf "$INSTALL_PREFIX/local"
    echo "    usr/local fuso in usr e rimosso"
fi

# Controllo finale: nessun file deve più trovarsi sotto usr/local.
if [[ -d "$INSTALL_PREFIX/local" ]]; then
    echo "    [ATTENZIONE] usr/local ancora presente: lintian segnalerà un errore."
fi

# ── 3a-bis. Individuazione anticipata dell'eseguibile ────────────────────────
# FIX 3: il file .desktop (passo 4) deve puntare al percorso REALE del binario.
# Prima era cablato a /usr/local/bin: se pip cambiava schema, l'app partiva da
# terminale ma la voce di menu no. Ora il percorso viene rilevato qui, subito
# dopo l'installazione, e riusato sia nel .desktop sia nel wrapper (passo 6b).
REAL_BIN=$(find "$PKG_ROOT" -path "*/bin/SongpressPlusPlus" -not -name "*_bin" | head -n1 || true)
if [[ -n "$REAL_BIN" ]]; then
    BIN_DIR=$(dirname "$REAL_BIN")
    INSTALLED_BIN_DIR="${BIN_DIR#"$PKG_ROOT"}"      # es. /usr/bin
else
    BIN_DIR=""
    INSTALLED_BIN_DIR="/usr/bin"
    echo "    [ATTENZIONE] eseguibile non trovato: il .desktop userà /usr/bin."
fi
echo "    Eseguibile installato in: $INSTALLED_BIN_DIR"

# ── 3b. Verifica dei template ────────────────────────────────────────────────
# Globals.InitDataPath() popola la cartella dati utente (~/.Songpress++)
# copiando templates/local_dir/ dal pacchetto. Se la wheel non include quella
# cartella (hatchling la esclude se non è dichiarata in pyproject.toml, e
# git non versiona le directory vuote), l'utente si ritrova senza
# templates/songs e templates/slides: il menu "Nuovo da template" resta vuoto
# e l'esportazione PowerPoint fallisce.
echo "$OK Verifica dell'albero templates/ nel pacchetto..."
# Individua la cartella del pacchetto Python cercando Globals.py (robusto
# rispetto al nome effettivo del package: songpress / songpressplusplus / ...).
PKG_DIR=$(find "$INSTALL_PREFIX" -type f -name "Globals.py" -path "*dist-packages*" \
    -printf '%h\n' 2>/dev/null | head -n1)

# Sottocartelle di templates/ che devono esistere. Devono restare allineate a
# Globals.TEMPLATE_SUBDIRS e a MyPreferencesDialog._TEMPLATE_SUBDIRS: sono
# esattamente quelle che l'utente vede premendo "Apri cartella template".
TEMPLATE_SUBDIRS=(fonts local_dir slides songs themes)

if [[ -z "$PKG_DIR" ]]; then
    echo "  ⚠ Cartella del pacchetto non individuata: salto la verifica dei template."
else
    MISSING=0

    # Radice globale: è la metà "programma" letta da ListLocalGlobalDir().
    for SUB in "${TEMPLATE_SUBDIRS[@]}"; do
        if [[ -d "$PKG_DIR/templates/$SUB" ]]; then
            echo "  ✓ templates/$SUB"
        else
            echo "  ⚠ templates/$SUB MANCANTE nella wheel: la creo."
            MISSING=1
            mkdir -p "$PKG_DIR/templates/$SUB"
            # git non versiona le cartelle vuote e dpkg-deb non le preserva:
            # un file segnaposto garantisce che la cartella arrivi all'utente.
            cat > "$PKG_DIR/templates/$SUB/.keep" <<'KEEP'
# Placeholder: keeps this directory inside the package.
# Songpress++ needs the full templates/ tree (fonts, local_dir, slides,
# songs, themes). Safe to delete once the folder holds real files.
KEEP
        fi
    done

    # Scheletro copiato nella cartella dati utente (~/.Songpress++) al primo
    # avvio da Globals.InitDataPath(): deve contenere lo stesso albero.
    LOCAL_DIR="$PKG_DIR/templates/local_dir"
    for SUB in "${TEMPLATE_SUBDIRS[@]}"; do
        [[ "$SUB" == "local_dir" ]] && continue   # niente ricorsione
        if [[ ! -d "$LOCAL_DIR/templates/$SUB" ]]; then
            echo "  ⚠ templates/local_dir/templates/$SUB MANCANTE: la creo."
            MISSING=1
            mkdir -p "$LOCAL_DIR/templates/$SUB"
            cp "$PKG_DIR/templates/$SUB/.keep" \
               "$LOCAL_DIR/templates/$SUB/.keep" 2>/dev/null || true
        fi
    done

    if [[ "$MISSING" -eq 1 ]]; then
        echo "  → Le cartelle mancanti sono state create nel pacchetto, ma per"
        echo "    renderle permanenti dichiarale in pyproject.toml, es.:"
        echo "        [tool.hatch.build.targets.wheel.force-include]"
        echo "        \"src/songpressplusplus/templates\" = \"songpressplusplus/templates\""
    fi
fi

# ── 4. Desktop entry & icona ─────────────────────────────────────────────────
echo "$OK Creazione .desktop e icona..."

ICON_SRC="$SCRIPT_DIR/installer/songpressplusplus.ico"
ICON_PNG="$SCRIPT_DIR/installer/songpressplusplus.png"
if [[ -f "$ICON_PNG" ]]; then
    cp "$ICON_PNG" "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png"
elif [[ -f "$ICON_SRC" ]]; then
    if [[ "$HAVE_IM" -eq 1 ]]; then
        # Estrae solo il primo layer [0] dell'ico → PNG con nome corretto
        IM "${ICON_SRC}[0]" -resize 64x64 \
            "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png" 2>/dev/null || \
        IM "$ICON_SRC" -thumbnail 64x64 \
            "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png" 2>/dev/null || true
    fi
fi
# Fallback: se convert ha prodotto file numerati (nome-0.png, nome-1.png...)
# invece del file atteso (nome.png), usa il primo layer e rimuovi gli altri.
if [[ ! -f "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png" ]]; then
    # FIX 2: senza "|| true" il glob a vuoto fa fallire ls; con set -e +
    # pipefail l'assegnamento aborte lo script PRIMA di poter stampare
    # l'avviso "Nessuna icona trovata" più sotto.
    FIRST_LAYER=$(ls "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}-"*.png 2>/dev/null | sort | head -n1 || true)
    if [[ -n "$FIRST_LAYER" ]]; then
        cp "$FIRST_LAYER" "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png"
        echo "    Icona: usato layer $FIRST_LAYER"
    fi
fi
# Rimuove sempre i layer numerati residui
rm -f "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}-"*.png

# Installa icona nelle cartelle hicolor/mimetypes per KDE/GNOME
# (necessario perché KDE usa hicolor per le icone e Discover per la card).
# Se ImageMagick non c'è, si copia comunque il PNG (senza ridimensionare):
# meglio un'icona non ottimizzata che nessuna icona.
if [[ -f "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png" ]]; then
    for SIZE in 256 128 64 48; do
        mkdir -p "$INSTALL_PREFIX/share/icons/hicolor/${SIZE}x${SIZE}/apps"
        mkdir -p "$INSTALL_PREFIX/share/icons/hicolor/${SIZE}x${SIZE}/mimetypes"
        DST_APP="$INSTALL_PREFIX/share/icons/hicolor/${SIZE}x${SIZE}/apps/${DEB_NAME}.png"
        DST_MIME="$INSTALL_PREFIX/share/icons/hicolor/${SIZE}x${SIZE}/mimetypes/${DEB_NAME}.png"
        if [[ "$HAVE_IM" -eq 1 ]]; then
            IM "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png" \
                -resize "${SIZE}x${SIZE}" "$DST_APP" 2>/dev/null || \
                cp "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png" "$DST_APP"
        else
            cp "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png" "$DST_APP"
        fi
        cp "$DST_APP" "$DST_MIME" 2>/dev/null || true
    done
    echo "    Icone hicolor installate (256/128/64/48)"
else
    echo "    [ATTENZIONE] Nessuna icona trovata!"
    echo "                 Metti un PNG in: installer/songpressplusplus.png"
    echo "                 (oppure installer/songpressplusplus.ico + ImageMagick)."
    echo "                 Senza icona Discover mostrerà il segnaposto '...'."
fi

# File XML tipo MIME per estensioni ChordPro
cat > "$INSTALL_PREFIX/share/mime/packages/${DEB_NAME}.xml" <<'MIME'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="text/x-chordpro">
    <comment>ChordPro song file</comment>
    <comment xml:lang="it">File canzone ChordPro</comment>
    <glob pattern="*.crd"/>
    <glob pattern="*.cho"/>
    <glob pattern="*.chordpro"/>
    <glob pattern="*.chopro"/>
    <glob pattern="*.pro"/>
    <glob pattern="*.sng"/>
    <icon name="songpressplusplus"/>
  </mime-type>
</mime-info>
MIME

cat > "$INSTALL_PREFIX/share/applications/${DEB_NAME}.desktop" <<DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Songpress++
GenericName=Song Typesetter
Comment=Genera canzonieri di alta qualità in PDF e PPTX
Exec=env GDK_BACKEND=x11 ${INSTALLED_BIN_DIR}/SongpressPlusPlus %f
Icon=${DEB_NAME}
Terminal=false
Categories=Office;Publishing;Education;
Keywords=song;chords;songbook;pdf;
MimeType=text/x-chordpro;
StartupNotify=true
DESKTOP

# ── 4b. AppStream metainfo ───────────────────────────────────────────────────
# È ciò che Discover usa per la scheda del pacchetto: nome leggibile,
# icona, autore e licenza. Senza questo file mostra il nome del file
# (es. "songpressplusplus_7") e nessuna icona.
echo "$OK Creazione AppStream metainfo..."
mkdir -p "$INSTALL_PREFIX/share/metainfo"
cat > "$INSTALL_PREFIX/share/metainfo/${DEB_NAME}.metainfo.xml" <<METAINFO
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>${DEB_NAME}</id>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>${LICENSE}</project_license>
  <name>Songpress++</name>
  <developer id="io.github.denisov21">
    <name>${AUTHOR_NAME}</name>
  </developer>
  <developer_name>${AUTHOR_NAME}</developer_name>
  <summary>Song typesetting program that generates high-quality songbooks</summary>
  <description>
    <p>
      Songpress++ is a free, easy-to-use song typesetting program
      that generates high-quality songbooks in PDF and PPTX.
    </p>
  </description>
  <launchable type="desktop-id">${DEB_NAME}.desktop</launchable>
  <icon type="stock">${DEB_NAME}</icon>
  <icon type="local">/usr/share/pixmaps/${DEB_NAME}.png</icon>
  <url type="homepage">${HOMEPAGE}</url>
  <categories>
    <category>Office</category>
    <category>Publishing</category>
  </categories>
  <content_rating type="oars-1.1"/>
</component>
METAINFO

# ── 4. File DEBIAN/control ────────────────────────────────────────────────────
echo "$OK Scrittura DEBIAN/control..."
mkdir -p "$PKG_ROOT/DEBIAN"

INSTALLED_SIZE=$(du -sk "$INSTALL_PREFIX" | awk '{print $1}')

cat > "$PKG_ROOT/DEBIAN/control" <<CONTROL
Package: ${DEB_NAME}
Version: ${DEB_VERSION}
Architecture: ${DEB_ARCH}
Maintainer: ${MAINTAINER}
Installed-Size: ${INSTALLED_SIZE}
Depends: ${DEPENDS}
Recommends: ${RECOMMENDS}
Section: utils
Priority: optional
Homepage: ${HOMEPAGE}
Description: ${DESCRIPTION}
CONTROL

# ── 4c. File copyright (DEP-5) ───────────────────────────────────────────────
# Convenzione Debian: la licenza sta in /usr/share/doc/<pkg>/copyright.
echo "$OK Scrittura copyright (DEP-5)..."
DOC_DIR="$INSTALL_PREFIX/share/doc/${DEB_NAME}"
mkdir -p "$DOC_DIR"
cat > "$DOC_DIR/copyright" <<COPYRIGHT
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: Songpress++
Source: ${HOMEPAGE}

Files: *
Copyright: $(date +%Y) ${AUTHOR_NAME}
License: ${LICENSE}
COPYRIGHT

# ── 5. Script postinst / postrm ───────────────────────────────────────────────
# Parte 1 (heredoc NON quotato): inietta la lista PIP_DEPS da build_deb.sh.
cat > "$PKG_ROOT/DEBIAN/postinst" <<POSTINST_HEAD
#!/bin/sh
set -e
# Dipendenze solo-PyPI (nome_pip:modulo), iniettate da build_deb.sh.
PIP_DEPS="${PIP_DEPS}"
POSTINST_HEAD

# Parte 2 (heredoc quotato): logica eseguita sul sistema di destinazione.
cat >> "$PKG_ROOT/DEBIAN/postinst" <<'POSTINST_BODY'

# FIX 4: dpkg invoca il postinst anche con abort-upgrade, abort-remove e
# abort-deconfigure. Senza questa guardia, in tutti quei casi partivano
# comunque la domanda interattiva e il download via pip.
case "$1" in
    configure)
        ;;
    abort-upgrade|abort-remove|abort-deconfigure)
        exit 0
        ;;
    *)
        exit 0
        ;;
esac

if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database /usr/share/mime || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -qf /usr/share/icons/hicolor || true
fi

# ── Installa le dipendenze Python presenti solo su PyPI (non nei repo Debian) ──
# python-pptx e pyshortcuts non sono pacchettizzati in Debian: si installano
# via pip. pywin32 è escluso (solo Windows). Passo NON bloccante: se manca la
# rete, l'installazione del pacchetto riesce comunque.
PY=$(command -v python3 || true)

# ── Avviso interattivo ────────────────────────────────────────────────────────
# Chiede conferma prima di scaricare le dipendenze da PyPI.
# Se il terminale non è disponibile (installazione da Discover/GDebi, apt in
# modalità non interattiva, script automatici) NON blocca nulla: procede da solo.
SP_SKIP=0
if [ -n "$PY" ]; then
    SP_ANSWER="s"
    if [ "${DEBIAN_FRONTEND:-}" != "noninteractive" ] && [ -r /dev/tty ] && [ -w /dev/tty ]; then
        {
            echo ""
            echo "=================================================================="
            echo "  Songpress++ — È RICHIESTA UNA CONNESSIONE A INTERNET 🌐"
            echo ""
            echo "  Alcune dipendenze Python non esistono nei repository Debian"
            echo "  (python-pptx, pyshortcuts) e verranno scaricate ORA via pip."
            echo ""
            echo "  Se rispondi No il pacchetto viene installato lo stesso, ma"
            echo "  dovrai installare le dipendenze a mano in un secondo momento"
            echo "  e l'applicazione potrebbe non funzionare correttamente."
            echo "=================================================================="
            printf "🌐  Continuare e scaricare le dipendenze ora? [S/n] "
        } > /dev/tty
        read SP_ANSWER < /dev/tty || SP_ANSWER="s"
        echo "" > /dev/tty
    fi

    case "$SP_ANSWER" in
        [nN]*)
            SP_SKIP=1
            echo "Songpress++: download delle dipendenze saltato su richiesta dell'utente."
            echo "Songpress++: per installarle più tardi esegui:"
            echo "    sudo pip3 install --break-system-packages python-pptx pyshortcuts"
            ;;
    esac
fi

if [ -n "$PY" ] && [ "$SP_SKIP" -eq 0 ]; then
    echo "Songpress++: controllo dipendenze PyPI (richiede una connessione a Internet)..."
    # Debian 12+/13 marca l'ambiente come "externally managed" (PEP 668):
    # serve --break-system-packages per installare a livello di sistema.
    BSP=""
    if "$PY" -m pip install --help 2>/dev/null | grep -q -- --break-system-packages; then
        BSP="--break-system-packages"
    fi
    echo "$PIP_DEPS" | while IFS=: read PIP_NAME MOD_NAME; do
        [ -z "$PIP_NAME" ] && continue
        if "$PY" -c "import $MOD_NAME" >/dev/null 2>&1; then
            echo "Songpress++: dipendenza '$PIP_NAME' già presente."
        else
            echo "Songpress++: installo '$PIP_NAME' via pip..."
            "$PY" -m pip install $BSP --root-user-action=ignore --no-warn-script-location "$PIP_NAME" \
                || echo "Songpress++: [ATTENZIONE] non sono riuscito a installare '$PIP_NAME'. Fallo a mano con:  sudo pip3 install $BSP $PIP_NAME"
        fi
    done
fi
POSTINST_BODY
chmod 0755 "$PKG_ROOT/DEBIAN/postinst"

cat > "$PKG_ROOT/DEBIAN/postrm" <<'POSTRM'
#!/bin/sh
set -e

# FIX 8: il postinst aggiornava tre cache (desktop, MIME, icone) ma il postrm
# solo una. Dopo la disinstallazione restavano il tipo MIME text/x-chordpro
# associato a Songpress++ e l'icona nella cache hicolor: file .crd/.cho con
# icona fantasma e associazione a un programma non più presente.
case "$1" in
    remove|purge|upgrade|failed-upgrade|abort-install|abort-upgrade|disappear)
        ;;
    *)
        exit 0
        ;;
esac

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database /usr/share/mime || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -qf /usr/share/icons/hicolor || true
fi
POSTRM
chmod 0755 "$PKG_ROOT/DEBIAN/postrm"

# ── 5b. Script preinst: migrazione dal vecchio layout /usr/local ──────────────
# FIX 9: fino alla 7.0.1 il pacchetto installava sotto /usr/local. Aggiornando
# da una di quelle versioni, dpkg non riesce a rimuovere le vecchie directory
# ("impossibile eliminare la vecchia directory ...: Directory non vuota", per
# via dei __pycache__ generati a runtime) e i file obsoleti restano lì.
# È un guasto silenzioso e cattivo: /usr/local/bin precede /usr/bin nel PATH e
# /usr/local/lib/pythonX.Y/dist-packages precede /usr/lib/python3/dist-packages
# in sys.path, quindi l'app continuerebbe a caricare il CODICE VECCHIO pur
# sembrando aggiornata.
#
# Il preinst gira PRIMA dello scompattamento e ripulisce i residui, ma solo
# dopo aver verificato con dpkg-query che nessun pacchetto li rivendichi: si
# tocca esclusivamente ciò che è rimasto orfano.
echo "$OK Scrittura preinst (migrazione da /usr/local)..."
cat > "$PKG_ROOT/DEBIAN/preinst" <<'PREINST'
#!/bin/sh
set -e

case "$1" in
    install|upgrade)
        ;;
    *)
        exit 0
        ;;
esac

LEGACY_REMOVED=0

# Rimuove un percorso solo se NON appartiene ad alcun pacchetto installato.
# dpkg-query è un comando di sola lettura: non richiede il lock di dpkg e si
# puo' quindi invocare senza rischi da dentro un maintainer script.
remove_if_unowned() {
    target="$1"
    [ -e "$target" ] || return 0

    if owner=$(dpkg-query -S "$target" 2>/dev/null); then
        echo "Songpress++: '$target' appartiene a ${owner%%:*}: lo lascio intatto."
        return 0
    fi

    echo "Songpress++: rimuovo residuo del vecchio layout: $target"
    rm -rf "$target"
    LEGACY_REMOVED=1
}

# Eseguibili e wrapper della vecchia installazione.
for f in SongpressPlusPlus SongpressPlusPlus_bin songpressplusplus; do
    remove_if_unowned "/usr/local/bin/$f"
done

# Moduli Python: il glob copre qualsiasi minor version (python3.11, 3.13, ...)
# e sia il layout dist-packages sia site-packages.
for d in /usr/local/lib/python3*/dist-packages /usr/local/lib/python3*/site-packages; do
    [ -d "$d" ] || continue
    remove_if_unowned "$d/songpressplusplus"
    for info in "$d"/songpressplusplus-*.dist-info "$d"/songpressplusplus-*.egg-info; do
        [ -e "$info" ] || continue
        remove_if_unowned "$info"
    done
done

# Directory rimaste vuote: rmdir fallisce (correttamente) se contengono ancora
# qualcosa di altrui, quindi non c'e' modo di fare danni.
if [ "$LEGACY_REMOVED" = 1 ]; then
    for d in /usr/local/lib/python3*/dist-packages /usr/local/lib/python3*/site-packages; do
        rmdir "$d" 2>/dev/null || true
    done
    for d in /usr/local/lib/python3*; do
        rmdir "$d" 2>/dev/null || true
    done
    echo "Songpress++: migrazione da /usr/local completata."
    echo "Songpress++: i file ora vivono in /usr/lib/python3/dist-packages e /usr/bin."
fi

exit 0
PREINST
chmod 0755 "$PKG_ROOT/DEBIAN/preinst"

# ── 6. Permessi ───────────────────────────────────────────────────────────────
echo "$OK Impostazione permessi..."
find "$PKG_ROOT" -type d -exec chmod 0755 {} \;
find "$PKG_ROOT" -type f -exec chmod 0644 {} \;
# Rende eseguibili tutti i file in qualsiasi cartella bin/
find "$PKG_ROOT" -path "*/bin/*" -type f -exec chmod 0755 {} \;
chmod 0755 "$PKG_ROOT/DEBIAN/preinst"
chmod 0755 "$PKG_ROOT/DEBIAN/postinst"
chmod 0755 "$PKG_ROOT/DEBIAN/postrm"

# ── 6b. Wrapper GDK_BACKEND=x11 e symlink minuscolo ──────────────────────────
# Fatto DOPO il passo permessi per evitare che chmod 0644 azzeri il wrapper.
# I percorsi arrivano dal passo 3a-bis, dopo la normalizzazione in /usr.
echo "$OK Creazione wrapper GDK_BACKEND=x11..."
# REAL_BIN / BIN_DIR / INSTALLED_BIN_DIR sono già stati calcolati al passo 3a-bis
# (servivano al .desktop): qui li riusiamo, così i due percorsi non possono
# divergere. Rifacciamo solo il find se nel frattempo il file è sparito.
echo "    Binario trovato: ${REAL_BIN:-(nessuno)}"

if [[ -n "$REAL_BIN" && -f "$REAL_BIN" ]]; then
    mv "$REAL_BIN" "${REAL_BIN}_bin"

    # FIX 7 (rivisto): niente "2>/dev/null", che azzerava anche i traceback
    # Python e rendeva impossibile diagnosticare un crash all'avvio. Qui si
    # scartano SOLO tre righe note e innocue, elencate una per una; tutto il
    # resto — errori, eccezioni, warning nuovi — arriva intatto.
    #
    # Il filtro è una rete di sicurezza per i casi che la patch 1h non copre
    # (Append spezzato su più righe, chiamate generate a runtime): la
    # correzione vera resta nel sorgente.
    #
    # Serve bash per la process substitution: è un pacchetto Essential, quindi
    # sempre presente. "exec" preserva il codice di uscita dell'applicazione,
    # che una pipeline normale avrebbe invece sostituito con quello di grep.
    cat > "$REAL_BIN" <<WRAPPER
#!/bin/bash
# Wrapper: forza backend X11 per compatibilità wxPython/Wayland
export GDK_BACKEND=x11

# SONGPRESS_VERBOSE=1 disattiva il filtro e mostra tutto (per il debug).
if [ -n "\${SONGPRESS_VERBOSE:-}" ]; then
    exec ${INSTALLED_BIN_DIR}/SongpressPlusPlus_bin "\$@"
fi

# Righe scartate, e perché:
#  1) gtk_image_menu_item_set_image  → icone nei menu: GtkImageMenuItem è
#     deprecato in GTK3 e "gtk-menu-images" è comunque off di default, quindi
#     l'icona non sarebbe mostrata in nessun caso.
#  2) invalid cast GtkMenuItem→GtkImageMenuItem → stessa causa, altro messaggio.
#  3) ScreenToClient ... toplevel window is not shown → log di livello Debug
#     di wx, emesso quando si chiedono coordinate prima di Show().
SPP_NOISE='gtk_image_menu_item_set_image'
SPP_NOISE="\$SPP_NOISE|invalid cast from .GtkMenuItem. to .GtkImageMenuItem."
SPP_NOISE="\$SPP_NOISE|ScreenToClient cannot work when toplevel window is not shown"

exec 2> >(grep --line-buffered -v -E "\$SPP_NOISE" >&2)
exec ${INSTALLED_BIN_DIR}/SongpressPlusPlus_bin "\$@"
WRAPPER
    chmod 0755 "$REAL_BIN"
    chmod 0755 "${REAL_BIN}_bin"
    echo "    Wrapper creato: $REAL_BIN → ${INSTALLED_BIN_DIR}/SongpressPlusPlus_bin"

    # Symlink minuscolo: songpressplusplus → SongpressPlusPlus
    # Nota: chmod su symlink non è supportato, il target eredita i permessi
    ln -sf "${INSTALLED_BIN_DIR}/SongpressPlusPlus" "$BIN_DIR/songpressplusplus" || true
    echo "    Symlink creato: $BIN_DIR/songpressplusplus"
else
    echo "    [ATTENZIONE] Binario non trovato. Struttura bin:"
    find "$PKG_ROOT" -name "bin" -type d -exec ls -la {} \; || true
fi

# ── 7. Costruzione del .deb ───────────────────────────────────────────────────
DEB_FILE="$BUILD_DIR/${DEB_NAME}_${DEB_VERSION}_${DEB_ARCH}.deb"
echo "$OK Costruzione del pacchetto .deb..."

if command -v fakeroot &>/dev/null; then
    fakeroot dpkg-deb --build "$PKG_ROOT" "$DEB_FILE"
else
    echo "    [ATTENZIONE] fakeroot non trovato."
    dpkg-deb --build "$PKG_ROOT" "$DEB_FILE"
fi

echo ""
echo "✅  Pacchetto creato: $DEB_FILE"
echo ""
echo "📦  Per installarlo:"
echo "   sudo dpkg -i \"$DEB_FILE\""
echo "   sudo apt-get install -f"
echo ""
echo "🌐  NOTA: l'installazione richiede una connessione a Internet."
echo "    Durante il postinst vengono scaricate via pip le dipendenze non"
echo "    presenti nei repository Debian (python-pptx, pyshortcuts) e via apt"
echo "    quelle di sistema mancanti. Senza rete l'app potrebbe non partire."
